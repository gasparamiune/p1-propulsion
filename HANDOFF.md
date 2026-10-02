# Handoff — estado actual (2026-10-02)

Rama: `claude/amazing-wright-rq0874`. **Ronda 4 de la auditoría en curso**; la cierra el agente principal después de
la corrida fina del FEA y de una re-auditoría. Los últimos commits son WIP.

## Hecho
- Paquete completo del waterjet P1-J (inputs.yaml → sizing → CAD 65 piezas → verify → estructural → planos → BOM →
  arquitectura → comparación JT132 → electrónica/firmware → probetas → FEA → visor → docs).
- Auditoría adversarial: rondas 1 (44 hallazgos) y 2 (27) corregidas; ronda 3 (FEA) superada por la ronda 4
  (`auditoria.md`).
- Ronda 4 en el repositorio: criterio de traba única (cada traba sola lleva M_h completo), cargas del chorro por
  cantidad de movimiento, bucket de 8 mm, pivote con brida y piloto, émbolo propio Ø16 / M24×1,5 con collar, orejas de 12 mm
  (D-17c); desbloqueo rediseñado (balancines P1-REV-09, vainas P1-REV-10, gatillo con barra igualadora P1-CTL-14);
  FEA de REV-01/STE-01 con casos de una traba sola, verificación de borde de agujeros y estática verificada;
  `structural.py` sin filas bajo objetivo; 02, decisiones, auditoría, README al día.

## Falta para cerrar la ronda 4 (agente principal)
- `fea_run.py --only P1-REV-01 P1-STE-01 --merge` (corrida fina) y después `docgen.py`; los marcadores `fea.*` de
  02/auditoría muestran la corrida de la ronda 3 hasta entonces. REV-01 tiene margen justo (sonda fina ≈ 2,08
  [CALCULADO: agente FEA]): si da < 2, sección extra en el brazo trabado (D-17c; auditoría R4-15).
- Abiertos de `auditoria.md` ronda 4 (IDs con la numeración original de los auditores; R4-10 en adelante aparecieron
  al corregir): R4-15 (margen de REV-01: depende de la corrida fina), R4-16 (fuerza de liberación: medir en banco),
  R4-17 (ruta de las vainas en la consola, plano de P1-CTL-10, B-GLINS), M2 en la BOM (B-REAM16 todavía pide
  «4 casquillos guía Ø16,5»: hacen falta casquillos recambiables por herramienta, 05 §4), L6 (tabla generada de
  P1.10 sin P1-REV-03; comentario del perfil de PrusaSlicer); M3 a confirmar (B-DIAL con base magnética para
  T0.M3/T0.M4: ¿hay acero donde apoyarla?). Cerrados en esta pasada: la contratuerca M24 se
  reemplazó por un collar integral Ø36 apretado a <!--V:manifest.params.REV_lock_T_Nm:g-->75<!--/V--> N·m con Loctite 243 (filas a mano de
  P1-REV-04 y P1-STE-01) (R4-12, antes «R4-10/R4-11»); BOM regenerada con `form: bars` (M7).
- Quedan textos con «contratuerca» del émbolo fuera de los documentos: comentarios de `piezas/_release.py`,
  textos de `fea/fea_run.py` y `fea/fea_parts.py` (salen en el bloque AUTO del README del FEA con el `--merge`) y el
  rótulo «barra Ø25» del plano P1-REV-04_embolo_cuerpo en `planos_direccion.py` (la BOM compra Ø40).
- `python run_all.py` completo + `pytest` completo; re-auditoría; cerrar `auditoria.md` y `PROGRESS.md`.
- Re-publicar el visor en `claude.ai/artifact/NAPEHA9H3BQ8r3dipj34j4` (archivos de 04_diseno/visor) y actualizar el PR.

## Abiertos declarados (no se resuelven desde la propulsión)
- Planeo: con resistencia alta no llega a planeo pleno; con la nominal el margen queda bajo el 10 % (README, 02 §3.2).
  Lo arregla el bote. Decide T4.
- Estabilidad del casco (W-14). Bloquea pruebas en agua.
- Chaveta del motor FS < 2 (C13): medir chavetero; cubo de acero + Loctite 648.
