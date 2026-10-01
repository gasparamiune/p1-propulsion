/*
 * throttle_logic.h — Lógica pura del acelerador de P1 (C99, sin dependencias de Arduino).
 *
 * Proyecto P1: propulsión eléctrica "cola larga" (VESC 75100 + outrunner 6374, LiFePO4 8S).
 * Este módulo NO toca hardware: recibe lecturas (ADC del hall, cordón, seta, VESC, dt) y
 * devuelve el comando normalizado, el ancho de pulso PPM, el estado y flags. Lo usan:
 *   - el sketch Arduino Nano (p1_throttle/p1_throttle.ino), y
 *   - los tests en PC (tests/test_firmware.py, vía ctypes con gcc).
 *
 * Reglas de seguridad implementadas (ver README §Firmware):
 *   1. Arranque/re-armado SOLO con el acelerador en zona muerta >= arm_hold_ms continuos, con
 *      cordón y seta OK, sensor válido y calibración válida (tras power-on, kill, fault o watchdog).
 *   2. Cordón o seta abiertos -> salida neutra en el MISMO tick y desarme con latch.
 *   3. Sensor fuera de rango (abierto/corto) o salto físicamente imposible -> FAULT, neutro.
 *   4. Rampa de subida limitada (0->100 % en >= ramp_up_ms); bajada rápida (ramp_down_ms).
 *   5. Marcha atrás escalada a reverse_limit (50 % por defecto).
 *   6. Inversión de sentido: pasar por cero y quedarse >= dwell_ms en cero.
 *   7. Watchdog lógico: si dt > watchdog_ms (tick no llamado a tiempo) -> neutro y desarme.
 *
 * Portabilidad AVR <-> x86: solo tipos de ancho fijo y float (en AVR double == float).
 * Los estados y flags se guardan en uint8_t/uint16_t (en AVR un enum ocupa 2 bytes y en x86 4).
 */
#ifndef P1_THROTTLE_LOGIC_H
#define P1_THROTTLE_LOGIC_H

#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#define TL_VERSION 0x0100u /* 1.0 */

/* ---- ADC: 10 bits, referencia = alimentación del sensor (5 V) -> lectura ratiométrica ---- */
#define TL_ADC_MAX 1023u
/* Convierte milivoltios a cuentas de un ADC de 10 bits con Vref = 5000 mV (redondeo). */
#define TL_MV_TO_ADC(mv) ((uint16_t)((((uint32_t)(mv)) * 1023u + 2500u) / 5000u))

/* ---- Estados (se guardan en uint8_t) ---- */
#define TL_DISARMED   0u /* salida neutra; esperando cero >= arm_hold_ms con todo OK         */
#define TL_ARMED      1u /* armado, comando = 0 (acelerador en zona muerta)                  */
#define TL_RUN_FWD    2u /* armado, avance                                                    */
#define TL_RUN_REV    3u /* armado, marcha atrás (limitada)                                   */
#define TL_DWELL_ZERO 4u /* armado, en cero tras marchar: cuenta dwell antes de poder invertir */
#define TL_FAULT      5u /* falla latcheada (sensor, VESC, calibración): neutro hasta re-armar */

/* ---- Flags (bitmask uint16_t). Los marcados (L) quedan latcheados hasta el próximo armado ---- */
#define TL_F_KILL_CORD  0x0001u /* (L) cordón abierto (clip afuera, cable cortado, conector suelto) */
#define TL_F_ESTOP      0x0002u /* (L) seta de emergencia pulsada / circuito abierto               */
#define TL_F_SENS_LOW   0x0004u /* (L) ADC < adc_fault_low  (cable de señal/5 V abierto, corto a GND) */
#define TL_F_SENS_HIGH  0x0008u /* (L) ADC > adc_fault_high (corto a 5 V, GND del sensor abierto)  */
#define TL_F_SENS_JUMP  0x0010u /* (L) salto imposible entre dos muestras (contacto intermitente)  */
#define TL_F_WATCHDOG   0x0020u /* (L) tick no llamado en > watchdog_ms                            */
#define TL_F_VESC       0x0040u /* (L) VESC reporta falla (solo si use_vesc_ok = 1)                */
#define TL_F_CAL        0x0080u /*     calibración inválida (no se puede armar)                    */
#define TL_F_NOT_ZERO   0x0100u /*     desarmado y acelerador fuera de cero (esperando que vuelva)  */
#define TL_F_RAMP       0x0200u /*     la rampa de subida está limitando el comando                 */
#define TL_F_REV_LIM    0x0400u /*     marcha atrás pedida: comando escalado a reverse_limit         */
#define TL_F_DWELL      0x0800u /*     inversión pedida, esperando dwell en cero                    */
#define TL_F_ARMING     0x1000u /*     contando tiempo en cero para armar                          */

/* Flags que provocan FAULT (el resto de los latcheados provocan DISARMED). */
#define TL_FAULT_MASK (TL_F_SENS_LOW | TL_F_SENS_HIGH | TL_F_SENS_JUMP | TL_F_VESC | TL_F_CAL)
/* Flags que se latchean hasta el próximo armado. */
#define TL_LATCH_MASK (TL_F_KILL_CORD | TL_F_ESTOP | TL_F_SENS_LOW | TL_F_SENS_HIGH | \
                       TL_F_SENS_JUMP | TL_F_WATCHDOG | TL_F_VESC)

/* ---- Configuración (valores por defecto en tl_default_config; ver etiquetas allí) ---- */
typedef struct {
    float deadband;            /* zona muerta, fracción de semicarrera (0..0,5)           */
    float expo;                /* 0 = lineal, 1 = cúbica pura                             */
    float reverse_limit;       /* |comando| máximo en marcha atrás (0..1)                 */
    float jump_travel_per_s;   /* velocidad física máxima del puño [carreras completas/s] */
    /* Calibración del puño (cuentas ADC). fwd puede ser < center (imán invertido): se admite. */
    uint16_t adc_rev;          /* tope de marcha atrás                                   */
    uint16_t adc_center;       /* reposo (resortes de retorno al centro)                  */
    uint16_t adc_fwd;          /* tope de avance                                          */
    uint16_t adc_fault_low;    /* lectura menor -> falla de sensor (~0,3 V)              */
    uint16_t adc_fault_high;   /* lectura mayor -> falla de sensor (~4,7 V)              */
    uint16_t min_half_span;    /* semicarrera mínima aceptable en calibración [cuentas]  */
    uint16_t jump_noise_counts;/* ruido admitido entre muestras, además de la pendiente   */
    uint16_t arm_hold_ms;      /* tiempo continuo en cero para armar                     */
    uint16_t ramp_up_ms;       /* tiempo 0 -> 100 % (subida de |comando|)               */
    uint16_t ramp_down_ms;     /* tiempo 100 % -> 0 (bajada de |comando|); 0 = inmediato */
    uint16_t dwell_ms;         /* tiempo mínimo en cero antes de invertir el sentido     */
    uint16_t watchdog_ms;      /* dt máximo entre ticks                                  */
    uint16_t ppm_min_us;       /* pulso a -100 %                                          */
    uint16_t ppm_center_us;    /* pulso neutro                                            */
    uint16_t ppm_max_us;       /* pulso a +100 %                                          */
    uint8_t cal_valid;         /* 1 = calibración cargada y validada                     */
    uint8_t use_vesc_ok;       /* 1 = usar la entrada vesc_ok (telemetría UART)          */
} tl_config_t;

/* ---- Entradas de un tick ---- */
typedef struct {
    uint16_t adc;          /* lectura del hall 0..1023 (promediada)                  */
    uint8_t kill_cord_ok;  /* 1 = cordón puesto y circuito cerrado                   */
    uint8_t estop_ok;      /* 1 = seta liberada y circuito cerrado                   */
    uint8_t vesc_ok;       /* 1 = VESC sin falla (o telemetría no usada)             */
    uint8_t _pad[3];
} tl_inputs_t;

/* ---- Salidas de un tick ---- */
typedef struct {
    float cmd;        /* comando final [-1, 1] tras zona muerta, expo, límite, dwell y rampa */
    float target;     /* objetivo antes de rampa/dwell (diagnóstico)                         */
    uint16_t ppm_us;  /* ancho de pulso PPM [ppm_min_us, ppm_max_us]; neutro = ppm_center_us  */
    uint16_t flags;   /* flags instantáneos | latcheados                                     */
    uint8_t state;    /* TL_DISARMED ... TL_FAULT                                            */
    uint8_t enable;   /* 1 = habilitar VESC (transistor que lleva ADC2 a GND); 0 = kill SW   */
    uint8_t _pad[2];
} tl_outputs_t;

/* ---- Contexto (estado persistente entre ticks) ---- */
typedef struct {
    tl_config_t cfg;
    tl_outputs_t last;     /* última salida                                          */
    float out;             /* comando con rampa                                      */
    uint32_t uptime_ms;    /* suma de dt (diagnóstico)                               */
    uint32_t arm_ms;       /* tiempo continuo en condición de armado                  */
    uint32_t zero_ms;      /* tiempo continuo con salida = 0 estando armado          */
    uint16_t latched;      /* flags latcheados desde el último armado                */
    uint16_t prev_adc;     /* muestra anterior (detección de saltos)                 */
    uint8_t prev_valid;    /* prev_adc utilizable                                    */
    uint8_t armed;         /* 1 = armado                                             */
    uint8_t arm_run;       /* 1 = el tick anterior ya cumplía la condición de armado */
    uint8_t zero_run;      /* 1 = el tick anterior ya tenía salida 0 (armado)        */
    int8_t last_dir;       /* +1 / -1 último sentido con salida != 0; 0 = libre      */
    uint8_t cfg_err;       /* resultado de tl_config_check al iniciar (0 = OK)       */
    uint8_t _pad[2];
} tl_ctx_t;

/* Códigos de tl_config_check / tl_calibrate (bitmask; 0 = OK). */
#define TL_CFG_OK             0x00u
#define TL_CFG_ERR_ORDER      0x01u /* rev, center, fwd no monótonos                     */
#define TL_CFG_ERR_SPAN       0x02u /* semicarrera < min_half_span                       */
#define TL_CFG_ERR_RANGE      0x04u /* algún punto de calibración fuera de la banda válida */
#define TL_CFG_ERR_PARAM      0x08u /* parámetro fuera de rango (zona muerta, límites...) */
#define TL_CFG_ERR_PPM        0x10u /* PPM no monótono o fuera de 800..2200 us            */

/* Carga los valores por defecto (etiquetados en throttle_logic.c). cal_valid queda en 0. */
void tl_default_config(tl_config_t *cfg);
/* Valida la configuración. Devuelve TL_CFG_OK o bitmask de errores. */
uint8_t tl_config_check(const tl_config_t *cfg);
/* Valida y guarda una calibración (rev, center, fwd); pone cal_valid = 1 si es válida. */
uint8_t tl_calibrate(tl_config_t *cfg, uint16_t adc_rev, uint16_t adc_center, uint16_t adc_fwd);
/* Inicializa el contexto: estado DISARMED, salida neutra. Copia cfg. */
void tl_init(tl_ctx_t *s, const tl_config_t *cfg);
/* Paso de la lógica: dt_ms = tiempo desde el tick anterior (el llamador lo mide con millis()). */
tl_outputs_t tl_tick(tl_ctx_t *s, const tl_inputs_t *in, uint32_t dt_ms);

/* Auxiliares puros (expuestos para tests y telemetría). */
float tl_position(const tl_config_t *cfg, uint16_t adc);   /* -1..1 sin zona muerta    */
float tl_shape(const tl_config_t *cfg, float pos);         /* zona muerta+expo+límite  */
uint16_t tl_cmd_to_ppm(const tl_config_t *cfg, float cmd); /* [-1,1] -> us             */
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
