; vesc_perfil.lisp — Perfil de velocidad del waterjet P1 en el VESC (LispBM, FW >= 6.00).
;
; Lee la línea de perfil que manda el Arduino (D12 -> 10 k -> ADC1 del puerto COMM, 20 k a GND:
; ALTO ≈ 3,3 V = ABIERTO; BAJO, MCU en reset o cable cortado = COSTA) y cambia el tope de ERPM:
;   COSTA   = l_max_erpm legal (5 kn dentro de los 300 m)      -> ERPM-COSTA
;   ABIERTO = techo técnico (fuera de la franja de 300 m)        -> ERPM-ABIERTO
; El Arduino solo pone ALTO estando ARMADO, con el selector pasado por costa y el acelerador en 0
; (throttle_logic.c, README §5.2 regla 7); este script solo traduce la línea.
;
; Valores: 04_diseno/electronica/electronica.json -> vesc_values.l_max_erpm / vesc_values.erpm_tech
; (los genera calc_electronica.py desde sizing.json; tests/test_firmware.py exige que coincidan).
; La configuración GUARDADA en el VESC queda en COSTA (README §6): si el script no corre, el bote
; queda en 5 kn. conf-set no escribe la flash: al reiniciar vuelve el valor guardado (COSTA).
;
; API usada [VERIFICADO: vedderb/bldc master lispBM/README.md, leído 2026-10-01]:
;   (get-adc 0)          tensión de ADC1 del puerto COMM [V]           (FW 6.00+)
;   (conf-set 'l-max-erpm v)  aplica en el acto, no guarda en flash     (FW 6.00+)
;   (loopwhile cond { ... }), (sleep s)                               (FW 6.00+)
;   define, if (con rama else explícita), and, =, >, >=, { } = progn, t, nil
;     [VERIFICADO: svenssonjoel/lispBM master doc/lbmref.md, leído 2026-10-01]
; Que el ADC1 del Flipsky FSESC 75350 esté libre en el conector COMM con la app PPM:
;   [ESTIMADO: verificar en VESC Tool, Realtime Data -> ADC1 debe seguir a D12].

(define erpm-costa 9200.0)    ; electronica.json vesc_values.l_max_erpm  [CALCULADO] (lo escribe calc_electronica.py)
(define erpm-abierto 24100.0)  ; electronica.json vesc_values.erpm_tech   [CALCULADO] (lo escribe calc_electronica.py)
(define v-umbral 1.65)        ; mitad de 3,3 V [SUPUESTO]
(define n-req 4)              ; 4 muestras seguidas en ALTO (4 × 50 ms) para pasar a ABIERTO [SUPUESTO]

(define n-alto 0)
(define perfil 0)             ; 0 = COSTA, 1 = ABIERTO
(conf-set 'l-max-erpm erpm-costa)   ; al arrancar: COSTA siempre

(loopwhile t {
    (if (> (get-adc 0) v-umbral)
        (if (< n-alto n-req) (define n-alto (+ n-alto 1)) nil)
        (define n-alto 0))
    ; COSTA en cuanto la línea cae (una muestra); ABIERTO solo tras n-req muestras en ALTO
    (if (and (= perfil 0) (>= n-alto n-req))
        { (conf-set 'l-max-erpm erpm-abierto) (define perfil 1) }
        nil)
    (if (and (= perfil 1) (= n-alto 0))
        { (conf-set 'l-max-erpm erpm-costa) (define perfil 0) }
        nil)
    (sleep 0.05)
})
