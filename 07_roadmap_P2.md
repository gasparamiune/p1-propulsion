# 07 — Roadmap P2: qué mejorar después del prototipo

Qué cambiar en la segunda iteración del waterjet, en qué orden y con qué **disparador medible**: nada de
esta lista se hace "porque sí"; cada ítem se activa con un resultado de las pruebas de 06 §7 o con un dato
que hoy falta. Los números del modelo van entre marcadores `<!--V:…-->` (los actualiza `docgen.py`).

Etiquetas: [VERIFICADO: fuente] · [CALCULADO] · [ESTIMADO: base] · [SUPUESTO].

## 0. Línea base del prototipo (contra la que se mide cada mejora)

| Magnitud | P1-J (modelo) | Etiqueta |
|---|---|---|
| Masa total con piloto de 90 kg | <!--V:sizing.masses.total_kg:.0f-->218<!--/V--> kg | [CALCULADO] |
| Masa de la unidad de jet (CAD) | <!--V:manifest.totals.jet_unit_mass_kg:.1f-->25.9<!--/V--> kg (JT132: 12 kg [VERIFICADO: R11 §4]) | [CALCULADO] |
| GM | <!--V:sizing.hydrostatics.GM_m:.3f-->0.009<!--/V--> m | [CALCULADO, casco ESTIMADO] |
| V máx. sostenida / por ratos | <!--V:sizing.performance.vmax_cont_kmh:.1f-->24.4<!--/V--> / <!--V:sizing.performance.vmax_peak_kmh:.1f-->28.3<!--/V--> km/h (objetivo 30) | [CALCULADO] |
| Margen mínimo en la joroba | <!--V:sizing.performance.hump_margin_min:.0%-->-8%<!--/V--> | [CALCULADO] |
| P de batería a 5 kn / autonomía a 5 kn | <!--V:sizing.performance.legal.P_bat:.0f-->1702<!--/V--> W / <!--V:sizing.energy.t_legal_h:.1f-->2.4<!--/V--> h | [CALCULADO] |
| Autonomía a V máx. | <!--V:sizing.energy.t_top_min:.0f-->37<!--/V--> min | [CALCULADO] |
| Limitante a fondo | corriente de batería (<!--V:sizing.electrical.I_bat_limit_A:.0f-->192<!--/V--> A, 80 % del BMS) | [CALCULADO] |
| Costo del sistema (BOM) | <!--V:bom.total_eur:.0f-->11847<!--/V--> € | [CALCULADO] |

## 1. Resumen priorizado

| # | Mejora | Disparador (medible) | Qué gana | Esfuerzo |
|---|---|---|---|---|
| 1 | Casco más ancho o flotadores laterales | Ensayo E1 (R13 §5): escora > 15° con el piloto a 0,2 m de crujía, o entrada de agua | Que el bote se pueda usar; también margen de cebado y capacidad | Alto (casco) |
| 2 | Calibrar el modelo con las pruebas | Siempre, al terminar 06 §7 | Saber de dónde sale la diferencia con 30 km/h | Bajo |
| 3 | Telemetría y límite por velocidad (GPS) | Siempre en P2; antes si la prueba legal (02 §3.1) no pasa con el tope de ERPM | Perfil costa por velocidad real; ley anti-cavitación por V (02 §4.6) | Bajo |
| 4 | Subir la potencia útil dentro de ≤ 50 V | Motor ≤ 80 °C de bobinado en 30 min a P continua **y** V máx. medida < 30 km/h | V máx. | Medio |
| 5 | Reducir la masa del jet | V máx. medida < <!--V:sizing.success.vmax_min_kmh:.1f-->20.8<!--/V--> km/h, o margen de joroba insuficiente con la batería baja | V máx. y margen en la joroba | Medio |
| 6 | Impulsor optimizado (CFD) | Empuje a punto fijo < <!--V:sizing.success.bollard_min_N:.0f-->612<!--/V--> N, o síntomas de cavitación con S de modelo < 3,5 | η de bomba, margen de cavitación | Alto |
| 7 | 72 V | Solo si 4 no alcanza **y** Søfartsstyrelsen confirma el criterio de potencia (R13 Q2) | Potencia útil por encima del límite de corriente de 12S | Alto (seguridad eléctrica) |
| 8 | Pasar a la JT132 | La cotización de AWT cierra (brida, altura del eje, curva) y el impulsor propio cuesta o tarda más de lo previsto | Masa, tiempo, riesgo de fabricación (03 §3) | Medio |

## 2. P2 inmediato

### 2.1 Casco: manga y estabilidad

- **Disparador:** E1 falla (escora > 15° con el piloto a 0,2 m de crujía, o entra agua) o el GM medido con
  la prueba de inclinación queda < 100 mm [SUPUESTO: criterio de R10b H1].
- **Qué hacer:** manga en la flotación ≥ 0,9 m (caja: GM ≈ +144 mm [CALCULADO: R10b §4.3]); en la práctica
  1,1–1,3 m de manga total como los cascos chicos de R04; asiento más bajo; batería en el fondo dentro de su
  caja estanca. Alternativa sin casco nuevo: flotadores laterales a la altura de la flotación.
- **Cómo se mide la mejora:** GM medido; E1–E4 de R13 §5 pasan; capacidad por 33 CFR 183.33 ≥ piloto + equipo
  (hoy <!--V:sizing.capacity.persons_gear_kg:.0f-->46<!--/V--> kg [CALCULADO]).
- Un casco más ancho cambia la resistencia (más superficie mojada, menos trimado): volver a correr
  `run_all.py` con las medidas nuevas antes de tocar la bomba.

### 2.2 Calibración del modelo

| Dato medido | Entrada que calibra | Prueba |
|---|---|---|
| Calado en el espejo con piloto y batería | `boat.*` (C_b, mangas), cebado | Muelle (R10a §8.1) |
| Empuje a punto fijo, rpm, corriente | η de bomba (`waterjet.pump.eta_design`), S real | Punto fijo con dinamómetro |
| V máx. y P de batería a varias V (GPS + VESC) | `resistance.r_hump`, `planing_band` | Agua calma, > 300 m de la costa |
| P de batería a 5 kn | R/Δ a baja velocidad | GPS + VESC dentro de la franja |
| Temperatura del motor en crucero | `rth_k_w`, potencia continua admisible | NTC + VESC, 30 min |
| Vacío en la garganta | η_in, pérdida de la rejilla | Vacuómetro (R10a §8.8) |

Criterio para dar el modelo por calibrado [SUPUESTO]: V máx. y P a 5 kn medidas dentro de ±10 % del modelo
con las entradas ajustadas.

### 2.3 Telemetría y límite por velocidad

- **Qué:** leer el VESC por UART (el firmware de `04_diseno/electronica/` ya tiene el hook `use_vesc_ok`)
  más un GPS; registrar V, rpm, corriente, temperatura y tensión.
- **Para qué:** (a) perfil costa por velocidad medida, que sirve para 5 kn, 4 kn (Als Sund) y 3 kn (marinas)
  sin depender de la masa ni de la batería; (b) ley anti-cavitación por velocidad (02 §4.6) en lugar de un
  tope fijo de ERPM; (c) detección de descarga de la bomba (aire, algas).
- **Disparador:** P2 siempre. Antes, si la prueba legal con tope de ERPM no pasa dos veces seguidas.

### 2.4 Más potencia útil dentro de ≤ 50 V

Hoy el bote no usa toda la potencia que puede dar el motor: a fondo limita la corriente de batería
(<!--V:sizing.electrical.I_bat_limit_A:.0f-->192<!--/V--> A) y en crucero la potencia continua estimada del motor
(P_bat <!--V:sizing.electrical.P_bat_cont_W:.0f-->6723<!--/V--> W). La potencia continua es la entrada más influyente
en la V máx. (02 §10).

- **Disparador:** la prueba térmica muestra el bobinado ≤ 80 °C [SUPUESTO: margen de 40 K a los 120 °C de
  catálogo] a la potencia continua configurada, y la V máx. medida no llega a 30 km/h.
- **Qué hacer, en orden:** (1) pedir a Maytech la potencia continua con camisa de agua y subir el límite del
  VESC hasta ese valor; (2) batería con BMS de más corriente o un pack 13S (47,45 V máx., sigue ≤ 50 V;
  R11 §3.2), que además da 8 % más de rpm con el mismo KV; (3) volver a correr el optimizador, que rediseña la
  bomba para la potencia nueva.
- **Límites que hay que revisar si sube la potencia:** traba del bucket, chaveta del acople y uniones de la
  toma (los FS más justos de 02 §9); pasador de corte (el corte se dimensiona contra el par del controlador);
  P pico < 19 kW (speedbåd, R13 §2).

### 2.5 Reducir la masa del jet

- **Disparador:** V máx. medida por debajo del criterio de éxito (<!--V:sizing.success.vmax_min_kmh:.1f-->20.8<!--/V--> km/h),
  o el bote no sale a planeo con la batería al 20 %.
- **Meta:** acercarse a los 12 kg de la JT132 con toma, bomba, dirección y bucket (hoy la unidad de jet del
  CAD pesa <!--V:manifest.totals.jet_unit_mass_kg:.1f-->25.9<!--/V--> kg con el tren; 03 §3 compara A y B).
- **Dónde está la masa** (CAD, `manifest.json`): el conducto y la placa base de la toma de Al 5083 son lo
  más pesado; después carcasa, estator, tobera y anillo de desgaste. Ideas: conducto de chapa de 4 mm donde
  el FS lo permita, placa base aligerada fuera de la zona de bulones, anillo de desgaste más corto, carcasa y
  estator en una sola pieza mecanizada.
- **Cómo se mide:** balanza; correr `run_all.py` (la masa del jet entra sola desde el CAD al dimensionamiento).

## 3. Más adelante

### 3.1 Impulsor optimizado con CFD

- **Disparador:** empuje a punto fijo < <!--V:sizing.success.bollard_min_N:.0f-->612<!--/V--> N (0,80 × modelo), η de bomba
  inferida < 0,65 [SUPUESTO], o ruido / rpm que sube sin empuje con S del modelo < 3,5.
- **Qué:** CFD de la etapa impulsor + estator con la toma (curva H-Q, η, inicio de cavitación); torbellino
  forzado para descargar el cubo (R12 §0: "most of the designs are of the forced vortex type"); revisar la
  holgura de punta medida contra la de diseño.
- **Cómo se valida:** mismo ensayo de punto fijo y curva P–V con GPS; criterio: +10 % de empuje a punto fijo
  a la misma corriente [SUPUESTO].

### 3.2 72 V

- **Disparador** (todos): (a) con ≤ 50 V y la mejora 2.4 hecha, el modelo calibrado no llega a 30 km/h;
  (b) existe un motor de 72 V con el KV correcto (el HPM5000L pide bobinado a medida de ~72 rpm/V, R11 §1.3);
  (c) Søfartsstyrelsen contesta cómo mide la potencia de speedbåd (R13 Q2) y el pico queda < 19 kW.
- **Qué implica** [VERIFICADO: R13 §4; R11 §8]: clase 100 V en contactor, fusible y controlador
  (FSESC 110300), bus flotante con monitor de aislamiento (Bender iso175C-1, 709 €), IP67 en todo lo que pase
  de 50 V, medición de aislamiento antes de cada temporada. Habilitar `electrical.allow_72v` y correr el
  optimizador.
- Mientras no se cumplan los tres disparadores, se queda en 12S.

### 3.3 Toma y aire

- **Disparador:** picos de rpm > 10 % sin mover el acelerador con ola corta (R10a §8.10) o tufts que muestran
  separación en el techo o en el labio.
- **Qué:** labio con más radio, rampa más baja (25°), generadores de vórtices en la rampa (R10a S8), o nada
  que genere burbujas delante de la toma.

### 3.4 Materiales y mantenimiento

- Anillo de desgaste e impulsor: medir la holgura en cada inspección; si pasa de 0,8 mm [SUPUESTO: el doble
  de la de diseño], tornear un anillo nuevo.
- Pasador de corte: si corta en uso normal (sin golpe), subir un paso de Ø y revisar el límite de corriente.
- Ánodo: si se consume más de la mitad en una temporada, revisar aislaciones (R06 §6).

## 4. Descartado para P2

| Idea | Por qué no |
|---|---|
| Imprimir conducto, carcasa, estator o boquilla en PETG | No cierran a FS 3 (02 §9; D-09, D-10, D-19) |
| Rim-drive o hélice entubada bajo el casco | Peor en la matriz (03 §2); rozamiento y fabricación (R03 §4) |
| 72 V sin monitor de aislamiento | Contra ISO 16315 §4.1 por encima de 50 V (R13 §4) |
| Llevar un acompañante | La capacidad del casco no da ni para el piloto (02 §2.3) |

## 5. Disparadores por prueba

| Prueba (06 §7) | Medición | Umbral | Si no pasa → ítem |
|---|---|---|---|
| E1 escora (R13 §5) | Escora y francobordo con lastre desplazado | ≤ 15° a 0,2 m de crujía, sin entrada de agua | 2.1 (bloqueante) |
| Punto fijo | Empuje, rpm, corriente | ≥ <!--V:sizing.success.bollard_min_N:.0f-->612<!--/V--> N | 3.1 |
| Térmico (30 min de crucero) | NTC del motor | ≤ <!--V:sizing.thermal.t_winding_max_C:.0f-->120<!--/V--> °C sin recorte; ≤ 80 °C habilita 2.4 | 2.4 |
| V máx. (GPS) | V media ida y vuelta | ≥ <!--V:sizing.success.vmax_min_kmh:.1f-->20.8<!--/V--> km/h | 2.2 → 2.4 → 2.5 |
| 0 a planeo | Tiempo | ≤ <!--V:sizing.success.t_plane_max_s:.0f-->15<!--/V--> s (también con batería al 20 %) | 2.5 |
| 5 kn (GPS + VESC) | P de batería | ≤ <!--V:sizing.success.p_legal_max_W:.0f-->2213<!--/V--> W | 2.2 |
| Perfil costa | V media a fondo | ≤ 9,0 km/h | 2.3 |
| Ola corta | rpm sin mover el acelerador | picos ≤ 10 % | 3.3 |
