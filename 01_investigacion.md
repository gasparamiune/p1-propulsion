# 01 — Investigación

> Versión de Pasada 1: síntesis. El detalle, con cada link abierto en esta sesión y su
> verificación adversarial, está en [`research/`](research/) (un archivo por tema).
> Pasada 2 completa este documento (proyectos, normativa DK, materiales, BOM).

| Tema | Archivo | Estado |
|---|---|---|
| Videos V1 y V2 | [research/R01_videos.md](research/R01_videos.md) | Verificado (transcripción V1, metadatos, comentarios) |
| Outboards impresos, trolling, long-tail eléctricos | [research/R02_proyectos_outboard.md](research/R02_proyectos_outboard.md) | Verificado |
| Waterjets, ducted/rim, eFoil, papers | [research/R03_proyectos_jet_ducted_efoil.md](research/R03_proyectos_jet_ducted_efoil.md) | Verificado |
| Jon boats < 2,5 m y referencias comerciales | [research/R04_bote_y_referencias.md](research/R04_bote_y_referencias.md) | Verificado |
| Materiales FDM en agua salobre y sellado | [research/R05_materiales_sellado.md](research/R05_materiales_sellado.md) | Verificado |
| Eléctrica: BLDC/VESC, kill switch, baterías, normas, galvánica | [research/R06_electrica.md](research/R06_electrica.md) | Verificado |
| Normativa danesa + Als Fjord | research/R07_dinamarca.md | En curso |
| BOM eléctrica / mecánica con envío a DK | research/R08a/R08b | En curso |
| Métodos (resistencia, B-series, cavitación) | research/R09_metodos.md | En curso |

## Hallazgos que cambian el diseño (Pasada 1)

1. **V1 no es un turbojet de combustión**: es una bomba waterjet de PETG que el autor llama "turbo jet" (transcripción 00:53). Ningún video trae datos de rendimiento. [VERIFICADO: research/R01]
2. **Capacidad del bote** ~100–185 kg (USCG ≈ 160 kg) → riesgo n.º 1. [VERIFICADO: research/R04]
3. **R(6 km/h) medida en botes análogos: 95–150 N**; 1 kW da 7,6–8,0 km/h con 2 personas; 12 km/h exige planear (2,6–5,9 kW). [VERIFICADO: research/R04]
4. **Hélice de 10–11" a ≤ 1 450 rpm** (como los fuerabordas eléctricos de 1 kW). [VERIFICADO: research/R04]
5. **Cero sellos dinámicos sumergidos** y motor seco: la cola larga es la mejor opción eléctrica para agua salobre. [VERIFICADO: research/R05, R06]
6. **Fatiga del PETG impreso**: f_fatiga ≈ 0,06 a 10⁷–10⁸ ciclos; el empuje y la correa deben ir a metal. [VERIFICADO: research/R05]
7. **Kill switch en hardware** (contactor monoestable + cordón cerrado con clip + seta); el antichispa MOSFET falla en corto. [VERIFICADO: research/R06]
8. **Aro protector romo** con 4–5 % de holgura pierde hasta 25 % de K_T → aro perfilado tipo 19A con 2–3 % de holgura. [VERIFICADO: research/R03]
9. **Reducción obligatoria y límite de corriente**: un 6374 en directo quemó 2 motores en un long-tail. [VERIFICADO: research/R02]
10. **Ángulo de eje ≥ 20°** (a 15° ventilaba). [VERIFICADO: research/R02]
