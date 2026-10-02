# Handoff — estado al cortar la sesión (2026-10-02)

Rama: `claude/amazing-wright-rq0874`. El último commit es WIP: el fix de la ronda 3 (FEA) quedó a medias.

## Hecho
- Paquete completo del waterjet P1-J (inputs.yaml → sizing → CAD 65 piezas → verify → estructural → planos → BOM → arquitectura → comparación JT132 → electrónica/firmware → probetas → FEA → visor → docs).
- Auditoría adversarial: ronda 1 (44 hallazgos) y ronda 2 (27) corregidas y documentadas en `auditoria.md`.
- `run_all.py --fast` y 113 tests pasaban antes del WIP de la ronda 3.

## A medias (ronda 3, FEA)
- F-01 CRÍTICO: P1-REV-01 bucket FS 0,44 (traba solo en un brazo). Fix en curso: traba en ambos brazos + brazos 6 mm
  (variante FEA V2: FS 2,34). Tocados: P1-REV-01, REV-04, REV-09, REV-10, `_release.py`, params_direccion, planos_direccion,
  fea_parts.py. Falta: modelo FEA con trabas por lado, rebuild, verify, structural_direccion (M_h al/los brazo/s trabado/s), FEA.
- F-02: P1-CTL-02 PETG FS 2,74 < 3 → paredes de 5 mm hacia afuera (variante FS 3,5). Ver si quedó aplicado.
- F-03: radios en STE-01 (oreja/labio) y DRV-03 (alma/alojamiento).

## Pendiente después
- BOM: 2.º émbolo de traba y lo que cambie del bucket/Bowden.
- `python run_all.py` completo (no --fast, con FEA) + `pytest` completo (incl. tests/test_regeneration_full.py).
- Cerrar auditoria.md (ronda 3) y PROGRESS.md (DoD).
- Re-publicar el visor en https://claude.ai/artifact/NAPEHA9H3BQ8r3dipj34j4 (archivos de 04_diseno/visor).
- Actualizar el PR de la rama (descripción: waterjet).

## Abiertos declarados (no se resuelven desde la propulsión)
- Planeo: con resistencia alta no llega a planeo pleno; nominal margen 4 % < 10 %. Lo arregla el bote (~22 kg menos o L_wl ≥ 1,96 m). Decide T4.
- Estabilidad del casco: GM ≈ 0,008 m (W-14). Bloquea pruebas en agua.
- Chaveta del motor FS 1,74 < 2 (C13): medir chavetero; cubo de acero + Loctite 648.
