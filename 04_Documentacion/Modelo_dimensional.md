> Copia documental de la implementación validada. Las referencias a rutas y estados históricos pertenecen al proyecto original; para ejecutar esta entrega utiliza los README de sus carpetas. Las evidencias seleccionadas están en ../05_Evidencias.

# Validacion 2025 y alcance definitivo 2022–2025

## Dictamen

2025 es utilizable para el proyecto academico como instantanea de la fuente disponible, excluyendo granos ambiguos. Su PIA se contrasto externamente; no se certifica de manera independiente su fecha de corte ni las seis medidas restantes. No debe presentarse como cierre oficial sin esos metadatos.

El grupo 2026 se excluye por completo de los hechos y de las restricciones del modelo. Sus columnas se leyeron solo para investigar la coincidencia; 2025 se extrae expresamente de las columnas con sufijo _2025.

No se modifico el CSV, la base dw_mef_2022_2024 ni el paquete implementacion. Tras autorizacion especifica nueva se creo y cargo dw_mef_2022_2025. El estado anterior a esa autorizacion se conserva en validacion_2025_pre_autorizacion.md.

## Coincidencia 2025/2026

La comparacion de las siete columnas en las 8 468 325 filas de raw confirma cero diferencias textuales. Esto demuestra repeticion del bloque, pero no su causa ni cual proceso lo genero. No hay codigo de extraccion o metadatos de corte que permitan atribuir el problema al MEF o determinar una fecha de copia.

Se encontro evidencia independiente a favor de 2025: PIA total, nueve genericas y tres niveles de gobierno coinciden exactamente con la Ley 32185. El total PIA de 2026 publicado para ese ejercicio es diferente; el bloque duplicado no representa evidencia independiente de 2026. No se corrigen etiquetas ni se sustituyen valores.

### Contraste externo de PIA 2025

Total CSV: **S/ 251 801 045 185.00**; total legal: **S/ 251 801 045 185.00**; diferencia: **0.00**.

| Generica | PIA CSV | PIA legal | Diferencia |
| --- | --- | --- | --- |
| 0 | 6876048927.00 | 6876048927 | 0.00 |
| 1 | 83655277143.00 | 83655277143 | 0.00 |
| 2 | 15544576011.00 | 15544576011 | 0.00 |
| 3 | 38785509480.00 | 38785509480 | 0.00 |
| 4 | 10849553720.00 | 10849553720 | 0.00 |
| 5 | 10357418086.00 | 10357418086 | 0.00 |
| 6 | 57708614343.00 | 57708614343 | 0.00 |
| 7 | 461275315.00 | 461275315 | 0.00 |
| 8 | 27562772160.00 | 27562772160 | 0.00 |

| Nivel | PIA CSV | PIA legal |
| --- | --- | --- |
| E | 162019333580.00 | 162019333580 |
| M | 35323230357.00 | 35323230357 |
| R | 54458481248.00 | 54458481248 |

Fuentes oficiales:
- [MEF, Anexo 1 Ley 32185](https://www.mef.gob.pe/contenidos/presu_publ/anexos/ppto2025/Anexo_1.PDF): total y nueve genericas.
- [Congreso, Ley 32185, articulo 1](https://leyes.congreso.gob.pe/Documentos/2021_2026/ADLP/Texto_Consolidado/32185-TXM.pdf): niveles y total.
- [Ley 32513, presupuesto 2026](https://www.mef.gob.pe/contenidos/presu_publ/anexos/ppto2026/Ley_N_32513-LeydePpto2026.pdf): S/ 257 561 619 143.00.
- [Congreso, financiamiento 2026](https://comunicaciones.congreso.gob.pe/noticias/aprueban-dictamen-de-ley-de-equilibrio-financiero-del-sector-publico-para-el-2026/): referencia HTML que respalda el monto 2026.

La coincidencia legal es una comprobacion agregada fuerte del presupuesto inicial. No demuestra por si sola que cada registro o toda la ejecucion sea correcta. Los importes de PIM y etapas de ejecucion se concilian contra la fuente, no contra un cierre externo.

## Comprobaciones 2025

- 2 637 463 grupos anuales activos.
- KEY_VALUE unico en los activos de 2025: cero repeticiones.
- 4 943 granos de los 27 codigos tienen dos filas activas e importes diferentes: 9 886 filas conservadas en evidencia y fuera de la seleccion.
- Sin vacios, formatos no numericos ni desbordamientos en las siete medidas.
- Escala maxima de dos decimales; 60 celdas negativas, con signo preservado.
- 1 293 contextos de meta anual tienen mas de una descripcion. Se conserva META_NOMBRE en la identidad observada de meta, como en el paquete anterior.
- Las pruebas globales previas de dimensiones y duplicados exactos cubrieron las 8 468 325 filas de fuente, incluidas las que aportan 2025; se reutilizan sin reinterpretar como alias las metas distintas.
- La transformacion de 2025 conserva las siete sumas exactas, incluidos los negativos. Los grupos de siete ceros no alteran sumas al excluirlos.

| Medida | Total fuente y anual 2025 | Diferencia |
| --- | --- | --- |
| pia | 251801045185.00 | 0.00 |
| pim | 272450859407.00 | 0.00 |
| certificado | 263083632991.19 | 0.00 |
| comprometido_anual | 258771064633.88 | 0.00 |
| comprometido | 256986995951.27 | 0.00 |
| devengado | 253678539140.74 | 0.00 |
| girado | 253349905780.84 | 0.00 |

## Seleccion nueva

Se mantienen las exclusiones conservadoras de 2022–2024 y se agregan las de 2025, sin borrar registros de auditoria. Poblacion elegible total: 10 328 637 hechos. En los cuatro ejercicios se separan 11 658 granos ambiguos y sus 23 316 filas; el grano corregido con nombre de meta no se utiliza para reintegrarlos automaticamente.

Se seleccionan exactamente 37 500 por ejercicio. Dentro de cada anio, un hecho por estrato nivel/entidad y reparto del resto proporcional a N_h-1 mediante mayores restos. Las prioridades usan SHA-256 de la semilla MEF_KIMBALL_2022_2025_V1 y la clave anual canonica (JSON de [anio como texto, grain_json de los 27 codigos]). Desempate por clave completa, independiente del orden del archivo. Repeticion con orden inverso: cero diferencias. La prueba se particiono por anio y nivel para mantener 1GB despues de conservar un intento global fuera de memoria.

| Anio | Hechos unicos | Niveles | Entidades |
| --- | --- | --- | --- |
| 2022 | 37500 | 3 | 2851 |
| 2023 | 37500 | 3 | 2853 |
| 2024 | 37500 | 3 | 2855 |
| 2025 | 37500 | 3 | 2873 |

| Anio | Nivel | Hechos | Entidades |
| --- | --- | --- | --- |
| 2022 | E | 6213 | 369 |
| 2022 | M | 24189 | 1922 |
| 2022 | R | 7098 | 560 |
| 2023 | E | 5601 | 372 |
| 2023 | M | 24910 | 1918 |
| 2023 | R | 6989 | 563 |
| 2024 | E | 5729 | 374 |
| 2024 | M | 24671 | 1917 |
| 2024 | R | 7100 | 564 |
| 2025 | E | 6022 | 391 |
| 2025 | M | 24335 | 1918 |
| 2025 | R | 7143 | 564 |

Las 28 sumas de anio/medida de la seleccion coinciden con las columnas originales de raw segun el ejercicio. Reparto anual equilibrado no significa muestra proporcional al universo. Pesos dentro de cada estrato N_h/q_h; los totales sin ponderar describen la muestra, no totales nacionales. Las exclusiones delimitan la poblacion y deben declararse.

## Modelo y ETL

Se conservan siete dimensiones: anio, entidad, intervencion, funcion, meta, financiamiento y clasificador del gasto. Meta incluye anio/contexto/META/departamento/META_NOMBRE. Las PK son sustitutas, salvo anio. El hecho tiene siete FK y unicidad por observacion anual y por combinacion dimensional. Claves y codigos no pierden ceros iniciales.

Gobiernos locales incluidos con sector/pliego no informados; no se inventan codigos. Negativos se preservan sin ABS ni cero de reemplazo. Nulos monetarios no se inventan. Nombres alternativos conservados y presentacion determinista sin vigencias historicas ficticias.

El paquete nuevo esta en C:/DataWarehouse_MEF/implementacion_2022_2025. SQL tiene CHECK de 2022 a 2025 y cuatro anios exactos; ninguna dimension de anio ni hecho de 2026. La seleccion tiene 150000 observaciones unicas y representa 2 898 entidades del periodo.

Verificacion local del paquete: 150000 filas; 150000 claves origen/grano; cero FK sin destino en los CSV; contexto de meta coherente; 28 totales exactos. La comprobacion real en PostgreSQL tambien paso tras la autorizacion: siete FK, cero huerfanos, 150000 hechos y 28 sumas exactas.

El nuevo cliente tiene destino fijo dw_mef_2022_2025, rechaza bases ya existentes al crear y rechaza tablas ya presentes al cargar. Carga por COPY en una sola transaccion, con validaciones antes de COMMIT. No usa DROP/TRUNCATE/DELETE. La base anterior se comprobo con 150000 hechos y su paquete conserva iguales los hashes de archivos de control.

## Analisis y limites

Se preparan nueve consultas, incluidas comparaciones por anio, nivel, funcion y variacion interanual con LAG. Comparan cuatro muestras equilibradas: no implican variacion real del gasto nacional ni ejecucion integral de una entidad. Los porcentajes de muestra pueden superar 100. No se suman etapas entre si.

## Evidencias y procedencia

Resultados en analisis/validacion_2022_2025_v1/resultados.json; consultas SQL, perfil decimal, variantes de meta, granos ambiguos, cuotas, seleccion Parquet y registro del intento interrumpido. Verificacion del paquete y manifiesto en implementacion_2022_2025/evidencias y manifest.json.

Se reutilizo raw de la auditoria anterior con su huella de fuente registrada. Se comprobo tamano, fecha de modificacion y cinco filas del CSV actual; no se recalculo su hash completo ni se volvio a importar el archivo. La huella conocida y sus limites de comprobacion quedan registrados. Los importes originales permanecen intactos.

## Estado

Completado tras autorizacion expresa: base dw_mef_2022_2025 creada y cargada; 150000 hechos verificados, 37500 por ejercicio, sin 2026. Nueve consultas ejecutadas. La base anterior conserva sus conteos y 21 totales. Ver implementacion_2022_2025/INFORME_IMPLEMENTACION.md y evidencias/implementacion_completada.json.
