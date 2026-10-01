# 03 — Arquitectura

## 1. Opciones evaluadas

| Id | Opción | Esencia |
|---|---|---|
| A1 | Fueraborda, motor en pod **seco sellado** | Motor en cápsula bajo el agua con retén dinámico en el eje |
| A2 | Fueraborda, motor en pod **inundado** | Outrunner/inrunner mojado (estilo eFoil) |
| A3 | **Cola larga (long-tail) eléctrica** | Motor seco arriba, correa, eje inclinado en tubo con bujes de agua |
| B | Conversión de trolling motor | Trolling comercial + soporte basculante, protector y caña impresos |
| C | Waterjet impreso | Impulsor + estator + tobera impresos (como el video V2) |
| D | Hélice entubada / rim-driven | Tobera o motor en anillo impresos |
| E | Propulsión aérea eléctrica | Hélice de aire (solo comparación) |
| F | Motor comercial completo (referencia) | Trolling de agua salada 55 lb + LiFePO4 (o fueraborda eléctrico de 1 kW) |

## 2. Pesos (justificación)

- **Seguridad 18 %** — uso en el mar con personas; manda sobre el alcance (requisito 1).
- **Eficiencia 15 % y costo 12 %** — prioridad declarada del usuario: autonomía + costo.
- **Poca profundidad/arena 10 %** — requisito explícito (basculación, protección, pasador).
- **Viabilidad con PETG/herramientas 10 %** — el proyecto existe para imprimir lo razonable.
- **Sellado 8 %, corrosión 7 %, consecuencia de falla 7 %, reparabilidad 7 %, tiempo 6 %** — agua salobre, casco de aluminio, < 300 m de la costa, prototipo.

Puntajes 1–5 en `inputs.yaml → architecture_matrix` (juicio de ingeniería [SUPUESTO] apoyado en research/R02–R06; motivos en §3).

## 3. Matriz ponderada y sensibilidad de pesos

<!-- AUTO:arch -->
| Opción | eficiencia (15 %) | seguridad (18 %) | viabilidad_petg (10 %) | sellado (8 %) | corrosion (7 %) | costo (12 %) | tiempo (6 %) | reparabilidad (7 %) | poca_prof (10 %) | falla_mar (7 %) | **Total** | Gana en MC |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **A3** Cola larga: motor seco arriba + correa + eje inclinado | 4 | 5 | 4 | 5 | 4 | 3 | 3 | 5 | 5 | 4 | **4.25** | 86 % |
| **F** Motor comercial completo (trolling de agua salada 55 lb + LiFePO4) | 3 | 5 | 5 | 5 | 4 | 4 | 5 | 2 | 2 | 4 | **3.93** | 14 % |
| **B** Conversión de trolling motor (soporte kick-up + protector impresos) | 3 | 4 | 4 | 4 | 4 | 4 | 4 | 3 | 3 | 4 | **3.68** | 0 % |
| **A2** Fueraborda con motor en pod inundado | 4 | 3 | 3 | 3 | 2 | 3 | 3 | 3 | 2 | 3 | **2.98** | 0 % |
| **C** Waterjet impreso | 2 | 4 | 2 | 3 | 3 | 3 | 2 | 3 | 4 | 3 | **2.97** | 0 % |
| **E** Propulsión aérea eléctrica (solo comparación) | 1 | 1 | 3 | 5 | 5 | 4 | 3 | 4 | 5 | 2 | **2.96** | 0 % |
| **D** Hélice entubada / rim-driven impreso | 3 | 4 | 2 | 2 | 2 | 3 | 2 | 2 | 3 | 3 | **2.80** | 0 % |
| **A1** Fueraborda con motor en pod seco sellado | 4 | 3 | 2 | 1 | 3 | 3 | 2 | 2 | 2 | 3 | **2.66** | 0 % |

Sensibilidad: variando cada peso ±50 % (renormalizado), el ganador **no cambia** en ninguno de los 20 casos.
Monte Carlo (20000 juegos de pesos Dirichlet alrededor de los nominales): A3 86 %, F 14 %.
<!-- /AUTO:arch -->

Motivos de los puntajes clave:
- **A3 seguridad 5 / sellado 5 / reparabilidad 5:** no hay electrónica ni sellos dinámicos sumergidos (research/R05: un retén estándar pide eje ≥ 45 HRC, el 316 no lo es; research/R06: un outrunner inundado exige desarme y enjuague tras cada uso). Todo lo que se rompe está arriba del agua y es estándar.
- **A3 poca profundidad 5:** la profundidad de la hélice se regula en marcha con la caña y la cola bascula sola ante un golpe; los surface drives se usan justamente en barro y arena (research/R02 B4).
- **A1/A2 eficiencia 4 pero sellado 1–3:** el pod da buena hidrodinámica pero la cápsula sellada en agua salobre es el modo de falla típico (research/R03: bombeo térmico, ingreso de agua).
- **C eficiencia 2:** un waterjet chico a 6–8 km/h rinde mucho menos que una hélice grande y lenta (research/R03; video V2 en research/R01).
- **E seguridad 1:** hélice de aire expuesta a la altura de las personas, ruido, empuje pobre a baja velocidad.
- **F costo 4 / tiempo 5 / poca profundidad 2:** barato y listo, pero sin basculación protegida y con ~0,6 kW (research/R04 §B.4).

## 4. Recomendación y plan B

**Recomendada: A3 cola larga** (gana por amplio margen y es robusta a los pesos).

**Plan B (concepto documentado): B/F — trolling motor de agua salada + accesorios impresos.**
Comprar un trolling de agua salada de 55 lb / 12 V (≈ 5 500 kr; research/R04) y una LiFePO4
12 V 100 Ah; imprimir (i) un soporte de popa basculante con retén y tope que reemplace la
abrazadera fija del trolling, (ii) un protector de hélice segmentado y un patín fusible, (iii)
una extensión de caña. Ventajas: costo ~1 000 €, días en vez de semanas. Desventajas: ~0,6 kW
(V máx ~6–7 km/h), pata larga para un espejo de 381 mm, motor sumergido no reparable. **Usarlo
si** P0.2 (capacidad) obliga a operar con 1 persona o si el objetivo se reduce a 6 km/h en agua profunda.

## 5. Se imprime / se compra / se tornea

| Se imprime (PETG) | Se compra | Se tornea / mecaniza |
|---|---|---|
| Abrazadera de popa, zapatas, base y mejillas de horquilla, cuna y su tapa, placa motriz y puente*, cubrecorrea, capó, abrazaderas de caña, carcasa inferior, protector (6 segmentos), patín fusible, caja ESC, puño del acelerador, collar del sensor, soporte de kill switch | Motor BLDC, ESC VESC, batería LiFePO4 + cargador, hélice, poleas y correa HTD-5M, rodamientos 6002 inox, tubos de Al (cola y caña), tornillería A4, fusible, desconectador, contactor + kill cord + seta, cables, prensaestopas, O-ring, ánodo | Eje 316 Ø16 (muñones, asientos, pasador, roscas), pernos de dirección y basculación (316), bujes de POM (3 de tubo, dirección, pivote), separadores del puente, pasadores de corte (Al), placa de caña y tapa-disipador (Al, taladrar) |

\* En la Pasada 2 la placa motriz pasa a aluminio por fatiga (ver decisiones D-25).

## 6. Cinco riesgos principales y mitigación

| # | Riesgo | Consecuencia | Mitigación |
|---|---|---|---|
| 1 | **Sobrecarga del bote** (capacidad ~160 kg vs carga ~250 kg) | Francobordo bajo, embarque de agua con ola, vuelco | P0.2 antes de todo; 1 adulto o carga reducida si no pasa; salir solo en calma; chalecos puestos |
| 2 | R(v) real mayor que la banda (casco más lleno o rocker) | Autonomía < 2 h | Calibrar por remolque **antes** de comprar la batería; crucero a 5,5 km/h si hace falta |
| 3 | Fatiga/creep de piezas PETG en la ruta de carga | Fisura y pérdida de la unidad | Piezas gruesas con σ_a ≪ 1 MPa, placa motriz en Al, cabo de seguridad, inspección post-uso, patín fusible |
| 4 | Golpe de hélice en piedra/arena | Rotura de eje/correa o hélice | Basculación con retén regulable, patín que toca primero, pasador de corte Al calibrado, ESC con límite de corriente |
| 5 | Falla eléctrica (agua en la caja ESC, kill que no corta) | Motor sin control o sin propulsión | Kill por contactor en hardware + kill por software (redundante), caja con O-ring y tapa Al, T0/T1 con criterio pasa/no-pasa, remos a bordo |
