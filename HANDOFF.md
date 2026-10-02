# Handoff — estado actual (2026-10-02)

Rama: `main` (la rama de trabajo `claude/amazing-wright-rq0874` se integró con el PR #1). **Ronda 5 de la auditoría
cerrada en software**: correcciones en el repositorio (commits `2f7c670`, `81f99ec`, `9e0dc79`, `da279d2`, `e516cac`,
`3dd8551`, `50e7bac`, `52f2a45`, `6621415`); la re-auditoría del cierre (MECH-1…10, CALC-1…4, FEA-1…5, TEST-1…2, DOC-1,
REGEN-1; `auditoria.md`) está corregida o documentada; corrida completa final (`run_all.py`, no `--fast`) con exit 0 y
`pytest` completo en verde, incluida la regeneración completa. Queda una medición física (R5-N6).

## Hecho
- Paquete completo del waterjet P1-J (inputs.yaml → sizing → CAD 65 piezas → verify → estructural → planos → BOM →
  arquitectura → comparación JT132 → electrónica/firmware → probetas → FEA → visor → docs).
- Auditoría adversarial: rondas 1 (44 hallazgos) y 2 (27) corregidas; ronda 3 (FEA) superada por la ronda 4; ronda 4
  (criterio de traba única, D-17c; corrida fina en `c25d433`) superada por la re-auditoría de la ronda 5 (`auditoria.md`).
- Ronda 5 en el repositorio (D-17d): pivote P1-REV-02 con el **piloto como camino de carga** (Ø<!--V:manifest.params.REV_sp_pilot_d:g-->24<!--/V--> H7/h6
  desde el cierre de la ronda; Ø20 en la primera versión), **dúplex 1.4462 en dos piezas** desde la re-auditoría del
  cierre (MECH-1: casquillo con brida Ø36 × 4 y piloto con Loctite 641 antes del bucket, muñón por el buje después), orejas de
  <!--V:manifest.params.STE_ear_t:g-->14<!--/V--> mm con **lóbulos engrosados** (R5-N5: pivote <!--V:manifest.params.STE_piv_t:g-->20<!--/V--> mm hacia adentro; traba <!--V:manifest.params.STE_lock_t:g-->23.5<!--/V--> mm, 3 mm por fuera de la
  placa y 6,5 por dentro con r <!--V:manifest.params.STE_lock_in_r:g-->18<!--/V-->), ISO 4017 M12 × 60 + ISO 7093 + tuerca baja ISO 4035 (m <!--V:manifest.params.REV_nut_h:g-->6<!--/V-->) a **12 N·m con
  Loctite 243**; **cuerpo del émbolo AJUSTADO** de un solo Ø, Ø<!--V:manifest.params.REV_lock_bore_d:g-->24<!--/V--> H7/h6 (como el piloto), con Loctite 641, collar
  exterior Ø32 × 1,5 y anillo DIN 471-24 por dentro, sin rosca ni precarga (R5-N1; reemplaza al cuerpo M24×1,5 a 110 N·m
  con K propio de la primera versión y al Ø26 de una versión intermedia); pomo de 316 Ø23 roscado a fondo en la cola
  (R5-N4); cola del perno 42 mm (MECH-2), hexágono en la punta y tapa con agujeros de llave (MECH-7), ranura del anillo a
  24,6 (+0,1/0) de la cara de apoyo del collar (MECH-5), garganta en el tubo de la boquilla bajo el émbolo −Y (MECH-3);
  `REV_impact` eliminado; resorte re-especificado (alambre 1,4, Ø15, 6,5 espiras; check con
  compacto + Sa), eslabón rígido ajustable ±2 mm, balancines fresados con cubos y ejes/pernos 1.4401+C, pestaña de tope
  agrandada; filas a mano del aplastamiento del cuerpo y del piloto con el brazo al plano medio del agujero (R5-N2); BOM
  corregida (R5-N3: B-PIVM12, B-LOCK243 = Loctite 243 + 641, B-REAM16 con un solo Ø24 H7, B-TAP24 M20×1/M10×1, B-RING24, S-LASER,
  B-BOWDEN, barras `MP-DPX-D40`/`MP-DPX-D22`/`MP-316-D35`/`MP-316-D18`); ligamentos a mano con la misma presión lineal
  que el aplastamiento y filas nuevas del muñón en el casquillo, de la guía del perno y del collar (CALC-1…4); FEA con
  criterio de convergencia conservador (FEA-R5-01) y STE-01 con el piloto y el cuerpo ajustado como apoyos lineales, sin
  precarga (FEA-R5-02 obsoleto por diseño), el mismo r_excl en `--quick` (FEA-1), lóbulos sin caras astilla (FEA-2) y los
  pies de los lóbulos declarados como aristas vivas (FEA-3). 02, 05,
  06, PENDIENTES (P1.8, P1.9, P1.11), checklist, decisiones (D-17d), auditoría (sección «Ronda 5»), README,
  04_diseno/README y la parte escrita a mano del README del FEA describen el cuerpo ajustado, los lóbulos engrosados y el
  pivote en dos piezas, con la tabla de la re-auditoría del cierre en `auditoria.md`.

## Cierre de la ronda 5 (hecho)
- **R5-N1 y R5-N5 — diseño nuevo verificado:** CAD, manifest, `bom.py`, `structural.py`, FEA fino, `tabla_fabricacion.py`
  y `docgen.py` regenerados por el `run_all.py` completo. FEA fino de la oreja P1-STE-01: FS
  <!--V:fea.piezas.P1-STE-01.FS_min:.2f-->2.52<!--/V--> (objetivo 2; con el cuerpo roscado de la primera versión daba 1,74
  en el borde de la rosca M24 por la precarga); bucket P1-REV-01 FS <!--V:fea.piezas.P1-REV-01.FS_min:.2f-->2.07<!--/V-->.
- **R5-N2, R5-N3 y R5-N4** corregidos en el repositorio (auditoria.md). **Re-auditoría del cierre:** MECH-1…10,
  CALC-1…4, FEA-1…4, TEST-1…2, DOC-1 y REGEN-1 corregidos; FEA-5 (ventana del borde de los agujeros) queda como
  limitación declarada en el README del FEA.
- Visor republicado en `claude.ai/artifact/NAPEHA9H3BQ8r3dipj34j4` (archivos de 04_diseno/visor); PR #1 integrado en
  `main`; sitio en GitHub Pages (rama `gh-pages`, generado con `build_site.py`).

## Pendientes (mundo físico y abiertos menores)
- **R5-N6** (numerado R5-N5 hasta el cierre de la ronda): margen de la fuerza del gatillo ≈ 7 %: medir el resorte al
  recibirlo (PENDIENTES P1.8).
- Abiertos que siguen de la ronda 4: R4-16 (medición de la fuerza en banco), R4-17 (vainas en la consola, plano de
  P1-CTL-10, B-GLINS), L6 (tabla generada de P1.10 sin P1-REV-03; comentario del perfil de PrusaSlicer), M3 (B-DIAL
  con base magnética para T0.M3/T0.M4).
- Orden de trabajo físico: `PENDIENTES_GASPAR.md` (P0 medir el casco y ensayo de escora E1 antes de comprar o cortar).

## Abiertos declarados (no se resuelven desde la propulsión)
- Planeo: con resistencia alta no llega a planeo pleno; con la nominal el margen queda bajo el 10 % (README, 02 §3.2).
  Lo arregla el bote. Decide T4.
- Estabilidad del casco (W-14). Bloquea pruebas en agua.
- Chaveta del motor FS < 2 (C13): medir chavetero; cubo de acero + Loctite 648.
