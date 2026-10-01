/*
 * p1_throttle.ino — Acelerador con marcha atrás + cadena de seguridad de P1.
 * Placa: Arduino Nano (ATmega328P, 16 MHz, 5 V), bootloader NUEVO (Optiboot; FQBN arduino:avr:nano).
 *
 * [NO EJECUTADO en hardware]. Compilado con arduino-cli (ver README §Firmware). Probar en T0.
 *
 * La lógica (armado, rampa, zona muerta, dwell de inversión, límite de reversa, fallas de sensor,
 * watchdog lógico) vive en src/throttle_logic.c (C99 puro, copia idéntica de ../throttle_logic.c,
 * testeada en PC con tests/test_firmware.py). Este sketch solo hace E/S:
 *
 *   A0  <- hall lineal ratiométrico (Vref = AVCC = 5 V = alimentación del sensor). Pull-down 100 kΩ
 *          externo: cable de señal o de 5 V cortado -> ~0 V -> FAULT.
 *   D2  <- cordón (INT0). INPUT_PULLUP + 10 kΩ externo; el transistor del opto U2 lo lleva a GND
 *          cuando la bobina del contactor está energizada (cordón Y seta cerrados).
 *          ALTO = kill (clip afuera, cable cortado, conector suelto, fusible de mando abierto).
 *   D3  <- seta de emergencia (INT1). Igual, opto U1 (nodo entre seta y cordón). ALTO = e-stop.
 *   D9  -> PPM al VESC (Timer1/OC1A por hardware, 50 Hz, 1000–2000 µs, 1500 = neutro).
 *   D4  -> Q_EN: habilita el VESC llevando su entrada ADC2 (kill por software) a GND a través del
 *          opto U3 en serie. D4 BAJO o MCU en reset (alta impedancia) -> ADC2 en alto -> VESC en kill.
 *   D6  -> LED de estado del panel (espejo en D13).
 *   WDT de hardware 120 ms: si el lazo se cuelga, reset -> pines en alta impedancia -> sin PPM (timeout
 *          del VESC) y Q_EN abierto (kill del VESC); al reiniciar arranca DESARMADO.
 */
#include <avr/wdt.h>
#include <avr/interrupt.h>
#include <util/atomic.h>
#include <EEPROM.h>
#include "src/throttle_logic.h"

#ifndef P1_TEST_COMMANDS
#define P1_TEST_COMMANDS 0 /* 1 solo para T0 (habilita 'h' = colgar el lazo para probar el WDT) */
#endif

/* ------------------------------------------------------------------ pines y tiempos */
static const uint8_t PIN_HALL = A0;
static const uint8_t PIN_KILL = 2;   /* INT0 */
static const uint8_t PIN_ESTOP = 3;  /* INT1 */
static const uint8_t PIN_VESC_EN = 4;
static const uint8_t PIN_LED = 6;
static const uint8_t PIN_PPM = 9;    /* OC1A */

static const uint16_t TICK_MS = 10;          /* [SUPUESTO: 100 Hz; corte por software <= 1 tick] */
static const uint16_t TELEMETRY_MS = 100;
static const uint8_t ADC_OVERSAMPLE = 4;     /* promedio de 4 lecturas (~0,45 ms) */
static const uint16_t PPM_PERIOD_US = 20000; /* [SUPUESTO: 50 Hz, trama RC estándar] */

/* ------------------------------------------------------------------ estado global */
static tl_config_t g_cfg;
static tl_ctx_t g_ctx;
static tl_outputs_t g_out;
static uint32_t g_last_tick_ms;
static uint32_t g_last_tele_ms;
static bool g_tele_on = true;
static volatile uint8_t g_isr_kill = 0;   /* flanco a "kill" visto por INT0 */
static volatile uint8_t g_isr_estop = 0;  /* flanco a "e-stop" visto por INT1 */
static uint8_t g_cal_step = 0;            /* 0 = sin calibrar en curso */
static uint16_t g_cal_center = 0, g_cal_fwd = 0, g_cal_rev = 0;
static uint8_t g_last_kill_ok = 1;    /* último kill_ok usado; 1 hasta que un tick confirme el cordón afuera */

/* Copia de MCUSR (causa de reset) y WDT apagado lo antes posible tras un reset por WDT. */
uint8_t g_mcusr __attribute__((section(".noinit")));
void p1_early_init(void) __attribute__((naked)) __attribute__((section(".init3")));
void p1_early_init(void)
{
    g_mcusr = MCUSR;
    MCUSR = 0;
    wdt_disable();
}

/* ------------------------------------------------------------------ PPM por Timer1 */
static inline uint16_t us_to_ticks(uint16_t us) { return (uint16_t)(us * 2u); } /* 16 MHz / 8 = 0,5 µs */

static void ppm_begin(void)
{
    digitalWrite(PIN_PPM, LOW);
    pinMode(PIN_PPM, OUTPUT);
    TCCR1A = 0;
    TCCR1B = 0;
    TCNT1 = 0;
    ICR1 = (uint16_t)(us_to_ticks(PPM_PERIOD_US) - 1u); /* TOP: 20 ms */
    OCR1A = us_to_ticks(g_cfg.ppm_center_us);           /* arranca en neutro */
    TCCR1A = _BV(COM1A1) | _BV(WGM11);                  /* OC1A no invertido, modo 14 (Fast PWM, TOP = ICR1) */
    TCCR1B = _BV(WGM13) | _BV(WGM12) | _BV(CS11);       /* prescaler 8 */
    /* En Fast PWM OCR1A tiene doble buffer: el cambio entra al inicio de la próxima trama (sin glitches). */
}

/* Corte inmediato desde las ISR: neutro + VESC en kill. Las ISR corren con interrupciones off,
 * así que la escritura de 16 bits de OCR1A es atómica. */
static inline void isr_cut(void)
{
    OCR1A = us_to_ticks(g_cfg.ppm_center_us);
    PORTD &= (uint8_t)~_BV(PD4); /* D4 = PIN_VESC_EN bajo */
}

ISR(INT0_vect) /* D2: cordón */
{
    if (PIND & _BV(PD2)) { /* ALTO = kill */
        isr_cut();
        g_isr_kill = 1;
    }
}

ISR(INT1_vect) /* D3: seta */
{
    if (PIND & _BV(PD3)) {
        isr_cut();
        g_isr_estop = 1;
    }
}

/* ------------------------------------------------------------------ calibración en EEPROM */
struct CalRecord {
    uint16_t magic;
    uint16_t rev, center, fwd;
    uint8_t crc;
};
static const uint16_t CAL_MAGIC = 0x5031; /* "P1" */

static uint8_t crc8(const uint8_t *p, uint8_t n)
{
    uint8_t crc = 0;
    while (n--) {
        crc ^= *p++;
        for (uint8_t i = 0; i < 8; i++) {
            crc = (crc & 0x80) ? (uint8_t)((crc << 1) ^ 0x07) : (uint8_t)(crc << 1);
        }
    }
    return crc;
}

static bool cal_load(void)
{
    CalRecord r;
    EEPROM.get(0, r);
    if (r.magic != CAL_MAGIC || crc8((const uint8_t *)&r, (uint8_t)(sizeof(r) - 1)) != r.crc) {
        return false;
    }
    return tl_calibrate(&g_cfg, r.rev, r.center, r.fwd) == TL_CFG_OK;
}

static bool cal_save(uint16_t rev, uint16_t center, uint16_t fwd)
{
    tl_config_t tmp = g_cfg;
    uint8_t e = tl_calibrate(&tmp, rev, center, fwd);
    if (e != TL_CFG_OK) {
        Serial.print(F("CAL: invalida, error 0x"));
        Serial.println(e, HEX);
        return false;
    }
    CalRecord r = {CAL_MAGIC, rev, center, fwd, 0};
    r.crc = crc8((const uint8_t *)&r, (uint8_t)(sizeof(r) - 1));
    EEPROM.put(0, r);
    g_cfg = tmp;
    tl_init(&g_ctx, &g_cfg); /* re-inicia DESARMADO con la calibración nueva */
    Serial.println(F("CAL: guardada. Volver el puno a cero 1 s para armar."));
    return true;
}

/* ------------------------------------------------------------------ entradas */
static uint16_t read_hall(void)
{
    uint16_t acc = 0;
    for (uint8_t i = 0; i < ADC_OVERSAMPLE; i++) {
        acc = (uint16_t)(acc + (uint16_t)analogRead(PIN_HALL));
    }
    return (uint16_t)((acc + ADC_OVERSAMPLE / 2u) / ADC_OVERSAMPLE);
}

/* ------------------------------------------------------------------ LED de estado */
static void led_update(uint32_t now)
{
    bool on;
    const uint16_t f = g_out.flags;
    switch (g_out.state) {
    case TL_ARMED:
    case TL_RUN_FWD:
    case TL_RUN_REV:
    case TL_DWELL_ZERO:
        on = true;                                  /* fijo: armado */
        break;
    case TL_FAULT:
        on = ((now / 50u) & 1u) != 0u;              /* 10 Hz: falla (sensor/VESC/calibración) */
        break;
    default:                                        /* DESARMADO */
        if (f & (TL_F_KILL_CORD | TL_F_ESTOP)) {
            on = (now % 2000u) < 60u;               /* destello cada 2 s: cordón/seta abiertos */
        } else if (f & TL_F_NOT_ZERO) {
            on = ((now / 125u) & 1u) != 0u;         /* 4 Hz: volver el acelerador a cero */
        } else {
            on = ((now / 250u) & 1u) != 0u;         /* 2 Hz: contando 1 s en cero para armar */
        }
        break;
    }
    digitalWrite(PIN_LED, on ? HIGH : LOW);
    digitalWrite(LED_BUILTIN, on ? HIGH : LOW);
}

/* ------------------------------------------------------------------ consola serie (115200) */
static void print_help(void)
{
    Serial.println(F("Comandos: t=telemetria on/off, c=calibrar (solo con CORDON AFUERA), "
                     "1=centro 2=tope avance 3=tope atras s=guardar x=cancelar"
#if P1_TEST_COMMANDS
                     ", h=colgar lazo (prueba WDT T0)"
#endif
                     ));
}

static void serial_poll(void)
{
    while (Serial.available() > 0) {
        char ch = (char)Serial.read();
        const bool may_cal = (g_out.state == TL_DISARMED || g_out.state == TL_FAULT) && !g_last_kill_ok;
        switch (ch) {
        case 't': g_tele_on = !g_tele_on; break;
        case '?': print_help(); break;
        case 'c':
            if (!may_cal) { Serial.println(F("CAL: sacar el cordon (contactor abierto) y desarmar primero")); break; }
            g_cal_step = 1;
            Serial.println(F("CAL: soltar el puno (centro) y enviar 1"));
            break;
        case '1': if (g_cal_step && may_cal) { g_cal_center = read_hall(); g_cal_step = 2; Serial.println(F("CAL: tope AVANCE y enviar 2")); } break;
        case '2': if (g_cal_step == 2 && may_cal) { g_cal_fwd = read_hall(); g_cal_step = 3; Serial.println(F("CAL: tope ATRAS y enviar 3")); } break;
        case '3': if (g_cal_step == 3 && may_cal) { g_cal_rev = read_hall(); g_cal_step = 4; Serial.println(F("CAL: enviar s para guardar")); } break;
        case 's':
            if (g_cal_step == 4 && may_cal) {
                Serial.print(F("CAL: rev/centro/avance = "));
                Serial.print(g_cal_rev); Serial.print('/'); Serial.print(g_cal_center); Serial.print('/'); Serial.println(g_cal_fwd);
                cal_save(g_cal_rev, g_cal_center, g_cal_fwd);
                g_cal_step = 0;
            }
            break;
        case 'x': g_cal_step = 0; Serial.println(F("CAL: cancelada")); break;
#if P1_TEST_COMMANDS
        case 'h':
            Serial.println(F("TEST: lazo colgado; el WDT (120 ms) debe reiniciar el MCU"));
            Serial.flush();
            for (;;) { /* sin wdt_reset(): reset por WDT */ }
#endif
        default: break;
        }
    }
}

static void telemetry(uint32_t now)
{
    /* CSV: t_ms,estado,adc,cmd,ppm_us,flags_hex,enable */
    Serial.print(now); Serial.print(',');
    Serial.print(tl_state_name(g_out.state)); Serial.print(',');
    Serial.print(g_ctx.prev_adc); Serial.print(',');
    Serial.print(g_out.cmd, 3); Serial.print(',');
    Serial.print(g_out.ppm_us); Serial.print(",0x");
    Serial.print(g_out.flags, HEX); Serial.print(',');
    Serial.println(g_out.enable);
}

/* ------------------------------------------------------------------ setup / loop */
void setup()
{
    /* Salidas seguras primero: VESC en kill, PPM bajo (sin pulsos). */
    digitalWrite(PIN_VESC_EN, LOW);
    pinMode(PIN_VESC_EN, OUTPUT);
    digitalWrite(PIN_PPM, LOW);
    pinMode(PIN_PPM, OUTPUT);
    pinMode(PIN_LED, OUTPUT);
    pinMode(LED_BUILTIN, OUTPUT);
    pinMode(PIN_KILL, INPUT_PULLUP);
    pinMode(PIN_ESTOP, INPUT_PULLUP);
    analogReference(DEFAULT); /* AVCC = 5 V = alimentación del hall -> ratiométrico */

    Serial.begin(115200);
    Serial.print(F("P1 throttle v"));
    Serial.print(TL_VERSION >> 8); Serial.print('.'); Serial.print(TL_VERSION & 0xFF);
    Serial.print(F(" reset MCUSR=0x")); Serial.println(g_mcusr, HEX); /* 0x08 = WDRF (Optiboot puede dejarlo en 0) */

    tl_default_config(&g_cfg);
    if (!cal_load()) {
        Serial.println(F("SIN CALIBRACION VALIDA: estado FAULT hasta calibrar (c)."));
    }
    tl_init(&g_ctx, &g_cfg);
    g_out = g_ctx.last;

    ppm_begin(); /* pulsos neutros desde ya: el safe start del VESC los necesita */

    EICRA = _BV(ISC00) | _BV(ISC10); /* INT0 e INT1 en cualquier cambio (la ISR filtra el flanco a ALTO) */
    EIFR = _BV(INTF0) | _BV(INTF1);
    EIMSK = _BV(INT0) | _BV(INT1);

    print_help();
    wdt_enable(WDTO_120MS);
    g_last_tick_ms = millis();
    g_last_tele_ms = g_last_tick_ms;
}

void loop()
{
    const uint32_t now = millis();
    if ((uint32_t)(now - g_last_tick_ms) >= TICK_MS) {
        const uint32_t dt = now - g_last_tick_ms;
        g_last_tick_ms = now;

        tl_inputs_t in;
        uint8_t isr_kill, isr_estop;
        ATOMIC_BLOCK(ATOMIC_RESTORESTATE) {
            isr_kill = g_isr_kill;
            isr_estop = g_isr_estop;
            g_isr_kill = 0;
            g_isr_estop = 0;
        }
        uint8_t kill_ok = (digitalRead(PIN_KILL) == LOW) && !isr_kill;
        uint8_t estop_ok = (digitalRead(PIN_ESTOP) == LOW) && !isr_estop;
        /* Coherencia del cableado en serie: el nodo del cordón (D2) no puede estar energizado
         * si el de la seta (D3) no lo está -> falla de cableado/opto: tratar ambos como abiertos. */
        if (kill_ok && !estop_ok) { kill_ok = 0; }
        g_last_kill_ok = kill_ok;

        in.adc = read_hall();
        in.kill_cord_ok = kill_ok;
        in.estop_ok = estop_ok;
        in.vesc_ok = 1; /* [NO IMPLEMENTADO] telemetría UART del VESC (hook para P2) */
        in._pad[0] = in._pad[1] = in._pad[2] = 0;

        g_out = tl_tick(&g_ctx, &in, dt);

        /* Aplicar salidas salvo que una ISR haya cortado después de leer las entradas:
         * en ese caso queda el neutro de la ISR y el próximo tick latchea el kill. */
        ATOMIC_BLOCK(ATOMIC_RESTORESTATE) {
            if (!g_isr_kill && !g_isr_estop) {
                OCR1A = us_to_ticks(g_out.ppm_us);
                if (g_out.enable) { PORTD |= _BV(PD4); } else { PORTD &= (uint8_t)~_BV(PD4); }
            }
        }
        wdt_reset(); /* solo tras un tick completo */
    }

    serial_poll();
    if (g_tele_on && (uint32_t)(now - g_last_tele_ms) >= TELEMETRY_MS) {
        g_last_tele_ms = now;
        telemetry(now);
    }
    led_update(now);
}
