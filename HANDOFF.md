# Handoff — estado actual (2026-10-02)

Rama: `claude/amazing-wright-rq0874`. **Ronda 4 de la auditoría en curso**; la cierra el agente principal después de
la corrida fina del FEA y de una re-auditoría. Los últimos commits son WIP.

## Hecho
- Paquete completo del waterjet P1-J (inputs.yaml → sizing → CAD 65 piezas → verify → estructural → planos → BOM →
  arquitectura → comparación JT132 → electrónica/firmware → probetas → FEA → visor → docs).
- Auditoría adversarial: rondas 1 (44 hallazgos) y 2 (27) corregidas; ronda 3 (FEA) superada por la ronda 4
  (`auditoria.md`).
- Ronda 4 en el repositorio: criterio de traba única (cada traba sola lleva M_h completo), cargas del chorro por
  cantidad de movimiento, bucket de 8 mm, pivote con brida y piloto, émbolo propio Ø16 / M24×1,5, orejas de 12 mm
  (D-17c); desbloqueo rediseñado (balancines P1-REV-09, vainas P1-REV-10, gatillo con barra igualadora P1-CTL-14);
  FEA de REV-01/STE-01 con casos de una traba sola, verificación de borde de agujeros y estática verificada;
  `structural.py` sin filas bajo objetivo; 02, decisiones, auditoría, README al día.

## Falta para cerrar la ronda 4 (agente principal)
- `fea_run.py --only P1-REV-01 P1-STE-01 --merge` (corrida fina) y después `docgen.py`; los marcadores `fea.*` de
  02/auditoría muestran la corrida de la ronda 3 hasta entonces. REV-01 tiene margen justo (sonda fina ≈ 2,08
  [CALCULADO: agente FEA]): si da < 2, sección extra en el brazo trabado (D-17c).
- Abiertos de `auditoria.md` ronda 4: R4-10 (contratuerca −Y contra el cuerpo de la boquilla: verify falla),
  R4-11 (par de la contratuerca M24), M2–M4/M6/M7/L2/L5/L6 (05, 06, PENDIENTES, BOM: procedimiento y prueba
  funcional nuevos, líneas del émbolo propio y del desbloqueo).
- `python run_all.py` completo + `pytest` completo; re-auditoría; cerrar `auditoria.md` y `PROGRESS.md`.
- Re-publicar el visor en `claude.ai/artifact/NAPEHA9H3BQ8r3dipj34j4` (archivos de 04_diseno/visor) y actualizar el PR.

## Abiertos declarados (no se resuelven desde la propulsión)
- Planeo: con resistencia alta no llega a planeo pleno; con la nominal el margen queda bajo el 10 % (README, 02 §3.2).
  Lo arregla el bote. Decide T4.
- Estabilidad del casco (W-14). Bloquea pruebas en agua.
- Chaveta del motor FS < 2 (C13): medir chavetero; cubo de acero + Loctite 648.
