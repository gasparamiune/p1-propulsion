# Registro de decisiones y supuestos — P1

Formato: **Decisión** · Alternativas · Justificación · Etiqueta · *Qué cambia si el dato real difiere*.
Todos los valores numéricos viven en [`inputs.yaml`](inputs.yaml); aquí se explica el porqué.

## Embarcación y carga

**D-01 Bote de diseño: jon boat de 8 ft (LOA 2,44 m, LWL 2,0 m, manga 1,20 m, fondo 0,95 m, puntal 0,38 m, casco 45 kg).**
- Alternativas: 2,1 m (car-topper) o 2,5 m.
- Justificación: casi no hay jon boats < 2,5 m en catálogos actuales; el del usuario es probablemente un 8 ft estadounidense o similar (research/R04 §A.1). Se toma LWL corta (Fr mayor → más resistencia) y casco pesado: conservador para la propulsión.
- [ESTIMADO: research/R04 §A.4].
- *Si difiere:* medir y actualizar `boat.*`; `run_all.py` recalcula R(v), batería, largo de cola (la hélice se ubica a profundidad fija bajo la flotación) y abrazadera.

**D-02 Carga: 2 × 100 kg + 12 kg de equipo + 5 kg de margen.**
- Alternativas: 75–85 kg por persona (promedio).
- Justificación: conservador para resistencia y empuje.
- [SUPUESTO].
- *Si difiere:* menos masa → menos potencia de crucero (sensibilidad n.º 2, 02 §10).

**D-16 Capacidad del bote estimada en 160 kg y señalada como RIESGO N.º 1.**
- Alternativas: suponer 250 kg (valor inicial, descartado).
- Justificación: los aluminio de fondo plano cargan 34–63 kg/m² (LOA × manga) → 100–185 kg; la regla USCG 33 CFR 183.35 da ≈ 160 kg (research/R04 §A.3). Con 2 adultos + propulsión la carga útil supera la capacidad. No se "sube la placa por cálculo".
- [ESTIMADO: research/R04].
- *Si difiere:* si la placa real es ≥ carga útil, el riesgo baja; si no, operar con 1 adulto + equipo, o 2 personas livianas con batería chica (opción LFP24_50, 11,5 kg) y nunca con ola.

## Arquitectura

**D-03 Arquitectura A3 "cola larga" eléctrica (motor seco arriba, correa, eje inclinado, hélice comprada).**
- Alternativas: pod sellado (A1), pod inundado (A2), conversión de trolling (B), waterjet (C), entubada/rim (D), aérea (E), comercial (F).
- Justificación: matriz ponderada 03 (gana con amplio margen y en 86 % de 20 000 pesos aleatorios). Decisivo: **cero sellos dinámicos y cero electrónica sumergida** en agua salobre (research/R05, R06), basculación natural para arena (research/R02 B4: los surface drives regulan la profundidad en marcha).
- [CALCULADO: arquitectura.py].
- *Si difiere:* si la prioridad pasa a "mínimo costo con 6 km/h en agua profunda", conviene F/B (plan B).

**D-04 Ángulo de eje 25° y pivote 135 mm sobre el borde del espejo, 80 mm a popa.**
- Alternativas: 15–20° (más eficiente, cola más larga y ventilación a baja inmersión); 30° (más pérdida axial).
- Justificación: research/R02 B4 — a 15° la hélice ventilaba; a 20° duplicó la velocidad. 25° da 9,4 % de pérdida axial con cola de ~1,1 m. El pivote alto despeja el plato de dirección y la basculación (verificado por `verify_parts.py`).
- [SUPUESTO + CALCULADO].
- *Si difiere:* el tornillo de trimado (MNT-03) permite ±5° in situ; cambiar `architecture.shaft_angle_deg` y regenerar.

**D-17 Basculación máxima 25°.**
- Alternativas: 30–45° (choca el cubrecorrea con la base de la horquilla y el espejo).
- Justificación: con ~22° la punta de la hélice sale del agua; a 25° queda ~110 mm sobre la flotación ([CALCULADO], 02 §8). Más ángulo exige subir el pivote o adelgazar el tren de poleas.
- [CALCULADO + VERIFICADO en software].
- *Si difiere:* si se necesita varar o remolcar con la cola más alta, desmontar la unidad (2 tornillos de apriete).

## Hidrodinámica y propulsor

**D-05 Modelo de resistencia por componentes (ITTC-57 + espejo de Holtrop + olas/joroba calibrable) con banda [0,75; 1,15].**
- Alternativas: Savitsky (fuera de rango: no planea), series sistemáticas (L/∇^⅓ ≈ 3 fuera de rango), Gerr (solo contraste).
- Justificación: ninguna serie cubre un casco tan corto y lleno. La banda se ancló a datos medidos de botes de 2,4–2,75 m (R(6 km/h) = 95–150 N; research/R04 §C.3). Se dimensiona con el borde alto.
- [ESTIMADO + calibración pendiente].
- *Si difiere:* el remolque con dinamómetro (PENDIENTES P2) ajusta `resistance.wave_cw`; batería y relación de poleas se recalculan solas.

**D-06 Hélice comprada de 10 × 8 in, 3 palas, cubo con pasador, bore ≥ 16 mm (no impresa).**
- Alternativas: 7,8 × 6 de fueraborda de 2,5–3,5 hp (η0 ≈ 0,38, +40 % de energía); 11 × 8 (no cumple calado máx.); hélice de PETG.
- Justificación: una hélice de PETG a ~1 kW tiene σ en raíz ≈ 30 MPa frente a una admisible en fatiga < 1,5 MPa (02 §4.4) → inviable. Los fuerabordas eléctricos de 1 kW usan 10–11" a 1 200–1 450 rpm (research/R04 §B.3).
- [CALCULADO + VERIFICADO: research/R04].
- *Si difiere:* cargar diámetro/paso/bore reales en `propeller.options`; el eje se tornea al bore real.

**D-07 Eje AISI 316 Ø16 con muñones Ø15 (6002).**
- Alternativas: Ø12 (FS fatiga 1,1 y torsión en el pasador 1,3: **rechazado**), dúplex 2205 (mejor, más caro).
- Justificación: FS ≥ 2,5 en todas las secciones (02 §7). Velocidad crítica ≥ 5× la máxima.
- [CALCULADO].
- *Si difiere:* si la hélice tiene bore 15,875 mm (5/8"), usar barra de 5/8".

**D-08 Polea conducida entre dos rodamientos (placa motriz + puente).**
- Alternativas: polea en voladizo con 2 rodamientos en un buje (FS fatiga 1,6 en el muñón).
- Justificación: momento en el eje ÷2; el puente trabaja en tracción en su plano.
- [CALCULADO].

**D-09 Tubo de cola Al 6061-T6 Ø40×3 (no inox 25×1,5).**
- Alternativas: inox 316 25×1,5 (capacidad ~120 N·m → **cede** con el momento dinámico de impacto ≈ 0,19·F·L ≈ 250 N·m), inox 38×2 (pesado), GFRP.
- Justificación: capacidad ≈ 720 N·m, 0,94 kg/m, mismo metal que el casco (no hay par galvánico con él); el eje inox está aislado por bujes de POM.
- [CALCULADO].

**D-10 Basculación con retén de bola (15 N·m) + gravedad; marcha atrás limitada al 50 % de corriente por firmware.**
- Alternativas: traba manual de marcha atrás (si se olvida, anula la protección), amortiguador.
- Justificación: momento de empuje en reversa ≈ 6 N·m ≪ gravedad + retén ≈ 40 N·m (FS ≈ 7); en avance el impacto libera con ~95 N horizontales en el patín.
- [CALCULADO].
- *Si difiere:* la precarga del émbolo es regulable; calibrar con dinamómetro (PENDIENTES P5).

**D-11 Pasador de corte de Al 6061-T6 Ø2,5–3 mm → corta a ≈ 2× el torque máximo normal.**
- Alternativas: inox (corta a ~3× más: no protege), latón (descincifica).
- Justificación: protege eje, correa y placa (02 §7.4).
- [CALCULADO].

**D-12 Patín fusible: rompe con 300 N horizontales en su punta.**
- Justificación: con la cola trabada (reversa o retén atascado), 300 N × 1,13 m mantienen el tubo de Al con FS ≥ 2 y todas las piezas impresas aguas arriba con FS ≥ 3 (02 §9). Arena (contacto largo) no lo rompe; una piedra a 9 km/h sí → se reemplaza (impresión de ~4 h).
- [CALCULADO].

## Montaje

**D-13 Abrazadera en C impresa, tornillos altos (z = −35), apriete ≤ 2,5 N·m, placa de reparto A4 y re-apriete antes de cada salida.**
- Alternativas: pasantes al espejo (perforar el bote), soporte comercial de fueraborda.
- Justificación: con 5 N·m la esquina de la C quedaba en FS 1,7 a creep. La C no depende del apriete para el empuje (apoyo directo). Cabo de seguridad obligatorio.
- [CALCULADO].
- *Si difiere:* espejo de chapa desnuda de 1,2 mm → agregar taco de HDPE ≥ 25 mm (research/R04 §A.5).

**D-14 Dirección por plato giratorio sobre la abrazadera + horquilla de 3 piezas planas.**
- Justificación: el tubo pasa por encima del plato; cada pieza se imprime con la carga en el plano de capas.
- [SUPUESTO + VERIFICADO en software].

**D-15 Caña sobre placa de Al 6082 de 10 mm apretada por los pernos pasantes de la tapa de cuna, desplazada 70 mm a babor.**
- Alternativas: caña en la placa motriz (7 mm: σ ≈ 200 MPa → rechazado), soporte lateral impreso (aplastamiento FS 0,5 → rechazado).
- Justificación: el momento de la caña llega a la cuna como par de fuerzas de compresión.
- [CALCULADO].
- *Si difiere:* la ergonomía (puño ~34 cm sobre el borde) se revisa en P2.

**D-18 Uniones roscadas: tuerca A4 cautiva como estándar; nunca Loctite 243 sobre PETG.**
- Justificación: research/R05 (tuerca cautiva 166 kg vs inserto 119 kg; anaeróbicos fisuran termoplásticos).
- [VERIFICADO: research/R05].

## Eléctrico

**D-19 Batería LiFePO4 24 V (2 × 12,8 V 100 Ah en serie) elegida por el optimizador.**
- Alternativas: 16S 51,2 V (V máx 10 km/h, pero 58,4 V supera 48 V nominal y el umbral de 50 V CC de ISO 16315: **rechazada**); 12S 38,4 V (evaluada en Pasada 2); 24 V 50 Ah (no cumple 2 h + 20 % en la banda de diseño).
- Justificación: mínimo costo que cumple energía, corriente, tensión, cavitación y calado (02 §6). LiFePO4 por seguridad térmica (research/R06).
- [CALCULADO].
- *Si difiere:* si el remolque da la banda nominal, alcanza una batería de 60 Ah.

**D-20 ESC en caja estanca dentro del bote con tapa-disipador de aluminio; cables DC cortos y fases largas.**
- Justificación: protege el ESC de cables largos de batería; la tapa de Al disipa (una caja PETG cerrada superaría 60 °C).
- [CALCULADO].

**D-21 Cable DC 16 mm² (el fusible de 100 A lo protege), fases 10 mm²; fusible ≤ 178 mm del borne.**
- Justificación: caída ≤ 3 % y ampacidad ≥ calibre del fusible (un test detectó 10 mm² + 100 A: corregido).
- [CALCULADO + VERIFICADO: research/R06 ABYC E-11 7"].

## Software y entorno

**D-24 Blender: `bpy` 5.0.1 (pip) en lugar de Blender 5.1.**
- Justificación: no hay `bpy` 5.1 para Python 3.11; el `.blend` generado abre en Blender 5.1. FEA con gmsh requiere `libglu1-mesa` del sistema.
- [VERIFICADO: instalación en esta sesión].
