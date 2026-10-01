# PENDIENTES_GASPAR — acciones físicas, en orden

Cada paso tiene **criterio pasa / no-pasa**. No avanzar al siguiente si el anterior no pasa.
Después de cada medición: actualizar `inputs.yaml` y correr `python run_all.py`.

## P0 — Antes de comprar nada

| # | Acción | Cómo | Pasa si | Si no pasa |
|---|---|---|---|---|
| P0.1 | **Medir el bote** | Cinta y nivel: LOA, LWL (marcar la flotación con 2 personas sentadas), manga, ancho de fondo, puntal, altura del espejo (fondo → borde), espesor del espejo (chapa + taco), material del taco, ancho útil del borde, peso del casco (balanza de baño ×2), fotos | Datos cargados en `inputs.yaml → boat.*` y `run_all.py` en verde | Revisar abrazadera (rango 20–65 mm) y largo de cola |
| P0.2 | **Placa de capacidad** | Leer la placa (personas / kg / hp). Si no hay: prueba de francobordo con la carga real en agua calma | Carga útil (personas + equipo + batería + propulsión) ≤ placa, **y** francobordo en popa ≥ 150 mm con 2 personas | **No salir con 2 adultos**; usar batería chica (LFP24_50), 1 adulto, o bote más grande |
| P0.3 | **Ensayo de remolque (calibración de R(v))** | Dinamómetro entre el bote cargado y otro bote/kayak que remolca (o desde un muelle caminando); GPS en el celular; 3–4 velocidades estables (3, 4,5, 6, 7 km/h), 3 pasadas por velocidad en ambos sentidos (cancela corriente/viento) | Dispersión entre pasadas ≤ 15 % | Repetir en día más calmo |
| P0.4 | Cargar los puntos (v, R) en `inputs.yaml` y ajustar `resistance.wave_cw` hasta que el modelo nominal pase por los puntos | `python sizing.py` y comparar con `figuras/R_v.png` | Error ≤ 10 % en los 3–4 puntos | Si R medida > banda alta: la batería elegida no da 2 h → elegir la siguiente o bajar crucero a 5,5 km/h |
| P0.5 | **Recién entonces comprar la batería** (la elección depende de P0.3–P0.4: con R medida ≤ nominal alcanza la LiTime 36 V 50 Ah, más liviana y barata; ver decisiones D-19/D-28). Medir las baterías elegidas contra la caja Biltema 340×200×245 antes de comprar las cajas | `run_all.py` con los puntos medidos | `resultados/sizing.json → requirements_met = true` | — |
| P0.7 | **Comprar la hélice ANTES de tornear nada** (elegida: Minn Kota MKP-32, Watski; decisiones D-06) y medir: diámetro, paso (marcado en el cubo), bore, Ø y largo del pin/ranura, retención (tuerca/rosca), largo y Ø del cubo | Calibre y cinta; cargar en `inputs.yaml → propeller.options.MKP32` | `run_all.py` en verde con los valores medidos (re-dimensiona eje, pasador, protector, patín) | Si el bore < 12 mm el asiento del eje no llega a FS 2: elegir otra hélice |
| P0.6 | Comprar motor/ESC/antichispa a Flipsky **declarando el valor real** (IVA 25 % + envío ≈ 105 €) | Checkout de flipsky.net: anotar el envío real en `costs.cn_shipping_eur` | — | Ruta AliExpress UE (decisiones D-32) |

## P1 — Probetas (imprimir con el perfil estructural, ver 05_fabricacion.md)

| # | Probeta (CAD en `04_diseno/probetas/`) | Ensayo | Pasa si |
|---|---|---|---|
| P1.1 | Peine de holguras (agujeros/ejes Ø12, 16, 20, 25, 30, 40; holgura 0,15/0,20/0,25/0,30) | Calibre + pernos reales | Encuentra la holgura que da ajuste deslizante sin juego visible; actualizar `geometry.clearance_mm` |
| P1.2 | Alojamiento de buje igus H370 Ø18 en PETG (Ø18 −0,05/−0,10/−0,15) | Prensar a mano / prensa de banco | Entra con prensa sin fisurar y no gira con la mano; actualizar `press_fit_mm` |
| P1.3 | Tuerca cautiva M6 (bolsillo transversal, h = 18 mm) | Tracción con el dinamómetro + palanca, 3 probetas | Arranque ≥ 2,1 kN (FS 3 sobre 701 N) |
| P1.4 | Inserto M4 inox en PETG (caja ESC) | Tracción, 3 probetas | Arranque ≥ 0,6 kN |
| P1.5 | Barra de flexión impresa en XY 10×10×100 seca vs 7 días en agua salada (25 g/L) | Flexión 3 puntos con dinamómetro | Pérdida ≤ 25 % (si es mayor, bajar `f_water`) |
| P1.6 | Caja con O-ring (ELE-01 reducida) + tapa Al | 24 h sumergida a 0,5 m con papel tisú adentro | Papel seco; 0 gotas |
| P1.7 | Absorción en agua salada 7 días (cubos 20 mm) | Pesar seco/mojado (balanza 0,01 g) | Ganancia ≤ 1 % |
| P1.8 | Cintura del patín (probeta del cuello) | Fuerza horizontal en la punta con dinamómetro hasta rotura | Rompe entre 200 y 400 N (diseño 300 N) |
| P1.9 | Pasador de corte 316 (3 pasadores del lote comprado) en un eje de prueba Ø = asiento de hélice | Palanca de 0,5 m + dinamómetro hasta el corte (torque = F × 0,5) | Corta entre 0,8 y 1,2 × el valor de 02_calculos §7; si no, cambiar el Ø y `propeller.shear_pin.tau_ult_mpa` |

## P2 — Banco en seco (T0) y estanqueidad (T1)

Ver 06_ensamblaje_y_pruebas.md §T0–T1. Criterios clave: kill switch corta en < 1 s en 10/10 intentos; sin arranque con acelerador fuera de cero; rampa de inversión ≥ 0,5 s; caja ESC seca tras 30 min a 0,5 m.

| # | Acción | Pasa si |
|---|---|---|
| P2.1 | **Interruptor de cordón Watski (12 V–15 A) a 24 V**: 200 aperturas sacando el clip con la bobina real del contactor y su supresor (diodo + R o TVS) | Contactor abre las 200 veces; contactos sin marcas de arco ni soldadura (lupa); resistencia de contacto < 0,1 Ω con el multímetro. Si falla: relé auxiliar 24 V entre cordón y bobina (decisiones D-33) |
| P2.2 | **VESC Tool**: filtro de fase APAGADO (FW ≥ 5.03, advertencia Flipsky); `l_in_current_max` ≤ 80 % del BMS; corriente de motor 70 A; reversa 50 %; **tope de ERPM** = valor de 02_calculos §3.1 | Parámetros guardados en `04_diseno/electronica/` (captura o XML exportado) |
| P2.3 | **Disipador del ESC**: comprar uno con R_th ≤ valor de 02_calculos §5.2 (dato del fabricante); en T2, 30 min a la potencia de crucero | Tapa de Al ≤ 50 °C (IR) con aire ≤ 30 °C a la sombra |

## P3 — Tanque / muelle (T2)

Bollard pull con el dinamómetro (bote amarrado al muelle con el dinamómetro en el cabo): **pasa si ≥ 0,85 × predicho** (≥ 247 N; predicho <!--V:sizing.bollard_fwd.T_horiz:.0f-->280<!--/V--> N), corriente de batería ≤ 75 A, motor ≤ 80 °C de carcasa tras 3 min, piezas impresas cerca del motor ≤ 50 °C (termómetro IR).

## P4 — Agua (T3, T4)

Ver 06 §T3–T4: primero agua calma, poco profunda, con remos y acompañante; luego Als Fjord en calma a < 300 m de la costa, chaleco puesto, kill cord atado, temperatura del agua registrada.

**T3 adicional — límite legal:** con 1 persona y batería llena, a fondo en agua calma, ida y vuelta con GPS: **pasa si la media ≤ 9,0 km/h** (5 kn = 9,26 km/h con margen). Si no, bajar el tope de ERPM en proporción.

## P5 — Ajustes finos

| # | Acción | Pasa si |
|---|---|---|
| P5.1 | Precarga del retén de basculación | Fuerza horizontal en el patín para que bascule (motor parado) = 60–130 N; en marcha atrás al 50 % la cola no se levanta |
| P5.2 | Tornillo de trimado | Hélice sin ventilar a máxima potencia; bote nivelado |
| P5.3 | Tensado de correa | Flecha ~3 mm con 10 N en el centro del ramal (HTD-5M 15 mm); sin salto de dientes en bollard |
