# Electrónica y control (Pasada 1: esquema mínimo; Pasada 2: diagrama, tabla de verdad, firmware y tests)

Cadena: batería LiFePO4 24 V → fusible ≤ 178 mm del borne → desconectador → contactor de
emergencia (bobina en serie con kill cord + seta) → ESC VESC → motor. Acelerador: puño con
imán + sensor hall lineal → MCU (rampa, zona muerta, retardo de inversión, límite de reversa,
watchdog, armado solo con acelerador en cero) → ESC (PPM con timeout).
