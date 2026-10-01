/*
 * throttle_logic.c — Lógica pura del acelerador de P1 (C99). Ver throttle_logic.h.
 *
 * Convenciones:
 *   - "pos"    = posición del puño normalizada [-1, 1] (antes de la zona muerta).
 *   - "target" = objetivo tras zona muerta, expo y límite de marcha atrás.
 *   - "out"    = comando final tras dwell de inversión y rampa (lo que se manda al VESC).
 *   - Toda transición a neutro por seguridad (kill, seta, sensor, watchdog) es INMEDIATA
 *     (sin rampa) y ocurre en el mismo tick en que se detecta.
 *
 * Etiquetas de los valores por defecto: [VERIFICADO: fuente] · [CALCULADO] · [ESTIMADO: base] · [SUPUESTO].
 */
#include "throttle_logic.h"

#define TL_SAT_MS 60000u /* saturación de contadores de tiempo (evita desborde) */

/* ------------------------------------------------------------------ utilidades */
static float tl_absf(float x) { return (x < 0.0f) ? -x : x; }

static float tl_clampf(float x, float lo, float hi)
{
    if (!(x == x)) { /* NaN -> valor seguro */
        return 0.0f;
    }
    if (x < lo) { return lo; }
    if (x > hi) { return hi; }
    return x;
}

static int8_t tl_signf(float x) { return (x > 0.0f) ? (int8_t)1 : ((x < 0.0f) ? (int8_t)-1 : (int8_t)0); }

static uint32_t tl_sat_add(uint32_t a, uint32_t b)
{
    uint32_t r = a + b;
    if (r < a || r > TL_SAT_MS) { r = TL_SAT_MS; }
    return r;
}

static uint16_t tl_absdiff_u16(uint16_t a, uint16_t b) { return (a > b) ? (uint16_t)(a - b) : (uint16_t)(b - a); }

/* ------------------------------------------------------------------ configuración */
void tl_default_config(tl_config_t *c)
{
    c->deadband = 0.08f;          /* [SUPUESTO: ±8 % de la semicarrera (pedido de diseño); ajustar en T0]          */
    c->expo = 0.0f;               /* [SUPUESTO: lineal; la rampa ya suaviza. 0,3 si el puño resulta "nervioso"]   */
    c->reverse_limit = 0.5f;      /* [SUPUESTO: = inputs.yaml motor.reverse_current_frac (0,5)]                  */
    c->jump_travel_per_s = 25.0f; /* [SUPUESTO: el puño no recorre tope a tope en < 40 ms; validar en T0.9]       */
    /* Calibración provisoria [ESTIMADO: hall lineal tipo SS49E ~2,5 V en reposo, ±1,2 V a ±30°; NO verificado].
     * cal_valid = 0: el sistema NO arma hasta calibrar con el puño real (T0.5). */
    c->adc_rev = TL_MV_TO_ADC(1300u);
    c->adc_center = TL_MV_TO_ADC(2500u);
    c->adc_fwd = TL_MV_TO_ADC(3700u);
    c->adc_fault_low = TL_MV_TO_ADC(300u);   /* [SUPUESTO: ~0,3 V (pedido de diseño)] = 61 cuentas  */
    c->adc_fault_high = TL_MV_TO_ADC(4700u); /* [SUPUESTO: ~4,7 V (pedido de diseño)] = 962 cuentas */
    c->min_half_span = TL_MV_TO_ADC(500u);   /* [SUPUESTO: semicarrera >= 0,5 V -> >= 102 cuentas de resolución] */
    c->jump_noise_counts = 12u;              /* [ESTIMADO: ruido hall+ADC tras promediar 4 muestras ~±5 cuentas, ×2] */
    c->arm_hold_ms = 1000u;  /* [SUPUESTO: >= 1 s en cero para armar (pedido de diseño)]                     */
    c->ramp_up_ms = 1000u;   /* [SUPUESTO: 0->100 % en >= 1 s (pedido de diseño; R06 §2.6 sugiere ~1 s)]     */
    c->ramp_down_ms = 250u;  /* [SUPUESTO: bajada rápida 100->0 % en 0,25 s; los cortes de seguridad son inmediatos] */
    c->dwell_ms = 500u;      /* [SUPUESTO: >= 0,5 s en cero antes de invertir (pedido de diseño; correa HTD)]  */
    c->watchdog_ms = 100u;   /* [SUPUESTO: tick nominal 10 ms; > 100 ms sin tick = lazo colgado]              */
    c->ppm_min_us = 1000u;   /* [VERIFICADO: VESC appconf_default.h APPCONF_PPM_PULSE_START 1,0 ms]           */
    c->ppm_center_us = 1500u;/* [VERIFICADO: APPCONF_PPM_PULSE_CENTER 1,5 ms]                                  */
    c->ppm_max_us = 2000u;   /* [VERIFICADO: APPCONF_PPM_PULSE_END 2,0 ms]                                     */
    c->cal_valid = 0u;
    c->use_vesc_ok = 0u;     /* [SUPUESTO: sin telemetría UART en P1; hook para P2]                           */
}

uint8_t tl_config_check(const tl_config_t *c)
{
    uint8_t e = TL_CFG_OK;
    int32_t dr = (int32_t)c->adc_center - (int32_t)c->adc_rev;  /* >0 si rev está por debajo del centro */
    int32_t df = (int32_t)c->adc_fwd - (int32_t)c->adc_center;  /* >0 si fwd está por encima del centro */
    int32_t adr = (dr < 0) ? -dr : dr;
    int32_t adf = (df < 0) ? -df : df;

    if (!((dr > 0 && df > 0) || (dr < 0 && df < 0))) { e |= TL_CFG_ERR_ORDER; }
    if (adr < (int32_t)c->min_half_span || adf < (int32_t)c->min_half_span) { e |= TL_CFG_ERR_SPAN; }
    if (c->adc_fault_high > TL_ADC_MAX || c->adc_fault_low >= c->adc_fault_high) { e |= TL_CFG_ERR_RANGE; }
    /* Los tres puntos deben quedar dentro de la banda válida (si no, un tope se confundiría con una falla). */
    if (c->adc_rev <= c->adc_fault_low || c->adc_rev >= c->adc_fault_high ||
        c->adc_center <= c->adc_fault_low || c->adc_center >= c->adc_fault_high ||
        c->adc_fwd <= c->adc_fault_low || c->adc_fwd >= c->adc_fault_high) {
        e |= TL_CFG_ERR_RANGE;
    }
    /* Parámetros (las comparaciones fallan con NaN -> error). */
    if (!(c->deadband >= 0.0f && c->deadband <= 0.5f)) { e |= TL_CFG_ERR_PARAM; }
    if (!(c->expo >= 0.0f && c->expo <= 1.0f)) { e |= TL_CFG_ERR_PARAM; }
    if (!(c->reverse_limit >= 0.0f && c->reverse_limit <= 1.0f)) { e |= TL_CFG_ERR_PARAM; }
    if (!(c->jump_travel_per_s > 0.0f && c->jump_travel_per_s < 1000.0f)) { e |= TL_CFG_ERR_PARAM; }
    if (c->arm_hold_ms == 0u || c->ramp_up_ms == 0u || c->watchdog_ms == 0u) { e |= TL_CFG_ERR_PARAM; }
    if (!(c->ppm_min_us < c->ppm_center_us && c->ppm_center_us < c->ppm_max_us &&
          c->ppm_min_us >= 800u && c->ppm_max_us <= 2200u)) {
        e |= TL_CFG_ERR_PPM;
    }
    return e;
}

uint8_t tl_calibrate(tl_config_t *cfg, uint16_t adc_rev, uint16_t adc_center, uint16_t adc_fwd)
{
    tl_config_t tmp = *cfg;
    uint8_t e;
    tmp.adc_rev = adc_rev;
    tmp.adc_center = adc_center;
    tmp.adc_fwd = adc_fwd;
    e = tl_config_check(&tmp);
    if (e == TL_CFG_OK) {
        tmp.cal_valid = 1u;
        *cfg = tmp;
    }
    return e; /* si falla, cfg queda intacta */
}

/* ------------------------------------------------------------------ funciones puras */
float tl_position(const tl_config_t *c, uint16_t adc)
{
    float d = (float)adc - (float)c->adc_center;
    float hf = (float)c->adc_fwd - (float)c->adc_center; /* semicarrera de avance (con signo)  */
    float hr = (float)c->adc_rev - (float)c->adc_center; /* semicarrera de reversa (con signo) */
    float p;
    if (hf == 0.0f || hr == 0.0f) {
        return 0.0f;
    }
    if (d * hf >= 0.0f) {
        p = d / hf;      /* lado de avance: adc = fwd -> +1 */
    } else {
        p = -(d / hr);   /* lado de reversa: adc = rev -> -1 */
    }
    return tl_clampf(p, -1.0f, 1.0f);
}

float tl_shape(const tl_config_t *c, float pos)
{
    float a = tl_absf(pos);
    float y;
    if (!(pos == pos) || a <= c->deadband) {
        return 0.0f; /* dentro de la zona muerta (borde incluido) o NaN */
    }
    /* Re-escalado continuo: el borde de la zona muerta da 0 y el tope da 1. */
    y = (a - c->deadband) / (1.0f - c->deadband);
    y = tl_clampf(y, 0.0f, 1.0f);
    y = (1.0f - c->expo) * y + c->expo * y * y * y;
    if (pos < 0.0f) {
        y = -y * c->reverse_limit; /* marcha atrás escalada: tope atrás = -reverse_limit */
    }
    return y;
}

uint16_t tl_cmd_to_ppm(const tl_config_t *c, float cmd)
{
    float us;
    cmd = tl_clampf(cmd, -1.0f, 1.0f);
    if (cmd >= 0.0f) {
        us = (float)c->ppm_center_us + cmd * (float)(c->ppm_max_us - c->ppm_center_us);
    } else {
        us = (float)c->ppm_center_us + cmd * (float)(c->ppm_center_us - c->ppm_min_us);
    }
    if (us < (float)c->ppm_min_us) { us = (float)c->ppm_min_us; }
    if (us > (float)c->ppm_max_us) { us = (float)c->ppm_max_us; }
    return (uint16_t)(us + 0.5f);
}

const char *tl_state_name(uint8_t state)
{
    switch (state) {
    case TL_DISARMED:   return "DISARMED";
    case TL_ARMED:      return "ARMED";
    case TL_RUN_FWD:    return "RUN_FWD";
    case TL_RUN_REV:    return "RUN_REV";
    case TL_DWELL_ZERO: return "DWELL_ZERO";
    case TL_FAULT:      return "FAULT";
    default:            return "?";
    }
}

uint16_t tl_sizeof_config(void) { return (uint16_t)sizeof(tl_config_t); }
uint16_t tl_sizeof_inputs(void) { return (uint16_t)sizeof(tl_inputs_t); }
uint16_t tl_sizeof_outputs(void) { return (uint16_t)sizeof(tl_outputs_t); }
uint16_t tl_sizeof_ctx(void) { return (uint16_t)sizeof(tl_ctx_t); }

/* ------------------------------------------------------------------ máquina de estados */
static void tl_disarm(tl_ctx_t *s)
{
    s->armed = 0u;
    s->out = 0.0f;       /* neutro inmediato, sin rampa */
    s->arm_ms = 0u;
    s->arm_run = 0u;
    s->zero_ms = 0u;
    s->zero_run = 0u;
    s->last_dir = 0;
}

void tl_init(tl_ctx_t *s, const tl_config_t *cfg)
{
    s->cfg = *cfg;
    s->cfg_err = tl_config_check(cfg);
    s->uptime_ms = 0u;
    s->latched = 0u;
    s->prev_adc = 0u;
    s->prev_valid = 0u;
    s->_pad[0] = 0u;
    s->_pad[1] = 0u;
    tl_disarm(s);
    s->last.cmd = 0.0f;
    s->last.target = 0.0f;
    s->last.ppm_us = cfg->ppm_center_us;
    s->last.flags = 0u;
    s->last.state = TL_DISARMED;
    s->last.enable = 0u;
    s->last._pad[0] = 0u;
    s->last._pad[1] = 0u;
}

/* Rampa asimétrica: sube |out| a lo sumo up_step por tick y la baja a lo sumo down_step.
 * Nunca cruza el cero en un mismo tick (la inversión la gestiona el dwell). */
static float tl_ramp(float out, float eff, float up_step, float down_step)
{
    int8_t so = tl_signf(out);
    int8_t se = tl_signf(eff);
    float d;
    if (so == 0 || (se == so)) {
        d = eff - out;
        if (tl_absf(eff) > tl_absf(out)) {          /* sube la magnitud */
            if (tl_absf(d) > up_step) { out += (d > 0.0f) ? up_step : -up_step; }
            else { out = eff; }
        } else {                                     /* baja la magnitud */
            if (tl_absf(d) > down_step) { out += (d > 0.0f) ? down_step : -down_step; }
            else { out = eff; }
        }
    } else {                                         /* eff = 0 o de signo opuesto: ir a 0 */
        if (tl_absf(out) > down_step) { out -= (so > 0) ? down_step : -down_step; }
        else { out = 0.0f; }
    }
    return out;
}

tl_outputs_t tl_tick(tl_ctx_t *s, const tl_inputs_t *in, uint32_t dt_ms)
{
    const tl_config_t *c = &s->cfg;
    tl_outputs_t o;
    uint16_t inst = 0u;  /* flags instantáneos de este tick */
    uint16_t trip;
    uint8_t wdt, s_low, s_high, s_jump = 0u, sensor_ok, in_zero = 0u, inversion = 0u;
    float pos = 0.0f, target = 0.0f;

    s->uptime_ms += dt_ms;

    /* 1) Watchdog lógico: el llamador mide dt con su reloj; si el lazo se colgó, dt es grande. */
    wdt = (uint8_t)(dt_ms > (uint32_t)c->watchdog_ms);
    if (wdt) { inst |= TL_F_WATCHDOG; }

    /* 2) Cadena de seguridad (se evalúa ANTES que todo lo demás, efecto en este mismo tick). */
    if (!in->kill_cord_ok) { inst |= TL_F_KILL_CORD; }
    if (!in->estop_ok) { inst |= TL_F_ESTOP; }

    /* 3) Sensor: rango eléctrico y saltos imposibles. */
    s_low = (uint8_t)(in->adc < c->adc_fault_low);
    s_high = (uint8_t)(in->adc > c->adc_fault_high);
    if (!s_low && !s_high && s->prev_valid && !wdt) {
        float span = tl_absf((float)c->adc_fwd - (float)c->adc_rev);
        float allowed = (float)c->jump_noise_counts + span * c->jump_travel_per_s * ((float)dt_ms / 1000.0f);
        if ((float)tl_absdiff_u16(in->adc, s->prev_adc) > allowed) {
            s_jump = 1u;
        }
    }
    s->prev_adc = in->adc;
    s->prev_valid = (uint8_t)(!s_low && !s_high);
    if (s_low) { inst |= TL_F_SENS_LOW; }
    if (s_high) { inst |= TL_F_SENS_HIGH; }
    if (s_jump) { inst |= TL_F_SENS_JUMP; }
    sensor_ok = (uint8_t)(!s_low && !s_high && !s_jump);

    /* 4) VESC (telemetría opcional) y calibración. */
    if (c->use_vesc_ok && !in->vesc_ok) { inst |= TL_F_VESC; }
    if (s->cfg_err != TL_CFG_OK || !c->cal_valid) { inst |= TL_F_CAL; }

    /* 5) Posición -> objetivo (solo con sensor y calibración válidos). */
    if (sensor_ok && !(inst & TL_F_CAL)) {
        pos = tl_position(c, in->adc);
        in_zero = (uint8_t)(tl_absf(pos) <= c->deadband);
        target = tl_shape(c, pos);
        if (pos < 0.0f && !in_zero) {
            inst |= TL_F_REV_LIM; /* marcha atrás pedida: el comando se escala a reverse_limit */
        }
    }

    /* 6) Cualquier condición insegura desarma YA (salida neutra en este tick) y se latchea. */
    trip = (uint16_t)(inst & (TL_LATCH_MASK | TL_F_CAL));
    if (trip) {
        s->latched |= (uint16_t)(inst & TL_LATCH_MASK);
        tl_disarm(s);
    }

    /* 7) Desarmado: contar tiempo continuo en cero con todo OK; armar a los arm_hold_ms. */
    if (!s->armed) {
        uint8_t can_arm = (uint8_t)(!trip && in_zero);
        if (can_arm) {
            if (s->arm_run) {
                s->arm_ms = tl_sat_add(s->arm_ms, dt_ms);
            } else {          /* primera muestra en cero: el reloj arranca acá */
                s->arm_run = 1u;
                s->arm_ms = 0u;
            }
            inst |= TL_F_ARMING;
        } else {
            s->arm_run = 0u;
            s->arm_ms = 0u;
        }
        if (sensor_ok && !(inst & TL_F_CAL) && !in_zero) { inst |= TL_F_NOT_ZERO; }
        if (can_arm && s->arm_ms >= (uint32_t)c->arm_hold_ms) {
            s->armed = 1u;
            s->latched = 0u;           /* el armado limpia el historial */
            s->out = 0.0f;
            s->last_dir = 0;           /* tras >= 1 s en cero no hay dwell pendiente */
            s->zero_run = 1u;
            s->zero_ms = c->dwell_ms;
            inst &= (uint16_t)~TL_F_ARMING;
        }
    }

    /* 8) Armado: dwell de inversión + rampa. */
    if (s->armed) {
        float eff = target;
        int8_t tdir = tl_signf(target);
        float up_step = (float)dt_ms / (float)c->ramp_up_ms;
        float down_step = (c->ramp_down_ms == 0u) ? 2.0f : (float)dt_ms / (float)c->ramp_down_ms;

        /* La salida estuvo en 0 durante todo el intervalo dt -> acumular tiempo en cero. */
        if (s->zero_run) {
            s->zero_ms = tl_sat_add(s->zero_ms, dt_ms);
            if (s->zero_ms >= (uint32_t)c->dwell_ms) {
                s->last_dir = 0;       /* dwell cumplido: cualquier sentido permitido */
            }
        }
        /* Pedido de sentido opuesto al último usado -> forzar cero hasta cumplir el dwell. */
        if (tdir != 0 && s->last_dir != 0 && tdir != s->last_dir) {
            eff = 0.0f;
            inversion = 1u;
            inst |= TL_F_DWELL;
        }
        s->out = tl_ramp(s->out, eff, up_step, down_step);
        if (tl_signf(s->out) == tl_signf(eff) && tl_absf(s->out) < tl_absf(eff)) {
            inst |= TL_F_RAMP;
        }
        if (s->out != 0.0f) {
            s->last_dir = tl_signf(s->out);
            s->zero_run = 0u;
            s->zero_ms = 0u;
        } else if (!s->zero_run) {   /* la salida llegó a 0 en este tick: el reloj de dwell arranca */
            s->zero_run = 1u;
            s->zero_ms = 0u;
        }
    }

    /* 9) Salidas. */
    o.cmd = s->armed ? s->out : 0.0f;
    o.target = target;
    o.ppm_us = tl_cmd_to_ppm(c, o.cmd);
    o.flags = (uint16_t)(inst | s->latched);
    o.enable = s->armed;
    o._pad[0] = 0u;
    o._pad[1] = 0u;
    if (!s->armed) {
        o.state = ((s->latched & TL_FAULT_MASK) || (inst & TL_FAULT_MASK)) ? TL_FAULT : TL_DISARMED;
    } else if (s->out > 0.0f) {
        o.state = TL_RUN_FWD;
    } else if (s->out < 0.0f) {
        o.state = TL_RUN_REV;
    } else if (inversion || s->last_dir != 0) {
        o.state = TL_DWELL_ZERO;
    } else {
        o.state = TL_ARMED;
    }
    s->last = o;
    return o;
}
