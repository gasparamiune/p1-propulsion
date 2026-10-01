# R06 — Eléctrica: BLDC / ESC (VESC) / kill switch / baterías / normas / corrosión galvánica

Proyecto P1: propulsión eléctrica, mini lancha de aluminio tipo jon boat (< 2,5 m), Als Fjord (Sønderborg). Fecha de la investigación: 2026-10-01.
Etiquetas: **[VERIFICADO: url]** = leído en esta sesión · **[ESTIMADO: base]** · **[SUPUESTO]**. Si algo no se pudo abrir: "buscar: …".

---

## 0. Resumen ejecutivo (lo que hay que hacer)

1. **Motor SECO arriba del agua (cola larga) es la opción eléctricamente más sana**: un outrunner inundado en agua salada exige desarmarlo y enjuagarlo después de *cada* uso según instrucciones publicadas en foil.zone para el Maytech 6579 (post del usuario PaulKirdy; el post **no** las atribuye explícitamente a Maytech — corregido en verificación). Con la cola larga el motor solo recibe salpicaduras → protector + rodamientos inox/híbridos + enjuague.
2. **VESC (Flipsky/Makerbase 75100)**: el firmware abierto tiene *safe start*, timeout, chequeo de rango ADC, kill switch por software y límites térmicos, **pero los valores por defecto no sirven para un bote** (corte de batería por defecto 10 V/8 V, rango ADC 0,0–3,5 V que en la práctica no detecta un cable cortado). Hay que configurarlos. (Los defaults genéricos de `mcconf_default.h` son sobrescritos por el archivo de hardware del 75_100: `l_max_voltage` = 90 V, `l_in_current_max` = 100 A, filtro de fase = false — ver §2.4.)
3. **Peligro concreto del modo ADC "Current Reverse Center"**: si se corta el cable del cursor del acelerador y la entrada cae a ~0 V, con `voltage_min = 0,0` (default) el VESC lo interpreta como **reversa máxima**. Poner `voltage_min` ≈ 0,3 V.
4. **El antichispa MOSFET NO es un elemento de seguridad**: sus MOSFET pueden fallar en cortocircuito (queda encendido; caso de foro con un antichispa Buildkit Boards). El kill switch debe abrir un **contactor monoestable** (bobina en serie con el cordón), no solo pedir "apagar" a la electrónica.
5. **Batería: LiFePO4**. En ensayo ARC la LFP no llegó a disparar runaway (Tmax 239 °C) mientras la NMC811 disparó a 147 °C y llegó a 463 °C. Penalidad: ~128 Wh/kg a nivel pack comercial.
6. **Tensión: preferir 12S LFP (38,4 V nominal, 43,8 V máx.)** en lugar de "48 V" (15–16S). 16S LFP cargado = 58,4 V: supera el fusible MRBF (58 V máx.), la "tensión de seguridad" de 50 V CC de ISO 16315, y la tensión máxima de interrupción del contactor SW80 estándar (48 V).
7. **Normas**: el bote (< 2,5 m) queda **fuera** de la Directiva 2013/53/UE (2,5–24 m). Como guía voluntaria aplica **ISO 16315:2026** (propulsión eléctrica, 2ª ed., reemplaza a la de 2016) + ISO 13297:2020 (resto del sistema CC ≤ 50 V) + ABYC E-11 (fusible a ≤ 7"/175 mm del borne, valor que da ABYC; fusible ≤ ampacidad del cable).
8. **Galvánica**: eje inox 316 pasivo (−150 mV) vs aluminio 5083/6061 (−820 mV) = ~670 mV de diferencia (límite práctico 200 mV). Aislar eje/tubo del casco (las piezas de PETG y la correa ya lo hacen), ánodo de **aluminio** (no zinc ni magnesio) en agua salobre, nada de latón bajo el agua.

---

## 1. Motor BLDC en ambiente marino

### 1.1 Comparación de configuraciones

| Configuración | Exposición | Mantenimiento reportado | Ventaja | Riesgo principal |
|---|---|---|---|---|
| **Outrunner seco arriba del agua (cola larga)** | Salpicadura/niebla salina | Enjuague con agua dulce + spray anticorrosivo [ESTIMADO: extrapolación de práctica eFoil, ver 1.2] | Motor barato estándar (patinete/eBike), fácil de cambiar, sin sellos | Corrosión de imanes/laminaciones por niebla salina si no se protege; refrigeración por aire limitada |
| Outrunner **inundado** (pod sumergido, estilo eFoil) | Inmersión continua en agua salobre | Post de foil.zone "How to maintain Maytech 6579…" (usuario PaulKirdy; no dice explícitamente que el texto sea de Maytech): *"take apart the rotor and stator, clean stator and rotor with fresh water after every time use, must remove salt on the surface of magnets and lamination… apply anti-rust paint"* [VERIFICADO: https://foil.zone/t/how-to-maintain-maytech-6579-waterproof-outrunner-motor/24647] | Refrigeración excelente por agua: *"water flows through it and therefore has excellent cooling properties"* [VERIFICADO: https://e-surfer.com/en/blog/build-your-own-e-foilboard-diy-e-foil-part-2/] | Desarme después de cada salida = inaceptable para uso recreativo; usuario reporta un motor Flipsky *"seized with salt water"* [VERIFICADO: https://foil.zone/t/waterproof-6374-with-no-shaft-for-efoil/17043] |
| Inrunner **sellado** IP68 (ej. Flipsky FS65161) | Inmersión | Fabricante: sello cerámico, vida ~10 000 h limitada por rodamiento, "anti-corrosion… works in the sea" [VERIFICADO: https://flipsky.net/blogs/vesc-tool/more-known-about-fs65161-motor] (afirmación del vendedor, no ensayo independiente) | Sin mantenimiento declarado; e-surfer: inrunners *"maintenance-free"*, se recomienda llenarlos de aceite [VERIFICADO: https://e-surfer.com/en/blog/build-your-own-e-foilboard-diy-e-foil-part-2/] | Motor de 6 kW/6–20S sobredimensionado para 0,3–0,5 kW; precio y peso altos; sello dinámico = punto único de falla |

### 1.2 Recubrimientos (estator/imanes)
- Práctica eFoil para outrunners en agua salada: *"seal the stator with thermal epoxy resin to prevent corrosion"* o baño periódico con aceite tipo Corrosion-X [VERIFICADO: https://e-surfer.com/en/blog/build-your-own-e-foilboard-diy-e-foil-part-2/].
- Para el motor SECO de la cola larga: barniz/epoxi sobre bobinado (la mayoría ya viene barnizado) [SUPUESTO], spray tipo Corrosion-X/ACF-50 sobre imanes y laminaciones expuestas cada ~10 salidas [ESTIMADO: práctica eFoil adaptada], **cubierta impresa en PETG con drenaje inferior y ventilación hacia abajo** (no hermética: una carcasa sellada atrapa condensación salina) [ESTIMADO: criterio de diseño].
- Sensor NTC de temperatura de motor conectado al VESC: el firmware lo soporta (`MCCONF_M_MOTOR_TEMP_SENS_TYPE = TEMP_SENSOR_NTC_10K_25C` por defecto) [VERIFICADO: https://raw.githubusercontent.com/vedderb/bldc/master/motor/mcconf_default.h].

### 1.3 Rodamientos

| Material | Dato | Fuente |
|---|---|---|
| Acero cromo (estándar en motores RC) | e-surfer: *"the simple steel bearings must be replaced with stainless steel or ceramic bearings"* | [VERIFICADO: https://e-surfer.com/en/blog/build-your-own-e-foilboard-diy-e-foil-part-2/] |
| Inox AISI 440C | Capacidad de carga ≈ **20 % menor** que acero cromo; **ojo**: SMB dice que el 440 *"will corrode in seawater environments"* (sí resiste agua dulce) | [VERIFICADO: https://www.smbbearings.com/technical/bearing-material.html] |
| Inox 316 | *"Suitable for very low load and low speed only"*; no endurecible; pitting en agua de mar > 30 °C y **corrosión en grietas ya a 10–15 °C**; poco apto sumergido permanentemente sin flujo | [VERIFICADO: https://www.smbbearings.com/technical/bearing-material.html] |
| Nitruro de silicio **full cerámico** (Si3N4, prefijo CCSI) | *"Very good corrosion resistance to water, salt water, acids and alkalis"*; acepta solo ~65–75 % de la carga y ~25 % de la velocidad límite de un rodamiento de acero; frágil a impactos | [VERIFICADO: https://www.smbbearings.com/technical/bearing-material.html] |
| Híbrido (aros de acero + bolas Si3N4) | La resistencia a corrosión es la de los **aros** (si son 440C, corroen en agua de mar); ventaja: velocidad +30–40 %, mejor con poca lubricación | [VERIFICADO: https://www.smbbearings.com/technical/bearing-material.html] |

**Recomendación** (corregida en verificación): motor seco con salpicadura salina → 440C sellado 2RS (o híbrido con aros 440C) **asumiendo que corroe** → enjuague con agua dulce + inhibidor y reemplazo como consumible [ESTIMADO: criterio, la fuente dice que el 440 corroe en agua de mar]; full cerámico Si3N4 solo si la carga/velocidad del motor cabe en el 65–75 % / 25 % indicado. Los bujes del eje en el agua son tema de otro informe (lubricados por agua).

---

## 2. VESC: control con marcha atrás y funciones de seguridad (código fuente abierto)

### 2.1 Hardware candidato

| ESC | Tensión | Corriente | Precio | Notas | Fuente |
|---|---|---|---|---|---|
| Flipsky 75100 (single; "PCB aluminio" **no figura** en la página citada [NO VERIFICADO]; 85×50,7×33,8 mm) | 14–84 V (4–20S) | 100 A cont. / 120 A máx. | 79 USD (oferta; lista 99 USD) | Specs: *"Phase filter: No"*. **Advertencia del vendedor**: *"Phase filering is not available for Flipsky ESC75100 and 75200! Please turn off the phase filter … when use firmware version on or above 5.3 … Without turning off the phase filter will result in esc damage. Please do not restore the default parameters when using the wizard interface."*; también *"It is recommended to keep firmware 5.2 from factory ship"* | [VERIFICADO: https://hobbygoat.com/products/flipsky-75100-75v-100a-single-esc] |
| Makerbase VESC 75100 V2 | 14–84 V (4–20S) | 100 A cont. / 120 A máx. ("depends on external heat dissipation") | 114,99 GBP | MOSFET HYG015N10NS1TA, STM32F405, 103×58×18,5 mm, cables 12 AWG | [VERIFICADO: https://escooter-parts.co.uk/products/makerbase-vesc-75100-v2-84v-100a-esc-with-alu-pcb-based-on-vesc] |

Ninguno declara grado IP → caja estanca con la PCB de aluminio atornillada a una placa disipadora [ESTIMADO: criterio de diseño]. Potencia real del proyecto 0,3–1,5 kW [ESTIMADO: ver §4.4] → corriente batería ≤ 45 A: el 75100 sobra en corriente; elegirlo por precio/firmware, no por potencia.

### 2.2 Versión de firmware (importa para el kill switch)
- FW **5.02** (`datatypes.h` del tag 5.02): **no existe** `KILL_SW_MODE` [VERIFICADO: https://raw.githubusercontent.com/vedderb/bldc/5.02/datatypes.h].
- FW **5.03**: aparece `KILL_SW_MODE` con 4 modos (PPM_LOW/HIGH, ADC2_LOW/HIGH) [VERIFICADO: https://raw.githubusercontent.com/vedderb/bldc/release_5_03/datatypes.h].
- master actual: 10 modos (agrega ADC3, SWDIO, SWCLK) [VERIFICADO: https://raw.githubusercontent.com/vedderb/bldc/master/datatypes.h].
- Conflicto: Flipsky recomienda quedarse en 5.2 por el filtro de fase; pero 5.2 no tiene kill switch por software. **Decisión: FW ≥ 5.03 con `foc_phase_filter_enable = false`** (Flipsky) o comprar un VESC con filtro de fase (buscar: "VESC 75100 phase filter hardware Makerbase V2").
- **Atenuante hallado en verificación**: en el firmware oficial, el archivo de hardware del 75100 (`hwconf/flipsky/hw_75_100.h`, igual en `hw_75_100_V2.h`) define `MCCONF_FOC_PHASE_FILTER_ENABLE false` y tiene los pines `PHASE_FILTER_*` comentados, tanto en `release_6_00`, `release_6_02`, `release_6_05` como en master [VERIFICADO: https://raw.githubusercontent.com/vedderb/bldc/master/hwconf/flipsky/hw_75_100.h], [VERIFICADO: https://raw.githubusercontent.com/vedderb/bldc/release_6_00/hwconf/flipsky/hw_75_100.h]. Con FW ≥ 6.00 (target "75_100") el default ya es "filtro apagado"; igual **verificar en VESC Tool tras el asistente** (el vendedor pide no restaurar defaults desde el wizard). En `release_5_03` no existe ese archivo (404) → no pude verificar el default de 5.03 para este hardware.

### 2.3 Modos de control con reversa (enumeraciones reales del firmware)

| App | Modo (`datatypes.h`) | Comportamiento (de `app_adc.c` / `app_ppm.c`) | Uso en el bote |
|---|---|---|---|
| ADC | `ADC_CTRL_TYPE_CURRENT_REV_CENTER` ("Current Reverse Center") | Mapea `voltage_start`→`voltage_center`→`voltage_end` a −1…0…+1; corriente proporcional, reversa debajo del centro | **Palanca única tipo náutica con retén central** (avance/neutro/reversa). Recomendado |
| ADC | `ADC_CTRL_TYPE_DUTY_REV_CENTER` | Igual pero manda ciclo de trabajo (≈ RPM ∝ palanca) | Alternativa: sensación "de fueraborda", evita embalamiento si la hélice sale del agua [ESTIMADO: física del control en duty vs corriente] |
| ADC | `ADC_CTRL_TYPE_CURRENT_REV_BUTTON` | Invierte el signo si el botón de reversa está presionado | Acelerador de pulgar + interruptor FWD/REV |
| PPM | `PPM_CTRL_TYPE_CURRENT` | Positivo acelera; negativo frena si gira hacia adelante y acelera en reversa cuando rpm ≤ 0 | Control remoto RC (inalámbrico) |
| PPM | `PPM_CTRL_TYPE_CURRENT_BRAKE_REV_HYST` | Freno primero, reversa solo tras volver a neutro y con rpm < `max_erpm_for_dir` (histéresis 20 %) | Tipo "auto RC" |
| PPM | `PPM_CTRL_TYPE_CURRENT_NOREV_BRAKE` | Sin reversa (negativo = freno) | No sirve (reversa obligatoria) |
| PPM | `PPM_CTRL_TYPE_CURRENT_SMART_REV` | **Corregido**: sí tiene reversa, pero indirecta: si la palanca está < −92 % con el motor casi detenido (duty < 1,5·`l_min_duty`), pasa a control por ciclo de trabajo hacia atrás limitado por `smart_rev_max_duty` con rampa `smart_rev_ramp_time` (default 3,0 s) | Posible pero poco intuitivo para maniobrar en un muelle; preferir `CURRENT` o `CURRENT_BRAKE_REV_HYST` |

Fuentes: [VERIFICADO: https://raw.githubusercontent.com/vedderb/bldc/master/applications/app_adc.c], [VERIFICADO: https://raw.githubusercontent.com/vedderb/bldc/master/applications/app_ppm.c], [VERIFICADO: https://raw.githubusercontent.com/vedderb/bldc/master/datatypes.h].

### 2.4 Parámetros por defecto relevantes (firmware master)

| Parámetro | Default | Archivo | Comentario para el bote |
|---|---|---|---|
| `APPCONF_TIMEOUT_MSEC` | 1000 ms | appconf_default.h | Sin comando válido (PPM/UART/CAN) durante 1 s → aplica corriente de freno |
| `APPCONF_TIMEOUT_BRAKE_CURRENT` | 0,0 A | appconf_default.h | 0 = rueda libre. Para hélice está bien (no hace falta frenar) |
| `APPCONF_KILL_SW_MODE` | `KILL_SW_MODE_DISABLED` | appconf_default.h | **Habilitar** (ver §3) |
| `APPCONF_PPM_SAFE_START` / `APPCONF_ADC_SAFE_START` | true / true | appconf_default.h | Mantener |
| `APPCONF_PPM_HYST` / `APPCONF_ADC_HYST` (zona muerta) | 0,15 / 0,15 | appconf_default.h | 15 % de zona muerta: razonable para palanca con retén |
| `APPCONF_PPM_PULSE_START/CENTER/END` | 1,0 / 1,5 / 2,0 ms | appconf_default.h | Calibrar con el emisor |
| `APPCONF_ADC_VOLTAGE_START/CENTER/END` | 0,9 / 2,0 / 3,0 V | appconf_default.h | Calibrar con la palanca |
| `APPCONF_ADC_VOLTAGE_MIN / MAX` (chequeo de rango) | **0,0 / 3,5 V** | appconf_default.h | **Con 0,0 V no detecta un cursor cortado → reversa máxima en REV_CENTER**. Poner ~0,3 V / ~3,1 V |
| `APPCONF_ADC_RAMP_TIME_POS / NEG` | 0,3 s / 0,1 s | appconf_default.h | Subir a ~1 s para no tirar a nadie al agua y cuidar la correa [ESTIMADO] |
| `APPCONF_PPM_RAMP_TIME_POS / NEG` | 0,4 s / 0,2 s | appconf_default.h | idem |
| `APPCONF_PPM_MAX_ERPM_FOR_DIR` | 4000 | appconf_default.h | Umbral para permitir reversa en modo HYST |
| `APPCONF_ADC_UPDATE_RATE_HZ` | 500 Hz | appconf_default.h | — |
| `MCCONF_L_CURRENT_MAX / MIN` (motor) | 60 / −60 A | mcconf_default.h | Ajustar al motor elegido |
| `MCCONF_L_IN_CURRENT_MAX / MIN` (batería) | 99 / −60 A genérico; **100 / −100 A en el target 75_100 y 75_100_V2** (hwconf) | mcconf_default.h / hw_75_100.h | **Bajar a ≤ 80 % de la corriente continua del BMS** (ej. 40 A para BMS de 50 A) para no disparar el BMS en el fiordo; y `l_in_current_min` (regeneración) a −5…−10 A si el BMS no admite carga alta [ESTIMADO: criterio] |
| `MCCONF_L_BATTERY_CUT_START / END` | **10,0 / 8,0 V** (el hwconf 75_100 no lo sobrescribe) | mcconf_default.h | **Inútil para 12S**: poner ~36,0 / 33,6 V (3,0 / 2,8 V por celda LFP) [ESTIMADO: rango LFP típico] |
| `MCCONF_L_MAX_VOLTAGE` | 57,0 V genérico; **90,0 V en el target 75_100 y 75_100_V2** (`HW_LIM_VIN` 6–120 V) | mcconf_default.h / hw_75_100.h | **Corregido**: con el firmware del 75100 el límite de 57 V **no aplica**; 16S LFP (58,4 V) no dispara sobretensión por software. El límite real es el hardware: 84 V (vendedor) |
| `MCCONF_L_MIN_VOLTAGE` | 8,0 V (75_100) / 12,0 V (75_100_V2) | hw_75_100*.h | — |
| `MCCONF_L_LIM_TEMP_FET_START / END` | 85 / 100 °C | mcconf_default.h | Limitación lineal de corriente entre ambos |
| `MCCONF_L_LIM_TEMP_MOTOR_START / END` | 85 / 100 °C | mcconf_default.h | Requiere NTC en el motor |
| `MCCONF_L_MAX_DUTY` | 0,95 | mcconf_default.h | — |

Fuentes: [VERIFICADO: https://raw.githubusercontent.com/vedderb/bldc/master/applications/appconf_default.h], [VERIFICADO: https://raw.githubusercontent.com/vedderb/bldc/master/motor/mcconf_default.h], [VERIFICADO: https://raw.githubusercontent.com/vedderb/bldc/master/hwconf/flipsky/hw_75_100.h], [VERIFICADO: https://raw.githubusercontent.com/vedderb/bldc/master/hwconf/flipsky/hw_75_100_V2.h]. Nota: qué target de firmware usa el Makerbase 75100 V2 no lo verifiqué (buscar: "Makerbase 75100 V2 VESC Tool firmware target").

### 2.5 Cómo funcionan las protecciones (leído en el código)

| Función | Implementación verificada | Consecuencia práctica |
|---|---|---|
| **Safe start ADC** | `MIN_MS_WITHOUT_POWER 500`: si la palanca no estuvo en cero ≥ 500 ms (tras encender o tras una falla, si `safe_start != SAFE_START_NO_FAULT`) se manda `mc_interface_set_brake_current(timeout_get_brake_current())` | Arrancar con la palanca adelantada NO mueve el motor hasta volver a neutro ½ s |
| **Safe start PPM** | `MIN_PULSES_WITHOUT_POWER 50` pulsos en neutro | ídem con radio (≈ 1 s a 50 Hz [ESTIMADO]) |
| **Timeout PPM** | `if (timeout_has_timeout() \|\| servodec_get_time_since_update() > timeout_get_timeout_msec())` → corriente de freno de timeout y `pulses_without_power = 0` | Si se pierde la señal de radio: rueda libre a los 1000 ms y re-exige neutro (safe start) |
| **Timeout ADC** | (Precisado en verificación) El ADC llama `timeout_reset()` en cada ciclo **en que pasa safe start y chequeo de rango** (y no está "detached"); si `range_ok` falla, hace `continue` antes del reset → freno inmediato y, además, el timeout general vence a los 1000 ms. Pero una lectura **dentro de rango** nunca produce timeout: la única defensa contra cable cortado es que el cable cortado caiga **fuera** de `range_ok = read_voltage >= voltage_min && read_voltage <= voltage_max`. Con REV_CENTER, 0 V se mapea a −1 (reversa máxima) tras `utils_truncate_number(&pwr, 0.0, 1.0)` y `pwr*2−1` | Configurar `voltage_min/max` es obligatorio; agregar pull-down/pull-up en la entrada para que un cable cortado caiga a un riel conocido fuera de rango [ESTIMADO: criterio de diseño] |
| **Timeout general (UART/CAN)** | `timeout.c`: si `timeout_msec != 0` y pasa ese tiempo sin `timeout_reset()` → freno con `timeout_brake_current` en ambos motores | Útil si se controla por UART desde un microcontrolador |
| **Kill switch por software** | `timeout.c`: `KILL_SW_MODE_PPM_HIGH` → `kill_sw = palReadPad(...)`; `ADC2_HIGH` → `ADC_VOLTS(ADC_IND_EXT2) > 1.65`; si `kill_sw` → `mc_interface_set_brake_current(...)` + `mc_interface_ignore_input_both(20)` | Con pull-up a 3,3 V y cordón que cierra a GND con el clip puesto: clip afuera **o cable cortado** → nivel alto → motor cortado (fail-safe). Un cortocircuito a GND por agua salada sí falla al lado peligroso → por eso el kill por software es **secundario** |
| Rampas | `utils_step_towards` con `ramp_time_pos/neg` | — |

Fuentes: [VERIFICADO: https://raw.githubusercontent.com/vedderb/bldc/master/applications/app_adc.c], [VERIFICADO: https://raw.githubusercontent.com/vedderb/bldc/master/applications/app_ppm.c], [VERIFICADO: https://raw.githubusercontent.com/vedderb/bldc/master/timeout.c].
No verificado: si el firmware activa pull-up interno en el pin de kill → usar **resistencia externa 10 kΩ a 3,3 V** [SUPUESTO: valor típico].

### 2.6 Riesgos de control específicos de hélice
- **Modo corriente + hélice fuera del agua** (kick-up, ola, ventilación): el torque comandado se mantiene y el motor acelera hasta el límite de ERPM [ESTIMADO: comportamiento de un lazo de corriente sin carga]. Mitigar: `l_max_erpm` ajustado a RPM máx. de hélice × reducción × pares de polos, o usar `DUTY_REV_CENTER`.
- Reversa con correa HTD: la rampa negativa por defecto (0,1 s) implica inversión brusca de torque → subir a ~0,5–1 s [ESTIMADO].

---

## 3. Corte de energía: antichispa, kill switch con cordón, contactor y precarga

### 3.1 Interruptor antichispa (Flipsky)

| Ítem | Dato | Fuente |
|---|---|---|
| Rango Pro (alu PCB) | 3S–14S (12–60 V); 100 A continuo con caja de aluminio V3.0, 60 A con disipador; 200 A máx. | [VERIFICADO: https://flipsky.net/products/flipsky-antispark-switch-pro-with-aluminum-pcb-case-200a-for-electric-skateboard-ebike-scooter-robots] |
| Precio | 33 USD (disipador) / 43 USD (alu PCB) / 48 USD (caja alu) | ídem |
| Advertencia | *"DO NOT power on switch without the LED button connected"*; *"Make sure the switch is off before applying power"* | ídem |
| Tipo de botón | **Pro: autoenclavante (mantenido)**; **Smart: pulsador momentáneo**; ambos usan pulsador con contactos NA+NC | [VERIFICADO: https://flipsky.net/blogs/vesc-tool/something-you-should-know-about-flipsky-anti-spark-switch] |
| Qué pasa si se corta el cable de control | **No documentado** por Flipsky (buscar: "Flipsky antispark button disconnected while on behaviour") | — |
| Modo de falla (antichispa MOSFET en general) | **Corregido**: el hilo trata de un antichispa de **Buildkit Boards** (no Flipsky); el autor lo describe *"stuck in the on position"* tras resoldarlo; usuario Gamer43: *"Yes, MOSFETs failed short-circuit."* (diagnóstico de foro, no análisis de falla); usuario Dareno: *"the most reliable way to control power to an ESC…is to use an XT90S loopkey"*. Extrapolar a Flipsky = [ESTIMADO: mismo principio, MOSFET en serie que falla en corto] | [VERIFICADO: https://forum.esk8.news/t/right-as-i-finished-the-build-i-broke-the-anti-spark-switch/22247] |
| Consumo en reposo (Smart V1) | 2,5 mA, con revisión de hardware anunciada a 300–400 µA | [VERIFICADO: https://forum.esk8.news/t/flipsky-smart-antispark-issues-feedback-and-review/11908] |

Conclusión: el antichispa sirve como **arranque suave (precarga) + encendido diario**, nunca como kill switch. 60 V máx. → incompatible con 16S LFP (58,4 V) sin margen.

**XT90-S**: conector con resistencia integrada: *"The connection first goes through an integrated resistor, allowing the capacitors on the controllers to be charged with controlled current"*; 45 A continuo / 90 A corto; 3,69 EUR el par [VERIFICADO: https://www.rotorama.com/product/xt90s-antispark-konektor-par]. Buena "llave" de aislamiento manual barata.

### 3.2 Kill switch náutico con cordón (lanyard)

| Tipo | Con clip puesto | Clip arrancado | Cable cortado | Uso típico |
|---|---|---|---|---|
| "Normally open-circuit" (encendido por magneto) | Contacto **abierto** | Contacto **cierra** → cortocircuita el encendido | Motor **sigue andando** (no fail-safe) | Fuerabordas de nafta: *"when the lanyard is in place the contacts of the kill switch are apart … when the lanyard is pulled out the contacts close the circuit"* [VERIFICADO: https://www.boatfittings.co.uk/how_to_fit_a_kill-switch] |
| **Cerrado con clip** (ej. Sea Dog SD-420487-1) | Contacto **cerrado** | Contacto **abre** | Circuito abierto = **parada** (fail-safe) | *"normally closed (Complete) with the lanyard clip in place on switch. When lanyard is pulled and clip is removed from switch, the circuit is open"*; *"Maximum 5A draw"* (**sin tensión especificada**); bornes de latón; cordón ~48" estirado; *"should be tested for proper function before each use"*; 15,69 USD [VERIFICADO: https://shop.hamiltonmarine.com/products/sea-dog-switch-kill-gray-cap-with-lanyard-normall-closed-29836.html] |

**Regla de cableado fail-safe**: usar el contacto "cerrado con clip" **en serie con la bobina de un contactor monoestable**: cordón tirado, cable cortado, conector suelto o bobina quemada → contactor abre. 5 A del interruptor ≫ corriente de bobina (~0,15–0,3 A a 48 V para 7–13 W) [ESTIMADO: P/V con datos SW80 abajo]. **Ojo** (verificación): el 5 A no tiene tensión declarada (producto pensado para encendido de 12 V); abrir 0,2–0,3 A de bobina inductiva a ~44 V CC puede arquear → supresión diodo+resistencia/TVS en la bobina es obligatoria también para proteger el interruptor [ESTIMADO: criterio]. Un segundo juego de contactos (o un relé auxiliar) puede alimentar la entrada de kill del VESC para cortar el torque **antes** de que abra el contactor.
No usar un "remote battery switch" **biestable/enclavado**: conserva el estado sin energía de bobina → no es fail-safe. Respaldo: la hoja del SW80 lista la opción *"Magnetic Latching (Not fail safe)"* [VERIFICADO: https://www.albrightinternational.com/wpcms/wp-content/uploads/2020/08/SW80-Data-Sheet.pdf] → pedir el SW80 **sin** sufijo M.

### 3.3 Contactor (ejemplo con datos: Albright SW80)

| Dato | Valor | Fuente |
|---|---|---|
| Corriente térmica | 100 A (interrumpido) / 125 A (no interrumpido) | [VERIFICADO: https://www.albrightinternational.com/wpcms/wp-content/uploads/2020/08/SW80-Data-Sheet.pdf] |
| Capacidad de corte en falla (UL583, τ 5 ms) | SW80: 600 A @ 48 V; **SW80B: 600 A @ 96 V** | ídem |
| Tensión máx. recomendada de contactos | **SW80: 48 V CC con corte bajo carga**, 60 V sin corte bajo carga; SW80B: 96 V | ídem |
| Bobina | 6–240 V CC; continua 7–13 W; prolongada 13–15 W | ídem |
| Tiempo de apertura | 5 ms sin supresión; **50 ms con diodo**; 8–20 ms con diodo+resistencia | ídem |
| Durabilidad mecánica | > 5×10⁶ ciclos; temp. −40 a +60 °C; caída 40 mV/polo a 100 A | ídem |
| Carga capacitiva | Declarado apto para cargas *"Capacitive and Inductive"* | ídem |
| Corte resistivo (UL508) | SW80: 190 A @ 60 V CC; SW80B: 190 A @ 96 V CC | ídem (agregado en verificación) |
| Tensión de cierre / apertura de bobina | Cierre máx. **66 % Us** (tipo continuo); caída 10–25 % Us; cierre típico 20 ms | ídem (agregado en verificación) |
| Opciones | **SW80P = IP66** (hoja aparte); *"Magnetic Latching (Not fail safe)"*; peso 350 g | ídem (agregado en verificación) |

Implicancias: (a) con un pack ≤ 48 V a plena carga (12S/13S LFP) alcanza el SW80 estándar; con 15–16S hace falta SW80B; (b) supresión **diodo + resistencia o TVS**, no solo diodo (50 ms); (c) consumo de bobina 7–13 W × 2 h = 14–26 Wh ≈ 1,4–2,6 % de 1 kWh [ESTIMADO: cálculo]; (d) **tensión de bobina para 12S LFP (33,6–43,8 V)** (agregado en verificación): bobina de **48 V** → cierra hasta 0,66×48 = 31,7 V (< 33,6 V de corte) y a 43,8 V disipa ~(43,8/48)² = 0,83× la nominal; una bobina de 36 V a 43,8 V quedaría a 122 % Us (≈ 1,48× potencia) sin tolerancia de sobretensión publicada [ESTIMADO: cálculo con datos SW80] → **pedir bobina 48 V continua**; (e) en ambiente salino preferir **SW80P (IP66)** o meterlo en la caja estanca. Precio SW80: buscar: "Albright SW80 48V continuous price EU".

### 3.4 Precarga
- Por qué: *"there will be a very large inrush current (thousands of Amps) … which will damage the devices and weld contacts together"*; método: cerrar primero a través de resistencia y cerrar el contactor principal cuando la tensión de bus esté cerca de la de batería; τ = R·C; la fuente dice "95 % within 4 TAU, 99 % within 5 TAU" (matemáticamente 1−e⁻³ = 95 %, 1−e⁻⁴ = 98 %, 1−e⁻⁵ = 99,3 %: la fuente es conservadora), ejemplo 470 Ω / 800 µF → τ 376 ms [VERIFICADO: https://docs.prohelion.com/Battery_Management_Systems/Prohelion_BMS_D1000_Gen1/Operation/Precharge.html].
- Cálculo para este bote: C_bus del VESC ≈ 1–2 mF [ESTIMADO: no publicado], V = 43,8 V, R = 100 Ω → τ = 0,1–0,2 s, 5τ ≤ 1 s, I_pico 0,44 A, energía en R = ½CV² ≈ 1–2 J → resistencia de 5–10 W alcanza [ESTIMADO: cálculo].
- Solución barata sin lógica: **contactor (kill) aguas arriba + antichispa Flipsky aguas abajo** → el antichispa hace la carga suave del bus; si sus MOSFET fallan en corto solo se pierde la precarga, el kill sigue funcionando.
- **Conflicto detectado en verificación**: Flipsky advierte *"Make sure the switch is off before applying power"* [VERIFICADO: https://flipsky.net/products/flipsky-antispark-switch-pro-with-aluminum-pcb-case-200a-for-electric-skateboard-ebike-scooter-robots]. Con el Pro (botón **autoenclavante**) aguas abajo del contactor, cada vez que se repone el cordón el contactor le aplica tensión con el botón ya en ON → uso fuera de lo que el fabricante indica. Opciones: (1) procedimiento "antichispa OFF antes de reponer el cordón" (frágil); (2) reemplazar el antichispa por una **resistencia de precarga en paralelo con los contactos del contactor** (p. ej. 1 kΩ / 5 W → con kill abierto el bus queda alimentado a ≤ 44 mA, ~1,9 W disponibles: el motor no puede mover la hélice, pero el VESC queda vivo y los condensadores cargados, sin pico al cerrar) [ESTIMADO: cálculo; validar que el VESC no arranque en bucle a baja corriente]; (3) usar el Smart (pulsador momentáneo) cuyo comportamiento al aplicar tensión no está documentado (buscar: "Flipsky antispark smart power applied state").

### 3.5 Arquitectura recomendada (sistema aislado/flotante)

```
 BAT+ (12S LFP con BMS) ─[MRBF/ANL ≤175 mm del borne]─[Interruptor manual de batería / XT90-S llave]─┐
                                                                                                      │
                ┌── bobina contactor monoestable ── cordón Sea Dog (cerrado con clip) ── seta E-stop NC ┤ (bobina tomada después del fusible)
                │                                                                                     │
                └──────────────── contactor SW80 (NA) ── antichispa Flipsky (arranque suave) ── VESC ── motor
 BAT− ──────────────────────────────────────────────────────────────────────────────────── (negativo NO conectado al casco)
 Entrada kill VESC (ADC2_HIGH): pull-up 10 kΩ a 3,3 V + segundo contacto del cordón a GND → redundancia por software
```

| Falla | Resultado | ¿Seguro? |
|---|---|---|
| Piloto cae al agua (cordón tirado) | Bobina sin corriente → contactor abre (5–20 ms) + VESC en kill | Sí |
| Cable del cordón cortado | Igual que arriba | Sí |
| Contactor soldado | Queda el kill por software del VESC | Parcial → probar el contactor antes de cada salida |
| MOSFET del antichispa en corto | Pierde precarga; kill intacto | Sí |
| Cursor del acelerador cortado | Range check → freno (si `voltage_min` configurado) | Sí solo si se configura |
| Pérdida de señal RC (si PPM) | Timeout 1 s → rueda libre + safe start | Sí |
| Agua salada puentea el kill por software | Kill por software inefectivo; contactor sigue | Sí (por el contactor) |

---

## 4. Baterías

### 4.1 Comparación de químicas

| Propiedad | LiFePO4 (LFP) | Li-ion NMC | LiPo (pouch RC, LCO/NMC) | Fuente |
|---|---|---|---|---|
| Tensión nominal por celda | 3,20–3,30 V | 3,60–3,70 V | 3,6–3,7 V [ESTIMADO] | [VERIFICADO: https://batteryuniversity.com/article/bu-205-types-of-lithium-ion] |
| Energía específica (celda) | 90–120 Wh/kg (valor BU, celdas modernas ~160 [ESTIMADO: memoria técnica, no verificado]) | 150–220 Wh/kg | 150–200 Wh/kg (LCO) | [VERIFICADO: https://batteryuniversity.com/article/bu-205-types-of-lithium-ion] |
| Energía específica pack comercial | **~128 Wh/kg** (LiTime 36 V 50 Ah: 1920 Wh / 33,14 lb = 15,0 kg) | — | — | [VERIFICADO: https://www.litime.com/products/litime-36v-55ah-tm-lifepo4-battery-low-temp-protection-for-trolling-motors] (cálculo propio) |
| Ciclos | ≥ 2000 (BU); 4000+ al 100 % DoD (LiTime) | 1000–2000 | 500–1000 (LCO) | BU + LiTime |
| Runaway (valor genérico BU) | 270 °C | 210 °C | 150 °C (LCO) | [VERIFICADO: https://batteryuniversity.com/article/bu-205-types-of-lithium-ion] |
| ARC 18650 al 100 % SOC (Toer / Ttr / Tmax) | 62,50 °C / **no detectado** / **239,26 °C** | NCM811: 62,49 °C / **147,35 °C** / **462,52 °C** | LCO: Ttr 180,16 °C, Tmax 545,11 °C | [VERIFICADO: https://pmc.ncbi.nlm.nih.gov/articles/PMC10963544/] |
| Ranking de peligro (mismo estudio) | *"LCO > NCA > NCM811 >> LFP"* | | | ídem |
| Gas en runaway | 1,14 L/Ah (0,36 L/Wh) | NMC 18650 MH1: 2,4 L/Ah (0,66 L/Wh); celda NMC puede superar 600 °C | — | [VERIFICADO: https://pmc.ncbi.nlm.nih.gov/articles/PMC11927001/] |
| BMS | Integrado en packs náuticos | Requiere BMS | RC: normalmente **sin BMS** | [ESTIMADO: mercado] |

### 4.2 Inmersión en agua salada/salobre
- Mecanismo: *"When salt water causes a short circuit by linking the battery's positive and negative terminals, the resulting fire can last hours"*; al menos un vehículo **reencendió** tras extinguirse (huracán Ian) [VERIFICADO: https://www.eenews.net/articles/why-6-flooded-evs-burst-into-flames-after-hurricane-ian/].
- *"Salt dissolved in water … rapidly bridges the electrodes and triggers severe internal short circuits"*; los cloruros corroen terminales e interconexiones de cobre y aluminio; **el runaway puede ocurrir días o semanas después** [VERIFICADO: https://contractlaboratory.com/understanding-the-dangers-of-lithium-ion-batteries-submerged-in-water/] (fuente comercial, no revisada por pares).
- Electrólisis externa en bornes a 36–58 V: H₂ en el negativo y **Cl₂ en el positivo** en agua con cloruros [ESTIMADO: electroquímica básica, proceso cloro-álcali; no hallé fuente abierta específica — buscar: "lithium battery seawater immersion chlorine gas evolution terminals"].
- Consecuencias de diseño: (1) batería en caja estanca **sobre** el nivel de agua de sentina (ISO 13297 8.1, ver §5); (2) bornes cubiertos; (3) **protocolo**: batería que estuvo sumergida en agua salada = no cargar, aislar en exterior y descartar.
- Ejemplo comercial LiTime 36 V 50 Ah: **IP65** (no inmersión), BMS 50 A continuo / 250 A 1 s, carga 43,2 ± 0,6 V, **no carga bajo 0 °C** (reanuda a 5 °C), 395,99 USD [VERIFICADO: https://www.litime.com/products/litime-36v-55ah-tm-lifepo4-battery-low-temp-protection-for-trolling-motors]. IP65 → igual necesita caja/ubicación protegida.

### 4.3 Elección de cantidad de celdas en serie (límites duros)

| Configuración | V nominal | V máx. (carga) | ≤ 50 V "tensión de seguridad" ISO 16315 | Fusible MRBF (≤ 58 V) | SW80 corte bajo carga (≤ 48 V) | Antichispa Pro (≤ 60 V) | VESC 75100 (≤ 84 V) |
|---|---|---|---|---|---|---|---|
| **LFP 12S** ("36 V") | 38,4 | 43,8 | ✔ | ✔ | ✔ | ✔ | ✔ |
| LFP 13S | 41,6 | 47,45 | ✔ | ✔ | ✔ | ✔ | ✔ |
| LFP 14S | 44,8 | 51,1 | ✘ a plena carga | ✔ | ✘ (SW80B) | ✔ | ✔ |
| LFP 15S ("48 V") | 48,0 | 54,75 | ✘ | ✔ | ✘ | ✔ | ✔ |
| LFP 16S ("51,2 V") | 51,2 | 58,4 | ✘ | **✘ (58,4 > 58)** | ✘ | ✔ justo | ✔ (corregido: en el target 75_100 `l_max_voltage` default = 90 V; el 57 V es solo el genérico) |
| NMC 12S | 43,2 | 50,4 | ✘ (marginal; la Nota 2 de la def. 3.1 pide no superar el límite *"either at full load or no load"*) | ✔ | ✘ | ✔ | ✔ |
| NMC 13S ("48 V") | 46,8 | 54,6 | ✘ | ✔ | ✘ | ✔ | ✔ |

V/celda LFP 3,2 nominal / 3,65 máx.; NMC 3,6 / 4,2 [ESTIMADO: valores estándar; BU da 3,2–3,3 y 3,6–3,7 nominal]. Límites: ISO 16315 [VERIFICADO: https://cdn.standards.iteh.ai/samples/56158/48d458359e3d4eceab7ba7711b5b118e/ISO-16315-2016.pdf], MRBF [VERIFICADO: https://www.currentconnected.com/product/cooper-bussmann-mrbf-terminal-fuse-30a-250a/], SW80 [VERIFICADO: https://www.albrightinternational.com/wpcms/wp-content/uploads/2020/08/SW80-Data-Sheet.pdf], antichispa [VERIFICADO: https://flipsky.net/products/flipsky-antispark-switch-pro-with-aluminum-pcb-case-200a-for-electric-skateboard-ebike-scooter-robots], VESC [VERIFICADO: https://hobbygoat.com/products/flipsky-75100-75v-100a-single-esc].

### 4.4 Dimensionamiento de energía (para cruzar con los informes de casco/hélice)

| P eléctrica crucero (6 km/h) | Energía 2 h | Nominal con 80 % DoD | Masa pack LFP a 128 Wh/kg |
|---|---|---|---|
| 300 W | 600 Wh | 750 Wh | 5,9 kg |
| 400 W | 800 Wh | 1000 Wh | 7,8 kg |
| 500 W | 1000 Wh | 1250 Wh | 9,8 kg |

P crucero 300–500 W = [ESTIMADO: orden de magnitud para un casco plano de ~250 kg a 1,67 m/s con η global ~40–50 %; debe reemplazarse con el dato de R04/otros]. Un pack comercial 36 V 50 Ah (1920 Wh) cubre el caso de 500 W con ~50 % de reserva.

### 4.5 Recomendación para bote abierto
**LFP 12S (38,4 V) ~1–2 kWh con BMS ≥ 50 A, en caja estanca (IP67 o caja sellada con pasacables) elevada sobre el piso**, VESC con `l_in_current_max` ≤ 40 A y corte 36/33,6 V. NMC solo si el peso es crítico (ahorra ~40 % de masa [ESTIMADO: 128 vs ~200 Wh/kg pack]) — no justifica el riesgo de runaway con inmersión posible. LiPo RC: **descartado** (sin BMS, pouch blanda, la química más inestable de la tabla).

---

## 5. Normas

### 5.1 Tabla de alcance (solo lo verificado)

| Norma | Edición vigente | Alcance verificado | Cláusulas útiles verificadas | Fuente |
|---|---|---|---|---|
| **ISO 13297** | **5ª ed., 2020-12** | CC **≤ 50 V** y CA monofásica ≤ 250 V en embarcaciones ≤ 24 m. **No cubre** propulsión eléctrica < 1500 V CC (→ ISO 16315) | 4.1 *"The hull of a metallic hull craft shall not be used as a circuit conductor."* · 5.1 bus negativo común, **excepto** *"propulsion systems that are clearly identified as part of the isolated system"* · 5.4 equipos funcionan de 75 % a 133 % de V nominal (48 V: 36–64 V) · 5.5 caída de tensión ≤ **10 %** · 5.6 Nota 2: **3 %** para equipos vitales · 8.1 *"Batteries shall be permanently installed in a dry, ventilated location above anticipated bilge water level."* | [VERIFICADO: https://cdn.standards.iteh.ai/samples/69551/4f5da7667b4642e2880fe10a27cd4c70/ISO-13297-2020.pdf] |
| **ISO 16315** | **2ª ed., 2026-02** (reemplaza 1ª ed. 2016-03-15, corr. 2021-11) | Sistemas eléctricos para propulsión eléctrica/híbrida: CC < 1500 V, CA ≤ 1000 V, embarcaciones ≤ 24 m (aplica a 36–48 V) | Cambios 2026: *"the overcurrent protection requirements have been clarified"*, *"the fault monitoring requirements for isolated DC systems have been revised"*. Índice incluye 5.1.2 **Emergency stop**, 6.3 monitoreo de falla a tierra en sistemas CC totalmente aislados y de tres hilos, 7.4 dispositivos de sobrecorriente en sistemas totalmente aislados (7.4.1 unipolar / 7.4.2 bipolar), 8.2 *"Isolation of batteries or battery banks"* (= **seccionamiento/desconexión** de baterías, no aislación eléctrica — corregido), 10.3 resistencia de aislación (10.3.2 sistemas de propulsión CC). **Texto de esas cláusulas no accesible** (buscar: "ISO 16315 emergency stop requirement text") | [VERIFICADO: https://cdn.standards.iteh.ai/samples/iso/iso-16315-2026/8c4b6a11aaaf46b4a56c4555d9993156/iso-16315-2026.pdf], [VERIFICADO: https://www.intertekinform.com/preview/905621887232.pdf?sku=879610_saig_nsai_nsai_3090358] |
| ISO 16315:2016 def. 3.1 | — | *"safety voltage … <DC> voltage which does not exceed 50 DC V"*; Nota 1: considerar reducir el límite de 50 V *"under certain conditions, such as wet surroundings or exposure to heavy seas"* | — | [VERIFICADO: https://cdn.standards.iteh.ai/samples/56158/48d458359e3d4eceab7ba7711b5b118e/ISO-16315-2016.pdf] |
| **ABYC E-11** | Extracto 2008 (cumplimiento desde 31-jul-2009); edición actual no verificada (buscar: "ABYC E-11 2024 edition") | Sistemas CA/CC en botes | 11.10.1.1.1 protección contra sobrecorriente a ≤ **7 in (175 mm)** del punto de conexión a la fuente; excepción 2: conductor directo a borne de batería y **enfundado/en conducto** en todo su recorrido → ≤ **72 in (1,83 m)**; excepción 3: fuente que no es batería, enfundado → ≤ **40 in (1,02 m)**; excepción 5: *pigtails* < 7 in exentos · 11.14.2.6 caída ≤ **3 %** (alimentadores de tablero, electrónica, luces de navegación) y ≤ 10 % (no críticos) · conductores ≥ 600 V de aislación, ≥ 60 °C | [VERIFICADO: https://www.paneltronics.com/images/technical/E11Excerpts.pdf] |
| **Directiva 2013/53/UE** (RCD) | vigente | *"‘recreational craft’ means any watercraft … of hull length from 2,5 m to 24 m"*; *"‘propulsion engine’ means any spark or compression ignition, internal combustion engine"* | **Bote < 2,5 m → fuera del alcance**; motores eléctricos no son "propulsion engine" en la RCD | [VERIFICADO: https://www.legislation.gov.uk/eudr/2013/53/adopted/data.html] |

Nota: ISO 13297/16315 no son obligatorias para este bote (fuera de la RCD); se usan como buena práctica [ESTIMADO: consecuencia del alcance verificado].

### 5.2 Ampacidad ABYC E-11 (Tabla VI-A, conductores simples no agrupados, extracto 2008)

| AWG | ≈ mm² [ESTIMADO: conversión estándar] | 90 °C fuera de sala de máquinas | 105 °C fuera | 105 °C dentro |
|---|---|---|---|---|
| 12 | 3,3 | 40 A | 45 A | 38,3 A |
| 10 | 5,3 | 55 A | 60 A | 51,0 A |
| 8 | 8,4 | 70 A | 80 A | 68,0 A |
| 6 | 13,3 | 100 A | 120 A | 102,0 A |

[VERIFICADO: https://www.paneltronics.com/images/technical/E11Excerpts.pdf]. Fórmula ABYC de caída: CM = K·I·L/E, K = 10,75 (cobre), L = ida+vuelta en pies [VERIFICADO: ídem].

**Agregado en verificación — Tabla VI-B (hasta 3 conductores agrupados, enfundados o en conducto)**, que es la que aplica si se usa la excepción 2 de 11.10.1.1.1 (cable enfundado para alejar el fusible hasta 1,83 m) o si + y − van juntos en un forro:

| AWG | 90 °C fuera | 105 °C fuera | 105 °C dentro |
|---|---|---|---|
| 12 | 28,0 A | 31,5 A | 26,8 A |
| 10 | 38,5 A | 42,0 A | 35,7 A |
| 8 | 49,0 A | 56,0 A | 47,6 A |
| 6 | 70,0 A | 84,0 A | 71,4 A |

[VERIFICADO: ídem]. Y **11.10.2.3**: *"The current rating of the overcurrent protection device shall not exceed the maximum current carrying capacity of the conductor being protected"* (excepción: si no hay valor estándar igual, el siguiente estándar hasta 150 %) [VERIFICADO: ídem].

### 5.3 Caída de tensión calculada (cobre ρ = 0,0175 Ω·mm²/m, ida+vuelta) [ESTIMADO: cálculo propio]

| Caso | 6 mm², 1,5 m | 6 mm², 2,5 m | 10 mm², 2,5 m |
|---|---|---|---|
| 38,4 V, 42 A pico (1,6 kW) | 0,37 V (1,0 %) · 15 W | 0,61 V (1,6 %) · 26 W | 0,37 V (1,0 %) |
| 38,4 V, 12 A crucero | 0,11 V (0,3 %) | 0,18 V (0,5 %) | 0,11 V (0,3 %) |
| 48 V, 32 A pico | 0,28 V (0,6 %) | 0,47 V (1,0 %) | 0,28 V (0,6 %) |

→ Con 6 mm² (≈ 10 AWG) se cumple el 3 % con holgura; manda la ampacidad (10 AWG = 60 A a 105 °C suelto, **42 A agrupado/enfundado**), no la caída.

### 5.4 Fusible principal
Blue Sea **MRBF**: 30–250 A, **máx. 58 V CC**, interrupción 10 000 A @ 14 V / 5 000 A @ 32 V / **2 000 A @ 58 V**, IP66; valores 30/40/50/60/75/80/100… A; portafusible de borne Blue Sea 5191 (58 V) [VERIFICADO: https://www.currentconnected.com/product/cooper-bussmann-mrbf-terminal-fuse-30a-250a/]. Para 12S LFP: MRBF a ≤ 175 mm del borne (ABYC dice *"seven inches (175mm)"*). **Corregido en verificación** (ABYC 11.10.2.3, fusible ≤ ampacidad del cable): con `l_in_current_max` = 40 A → **MRBF 50–60 A con cable ≥ 8 AWG / 10 mm²** (8 AWG 105 °C: 80 A suelto, 56 A agrupado → 60 A admisible por la excepción del siguiente valor estándar); un MRBF 80 A exige 8 AWG suelto o 6 AWG agrupado; **10 AWG/6 mm² solo admite ≤ 60 A suelto o ≤ 40–50 A agrupado** [ESTIMADO: aplicación de la tabla VI-A/VI-B verificada]. Verificar que la corriente de cortocircuito del pack no supere la capacidad de interrupción del fusible a esa tensión [ESTIMADO: un pack de ~50 Ah puede dar del orden de 1–2 kA; el BMS normalmente corta antes].

---

## 6. Corrosión galvánica (casco de aluminio, agua salobre)

### 6.1 Serie galvánica en agua de mar (referencia Ag/AgCl)

| Material | Gerr (mV) | Tabla "Ref ABYC" (V) |
|---|---|---|
| Magnesio | −1730 (puro) / −1580 a −1670 (aleaciones) | −1,60 a −1,63 |
| Aluminio para ánodos | — | −1,10 |
| Zinc | −1050 | −0,98 a −1,03 |
| **Aluminio marino 5086/5083/6061** | **−820** | −0,76 a −1,00 (aleaciones) |
| Inox 316 **activo** (sin oxígeno, en grietas/tubos) | −550 | −0,43 a −0,54 |
| Latón naval / amarillo | −450 | −0,30 a −0,40 |
| Bronce al aluminio | −150 (90/10) | −0,31 a −0,42 (92/8) |
| **Inox 316 pasivo** | **−150** | 0,00 a −0,10 |
| Titanio | — | +0,06 a −0,05 |
| Grafito / fibra de carbono | +250 | +0,20 a +0,30 |

[VERIFICADO: https://www.gerrmarine.com/Articles/controllingcorrosionpt1.pdf] · [VERIFICADO: https://archive.nordhavn.com/tech/images/Galvanic_Series.pdf]. Regla práctica: metales a **< 200 mV** se corroen poco entre sí; más de 200 mV → tomar medidas [VERIFICADO: Gerr].

### 6.2 Pares críticos de este diseño

| Par | ΔV aprox. | Riesgo | Mitigación |
|---|---|---|---|
| Eje inox 316 (pasivo) ↔ hélice de aluminio | ~670 mV [ESTIMADO: −820 vs −150] | Alto en la hélice (ánodo) | Ánodo de collar de **aluminio** en el eje junto a la hélice; buje de la hélice de goma/plástico si existe [ESTIMADO] |
| Eje/tubo inox ↔ casco de aluminio (si hubiera contacto) | ~670 mV | Alto en el casco alrededor de la fijación | **No conectar**: soporte de popa en PETG + correa HTD (no conductora) aíslan el tren de propulsión del casco [ESTIMADO: propiedades dieléctricas de PETG/caucho] |
| Tornillería A4 (316) en abrazadera/espejo de aluminio | ~670 mV | Moderado: cátodo chico/ánodo grande es el caso favorable; el caso grave es ánodo chico + cátodo grande (*"for the exposed anodic area the corrosion rate will be correspondingly high"*) [VERIFICADO: https://en.wikipedia.org/wiki/Galvanic_corrosion] | Tef-Gel en roscas y asientos (*"ideal to isolate and separate dissimilar materials such as Aluminium and Stainless Steel"* [VERIFICADO: https://www.anzor.com.au/chemicals/lubricants-and-corrosion-inhibitors/tef-gel]) + arandelas de nylon/G10 bajo cabeza y tuerca |
| Inox 316 dentro del tubo/bujes (sin oxígeno) | pasa a "activo" −550 mV | Picado bajo bujes y depósitos: *"enclosed in a stern tube—it can loose its protective oxide film… can suffer severely from pitting corrosion"* [VERIFICADO: https://www.gerrmarine.com/Articles/controllingcorrosionpt1.pdf] | Agua circulante en los bujes; enjuague; inspección; considerar 2205 dúplex [ESTIMADO: alternativa no verificada aquí] |
| Latón (pasador de corte, insertos roscados, conectores) bajo el agua | — | **Descincificación**: *"the zinc in all brass is eaten away by the more noble copper"* (incluye el "manganese bronze") [VERIFICADO: Gerr] | Pasador de corte de acero inox/aluminio según el fabricante de la hélice; insertos roscados de inox 316 (o nada de metal) en las piezas impresas sumergidas |
| Fibra de carbono ↔ aluminio | > 1000 mV | Muy alto | No usar CF en contacto con el casco/ánodos [ESTIMADO] |

### 6.3 Ánodos de sacrificio en agua salobre
- Fisheries Supply: agua salobre → *"Aluminum anodes provide superior protection here"*; agua de mar → aluminio *"more active, protect better, and last longer than zinc"*; agua dulce → magnesio; cascos/fueraborda de aluminio: zinc *"barely above these aluminum parts… aluminum and magnesium anodes are better suited"*; **no mezclar** metales de ánodo; cambiar al ~50 % consumido o anualmente [VERIFICADO: https://www.fisheriessupply.com/understanding-sacrificial-anodes].
- Magnesio en agua salobre/salada sobre aluminio: riesgo de **sobreprotección**: *"Even on FRP, steel and aluminum hulls overprotection can cause gas bubbles, destroy paint, generate alkaline solutions that actually eat away aluminum"*; sobreprotección = > 400 mV más negativo que el potencial natural [VERIFICADO: https://www.gerrmarine.com/Articles/controllingcorrosionpt1.pdf].
- Salinidad de la zona: Kerteminde Fjord (Fionia) varía *"between 14 and 22 ‰"*; en el Gran Belt la capa superior va de 10 ‰ (salida báltica) a 27 ‰ (entrada) [VERIFICADO: https://www.marbio.sdu.dk/index.php?page=surrounding-field-study-sites]. Als Fjord/Sønderborg ≈ 12–22 PSU [ESTIMADO: interpolación regional, no medido en Als] → rango donde el **aluminio (Al-Zn-In)** es la elección; zinc: Fisheries Supply dice *"While zinc works adequately in saltwater, it will not protect your boat in fresh or brackish water"* y que en agua dulce *"develop a hard, dense coating over time"* [VERIFICADO: https://www.fisheriessupply.com/understanding-sacrificial-anodes] (fuente comercial; "Al-Zn-In" como aleación específica [ESTIMADO: memoria técnica, no verificado]).
- Verificación barata con el multímetro disponible: electrodo Ag/AgCl; protegido = 200–400 mV más negativo que el valor de la tabla; > 400 mV = sobreprotección [VERIFICADO: Gerr].

### 6.4 Corrientes parásitas (más rápidas que la galvánica)
- **Sistema de propulsión flotante**: negativo de batería sin conexión al casco (ISO 13297 4.1 y excepción de 5.1, §5.1). El VESC, el motor y la batería no tocan el aluminio; el tren eje/hélice queda aislado del motor por la correa y del casco por el soporte impreso.
- Revisar aislación con el multímetro: resistencia BAT− ↔ casco y BAT− ↔ eje > 1 MΩ [ESTIMADO: criterio práctico; ISO 16315:2026 trata monitoreo de aislación en CC aislados (cl. 6.3/10.3, texto no accesible)].

---

## 7. Lista eléctrica con precios verificados (resto: buscar)

| Ítem | Opción | Precio | Fuente |
|---|---|---|---|
| ESC | Flipsky 75100 | 79 USD | [VERIFICADO: https://hobbygoat.com/products/flipsky-75100-75v-100a-single-esc] |
| ESC alternativo | Makerbase 75100 V2 | 114,99 GBP | [VERIFICADO: https://escooter-parts.co.uk/products/makerbase-vesc-75100-v2-84v-100a-esc-with-alu-pcb-based-on-vesc] |
| Arranque suave | Flipsky Antispark Pro | 33–48 USD | [VERIFICADO: https://flipsky.net/products/flipsky-antispark-switch-pro-with-aluminum-pcb-case-200a-for-electric-skateboard-ebike-scooter-robots] |
| Kill con cordón (cerrado con clip) | Sea Dog SD-420487-1 | 15,69 USD | [VERIFICADO: https://shop.hamiltonmarine.com/products/sea-dog-switch-kill-gray-cap-with-lanyard-normall-closed-29836.html] |
| Llave/aislador manual | XT90-S (par) | 3,69 EUR | [VERIFICADO: https://www.rotorama.com/product/xt90s-antispark-konektor-par] |
| Contactor | Albright SW80 bobina continua 36/48 V | buscar: "SW80 contactor price" | datos técnicos verificados (§3.3) |
| Fusible | Blue Sea MRBF 50–60 A + portafusible 5191 (corregido: ver §5.4, fusible ≤ ampacidad del cable) | buscar: "MRBF 5191 price EU" | ratings verificados (§5.4) |
| Batería | LiTime 36 V 50 Ah LFP (1920 Wh, IP65, BMS 50 A) | 395,99 USD | [VERIFICADO: https://www.litime.com/products/litime-36v-55ah-tm-lifepo4-battery-low-temp-protection-for-trolling-motors] |
| Anticorrosivo | Tef-Gel | buscar: "Tef-Gel 2 oz price" | [VERIFICADO: https://www.anzor.com.au/chemicals/lubricants-and-corrosion-inhibitors/tef-gel] |

---

## Hallazgos que cambian el diseño

- **Bajar de "48 V" a 12S LFP (38,4 V nom., 43,8 V máx.)**: 16S LFP (58,4 V) supera el MRBF (58 V), la tensión de corte bajo carga del SW80 (48 V) y la "tensión de seguridad" de 50 V CC de ISO 16315; 12S/13S cumplen todo. (Corregido en verificación: el `l_max_voltage` de 57 V **no** es límite para el 75100 — su hwconf lo pone en 90 V.) A 0,3–1,5 kW las corrientes siguen siendo bajas (12 A crucero / 42 A pico a 38,4 V) [ESTIMADO: cálculo].
- **El kill switch debe ser hardware**: contactor monoestable con bobina en serie con un cordón "cerrado con clip" (Sea Dog SD-420487-1, 5 A, 15,69 USD) + seta de emergencia. El antichispa MOSFET queda solo como arranque suave porque puede fallar en cortocircuito (encendido permanente; caso documentado en foro con un antichispa Buildkit Boards). Kill por software del VESC (`KILL_SW_MODE_ADC2_HIGH`, FW ≥ 5.03) como redundancia. Agregado en verificación: contactor SW80 **sin** opción de enclavamiento magnético ("Not fail safe" según Albright), **bobina 48 V continua** (cierra hasta 31,7 V, cubre 12S LFP 33,6–43,8 V), supresión diodo+resistencia/TVS; y resolver el conflicto con Flipsky (*"Make sure the switch is off before applying power"*): el contactor no debe energizar un antichispa Pro ya enclavado en ON → resistencia de precarga en paralelo al contactor o procedimiento explícito.
- **Firmware: ≥ 5.03 con filtro de fase desactivado** (Flipsky 75100) — 5.02 no tiene kill switch por software y ≥ 5.3 con filtro de fase activado daña el ESC según el vendedor. En el firmware oficial ≥ 6.00 el target 75_100 ya trae el filtro en `false` por defecto; verificarlo igual en VESC Tool tras el asistente.
- **Configuración obligatoria del VESC** (los defaults no sirven): `adc voltage_min` ≈ 0,3 V (si no, un cursor cortado en "Current Reverse Center" = reversa máxima); `battery_cut_start/end` = 36,0/33,6 V para 12S (default 10/8 V); `l_in_current_max` ≤ 80 % del BMS (≤ 40 A con BMS de 50 A; default 100 A en el target 75_100, 99 A genérico); rampas ≥ 0,5–1 s (default 0,3/0,1 s); `l_max_erpm` limitado para el caso hélice fuera del agua.
- **Motor seco arriba del agua (cola larga) confirmado como mejor opción eléctrica**: un outrunner inundado requiere desarme + enjuague después de cada uso (instrucciones para el Maytech 6579 en foil.zone, no atribuidas explícitamente al fabricante); el inrunner IP68 Flipsky FS65161 es de 6 kW (≈ 450 € según e-surfer; peso **no verificado** — el "3 kg" anterior no figura en las fuentes abiertas), sobredimensionado ~10× para 0,3–0,5 kW de crucero. Rodamientos del motor: 440C (−20 % de carga; **corroe en agua de mar** según SMB → consumible con enjuague) o full cerámico Si3N4 si la carga lo permite; protector impreso con drenaje.
- **Batería LiFePO4, ~1–2 kWh, en caja estanca elevada**: LFP no disparó runaway en ARC (Tmax 239 °C) vs NCM811 147 °C → 463 °C; gas 1,14 vs 2,4 L/Ah. Pack comercial ≈ 128 Wh/kg → 1 kWh ≈ 8 kg. Packs náuticos típicos son IP65 (no inmersión) y no cargan bajo 0 °C (relevante en primavera/otoño danesa).
- **Fusible ≤ 175 mm (7") del borne** (o ≤ 1,83 m si el cable va enfundado). **Corregido en verificación**: el fusible no puede superar la ampacidad del cable (ABYC 11.10.2.3) → **MRBF 50–60 A + cable 8 AWG/10 mm²** (56 A agrupado, 80 A suelto a 105 °C); 6 mm²/10 AWG da < 1,6 % de caída a 42 A en 2,5 m pero solo admite 60 A suelto / 42 A agrupado-enfundado, incompatible con un MRBF 80 A.
- **Sistema de propulsión flotante y aislado del casco**: el negativo no va al aluminio (ISO 13297 4.1); soporte PETG + correa HTD aíslan eje inox (−150 mV pasivo) del casco (−820 mV): evita una pila de ~670 mV.
- **Ánodo de aluminio (no zinc, no magnesio)** en el eje junto a la hélice: salinidad local ~12–22 PSU [ESTIMADO]; el magnesio sobreprotege y ataca al aluminio en agua salobre/salada. Nada de latón bajo el agua (descincificación); tornillería A4 en aluminio con Tef-Gel + arandelas nylon/G10.
- **Marco legal**: bote < 2,5 m → fuera de la RCD 2013/53/UE; ISO 16315:2026 (2ª ed., feb-2026) es la referencia de buena práctica para la propulsión; su cláusula 5.1.2 "Emergency stop" existe pero el texto no es de acceso abierto.

---

## Fuentes abiertas con éxito en esta sesión

- https://raw.githubusercontent.com/vedderb/bldc/master/applications/app_adc.c
- https://raw.githubusercontent.com/vedderb/bldc/master/applications/app_ppm.c
- https://raw.githubusercontent.com/vedderb/bldc/master/applications/appconf_default.h
- https://raw.githubusercontent.com/vedderb/bldc/master/motor/mcconf_default.h
- https://raw.githubusercontent.com/vedderb/bldc/master/timeout.c
- https://raw.githubusercontent.com/vedderb/bldc/master/datatypes.h
- https://raw.githubusercontent.com/vedderb/bldc/5.02/datatypes.h
- https://raw.githubusercontent.com/vedderb/bldc/release_5_03/datatypes.h
- https://raw.githubusercontent.com/vedderb/bldc/master/hwconf/flipsky/hw_75_100.h (agregado en verificación)
- https://raw.githubusercontent.com/vedderb/bldc/master/hwconf/flipsky/hw_75_100_V2.h (agregado en verificación)
- https://raw.githubusercontent.com/vedderb/bldc/release_6_00/hwconf/flipsky/hw_75_100.h (agregado en verificación; idem release_6_02 y release_6_05)
- https://hobbygoat.com/products/flipsky-75100-75v-100a-single-esc
- https://escooter-parts.co.uk/products/makerbase-vesc-75100-v2-84v-100a-esc-with-alu-pcb-based-on-vesc
- https://flipsky.net/blogs/vesc-tool/something-you-should-know-about-flipsky-anti-spark-switch
- https://flipsky.net/products/flipsky-antispark-switch-pro-with-aluminum-pcb-case-200a-for-electric-skateboard-ebike-scooter-robots
- https://flipsky.net/blogs/vesc-tool/more-known-about-fs65161-motor
- https://forum.esk8.news/t/right-as-i-finished-the-build-i-broke-the-anti-spark-switch/22247
- https://forum.esk8.news/t/flipsky-smart-antispark-issues-feedback-and-review/11908
- https://www.rotorama.com/product/xt90s-antispark-konektor-par
- https://www.boatfittings.co.uk/how_to_fit_a_kill-switch
- https://shop.hamiltonmarine.com/products/sea-dog-switch-kill-gray-cap-with-lanyard-normall-closed-29836.html
- https://www.albrightinternational.com/wpcms/wp-content/uploads/2020/08/SW80-Data-Sheet.pdf
- https://docs.prohelion.com/Battery_Management_Systems/Prohelion_BMS_D1000_Gen1/Operation/Precharge.html
- https://foil.zone/t/how-to-maintain-maytech-6579-waterproof-outrunner-motor/24647
- https://foil.zone/t/waterproof-6374-with-no-shaft-for-efoil/17043
- https://e-surfer.com/en/blog/build-your-own-e-foilboard-diy-e-foil-part-2/
- https://www.smbbearings.com/technical/bearing-material.html
- https://batteryuniversity.com/article/bu-205-types-of-lithium-ion
- https://pmc.ncbi.nlm.nih.gov/articles/PMC10963544/
- https://pmc.ncbi.nlm.nih.gov/articles/PMC11927001/
- https://www.eenews.net/articles/why-6-flooded-evs-burst-into-flames-after-hurricane-ian/
- https://contractlaboratory.com/understanding-the-dangers-of-lithium-ion-batteries-submerged-in-water/
- https://www.litime.com/products/litime-36v-55ah-tm-lifepo4-battery-low-temp-protection-for-trolling-motors
- https://cdn.standards.iteh.ai/samples/69551/4f5da7667b4642e2880fe10a27cd4c70/ISO-13297-2020.pdf
- https://cdn.standards.iteh.ai/samples/56158/48d458359e3d4eceab7ba7711b5b118e/ISO-16315-2016.pdf
- https://cdn.standards.iteh.ai/samples/iso/iso-16315-2026/8c4b6a11aaaf46b4a56c4555d9993156/iso-16315-2026.pdf
- https://www.intertekinform.com/preview/905621887232.pdf?sku=879610_saig_nsai_nsai_3090358
- https://www.paneltronics.com/images/technical/E11Excerpts.pdf
- https://www.currentconnected.com/product/cooper-bussmann-mrbf-terminal-fuse-30a-250a/
- https://www.legislation.gov.uk/eudr/2013/53/adopted/data.html
- https://www.gerrmarine.com/Articles/controllingcorrosionpt1.pdf
- https://archive.nordhavn.com/tech/images/Galvanic_Series.pdf
- https://www.fisheriessupply.com/understanding-sacrificial-anodes
- https://www.marbio.sdu.dk/index.php?page=surrounding-field-study-sites
- https://www.anzor.com.au/chemicals/lubricants-and-corrosion-inhibitors/tef-gel
- https://en.wikipedia.org/wiki/Galvanic_corrosion

No accesibles (403/WAF) y por eso no citados: iso.org (ISO 13297/16315 páginas de catálogo), RSC Advances (Golubkov 2014), MDPI Batteries 9/5/237, Blue Sea Systems, ebikes.ca, eur-lex.europa.eu, Sensata whitepaper de precarga.

---

## Verificación (adversarial)

Fecha: 2026-10-01. Se reabrieron **las 43 URLs citadas** (curl; las que devolvieron captcha/JS — foil.zone, forum.esk8.news, PMC, Nordhavn — con WebFetch) y se descargó además el `hwconf` del Flipsky 75100 del repositorio oficial. Todas abrieron. Ninguna cita resultó inventada; hubo errores de **atribución**, **alcance del default** y **reglas omitidas** que cambian el diseño.

| Afirmación / URL | Estado | Nota |
|---|---|---|
| Defaults `appconf_default.h` (timeout 1000 ms, freno 0 A, kill DISABLED, safe start, hyst 0,15, PPM 1,0/1,5/2,0 ms, ADC 0,9/2,0/3,0 V, min/max 0,0/3,5 V, rampas 0,3/0,1 y 0,4/0,2 s, max_erpm_for_dir 4000, 500 Hz) | OK | Todos coinciden con master |
| Defaults `mcconf_default.h` (±60 A, 99/−60 A, corte 10/8 V, 57 V, temp. 85/100 °C, duty 0,95, NTC 10k) | Corregido | Valores bien transcritos, pero **el target 75_100 los sobrescribe**: `l_max_voltage` 90 V, `l_in_current` ±100 A, `l_min_voltage` 8 V (V2: 12 V), filtro de fase false (`hwconf/flipsky/hw_75_100.h`) |
| "16S LFP supera el `l_max_voltage` default de 57 V del VESC" (§2.4, §4.3, Hallazgos) | Corregido | Falso para el 75100 (90 V). La conclusión "12S" se mantiene por MRBF/SW80/ISO 50 V |
| `KILL_SW_MODE` ausente en 5.02, 4 modos en 5.03, 10 en master | OK | Conteo verificado en los tres `datatypes.h` |
| Conflicto FW 5.2 vs filtro de fase | Corregido (atenuado) | En `release_6_00/6_02/6_05` y master el 75_100 trae `MCCONF_FOC_PHASE_FILTER_ENABLE false`; no se pudo verificar 5.03 (archivo 404) |
| `PPM_CTRL_TYPE_CURRENT_SMART_REV` = "sin reversa" | Corregido | El código tiene reversa por duty con palanca < −92 % a baja velocidad (`smart_rev_max_duty`, rampa 3,0 s) |
| ADC REV_CENTER: 0 V → reversa máxima con `voltage_min` 0,0 | OK | Verificado en `app_adc.c` (mapeo, truncado, `pwr*2−1`, `range_ok`) |
| "Un ADC nunca hace timeout" | Corregido (precisión) | `timeout_reset()` solo se llama si pasa safe start y rango; lo que nunca hace timeout es una lectura dentro de rango |
| Safe start 500 ms / 50 pulsos; timeout PPM; kill en `timeout.c` (umbral 1,65 V, `ignore_input_both(20)`) | OK | Verificado en código; ADC2 existe en el 75_100 (`ADC_IND_EXT2` 7) |
| hobbygoat Flipsky 75100: 14–84 V, 100/120 A, 79/99 USD, advertencia filtro de fase | OK | Agregado: "Phase filter: No" y "do not restore the default parameters"; **"PCB aluminio" no figura** → [NO VERIFICADO] |
| escooter-parts Makerbase 75100 V2: 14–84 V, 100/120 A, 114,99 GBP, HYG015N10NS1TA, 103×58×18,5 mm, 12 AWG | OK | — |
| flipsky.net FS65161: IP68, sello cerámico, ~10 000 h, "works in the sea", 6000 W, 6–20S | OK | "**3 kg**" en Hallazgos **no figura** en ninguna fuente → eliminado/[NO VERIFICADO]; "150 g" de la página es la hélice |
| foil.zone Maytech 6579 (desarme tras cada uso) | Corregido | Cita textual correcta, pero es un post del usuario PaulKirdy, **no atribuido explícitamente a Maytech** |
| foil.zone 17043 "seized with salt water" | OK | Usuario brycej, motor Flipsky |
| e-surfer: refrigeración, epoxi, Corrosion-X, rodamientos inox/cerámicos, inrunners "maintenance-free", aceite | OK | Agregado: FS65161 ≈ 450 € |
| SMB bearings: 440 −20 % carga; 316 baja carga, pitting > 30 °C; Si3N4 resistente | Corregido | Faltaba: 440 *"will corrode in seawater"*, crevice 316 a 10–15 °C; la cita Si3N4 es de **full cerámico** (65–75 % carga, 25 % velocidad), no de híbridos |
| `mcconf` NTC motor | OK | — |
| Flipsky Antispark Pro: 3S–14S (12–60 V), 100/60/200 A, 33/43/48 USD, advertencias | OK | Agregado conflicto: "switch off before applying power" vs contactor aguas arriba |
| Flipsky blog: Pro autoenclavante, Smart momentáneo, NO+NC | OK | — |
| esk8 "MOSFETs failed short-circuit" + XT90S loopkey | Corregido | El antichispa era **Buildkit Boards**, no Flipsky; diagnóstico de foro |
| esk8 Smart 2,5 mA | Corregido | Es Smart V1, con revisión a 300–400 µA |
| rotorama XT90-S: resistencia integrada, 45/90 A, 3,69 EUR | OK | — |
| boatfittings: kill "normally open-circuit" | OK | — |
| Hamilton Sea Dog SD-420487-1: NC con clip, 5 A, 15,69 USD | OK | 5 A sin tensión declarada; bornes de latón → nota agregada |
| Albright SW80 (100/125 A, 600 A@48 V, 48/60 V, bobina 6–240 V, 7–13 W, 5/50/8–20 ms, 5×10⁶, −40…+60 °C, 40 mV) | OK | Agregado: cierre 66 % Us, caída 10–25 % Us, SW80P IP66, "Magnetic Latching (Not fail safe)" → respalda la regla anti-biestable (antes [ESTIMADO]) |
| Prohelion precarga (miles de A, soldadura, 470 Ω/800 µF/376 ms) | OK | "95 % en 4τ" es lo que dice la fuente; matemáticamente 95 % = 3τ (nota agregada) |
| Battery University (V nominal, Wh/kg, ciclos, runaway 270/210/150 °C) | OK | — |
| PMC10963544 (Frontiers in Chemistry 2024) ARC LFP/NCM811/LCO y ranking | OK | Valores exactos coinciden |
| PMC11927001 gas 1,14 L/Ah (0,36 L/Wh) LFP, 2,4 L/Ah (0,66 L/Wh) MH1, 600 °C | OK | LFP = celdas 26650 de un estudio previo citado en el paper |
| eenews (agua salada → incendio de horas, reignición) | OK | — |
| contractlaboratory (cloruros, runaway días/semanas) | OK | Fuente comercial; "días o semanas" atribuido a NFPA por el sitio |
| LiTime 36 V 50 Ah: 1920 Wh, 33,14 lb, IP65, BMS 50 A / 250 A 1 s, 43,2 ± 0,6 V, carga 0–5 °C, 4000+ ciclos, 395,99 USD | OK | 128 Wh/kg recalculado = 127,7 |
| iteh ISO 13297:2020 (5ª ed., ≤ 50 V, 4.1, 5.1, 5.4, 5.5, 5.6 nota 2, 8.1) | OK | — |
| iteh ISO 16315:2016 def. 3.1 (50 V, Nota 1) | OK | Agregada Nota 2 ("ni a plena carga ni en vacío") → NMC 12S pasa a ✘ |
| iteh ISO 16315:2026 (2ª ed. 2026-02, cambios, índice) | Corregido (menor) | 8.2 "Isolation of batteries" = seccionamiento, no aislación |
| intertekinform EN ISO 16315:2016 corr. 2021-11 | OK | — |
| paneltronics ABYC E-11 (7 in/175 mm, 72 in, 40 in, pigtails, 3 %/10 %, 600 V, 60 °C, K = 10,75, Tabla VI-A) | Corregido | Tabla VI-A bien transcrita; **faltaba Tabla VI-B y 11.10.2.3** → MRBF 60–80 A sobre 10 AWG no cumple; "178 mm" → 175 mm (valor ABYC) |
| currentconnected MRBF (30–250 A, 58 V, 10 000/5 000/2 000 A, IP66) | OK | Agregado: valores estándar y bloque 5191 |
| legislation.gov.uk RCD 2013/53/UE (2,5–24 m; "propulsion engine" = combustión) | OK | — |
| Gerr (serie galvánica, 200 mV, inox activo en tubo, descincificación, sobreprotección > 400 mV) | OK | — |
| Nordhavn "Galvanic Series" (Ref ABYC) | OK | curl devolvió captcha; abierto vía WebFetch; valores coinciden |
| Fisheries Supply (ánodos Al en salobre, no mezclar, 50 %/anual) | OK | Agregada cita sobre zinc en agua salobre (antes [ESTIMADO]) |
| SDU marbio (Kerteminde 14–22 ‰; Gran Belt 10–27 ‰) | OK | Als 12–22 PSU sigue [ESTIMADO] (sin presupuesto de búsqueda para verificar) |
| anzor Tef-Gel; Wikipedia galvanic corrosion | OK | — |
| Cálculos propios (caída de tensión, masas de pack, τ precarga, consumo bobina, Wh/kg) | OK | Recalculados; coinciden |
| Contenido de videos | OK | No se describe contenido de ningún video como visto (solo se menciona que el post de foil.zone enlaza uno) |
| Precios | OK | Todos los precios citados están en páginas abiertas; los no hallados figuran como "buscar:" |
| Números de pieza (SD-420487-1, HYG015N10NS1TA, 5191) | OK | Presentes en las páginas citadas |
