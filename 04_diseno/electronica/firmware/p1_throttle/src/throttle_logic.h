/*
 * throttle_logic.h — Lógica pura del acelerador de P1 (C99, sin dependencias de Arduino).
 *
 * Proyecto P1: WATERJET eléctrico (VESC + motor directo al eje del impulsor, LiFePO4 12S).
 * La marcha atrás NO es invertir el giro: es bajar el BUCKET (cuchara) con su palanca y cable. El
 * motor gira SIEMPRE en avance; con el bucket abajo el empuje se desvía hacia proa y el comando se
 * limita a reverse_limit. El único giro inverso es la "limpieza de rejilla" (pulsador dedicado).
 *
 * Este módulo NO toca hardware: recibe lecturas (ADC del hall A1324, cordón, seta, VESC, fin de
 * carrera del bucket, selector de perfil, pulsador de rejilla, dt) y devuelve el comando
 * normalizado, el ancho de pulso PPM, el estado, el perfil y flags. Lo usan:
 *   - el sketch Arduino Nano (p1_throttle/p1_throttle.ino), y
 *   - los tests en PC (tests/test_firmware.py, vía ctypes con gcc).
 *
 * Reglas de seguridad implementadas (ver README §5):
 *   1. Arranque/re-armado SOLO con el acelerador en zona muerta >= arm_hold_ms continuos, con
 *      cordón y seta OK, sensor válido y calibración válida (tras power-on, kill, fault o watchdog).
 *   2. Cordón o seta abiertos -> salida neutra en el MISMO tick y desarme con latch.
 *   3. Sensor fuera de rango (abierto/corto) o salto físicamente imposible -> FAULT, neutro.
 *   4. Rampa de subida limitada (0->100 % en >= ramp_up_ms); bajada rápida (ramp_down_ms).
 *   5. Bucket ABAJO (fin de carrera abierto, o cable cortado) -> comando <= reverse_limit, en avance.
 *      Pasar a ABAJO es inmediato; pasar a ARRIBA exige sw_debounce_ms de contacto cerrado.
 *   6. Cambio de estado del bucket con el acelerador fuera de cero -> salida 0 en ese tick y hasta
 *      que el acelerador vuelva a la zona muerta (BKT_HOLD).
 *   7. Palanca del lado de reversa con el fin de carrera en ARRIBA (incoherente: el enclavamiento
 *      mecánico lo impide) -> salida 0 (BKT_MISM).
 *   8. Giro inverso SOLO en la limpieza de rejilla: pulsador sostenido >= weed_hold_ms, acelerador
 *      en cero, motor parado >= dwell_ms; |comando| <= weed_cmd; dura <= weed_max_ms; se corta al
 *      soltar el pulsador o mover el acelerador. La velocidad la topea el VESC (l_min_erpm).
 *   9. Cambio de sentido (avance <-> limpieza): la salida queda >= dwell_ms en cero.
 *  10. Perfil COSTA (5 kn) al encender y en cada armado; ABIERTO solo pasando el selector por
 *      costa -> abierto y con el acelerador en cero; volver a costa es inmediato.
 *  11. Watchdog lógico: si dt > watchdog_ms (tick no llamado a tiempo) -> neutro y desarme.
 *
 * Portabilidad AVR <-> x86: solo tipos de ancho fijo y float (en AVR double == float).
 * Los estados se guardan en uint8_t y los flags en uint32_t (en AVR un enum ocupa 2 bytes y en x86 4).
 * OJO en AVR: los flags < 0x10000 son unsigned int de 16 bits -> negar siempre como ~(uint32_t)TL_F_x.
 */
#ifndef P1_THROTTLE_LOGIC_H
#define P1_THROTTLE_LOGIC_H

#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#define TL_VERSION 0x0200u /* 2.0: waterjet (bucket, limpieza de rejilla, perfiles) */

/* ---- ADC: 10 bits, referencia = alimentación del sensor (5 V) -> lectura ratiométrica ---- */
#define TL_ADC_MAX 1023u
/* Convierte milivoltios a cuentas de un ADC de 10 bits con Vref = 5000 mV (redondeo). */
#define TL_MV_TO_ADC(mv) ((uint16_t)((((uint32_t)(mv)) * 1023u + 2500u) / 5000u))

/* ---- Estados (se guardan en uint8_t) ---- */
#define TL_DISARMED   0u /* salida neutra; esperando cero >= arm_hold_ms con todo OK             */
#define TL_ARMED      1u /* armado, comando = 0 (acelerador en zona muerta)                      */
#define TL_RUN_FWD    2u /* armado, avance con el bucket ARRIBA                                   */
#define TL_RUN_REV    3u /* armado, marcha atrás = bucket ABAJO (motor en avance, <= reverse_limit) */
#define TL_DWELL_ZERO 4u /* armado, en cero tras girar: cuenta dwell antes de cambiar de sentido  */
#define TL_FAULT      5u /* falla latcheada (sensor, VESC, calibración): neutro hasta re-armar     */
#define TL_WEED       6u /* armado, limpieza de rejilla: giro INVERSO lento y por tiempo limitado  */

/* ---- Perfiles de velocidad (salida al VESC; uint8_t) ---- */
#define TL_PROF_COAST 0u /* costa: l_max_erpm legal (5 kn dentro de 300 m); por defecto */
#define TL_PROF_OPEN  1u /* abierto: l_max_erpm técnico (fuera de la franja de 300 m)   */

/* ---- Flags (bitmask uint32_t). Los marcados (L) quedan latcheados hasta el próximo armado ---- */
#define TL_F_KILL_CORD  0x00000001u /* (L) cordón abierto (clip afuera, cable cortado, conector suelto) */
#define TL_F_ESTOP      0x00000002u /* (L) seta de emergencia pulsada / circuito abierto               */
#define TL_F_SENS_LOW   0x00000004u /* (L) ADC < adc_fault_low  (cable de señal/5 V abierto, corto a GND) */
#define TL_F_SENS_HIGH  0x00000008u /* (L) ADC > adc_fault_high (corto a 5 V, GND del sensor abierto)  */
#define TL_F_SENS_JUMP  0x00000010u /* (L) salto imposible entre dos muestras (contacto intermitente)  */
#define TL_F_WATCHDOG   0x00000020u /* (L) tick no llamado en > watchdog_ms                            */
#define TL_F_VESC       0x00000040u /* (L) VESC reporta falla (solo si use_vesc_ok = 1)                */
#define TL_F_CAL        0x00000080u /*     calibración inválida (no se puede armar)                    */
#define TL_F_NOT_ZERO   0x00000100u /*     desarmado y acelerador fuera de cero (esperando que vuelva)  */
#define TL_F_RAMP       0x00000200u /*     la rampa de subida está limitando el comando                 */
#define TL_F_BKT_LIM    0x00000400u /*     bucket ABAJO: comando limitado a reverse_limit                */
#define TL_F_DWELL      0x00000800u /*     cambio de sentido pedido, esperando dwell en cero             */
#define TL_F_ARMING     0x00001000u /*     contando tiempo en cero para armar                          */
#define TL_F_BKT_DOWN   0x00002000u /*     estado del bucket (filtrado): 1 = ABAJO (o cable cortado)     */
#define TL_F_BKT_HOLD   0x00004000u /*     el bucket cambió con el acelerador fuera de cero: salida 0    */
#define TL_F_BKT_MISM   0x00008000u /*     lado de la palanca incoherente con el fin de carrera          */
#define TL_F_WEED       0x00010000u /*     limpieza de rejilla en curso (giro inverso)                   */
#define TL_F_WEED_WAIT  0x00020000u /*     pulsador de rejilla apretado sin las condiciones para girar   */
#define TL_F_PROF_OPEN  0x00040000u /*     perfil ABIERTO activo                                         */
#define TL_F_PROF_WAIT  0x00080000u /*     selector en ABIERTO pero perfil COSTA (pasar por costa / acelerador a 0) */

/* Flags que provocan FAULT (el resto de los latcheados provocan DISARMED). */
#define TL_FAULT_MASK (TL_F_SENS_LOW | TL_F_SENS_HIGH | TL_F_SENS_JUMP | TL_F_VESC | TL_F_CAL)
/* Flags que se latchean hasta el próximo armado. */
#define TL_LATCH_MASK (TL_F_KILL_CORD | TL_F_ESTOP | TL_F_SENS_LOW | TL_F_SENS_HIGH | \
                       TL_F_SENS_JUMP | TL_F_WATCHDOG | TL_F_VESC)

/* ---- Configuración (valores por defecto en tl_default_config; ver etiquetas allí) ---- */
typedef struct {
    float deadband;            /* zona muerta, fracción de semicarrera (0..0,5)           */
    float expo;                /* 0 = lineal, 1 = cúbica pura                             */
    float reverse_limit;       /* comando máximo con el bucket ABAJO (0..1], en avance    */
    float jump_travel_per_s;   /* velocidad física máxima de la palanca [carreras/s]      */
    float weed_cmd;            /* |comando| de la limpieza de rejilla (giro inverso)      */
    /* Calibración de la palanca (cuentas ADC). fwd puede ser < center (imán invertido): se admite. */
    uint16_t adc_rev;          /* tope del lado de reversa (bucket abajo)                */
    uint16_t adc_center;       /* reposo (resortes de retorno al centro)                  */
    uint16_t adc_fwd;          /* tope de avance                                          */
    uint16_t adc_fault_low;    /* lectura menor -> falla de sensor (~0,3 V)              */
    uint16_t adc_fault_high;   /* lectura mayor -> falla de sensor (~4,7 V)              */
    uint16_t min_half_span;    /* semicarrera mínima aceptable en calibración [cuentas]  */
    uint16_t jump_noise_counts;/* ruido admitido entre muestras, además de la pendiente   */
    uint16_t arm_hold_ms;      /* tiempo continuo en cero para armar                     */
    uint16_t ramp_up_ms;       /* tiempo 0 -> 100 % (subida de |comando|)               */
    uint16_t ramp_down_ms;     /* tiempo 100 % -> 0 (bajada de |comando|); 0 = inmediato */
    uint16_t dwell_ms;         /* tiempo mínimo en cero antes de cambiar el sentido      */
    uint16_t watchdog_ms;      /* dt máximo entre ticks                                  */
    uint16_t ppm_min_us;       /* pulso a -100 %                                          */
    uint16_t ppm_center_us;    /* pulso neutro                                            */
    uint16_t ppm_max_us;       /* pulso a +100 %                                          */
    uint16_t weed_max_ms;      /* duración máxima de una limpieza de rejilla (<= 3000)    */
    uint16_t weed_hold_ms;     /* pulsación sostenida para iniciar la limpieza            */
    uint16_t sw_debounce_ms;   /* antirrebote: bucket hacia ARRIBA y selector de perfil   */
    uint8_t cal_valid;         /* 1 = calibración cargada y validada                     */
    uint8_t use_vesc_ok;       /* 1 = usar la entrada vesc_ok (telemetría UART)          */
} tl_config_t;

/* ---- Entradas de un tick ---- */
typedef struct {
    uint16_t adc;          /* lectura del hall 0..1023 (promediada)                          */
    uint8_t kill_cord_ok;  /* 1 = cordón puesto y circuito cerrado                           */
    uint8_t estop_ok;      /* 1 = seta liberada y circuito cerrado                           */
    uint8_t vesc_ok;       /* 1 = VESC sin falla (o telemetría no usada)                     */
    uint8_t bucket_up;     /* 1 = fin de carrera NC CERRADO = bucket ARRIBA; 0 = abajo/cortado */
    uint8_t sel_open;      /* 1 = selector de perfil en ABIERTO; 0 = COSTA (o cable cortado)  */
    uint8_t weed_btn;      /* 1 = pulsador de limpieza de rejilla apretado                   */
} tl_inputs_t;

/* ---- Salidas de un tick ---- */
typedef struct {
    float cmd;        /* comando final [-weed_cmd, 1] tras zona muerta, expo, bucket, dwell y rampa */
    float target;     /* objetivo antes de rampa/dwell/retención (diagnóstico)                     */
    uint32_t flags;   /* flags instantáneos | latcheados                                           */
    uint16_t ppm_us;  /* ancho de pulso PPM [ppm_min_us, ppm_max_us]; neutro = ppm_center_us        */
    uint8_t state;    /* TL_DISARMED ... TL_WEED                                                   */
    uint8_t enable;   /* 1 = habilitar VESC (transistor que lleva ADC2 a GND); 0 = kill SW         */
    uint8_t profile;  /* TL_PROF_COAST / TL_PROF_OPEN (COAST siempre que no esté armado)           */
    uint8_t _pad[3];
} tl_outputs_t;

/* ---- Contexto (estado persistente entre ticks) ---- */
typedef struct {
    tl_config_t cfg;
    tl_outputs_t last;     /* última salida                                          */
    float out;             /* comando con rampa                                      */
    uint32_t uptime_ms;    /* suma de dt (diagnóstico)                               */
    uint32_t arm_ms;       /* tiempo continuo en condición de armado                  */
    uint32_t zero_ms;      /* tiempo continuo con salida = 0 estando armado          */
    uint32_t latched;      /* flags latcheados desde el último armado                */
    uint32_t bkt_up_ms;    /* tiempo continuo con el fin de carrera cerrado          */
    uint32_t sel_ms;       /* tiempo continuo con el selector distinto del filtrado  */
    uint32_t weed_press_ms;/* tiempo continuo con el pulsador de rejilla apretado    */
    uint32_t weed_ms;      /* duración de la limpieza en curso                       */
    uint16_t prev_adc;     /* muestra anterior (detección de saltos)                 */
    uint8_t prev_valid;    /* prev_adc utilizable                                    */
    uint8_t armed;         /* 1 = armado                                             */
    uint8_t arm_run;       /* 1 = el tick anterior ya cumplía la condición de armado */
    uint8_t zero_run;      /* 1 = el tick anterior ya tenía salida 0 (armado)        */
    int8_t last_dir;       /* +1 / -1 último sentido con salida != 0; 0 = libre      */
    uint8_t cfg_err;       /* resultado de tl_config_check al iniciar (0 = OK)       */
    uint8_t bkt_down;      /* bucket filtrado: 1 = ABAJO (arranca en 1: lo más restrictivo) */
    uint8_t bkt_up_run;    /* 1 = el tick anterior ya tenía el fin de carrera cerrado */
    uint8_t bkt_hold;      /* 1 = salida retenida en 0 hasta que el acelerador vuelva a cero */
    uint8_t sel_db;        /* selector filtrado: 1 = ABIERTO                          */
    uint8_t sel_run;       /* 1 = el tick anterior ya tenía selector != filtrado      */
    uint8_t sel_ready;     /* 1 = el selector pasó por COSTA desde el último armado   */
    uint8_t profile;       /* perfil activo                                          */
    uint8_t weed_run;      /* 1 = limpieza de rejilla en curso                        */
    uint8_t weed_ready;    /* 1 = el pulsador estuvo suelto desde el armado / la última limpieza */
    uint8_t weed_press_run;/* 1 = el tick anterior ya tenía el pulsador apretado       */
    uint8_t _pad[2];
} tl_ctx_t;

/* Códigos de tl_config_check / tl_calibrate (bitmask; 0 = OK). */
#define TL_CFG_OK             0x00u
#define TL_CFG_ERR_ORDER      0x01u /* rev, center, fwd no monótonos                     */
#define TL_CFG_ERR_SPAN       0x02u /* semicarrera < min_half_span                       */
#define TL_CFG_ERR_RANGE      0x04u /* algún punto de calibración fuera de la banda válida */
#define TL_CFG_ERR_PARAM      0x08u /* parámetro fuera de rango (zona muerta, límites...) */
#define TL_CFG_ERR_PPM        0x10u /* PPM no monótono o fuera de 800..2200 us            */

/* Topes de la limpieza de rejilla que tl_config_check exige (pedido de diseño). */
#define TL_WEED_MAX_MS_LIMIT 3000u  /* <= 3 s por pulsación                                 */
#define TL_WEED_CMD_LIMIT    0.25f  /* |comando| inverso <= 25 % (la velocidad la topea el VESC) */

/* Carga los valores por defecto (etiquetados en throttle_logic.c). cal_valid queda en 0. */
void tl_default_config(tl_config_t *cfg);
/* Valida la configuración. Devuelve TL_CFG_OK o bitmask de errores. */
uint8_t tl_config_check(const tl_config_t *cfg);
/* Valida y guarda una calibración (rev, center, fwd); pone cal_valid = 1 si es válida. */
uint8_t tl_calibrate(tl_config_t *cfg, uint16_t adc_rev, uint16_t adc_center, uint16_t adc_fwd);
/* Inicializa el contexto: estado DISARMED, salida neutra, perfil COSTA, bucket ABAJO. Copia cfg. */
void tl_init(tl_ctx_t *s, const tl_config_t *cfg);
/* Paso de la lógica: dt_ms = tiempo desde el tick anterior (el llamador lo mide con millis()). */
tl_outputs_t tl_tick(tl_ctx_t *s, const tl_inputs_t *in, uint32_t dt_ms);

/* Auxiliares puros (expuestos para tests y telemetría). */
float tl_position(const tl_config_t *cfg, uint16_t adc);   /* -1..1 sin zona muerta         */
float tl_shape(const tl_config_t *cfg, float pos);         /* zona muerta + expo, con signo */
float tl_thrust(const tl_config_t *cfg, float pos, uint8_t bkt_down); /* objetivo 0..1 (avance) */
uint16_t tl_cmd_to_ppm(const tl_config_t *cfg, float cmd); /* [-1,1] -> us                  */
const char *tl_state_name(uint8_t state);

/* Tamaños (para verificar desde ctypes que el layout coincide). */
uint16_t tl_sizeof_config(void);
uint16_t tl_sizeof_inputs(void);
uint16_t tl_sizeof_outputs(void);
uint16_t tl_sizeof_ctx(void);

#ifdef __cplusplus
}
#endif

#endif /* P1_THROTTLE_LOGIC_H */
