# R13 — Marco legal y normativo del jet boat eléctrico de Jorge (2,30 × 0,80 m, waterjet inboard; motor de 18,8 kW de catálogo limitado por configuración a ≈ 6,6 kW pico en el eje, 43,8 V)

Fecha de investigación: 2026-10-01. Alcance: bote propio de Jorge, piloto sentado **dentro** del casco con volante, waterjet inboard eléctrico (diseño actual: Maytech MTI120116, **18,8 kW máx. de catálogo**, limitado por la configuración del VESC a ≈ 6,6 kW pico en el eje; batería 12S2P de 43,8 V; ver §2 "Potencia configurada"), objetivo ≥ 30 km/h (16,2 kn) fuera de la franja costera, Als Fjord / Als Sund (Sønderborg, DK).
**No es asesoría legal.** Todo lo que no está citado textualmente queda "a confirmar" (ver §8).

Convenciones: [VERIFICADO: url] = página abierta en esta sesión, con el texto citado presente (cita en danés o inglés + traducción). [ESTIMADO: base] = deducción o cálculo propio. [SUPUESTO] = decisión de diseño propuesta. Lo ya verificado en R07 y R10b no se repite: se remite a esas secciones.

Ya verificado y que no se repite aquí: el límite de 5 kn a menos de 300 m de la costa (R07 §1.2); los chalecos (BEK 765/2024 §5, R07); el umbral de 19 kW y la definición de "planende" en la página de Søfartsstyrelsen (R07); la LVD de 75–1 500 V CC (R07); ISO 16315 3.1, que fija 50 V CC (R06/R10b); ISO 13297 8.1 y ABYC E-11 (R06); el GM, la capacidad (33 CFR 183.33) y la estabilidad del plano (R10b H1/H6).

---

## 0. Resumen ejecutivo

| # | Pregunta | Respuesta corta | Etiqueta |
|---|---|---|---|
| 1 | ¿Norma de vandscooter vigente? | **BEK 809/2019 sigue vigente** ("Status: Valid", no histórica). El "EndDate 2026‑06‑23" es un campo de metadatos, no una fecha de derogación: otras normas vigentes traen EndDate ya pasados. No hay una norma que la reemplace | [VERIFICADO: retsinformation, §1.1] |
| 1 | ¿El bote es vandscooter? | **Probablemente no**, siempre que el piloto vaya sentado *dentro* de un cockpit. La definición exige operarlo "sidder, står eller knæler på – snarere end i – skroget". La guía oficial de la RCD dice que los "mini jet boats" < 4 m **no** son PWC. Que sea eléctrico **no** lo excluye: Søfartsstyrelsen incluye como "lignende fartøjer" los surf y SUP eléctricos | [VERIFICADO, §1] |
| 1 | Si cayera en la definición | Prohibido navegar a < 300 m de la costa salvo tránsito directo y perpendicular a ≤ 5 kn, lo que deja **inutilizable Als Sund** (~500 m de ancho). Prohibido en Natura 2000 (N197: Sønderborg Bugt, Flensborg Fjord, Nybøl Nor), en el vildtreservat de Augustenborg y en zonas fredede. Hacen falta vandscooterbevis (16 años), seguro obligatorio y límite de 0,5 ‰. Multa de 5 000 / 10 000 DKK | [VERIFICADO, §1.3] |
| 2 | Speedbåd | Norma vigente: **BEK 749/2020**. Con < 4 m y planeante, hace falta bevis **desde 19 kW de "fremdrivningseffekt"**. La norma **no define** cómo se mide esa potencia y no tiene regla especial para motores eléctricos. El motor elegido declara 18,8 kW de catálogo: el margen lo da la **configuración del VESC** (≈ 8,4 kW de batería, ≈ 6,6 kW pico en el eje; §2 "Potencia configurada"), no el hardware | [VERIFICADO] + [ESTIMADO, §2] |
| 2 | Seguro / edad | Seguro obligatorio solo si el fartøj exige "uddannelseskrav" (speedbåd o vandscooter). Con < 19 kW y sin ser vandscooter no es obligatorio, y no encontré edad mínima | [VERIFICADO: BEK 1340/2018 §1] |
| 3 | Velocidad fuera de 300 m | No hay límite numérico general fuera de los 300 m. Rigen la "sikker fart" y las zonas portuarias: **Sønderborg Havn (todo Als Sund entre el sur del castillo y Alssundbroen): 4 kn**. A 250 m de cada lado del puente Christian X, solo la velocidad mínima para maniobrar. Augustenborg Havn 4 kn; Sønderborg Lystbådehavn, Augustenborg Yachthavn y Egernsund 3 kn. **Hay corriente de hasta 3 kn en Als Sund** | [VERIFICADO: Den Danske Havnelods, §3] |
| 3 | ¿Dónde son legales los 30 km/h? | Solo en la franja central de **Als Fjord** (2–3 km de ancho, a más de 300 m de cada orilla) y en la parte danesa ancha de Flensborg Fjord / Sønderborg Bugt. **Nunca en Als Sund ni en Augustenborg Fjord** | [ESTIMADO: geometría R07 + reglas §3] |
| 4 | 72 V | **No hay obligación legal en DK** para la instalación a bordo de un bote propio < 2,5 m: la RCD no aplica (eslora y construcción propia) y la elsikkerhedsloven excluye las "elektriske installationer på skibe". ISO 16315 es voluntaria: por encima de 50 V pide "precautions against the risk of electric shock". El cargador de 230 V sí entra en la LVD y en la normativa eléctrica | [VERIFICADO, §4] |
| 5 | Estabilidad y flotación | **No hay norma obligatoria** para este casco: está fuera de la RCD y BEK 765/2024 solo exige equipo. Solo rige el deber general de navegabilidad del patrón. Referencia voluntaria: ISO 12217‑3 (< 6 m; vigente la ed. 2022), con criterios numéricos verificables de 33 CFR 183.105 / .225 / .230 | [VERIFICADO, §5] |
| 6 | Kill switch | **No es obligatorio** en DK para este bote. La RCD 5.1.5 lo exige solo a PWC comercializados (corte automático o giro lento en círculo) y la 5.1.6 solo a fuerabordas con caña. No existe un punto "5.1.8" sobre este tema. BEK 809/2019 no dice nada al respecto | [VERIFICADO, §6] |
| 7 | Ruido / ola | No hay límite numérico de ruido aplicable. El reglamento policial prohíbe "unødig støj" y causar "fare, hinder eller ulempe" a bañistas y a otros. Pasar con "ringe fart" junto a botes fondeados. Generar ola innecesaria con riesgo para otros = "groft hensynsløs sejlads" | [VERIFICADO, §7] |

---

## 1. ¿Es "vandscooter"? Norma vigente y criterios de diseño

### 1.1 Vigencia de BEK 809/2019 (resuelve el pendiente de R10b H22)

| Ítem | Dato | Fuente |
|---|---|---|
| Metadatos de BEK 809/2019 | `<Status>Valid</Status>`, `<StartDate>2019-08-15`, `<EndDate>2026-06-23`, `<PopularTitle>Vandscooterbekendtgørelsen` | [VERIFICADO: https://www.retsinformation.dk/eli/lta/2019/809/xml] |
| Búsqueda "vandscooter" en Retsinformation (87 resultados, ordenados por fecha) | BEK 809/2019 aparece con `"isHistoryFlag": false`. No hay ninguna bekendtgørelse de vandscooter posterior a 2019 | [VERIFICADO: https://www.retsinformation.dk/api/documentsearch?t=vandscooter&ps=15&o=40] |
| ¿EndDate = derogación? | **No.** Otras normas vigentes traen EndDate pasados: BEK 766/2024, "Valid" con EndDate 2024‑06‑22; BEK 1548/2025, "Valid" con 2025‑12‑09; BEK 637/2025, "Valid" con 2026‑06‑23. Es una fecha de metadatos, no de vigencia | [VERIFICADO: …/eli/lta/2024/766/xml, …/2025/1548/xml, …/2025/637/xml] + [ESTIMADO: interpretación del campo] |
| Confirmación por las autoridades (2026) | Søfartsstyrelsen enlaza "Miljøministeriets bekendtgørelse om sejlads med vandscootere". Sønderborg Kommune y Styrelsen for Grøn Arealomlægning og Vandmiljø (SGAV) describen las mismas reglas (300 m, Natura 2000, playas). La circular del Rigsadvokat del 15‑02‑2026 sigue usando la "vandscooterbekendtgørelsen" para las multas | [VERIFICADO: https://www.soefartsstyrelsen.dk/fritidssejlads/fritidsfartoejer/vandscooter-og-jetski] [VERIFICADO: https://sonderborgkommune.dk/vandscootersejlads] [VERIFICADO: https://sgavmst.dk/natur-og-jagt/regler-for-faerdsel-i-naturen/hvor-maa-jeg-faerdes/paa-havet] [VERIFICADO: https://www.retsinformation.dk/eli/retsinfo/2026/9486/xml] |
| Norma del bevis de vandscooter vigente | **BEK 663/2020** (vandscooterførerbekendtgørelsen), "Valid", en vigor desde el 27‑05‑2020; deroga BEK 555/2020. BEK 1725/2017 es histórica | [VERIFICADO: https://www.retsinformation.dk/eli/lta/2020/663/xml] [VERIFICADO: …/eli/lta/2017/1725/xml] |

### 1.2 Definiciones exactas (las tres normas usan el mismo texto)

| Norma | Texto literal | Traducción | Fuente |
|---|---|---|---|
| BEK 809/2019 §1 (zonas) | "Ved en vandscooter forstås et vandfartøj beregnet til fritidsformål med en skroglængde på under 4 m, som anvender en fremdriftsmotor med vandstrålepumpe som hovedfremdrivningsmiddel, og som er beregnet til at skulle betjenes af en eller flere personer, som sidder, står eller knæler på – snarere end i – skroget." | "Se entiende por vandscooter una embarcación de recreo de eslora de casco menor de 4 m que usa un motor de propulsión con bomba de chorro de agua como medio principal de propulsión, y que está pensada para ser manejada por una o más personas que se sientan, están de pie o arrodilladas **sobre** el casco, y no **dentro** de él." | [VERIFICADO: https://www.retsinformation.dk/eli/lta/2019/809/xml] |
| BEK 809/2019 §1 stk. 2 | "Kapitel 1 gælder tilsvarende for fritidssejlads med luftpudefartøjer og andre motordrevne fartøjer af tilsvarende karakter, der er konstrueret til at blive fremført af personer, som sidder, står eller knæler på – snarere end i – skroget." | "El capítulo 1 rige igual para aerodeslizadores y otros fartøjer motorizados de carácter similar, construidos para que los manejen personas sentadas, de pie o arrodilladas sobre el casco, y no dentro." | [VERIFICADO: idem] |
| BEK 663/2020 §1 (bevis) | Misma definición. §1 stk. 5: "I tvivlstilfælde træffer Søfartsstyrelsen afgørelse om, hvorvidt et fartøj er omfattet af denne bekendtgørelse." | "En caso de duda, Søfartsstyrelsen decide si un fartøj queda comprendido." | [VERIFICADO: https://www.retsinformation.dk/eli/lta/2020/663/xml] |
| BEK 1548/2025 §3 nr. 3 (RCD en DK, "personligt fartøj") | Misma definición, "på snarere end i skroget". Ojo: §3 nr. 5 define "Fremdriftsmotor: Enhver forbrændingsmotor med gnist- eller kompressionstænding" | Para la RCD, "motor de propulsión" = **solo combustión** | [VERIFICADO: https://www.retsinformation.dk/eli/lta/2025/1548/xml] |
| Guía oficial de aplicación de la RCD (junio 2018), sobre el Art. 3(3) | "Other types of watercraft with water jet propulsion units that are less than 4,0 m in hull length, such as **mini jet boats** and small RIBs … with water jet propulsion, are not 'personal watercraft'." | "Otras embarcaciones con waterjet y menos de 4,0 m, como los **mini jet boats** y las RIB pequeñas con waterjet, no son 'personal watercraft'." | [VERIFICADO: https://www.europeanboatingindustry.eu/images/News/RCD-Application-Guide-June-2018.pdf (p. 12)] |
| Interpretación danesa de "lignende" | "Lignende fartøjer omfatter eksempelvis elektriske surf- og SUP-boards, jetboards mv." | "Los fartøjer similares incluyen, por ejemplo, surf y SUP eléctricos, jetboards, etc." → **ser eléctrico no lo saca** de la categoría | [VERIFICADO: https://www.soefartsstyrelsen.dk/fritidssejlads/fritidsfartoejer/vandscooter-og-jetski] |

**Lectura.** El bote cumple dos de los tres criterios: < 4 m y waterjet como propulsión principal. El tercero, operarlo "på snarere end i", es el que decide. BEK 809 no define "fremdriftsmotor" y su §1 stk. 2 cubre "andre motordrevne fartøjer". Por eso no conviene apoyarse en que la RCD reserva "propulsion engine" a los motores de combustión: en el régimen danés de zonas, el motor eléctrico no salva al bote [ESTIMADO: lectura conjunta de las normas citadas].

### 1.3 Qué implica si se lo clasifica como vandscooter

| Regla | Texto / dato | Efecto en Als | Fuente |
|---|---|---|---|
| Zonas prohibidas | §2: prohibido en zonas Natura 2000, vildtreservater y "fredede arealer på søterritoriet" | Los puntos que consulté en **Sønderborg Bugt, Flensborg Fjord (54,83 N 9,75 E) y Nybøl Nor** caen en el hábitat H173 "Flensborg Fjord, Bredgrund og farvandet omkring Als" y en el área de aves F64. Los puntos de **Als Fjord (centro), Als Sund (3 puntos) y Augustenborg Fjord exterior no** caen en esas áreas (consulta por punto, no por polígono completo) | [VERIFICADO: BEK 809 §2] + [VERIFICADO: consulta WFS https://arealeditering-dist-geo.miljoeportal.dk/geoserver/ows, capas `dai:habitat_omr`, `dai:fugle_bes_omr`, `dai:natur_vildt_reservat`, puntos en UTM32 con cálculo propio] |
| Vildtreservat | La parte interior de Augustenborg Fjord (al oeste de la línea 54°56'30,7"N 9°51'21,6"E – 54°56'21,4"N 9°51'27,5"E, hasta Banegårdsgade) y Lillehav son "Augustenborg Vildtreservat" | Una vandscooter no puede entrar. Para cualquier bote rige además la prohibición de "forjage" (espantar) aves | [VERIFICADO: https://www.retsinformation.dk/eli/lta/2025/637/xml] |
| 300 m | §3: "forbudt inden for 300 meter fra kystlinjen"; stk. 2: "maksimalt 5 knob vinkelret på kystlinjen. Der må alene foretages direkte gennemsejling af 300 meter zonen." | Als Sund mide "ca. 500 meter" de ancho (R07): como vandscooter **no se podría navegar a lo largo del sund** | [VERIFICADO: BEK 809 §3] + [ESTIMADO: geometría] |
| Botadura | §3 stk. 3: "Ved isætning i havne skal vandscootere følge sejlløbet". Reglamento policial §3: prohibido salir o llegar a "kommunale badestrande" con "vandscootere, jetski og lignende fartøjer" | Botar solo en puerto o rampa, siguiendo el canal | [VERIFICADO: BEK 809] [VERIFICADO: https://politi.dk/politikredse/syd-og-soenderjyllands-politi/sejladsreglement] |
| Bevis | BEK 663/2020 §2: "der er fyldt 16 år og har vandscooterbevis". Examen a partir de los 15 años | Jorge necesitaría vandscooterbevis | [VERIFICADO: …/2020/663/xml] [VERIFICADO: …/2025/1441/xml (§ "Aflæggelse af prøve kan ske efter prøveaflæggers fyldte 15. år")] |
| Seguro | BEK 1340/2018 §1: seguro obligatorio para "en dansk vandscooter og et lignende dansk fartøj, hvortil der er foreskrevet uddannelseskrav". Cobertura hasta los límites de søloven §175 (~27 MDKK por daños personales, ~13,5 MDKK por daños materiales, según Søfartsstyrelsen) | Obligatorio, con certificado a bordo | [VERIFICADO: https://www.retsinformation.dk/eli/lta/2018/1340/xml] [VERIFICADO: página de vandscooter de Søfartsstyrelsen] |
| Alcohol | Søsikkerhedsloven §29 a stk. 2: "Førere af vandscootere og lignende fartøjer er dog omfattet af stk. 1" (0,50 ‰) | Límite fijo de 0,5 ‰ | [VERIFICADO: https://www.retsinformation.dk/eli/lta/2022/221/xml] |
| Multas | Velocidad o zona (BEK 809 §2 y §3): 5 000 DKK la primera vez, 10 000 DKK la segunda. Mismas cifras para los límites locales de velocidad | — | [VERIFICADO: https://www.retsinformation.dk/eli/retsinfo/2026/9486/xml (§5.3–5.4)] |
| Ordenanzas de playa | BEK 809 cap. 2: el municipio puede prohibir a vandscootere **y a speedbåde** a < 300 m de zonas de baño entre el 1‑6 y el 1‑9 (ampliable al 15‑9) | No encontré ordenanzas de Sønderborg (la página municipal no las menciona) | [VERIFICADO: BEK 809 §§5–9] + [VERIFICADO: https://sonderborgkommune.dk/vandscootersejlads] |
| Kill switch | BEK 809, BEK 663/2020 y BEK 765/2024 **no exigen** kill switch (leídas completas) | — | [VERIFICADO: textos citados] |

### 1.4 Criterios concretos de diseño para NO caer en la definición

| # | Criterio | Por qué | Etiqueta |
|---|---|---|---|
| D1 | **Cockpit cerrado por costados.** El asiento va por debajo de la borda, con brazola o costado de **≥ 250 mm por encima del asiento** a ambos lados y detrás del piloto. Las caderas y las piernas del piloto quedan dentro del contorno del casco | Es la diferencia entre "i" (dentro) y "på" (sobre), que es lo que decide | [SUPUESTO: valor numérico propio; ninguna norma da cifra] |
| D2 | **Pies sobre el piso del cockpit**, dentro del casco. Nada de estribos ni plataformas laterales exteriores como en un jetski | Igual que D1 | [SUPUESTO] |
| D3 | **Volante y acelerador de palanca**, sin manillar. **Asiento con respaldo**, sin montura a horcajadas | La guía de la RCD separa "mini jet boats" de PWC | [VERIFICADO: RCD Guide p. 12] + [SUPUESTO: rasgos concretos] |
| D4 | Aspecto y equipamiento de bote: francobordo, placa de capacidad y número de personas (H6 de R10b: 1 persona) | Ayuda a la decisión "i tvivlstilfælde" | [SUPUESTO] |
| D5 | **Pedir la decisión por escrito antes de construir**, con plano del cockpit y fotos, a **Søfartsstyrelsen** (bevis, BEK 663 §1 stk. 5) y a **Sønderborg Kommune, Natur & Vandmiljø**, que es la autoridad de supervisión de BEK 809 | Son dos autoridades distintas y conviene tener las dos respuestas | [VERIFICADO: BEK 663/2020 §1 stk. 5; Sønderborg Kommune: "Det er kommunen, der er tilsynsmyndighed efter vandscooterbekendtgørelsen"] |
| D6 | No tomar como argumento que "eléctrico ≠ fremdriftsmotor" | Søfartsstyrelsen ya incluye los eléctricos en "lignende" | [VERIFICADO: §1.2] |
| D7 | Eslora < 2,5 m **y** no ser PWC → completamente fuera de la RCD, aunque se venda. Si se lo clasificara como PWC, la RCD sí aplica sin mínimo de eslora: "personal watercraft having the hull length less than 2.5 m is covered". En ese caso solo lo salva la exclusión por construcción propia, que se pierde si se vende antes de 5 años | Opción de reventa | [VERIFICADO: RCD Guide p. 12–13; BEK 1548/2025 §2 stk. 2 nr. 1 g] |

---

## 2. Speedbåd: umbral vigente y cómo se cuenta la potencia

| Ítem | Dato | Fuente |
|---|---|---|
| Norma vigente | **BEK 749/2020** (speedbådsførerbekendtgørelsen), "Valid", en vigor desde el 4‑6‑2020; deroga BEK 664/2020. BEK 554/2020, que citó R07, es histórica | [VERIFICADO: https://www.retsinformation.dk/eli/lta/2020/749/xml] |
| Umbral < 4 m | §1 stk. 2: "planende fritidsfartøjer med en skroglængde under 4 meter og med en fremdrivningseffekt på 19 kW eller derover med undtagelse af fartøjer, der er nævnt i vandscooterførerbekendtgørelsen" | [VERIFICADO: idem] |
| 4–15 m (por si el casco crece) | Anexo 1 (gráfico): "P (kW) = L² (meter) + 3"; a 4 m da 19 kW | [VERIFICADO: https://www.retsinformation.dk/eli/lta/2020/749/pdf (imagen del Bilag 1)] |
| ¿Es "planende" el casco? | §1 stk. 5: "uden egentlig køl med ren V-formet bund eller med flad bund i den agterste tredjedel, eller … skroget ved en vis hastighed løftes delvist ud af vandet". Un jet de 30 km/h **sí** es planende | [VERIFICADO: idem] |
| ¿Cómo se mide la "fremdrivningseffekt"? | **No hay definición** en BEK 749/2020 (leída completa), ni en BEK 1724/2017, ni en la página de Søfartsstyrelsen, que habla de "motoreffekt på 19 kW / 25 HK". **No existe regla especial para motores eléctricos.** En la RCD danesa, el anexo I §4 pide declarar "den maksimale effekt" en el manual, pero eso rige para motores de combustión | [VERIFICADO: …/2020/749/xml; https://www.soefartsstyrelsen.dk/fritidssejlads/beviser-og-certifikater/speedbaadsbevis; BEK 1548/2025 bilag 1 §4] |
| Interpretación prudente | Contar la **potencia máxima que puede entregar el sistema** (el pico del motor limitado por el controlador), no la continua | [ESTIMADO: lectura conservadora; a confirmar, §8] |
| **Potencia configurada del diseño actual** (actualizado 2026-10-02, auditoría H12) | El motor elegido (Maytech MTI120116) declara **18,8 kW máx.** y el FSESC 75350 admite 350 A continuos (≈ 15 kW a 43,8 V): **sin configuración, el sistema podría pasar de 19 kW** en la ficha. Lo que limita es la configuración del VESC: `l_in_current_max` = 192 A → ≤ 192 A × 43,8 V = **8,4 kW de batería** (≈ 7,5 kW en el eje con η 0,92 × 0,97) y `l_current_max` = 292 A de fase; sizing da **≈ 6,6 kW** pico en el eje. Aun con el VESC mal configurado, los BMS (2 × 120 A) cortan a ≈ 10,5 kW continuos [CALCULADO: 240 A × 43,8 V; pico del BMS no publicado]. Por eso la potencia "de diseño" < 19 kW depende de la configuración: se guarda el XML del VESC (mcconf/appconf) y las hojas de datos a bordo y se documenta la configuración (04_diseno/electronica §6, T0.0/T0.6) | [VERIFICADO: página Maytech (18,8 kW), Flipsky (350 A)] + [CALCULADO: 04_diseno/electronica/electronica.json, resultados/sizing.json P_shaft_peak_kW] |
| Trampa con un motor de 72 V | El motor de referencia de R10b (HPM5000B 72 V) declara "Power 5000W" y "**Rated Power 3KW-7.5KW**". Pero un controlador de 72 V y 250 A a 84 V pide **21 kW** de batería, por encima de 19 kW, si el motor puede absorberlos | [VERIFICADO: https://www.kellycontrollers.eu/hpm5000b-5kw-72v-leghuteses] + [ESTIMADO: 84 V × 250 A] |
| Criterio de diseño | Limitar por firmware la **corriente de batería** a ≤ 150 A con 72 V (≤ 12,6 kW a 84 V), o ≤ 250 A con 48 V (≤ 12,8 kW a 51 V); el diseño actual usa 192 A a 43,8 V (8,4 kW). Llevar a bordo, en funda estanca, las hojas de datos del motor y del controlador **y el respaldo de la configuración del VESC** (XML exportado en T0.0) que muestra el límite configurado < 19 kW; no subir `l_in_current_max` por encima de 19 kW / 43,8 V ≈ 430 A (en la práctica lo limitan antes los BMS) | [SUPUESTO] |
| Si pasara a ser speedbåd | Bevis desde los 16 años (§2); seguro obligatorio (BEK 1340/2018); 0,5 ‰; a < 300 m solo "direkte gennemsejling … vinkelret på kystlinjen" (reglamento policial §4 stk. 3); entra en las ordenanzas municipales de playa (BEK 809 §7 nr. 2) | [VERIFICADO: fuentes citadas en §1.3 y https://politi.dk/politikredse/syd-og-soenderjyllands-politi/sejladsreglement] |
| Seguro y edad sin speedbåd ni vandscooter | No hay seguro obligatorio: BEK 1340 §1 lo limita a fartøjer "hvortil der er foreskrevet uddannelseskrav". Edad mínima: no la encontré. Søfartsstyrelsen: "Der er ikke krav om formelle kompetencer … under 15 meter, medmindre det falder ind under reglerne for speedbåde og vandscootere" (R07) | [VERIFICADO: BEK 1340/2018 §1] + R07 |

---

## 3. Velocidad: zonas en Als Sund, Sønderborg Havn, Augustenborg, Flensborg Fjord, puentes y playas

| Zona | Regla | Fuente |
|---|---|---|
| Toda la costa del distrito policial, < 300 m | 5 kn (ya en R07). §1: el reglamento rige para "motorbåde, herunder vandscootere, jetski og lignende fartøjer … indtil 300 meter ud fra kyststrækningerne". **El texto no fija zonas específicas** para Als Sund, Augustenborg ni Flensborg; la única zona nombrada es Sønderstrand (Aabenraa) | [VERIFICADO: https://politi.dk/politikredse/syd-og-soenderjyllands-politi/sejladsreglement] |
| **Sønderborg Havn**: el área portuaria es "Als Sund" entre "en linie fra høfden ved Strandpromenaden S for Slottet" y "den S-vendte begrænsning af Alssundbroen" | "Maskindrevne skibe må kun sejle med langsom fart ind i eller ud af havnen samt inden for havnens grænser (**max. 4 knob**)." | "Las embarcaciones a motor solo pueden navegar a velocidad lenta al entrar, salir y dentro de los límites del puerto (**máx. 4 kn**)." → la mitad sur de Als Sund tiene **4 kn, más restrictivo que los 5 kn** costeros | [VERIFICADO: https://www.danskehavnelods.dk/Havnelodsen/harbours/d9eb9b5c-16e2-46d3-bb4d-4f6d025d5de3.html (texto actualizado 26‑06‑2026)] |
| Puente Kong Christian X | "Skibe må under passage af Kong Christian den X's Bro inden for en afstand af **250 m på hver side** af denne kun gå med den for skibets manøvreevne nødvendige fart." Además: "et maskindrevet skib skal vente på et sejlskib" en el puente | "Al pasar el puente, a 250 m de cada lado, solo la velocidad necesaria para maniobrar"; los botes a motor esperan a los veleros | [VERIFICADO: Havnelods idem] [VERIFICADO: https://www.retsinformation.dk/eli/lta/2023/1316/xml (§18 nr. 1)] |
| Gálibo y horario del puente | Gálibo cerrado ~4,5 m en el tramo basculante y ~6,0 m en el tramo oeste. Apertura cada hora a los :45 (1‑4 al 31‑10: 06:45–21:45). El jet pasa por debajo sin abrir | [VERIFICADO: https://sonderborgkommune.dk/broer] |
| **Corriente en Als Sund** (pendiente en R07 §4.4) | "Strømmen er i reglen svag N-gående, men kan … være meget hård, **indtil 3 knob**, og vanskeliggøre sejladsen gennem broen." En Egernsund: "stærk N-gående strøm (3-4 knob)" | "En general es débil hacia el norte, pero con viento puede llegar a 3 kn." → **el 0,5 m/s de inputs.yaml queda corto**: 3 kn = 1,54 m/s | [VERIFICADO: Havnelods Sønderborg Havn; https://www.danskehavnelods.dk/Havnelodsen/harbours/ff9132aa-1230-4a46-8286-c01931b955ad.html] |
| Nivel del agua | "E-lig vind kan give indtil 1,2 m højvande og W-lig vind indtil 1,2 m lavvande" | Coherente con R07 §4.3 | [VERIFICADO: Havnelods Sønderborg Havn] |
| Sønderborg Lystbådehavn | "I havnen og i indsejlingen **3 knob**." | [VERIFICADO: https://www.danskehavnelods.dk/Havnelodsen/harbours/847c9e50-e5e2-4e98-a4e8-c7ccc2548bf6.html] |
| Augustenborg Havn / Yachthavn | "Fartbegrænsning 4 knob" (Havn) y "3 knob" (Yachthavn) | [VERIFICADO: …/harbours/127db00a-bd23-4d34-bc77-c484ff721baf.html] [VERIFICADO: …/harbours/cfb84dd8-b6d0-420a-94e8-b919274dee38.html] |
| Egernsund Havn (Flensborg Fjord DK) | "Fartbegrænsning 3 knob." | [VERIFICADO: Havnelods Egernsund] |
| Reglamento estándar de puertos comerciales (rige en Sønderborg Havn) | §5 stk. 2: velocidad que no supere "opslåede fartgrænser eller i mangel af sådanne med så lav hastighed, at der ikke voldes ulempe for andre" | "Los límites señalizados o, si no los hay, tan baja que no moleste a otros" | [VERIFICADO: https://danskehavne.dk/wp-content/uploads/2015/10/bekendtgorelsenda.pdf (BEK 1146/2004)] |
| Canales estrechos (nacional) | BEK 1316/2023 §12 stk. 2: "I et snævert løb skal skibe passere hinanden med en efter forholdene afpasset langsom fart"; stk. 4: pasar botes detenidos o amarrados junto a un canal dragado "med ringe fart". La lista de §16 (límites por zona) **no incluye** Als Sund, Als Fjord ni Augustenborg | [VERIFICADO: https://www.retsinformation.dk/eli/lta/2023/1316/xml] |
| Fuera de 300 m y fuera de puertos | No encontré límite numérico. Rigen la "sikker fart" de las reglas de navegación ("sejle med 'Sikker fart' under hensyn til overskuelighed, trafiktæthed samt roere og badende") y el buen arte marinero (søsikkerhedsloven §29 stk. 2) | [VERIFICADO: página de vandscooter de Søfartsstyrelsen] [VERIFICADO: LBK 221/2022 §29] |
| Zonas de baño | Sønderborg tiene "25 badestrande"; temporada de baño "1. juni til den 15. september". Reglamento policial §4: no ser "til fare, hinder eller ulempe for badende". Playas municipales: prohibido salir o llegar con "vandscootere, jetski og lignende fartøjer" (§3) | [VERIFICADO: https://sonderborgkommune.dk/badevand] [VERIFICADO: reglamento policial] |
| ¿Cuenta como "jetski og lignende" para la regla de playa (§3)? | El reglamento policial no define "lignende fartøjer". Un jet de cockpit cerrado podría interpretarse como "lignende" → **no salir ni llegar a playas municipales**; usar rampa | [ESTIMADO] → a confirmar (§8) |
| Dónde son legales los 30 km/h | Als Fjord tiene 2–3 km de ancho, lo que deja una franja central de ~1,4–2,4 km a > 300 m de cada orilla y ~8–10 km de largo. También la parte danesa de Flensborg Fjord y Sønderborg Bugt a > 300 m de la costa DK (Natura 2000 **no** limita la velocidad de un bote normal). **No** en Als Sund (≤ ~250 m de cualquier orilla, 4–5 kn) ni en la mayor parte de Augustenborg Fjord | [ESTIMADO: anchos de R07 §2.1 y §4.2] |

---

## 4. Seguridad eléctrica a 72 V

| Tema | Dato | Fuente |
|---|---|---|
| ¿Ley eléctrica danesa a bordo? | Elsikkerhedsloven (LBK 57/2026) §1 stk. 2: "Ved elektriske installationer forstås … bortset fra **elektriske installationer på skibe**". La instalación a bordo **queda fuera**. El cargador y el enchufe en tierra sí están dentro | "Se entienden por instalaciones eléctricas … salvo las instalaciones eléctricas en buques" | [VERIFICADO: https://www.retsinformation.dk/eli/lta/2026/57/xml] |
| RCD 5.3 (si aplicara) | "minimise risk of fire and electric shock"; circuitos "safe when exposed to overload"; "Batteries shall be firmly secured and protected from ingress of water". **No aplica** (< 2,5 m y construcción propia), pero sirve como lista de control | [VERIFICADO: https://www.legislation.gov.uk/eudr/2013/53/annex/I] [VERIFICADO: BEK 1548/2025 bilag 1 §5.3] |
| Guía de la RCD sobre la LVD | "Low voltage with regard to the LVD refers to 75 to 1500 volts DC". 72 V nominales (80–84 V con la batería llena) quedan en el límite. La LVD obliga a quien **comercializa** equipos, no a quien los instala para uso propio | [VERIFICADO: RCD Guide, comentario a 5.3] + [ESTIMADO: alcance] |
| ISO 16315 §4.1, por encima de 50 V | "For DC electric propulsion systems and other electrical systems with rated nominal voltages in excess of safety voltage, **the precautions against the risk of electric shock shall be observed**." Y: "Electric propulsion circuits shall be designed to protect against … shock by the use of enclosures, conductor and terminal insulation, automatic disconnection and grounding/earthing system protection as appropriate." | "Por encima de la tensión de seguridad hay que tomar precauciones contra el choque eléctrico: envolventes, aislación de conductores y bornes, desconexión automática y protección de puesta a tierra." | [VERIFICADO: https://cdn.standards.iteh.ai/samples/56158/48d458359e3d4eceab7ba7711b5b118e/ISO-16315-2016.pdf] |
| ISO 16315: alternativa de tres hilos | "For DC propulsion systems operating at voltages greater than safety voltage, a three-wire system (e.g. DC +48 V/0/−48V) may be considered with the mid-point conductor earthed to limit prospective touch voltage." | "Se puede usar un sistema de tres hilos (±36 V con el punto medio a tierra) para limitar la tensión de contacto." | [VERIFICADO: idem] |
| ISO 16315: cláusulas de las que solo se ve el título | 5.1.2 "Emergency stop"; 6.1 "Protection against direct contact"; 6.3 "Fault-to-earth monitoring and tripping arrangements for DC fully insulated systems"; 7.3 "Overcurrent devices in the outgoing circuit(s) from a battery"; 8.2 "Isolation of battery packs or battery banks"; 10.3.2 "Insulation resistance — DC electrical propulsion systems". El texto no es accesible. Vigente la 2.ª ed. 2026 (R06) | [VERIFICADO: índice del PDF anterior] |
| ISO 13297 / ISO 10133 | Cubren CC ≤ 50 V y no tratan la propulsión eléctrica: ISO 16315 dice "Neither of these standards includes requirements for electrical propulsion systems" | [VERIFICADO: ISO 16315:2016, Introducción] + R06 |
| ABYC E‑13 (litio) | Alcance: "selection and installation of lithium-ion batteries on boats, lithium-ion battery system design (house bank, cranking, propulsion)". Rige "to systems of 600-watt hours or greater" (ed. 2022), así que **aplica a 3 kWh** | [VERIFICADO: https://tradeonlytoday.com/industry-news/setting-the-standard/] [VERIFICADO: https://panbo.com/abyc-ratifies-e-13-their-first-lithium-battery-standard/] |
| ABYC E‑30 (propulsión eléctrica) | Solo la vi en un resultado de búsqueda; no abrí ninguna página con su contenido | [no verificado] |
| **Conclusión legal** | En DK **no hay obligación legal** de cumplir ISO 16315, ISO 13297 ni ABYC para este bote: son voluntarias. Rige el deber general del patrón de zarpar con el bote "i forsvarlig stand" (søloven §131, R07). La aseguradora puede pedir más | [ESTIMADO: consecuencia de las exclusiones verificadas] |

**Requisitos de diseño si se queda en 72 V** [SUPUESTO, basado en ISO 16315 §4.1 y R06/R10b H8]:
- IP67 en todo lo que esté a más de 50 V, con bornes protegidos contra contacto con los dedos (IP2X).
- Bus **flotante**: ningún polo al casco de aluminio, con monitor de aislamiento con alarma (equivalente a 6.3).
- Seccionador y fusible en la salida de la batería, ambos de clase ≥ 100 V CC.
- Contactor de 96 V con precarga.
- Parada de emergencia (5.1.2) en el cordón y en una seta.
- Medición de aislamiento BAT± ↔ casco antes de cada temporada.

**Alternativa recomendada:** LFP 13S (≤ 47,45 V, por debajo de los 50 V; R10b H8). A 7,2 kW son ~180 A [ESTIMADO: 7 200 W / 40 V]. Elimina el problema de choque eléctrico y el riesgo de llegar a 19 kW con un controlador grande.

---

## 5. Estabilidad, flotación y capacidad de un casco propio de 2,30 m

| Tema | Dato | Fuente |
|---|---|---|
| ¿Aplica la RCD? | No, por dos motivos. (a) "Fritidsfartøj … med en skroglængde på 2,5-24 m" (§3 nr. 2). (b) Exclusión g: "Vandfartøjer bygget til eget brug, såfremt de ikke efterfølgende inden for en periode på fem år … bringes i omsætning". Construcción propia = "hovedsagelig bygget af den fremtidige bruger" (§3 nr. 4) | [VERIFICADO: https://www.retsinformation.dk/eli/lta/2025/1548/xml] |
| Alcance de "construcción propia" | "A member of the general public building his own watercraft (in his garage or garden …) from materials bought on the open market is deemed to be 'building a watercraft for his own use'." Se puede contratar a especialistas, por ejemplo "electrical or electronic engineers". "Kit boat cannot be considered as a watercraft built for own use." Si se vende antes de 5 años, hace falta evaluación posterior a la construcción con organismo notificado | [VERIFICADO: RCD Guide, comentario al Art. 2(2)(a)(vii)] |
| ¿Otra norma obligatoria en DK? | BEK 765/2024 (fritidsfartøjer < 24 m) solo exige equipo (§4) y chalecos (§5). No hay requisitos de estabilidad ni de flotación para < 24 m | [VERIFICADO: https://www.retsinformation.dk/eli/lta/2024/765/xml] |
| Norma de referencia voluntaria | RCD 3.2 / 3.3 → norma armonizada **EN ISO 12217‑3** "Boats of hull length less than 6 m". ISO 12217‑3:2015 "specifies methods for evaluating the stability and buoyancy of intact … boats. The flotation characteristics of craft susceptible to swamping are also encompassed" → categoría C o D. **Excluye** "personal watercraft covered by ISO 13590 and other similar powered craft". La ed. 2015 fue "Replaced by: ISO 12217-3:2022" | [VERIFICADO: RCD Guide, lista de normas en 3.2/3.3] [VERIFICADO: https://www.sis.se/en/produkter/shipbuilding-and-marine-structures/small-craft/iso1221732015/] [VERIFICADO: https://www.en-standard.eu/iso-12217-3-2015-small-craft-stability-and-buoyancy-assessment-and-categorization-part-3-boats-of-hull-length-less-than-6-m/] |
| Requisito esencial de flotación (RCD 3.3, lista de control) | "Watercraft of less than 6 metres in length that are susceptible to swamping … shall be provided with appropriate means of flotation in the swamped condition." | [VERIFICADO: legislation.gov.uk annex I] |
| Reabordaje (RCD 2.3, lista de control) | "Means of reboarding shall be accessible to or deployable by a person in the water unaided." | [VERIFICADO: idem] |
| Ensayo ISO 12217‑3 de carga desplazada | Existe un procedimiento simplificado en 6.5.2 (VCG de la tripulación a 100 mm sobre el asiento), según un foro técnico. **No pude abrir el texto de la norma** (iso.org da 403; iteh pide JavaScript) | [ESTIMADO: https://www.boatdesign.net/threads/iso-12217-3-simplified-offset-load-test.69080/ (foro, no es la norma)] |
| Criterio numérico verificable: flotación de inboards < 20 ft (EE. UU.) | 33 CFR 183.105: debe mantener "any portion of the boat above the surface" tras **18 h** inundado y cargado con un peso sumergido igual a **2/15 de la capacidad de personas** + **25 % del peso muerto** | [VERIFICADO: https://www.law.cornell.edu/cfr/text/33/183.105] (aplicabilidad: "monohull inboard boats … less than 20 feet" [VERIFICADO: …/183.101]) |
| Criterio más exigente: flotación nivelada | 33 CFR 183.220: inundado 18 h, con peso sumergido = 50 % de las primeras 550 lb de capacidad de personas + 12,5 % del resto. 183.225: escora **≤ 10°**. 183.230: con la mitad del peso de personas en una banda, escora **≤ 30°** | [VERIFICADO: …/183.220, …/183.225, …/183.230] |

**Ensayo mínimo recomendado antes de navegar** [SUPUESTO, con los criterios citados]:

| Ensayo | Cómo | Criterio | Base |
|---|---|---|---|
| E1. Escora con carga desplazada (intacto, en muelle) | Piloto de 100 kg o lastre equivalente; desplazarlo 0,1 m, 0,2 m y hasta la borda, con el CG del lastre a ≥ 100 mm sobre el asiento. Medir escora y francobordo mínimo hasta la primera entrada de agua | Sin entrada de agua; francobordo residual ≥ 100 mm; escora ≤ 15° con el piloto a 0,2 m de crujía | [SUPUESTO: umbrales propios]. Método: concepto de carga desplazada de ISO 12217‑3 [ESTIMADO] y 33 CFR 183.230 [VERIFICADO] |
| E2. Inundado (swamped) | Llenar de agua con **lastre inerte en lugar de las baterías y el motor** (mismo peso sumergido) más 2/15 del peso del piloto. Esperar 18 h | Flota. Ideal: nivelado (escora ≤ 10°, criterio de 183.225) | [VERIFICADO: 33 CFR 183.105 / 183.225] |
| E3. Inundado con carga desplazada | Como E2, con medio peso de persona en una banda | Escora ≤ 30° (183.230) | [VERIFICADO: 33 CFR 183.230] |
| E4. Reabordaje | Persona con chaleco, desde el agua y sin ayuda, con agua < 15 °C simulada (sin escalera auxiliar) | Sube sin volcar el bote | [VERIFICADO: RCD 2.3] + R07 §3 |

R10b H1 calcula un GM de −40 a +90 mm, así que con la geometría actual **E1 probablemente falla** [ESTIMADO: R10b]. Hacer E1 antes de instalar la electrónica.

---

## 6. Kill switch / hombre al agua

| Norma | Texto | ¿Aplica? | Fuente |
|---|---|---|---|
| RCD 5.1.5 (PWC) | "Personal watercraft shall be designed either with an automatic propulsion engine cut-off or with an automatic device to provide reduced speed, circular, forward movement when the driver dismounts deliberately or falls overboard." | Solo a PWC **comercializados**. El bote no es PWC (§1) y además es de construcción propia | [VERIFICADO: legislation.gov.uk annex I; BEK 1548/2025 bilag 1 §5.1.5] |
| RCD 5.1.6 | "Tiller-controlled outboard propulsion engines shall be equipped with an emergency stopping device which can be linked to the helmsman." | No: no es un fueraborda con caña | [VERIFICADO: idem] |
| "RCD 5.1.8" | **No existe** en el anexo I.A: 5.1 termina en 5.1.6 y sigue 5.2 "Fuel system" | — | [VERIFICADO: legislation.gov.uk annex I] |
| RCD 5.4.2 | "single-propulsion engine non-sailing recreational craft with remote-controlled rudder steering systems shall be provided with emergency means of steering". Lista de control: un jet **sin empuje no gobierna** (R10b H10) | Voluntario | [VERIFICADO: idem] |
| BEK 809/2019, BEK 663/2020, BEK 765/2024 | No mencionan cordón, nødstop ni parada de emergencia | — | [VERIFICADO: textos completos leídos] |
| ISO 16315 5.1.2 | Existe la cláusula "Emergency stop"; su texto no es accesible | Voluntario | [VERIFICADO: índice] |
| **Conclusión** | **No es obligatorio en DK ni en la UE para este bote.** Recomendación [SUPUESTO]: cordón al chaleco que **corta** la propulsión (no el modo de giro en círculo: con el piloto dentro del casco y bañistas cerca, conviene detener el chorro), más seta. Arquitectura de R06 §3.5 con contactor de la clase de tensión correcta (R10b H9) | — | — |

---

## 7. Ruido y ola

| Tema | Regla | Fuente |
|---|---|---|
| Ruido (local) | Reglamento policial §4: "sejlads ikke må medføre unødig støj til ulempe for andre" | [VERIFICADO: politi.dk sejladsreglement] |
| Ruido (UE) | RCD anexo I.C: el ruido aplica a intraborda, PWC y fueraborda de combustión; los fartøjer de construcción propia quedan excluidos de I.C (§2 stk. 2 nr. 3 b). La BEK danesa de ruido de fritidsfartøjer (BEK 1535/2004) figura como histórica | [VERIFICADO: BEK 1548/2025] [VERIFICADO: búsqueda en Retsinformation, BEK 1535/2004 "isHistoryFlag": true] |
| Ola (local) | §4: no ser "til fare, hinder eller ulempe for badende eller for anden sejlads" | [VERIFICADO: politi.dk] |
| Ola (nacional) | BEK 1316/2023 §12 stk. 4: botes detenidos o amarrados junto a un canal dragado "skal af maskindrevne skibe passeres med særlig agtpågivenhed og med ringe fart" | [VERIFICADO: …/2023/1316/xml] |
| Ola peligrosa (penal) | Rigsadvokat: hay "groft hensynsløs sejlads" cuando se navega "for tæt på bemandede både med for høj hastighed, således at den unødige søgang medfører, at andre personer mister herredømmet over deres fartøj" | "… demasiado cerca de botes tripulados a demasiada velocidad, de modo que el oleaje innecesario hace que otros pierdan el control" | [VERIFICADO: https://www.retsinformation.dk/eli/retsinfo/2026/9486/xml] |
| Aves (N197 / vildtreservat) | La Natura 2000 de N197 tiene una actuación para proteger al eider "mod forstyrrelser" (de perturbaciones). En el vildtreservat de Augustenborg está prohibido "forjage" aves. Evitar planear cerca de bandadas | [VERIFICADO: https://sgavmst.dk/media/ypskhfo2/n197-smv-for-natura-2000-plan-2022-27-flensborg-fjord-bredgrund-og-farvandet-omkring-als.pdf] [VERIFICADO: BEK 637/2025 §3] |

---

## 8. A confirmar con la autoridad (preguntas redactadas en danés)

| # | A quién | Pregunta (danés) | Por qué |
|---|---|---|---|
| Q1 | **Søfartsstyrelsen**, fritid@dma.dk, +45 72 19 60 19 [VERIFICADO: página del speedbådsbevis] | "Vi bygger selv et fritidsfartøj med skroglængde 2,30 m og vandjet (elektrisk motor, katalog 18,8 kW maks., begrænset i controlleren til ca. 8,4 kW batterieffekt) som hovedfremdrivning. Føreren sidder **i** en lukket cockpit under rælingen, med ryglæn, rat og gashåndtag, og fødderne på cockpitdørken. Vil I bekræfte skriftligt, jf. vandscooterførerbekendtgørelsen (BEK nr. 663 af 20/05/2020) § 1, stk. 5, at fartøjet **ikke** er omfattet som vandscooter eller lignende fartøj? Vi vedlægger tegninger og fotos." | §1.4 D5 |
| Q2 | Søfartsstyrelsen | "Hvordan fastlægges 'fremdrivningseffekt' i speedbådsførerbekendtgørelsen (BEK nr. 749 af 29/05/2020) § 1, stk. 2, for en elektrisk motor: motorens nominelle (kontinuerlige) effekt, motorens maksimale/peak-effekt, eller den maksimale effekt, som motorstyringen er begrænset til? Er det tilstrækkeligt at dokumentere en softwarebegrænsning under 19 kW?" | §2 |
| Q3 | Søfartsstyrelsen | "Gælder der krav til en 72 V DC elektrisk fremdriftsinstallation i et selvbygget fritidsfartøj under 2,5 m, eller er ISO 16315 alene vejledende?" | §4 |
| Q4 | **Sønderborg Kommune, Natur & Vandmiljø** (autoridad de supervisión de BEK 809), naturogvandmiljo@sonderborg.dk, +45 88 72 40 85 [VERIFICADO: https://sonderborgkommune.dk/vandscootersejlads] | "Er et selvbygget jetfartøj på 2,30 m, hvor føreren sidder i en cockpit inde i skroget, omfattet af vandscooterbekendtgørelsen (BEK nr. 809 af 09/08/2019) § 1, stk. 1 eller stk. 2? Og har Sønderborg Kommune vedtaget lokale forskrifter efter bekendtgørelsens kapitel 2 om sejladsforbud ved badeområder i Als Fjord, Als Sund eller Augustenborg Fjord?" | §1.3–1.4 |
| Q5 | **Syd- og Sønderjyllands Politi** (vía politi.dk; la página invita a preguntar sobre sejlads) [VERIFICADO: politi.dk sejladsreglement] | "Er det tilladt at sejle 16 knob (30 km/t) med en motorbåd i Als Fjord mere end 300 m fra kystlinjen? Måles de 300 m fra enhver kyst, herunder holme, moler og broer? Og er en lille jetbåd, hvor føreren sidder i en cockpit, omfattet af 'vandscootere, jetski og lignende fartøjer' i sejladsreglementets § 3 om kommunale badestrande?" | §3 |
| Q6 | **Sønderborg Havn**, havnekontoret, havnen@sonderborg.dk, 74 42 27 65 [VERIFICADO: Havnelods] | "Gælder fartbegrænsningen på max. 4 knob i hele Als Sund fra Strandpromenaden til Alssundbroen, og er der lokale regler for jetfartøjer ved brug af slæbestedet på fiskerikajen?" | §3 |
| Q7 | Aseguradora (seguro de hogar / indbo) | "Dækker min indboforsikring ansvar for en selvbygget elektrisk jetbåd på 2,30 m (ca. 8,4 kW begrænset i controlleren), eller skal den tegnes som særskilt bådforsikring?" | Seguro no obligatorio, pero recomendable |

Otros pendientes:
- Límite exacto de N197 en Als Fjord. Consulté solo puntos, no polígonos; revisar en Arealinformation (Danmarks Miljøportal) con las capas Natura 2000 / vildtreservat / fredning.
- Texto de ISO 12217‑3:2022 (offset load, swamped) e ISO 16315:2026 5.1.2 y 6.3: normas de pago.
- ABYC E‑30.
- Edad mínima para botes sin certificado (sigue sin fuente, como en R07).

---

## 9. Conclusiones de diseño

1. **Cockpit "dentro" del casco** (D1–D4): asiento bajo la borda con brazola de ≥ 250 mm, volante, palanca y respaldo, sin montura ni manillar. Pedir la decisión escrita a Søfartsstyrelsen y a Sønderborg Kommune **antes** de construir. Si lo clasifican como vandscooter, el proyecto pierde Als Sund y la costa sur de Als.
2. **Potencia < 19 kW con margen y documentada**: limitar la corriente de batería (≤ 150 A a 72 V o ≤ 250 A a 48 V) y llevar a bordo las hojas de datos.
3. **48 V (13S) en lugar de 72 V**: no hay obligación legal en ninguno de los dos casos, pero por debajo de 50 V desaparece el requisito de ISO 16315 sobre choque eléctrico. Si se mantienen 72 V: IP67, bus flotante con monitor de aislamiento, componentes de clase 100 V y parada de emergencia.
4. **Velocidad**: modo puerto ≤ 3 kn (marinas), modo sund ≤ 4 kn (Sønderborg Havn) o ≤ 5 kn (costa), y planeo solo en la franja central de Als Fjord, a más de 300 m de la costa. Prever **3 kn de corriente** en Als Sund (inputs.yaml usa 0,5 m/s, que queda corto).
5. **Flotación y estabilidad**: no son obligatorias, pero hay que superar E1–E4 (33 CFR 183.105 / .225 / .230 + RCD 2.3) antes de la primera salida. Con la manga actual, E1 probablemente falla (R10b).
6. **Kill switch que corta la propulsión**, aunque no sea obligatorio.

---

## 10. Fuentes abiertas en esta sesión

- Retsinformation (XML/PDF): BEK 809/2019 https://www.retsinformation.dk/eli/lta/2019/809/xml · BEK 663/2020 …/2020/663/xml · BEK 749/2020 …/2020/749/xml y …/2020/749/pdf · BEK 1725/2017 …/2017/1725/xml · BEK 1340/2018 …/2018/1340/xml · BEK 1441/2025 …/2025/1441/xml · BEK 1548/2025 …/2025/1548/xml · BEK 765/2024 …/2024/765/xml · BEK 766/2024 …/2024/766/xml · LBK 221/2022 …/2022/221/xml · BEK 1316/2023 …/2023/1316/xml · BEK 637/2025 …/2025/637/xml · LBK 57/2026 …/2026/57/xml · CIR1H 9486/2026 https://www.retsinformation.dk/eli/retsinfo/2026/9486/xml · API de búsqueda https://www.retsinformation.dk/api/documentsearch?t=vandscooter
- Søfartsstyrelsen: https://www.soefartsstyrelsen.dk/fritidssejlads/fritidsfartoejer/vandscooter-og-jetski ; https://www.soefartsstyrelsen.dk/fritidssejlads/beviser-og-certifikater/speedbaadsbevis
- Policía: https://politi.dk/politikredse/syd-og-soenderjyllands-politi/sejladsreglement
- Sønderborg Kommune: https://sonderborgkommune.dk/vandscootersejlads ; https://sonderborgkommune.dk/broer ; https://sonderborgkommune.dk/badevand
- SGAV: https://sgavmst.dk/natur-og-jagt/regler-for-faerdsel-i-naturen/hvor-maa-jeg-faerdes/paa-havet ; N197 SMV PDF (URL en §7)
- Danmarks Miljøportal WFS: https://arealeditering-dist-geo.miljoeportal.dk/geoserver/ows (capas dai:habitat_omr, dai:fugle_bes_omr, dai:natur_vildt_reservat, dai:fredede_omr)
- Trap Danmark: https://trap.lex.dk/Natur-_og_landskabsforvaltning_i_S%C3%B8nderborg_Kommune ("Lillehav og den inderste del af Augustenborg Fjord er desuden udpeget som natur- og vildtreservat")
- Den Danske Havnelods (Søfartsstyrelsen/Geodatastyrelsen): fichas de Sønderborg Havn, Sønderborg Lystbådehavn, Augustenborg Havn, Augustenborg Yachthavn y Egernsund (URLs en §3)
- Reglamento estándar de puertos comerciales: https://danskehavne.dk/wp-content/uploads/2015/10/bekendtgorelsenda.pdf
- RCD: https://www.legislation.gov.uk/eudr/2013/53/annex/I ; guía oficial: https://www.europeanboatingindustry.eu/images/News/RCD-Application-Guide-June-2018.pdf
- ISO 16315:2016 (muestra): https://cdn.standards.iteh.ai/samples/56158/48d458359e3d4eceab7ba7711b5b118e/ISO-16315-2016.pdf
- ISO 12217‑3: https://www.sis.se/en/produkter/shipbuilding-and-marine-structures/small-craft/iso1221732015/ ; https://www.en-standard.eu/iso-12217-3-2015-small-craft-stability-and-buoyancy-assessment-and-categorization-part-3-boats-of-hull-length-less-than-6-m/ ; foro: https://www.boatdesign.net/threads/iso-12217-3-simplified-offset-load-test.69080/
- 33 CFR 183.101 / .105 / .220 / .225 / .230: https://www.law.cornell.edu/cfr/text/33/183.105 (y siguientes)
- ABYC E‑13: https://panbo.com/abyc-ratifies-e-13-their-first-lithium-battery-standard/ ; https://tradeonlytoday.com/industry-news/setting-the-standard/
- Motor de referencia: https://www.kellycontrollers.eu/hpm5000b-5kw-72v-leghuteses

No accesibles: iso.org (403), standards.iteh.ai (página de catálogo con JavaScript), docplayer.dk (502), webstore.ansi.org (403), pdfcoffee (403), globalspec (403).
