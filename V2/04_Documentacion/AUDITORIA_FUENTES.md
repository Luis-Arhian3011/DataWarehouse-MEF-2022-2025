# Auditoría poblacional de devengado mensual MEF 2022–2025

**Estado: completada para los cuatro CSV mensuales. Modelo V2 no implementado.** Fecha: 25 de octubre de 2026.

## 1. Dictamen

La ampliación mediante **150.000 hechos anuales conservados + aproximadamente 150.000 mensuales es viable**, usando una población de selección explícita y controles de correspondencia.

Se auditaron **10.957.342 filas físicas**, con cero importes inválidos según el contrato numérico comprobado y **cero diferencias entre los doce meses y el devengado anual**. La expansión virtual de control produjo 131.488.104 observaciones mensuales, sin materializar una tabla de ese tamaño.

No toda la fuente es directamente cargable con una PK de negocio: hay **714 claves repetidas** que afectan 1.428 filas, incluidas 14 repeticiones exactas adicionales y 700 grupos con importes distintos. Se preservaron todos los registros. Esos grupos se apartaron únicamente de la población candidata de enlace; no se borraron ni sumaron arbitrariamente.

Hay **149.207 series** enlazadas uno a uno al snapshot anual, únicas bajo la política aplicada y conciliadas en las seis medidas comunes. Permiten seleccionar 12.500 series completas para obtener 150.000 hechos mensuales. **No se seleccionó ninguna muestra definitiva.**

La diferencia de 59.000 de 2024 quedó resuelta por una lectura adicional del comparativo, autorizada expresamente: se estaba comparando una fila con bloque 2024 cero mientras otra contraparte tenía actividad de 59.000 en 2024. Las seis medidas comunes concilian al identificar esa observación correctamente.

Persisten **136 series enlazadas con diferencias en devengado o girado**; no se atribuyen a redondeo, corte o error sin evidencia. Quedaron catalogadas y fuera de la cohorte conciliada. El diagnóstico completo no equivale a certificar todas las filas como válidas para una carga indiscriminada.

## 2. Alcance, fuentes y método

Carpeta de esta reanudación: [ORIGEN_LOCAL]\analisis_ampliacion\reanudacion_mensual_20261025T070033Z.

Se conservaron íntegros el análisis anterior y la auditoría detenida. Se reutilizó su entorno de análisis DuckDB 2.0.0 y se escribieron scripts/evidencias nuevos; no se modificó ENTREGA_FINAL.

Fuentes completas autorizadas:
- nuevas fuentes/devengado_mensual/2022-Gasto-Devengado.csv
- nuevas fuentes/devengado_mensual/2023-Gasto-Devengado.csv
- nuevas fuentes/devengado_mensual/2024-Gasto-Devengado.csv
- nuevas fuentes/devengado_mensual/2025-Gasto-Devengado-Mensual.csv

Suman **10.873.195.954 bytes**. Tienen 73 columnas iguales y los doce meses explícitos. Se aplicó lectura por bloques, CSV estricto UTF-8, sin omitir errores ni convertir vacíos en cero. Se conservaron los valores crudos en Parquet temporal y se usó Decimal/DECIMAL, sin float monetario.

La reanudación no cargó registros a ninguna base. DuckDB se utilizó en memoria sobre archivos, con salidas Parquet, CSV/JSON de diagnóstico y sin CREATE TABLE/INSERT. No hubo conexiones ni comandos contra PostgreSQL o Docker.

### Verificación del Parquet reutilizado de 2022

Se volvió a recorrer el CSV 2022 con csv.reader estricto, contándolo y calculando SHA-256 del archivo. Se verificó el número de columnas de todas las filas y una firma multiconjunto del contenido: dos sumas exactas de segmentos independientes de SHA-256 por fila JSON canónica. Se compararon con una lectura completa del Parquet, sin depender de su orden.

El conteo de ambos fue **2.620.993** y las firmas coincidieron. Se guardaron también los hashes SHA-256 del CSV y del Parquet. Esta prueba ofrece evidencia criptográfica fuerte de completitud y contenido; como cualquier firma, no es una demostración matemática sin posibilidad de colisión. No se reutilizó el Parquet basándose solo en que pudiera abrirse.

### Referencia anual compacta y checkpoints

Se verificaron los hashes de los ocho CSV preparados del snapshot y se construyó una referencia temporal de **150.000 filas y 150.000 claves únicas**, 37.500 por año. Contiene clave canónica completa con año, códigos dimensionales y META_NOMBRE, identificadores y seis medidas; ocupa **7.665.040 bytes**.

Las uniones mensuales usan esa referencia única, sin repetir la cadena de siete lectores CSV sobre millones de filas. Se comprobó que cada cruce conserva el número de filas de entrada y que las subseries exportadas coinciden con las agrupadas. No hubo uniones cartesianas.

Cada consulta guarda de inmediato su resultado pequeño o recibo de COPY, además de SQL, eventos y métricas. No se repitió el fallo anterior de guardar toda la evidencia solo al final del año.

Los ejercicios se procesaron secuencialmente. Tras ellos se contrastaron atributos entre años en el mismo motor acotado. La lectura extraordinaria del comparativo original de 8,98 GB se ejecutó después y filtrada solo al caso 2024; no se materializó el comparativo completo.

## 3. Calidad poblacional por año

| Año | Filas físicas | Filas válidas de formato | Importes inválidos | Diferencias meses/anual |
| --- | --- | --- | --- | --- |
| 2022 | 2.620.993 | 2.620.993 | 0 | 0 |
| 2023 | 2.739.423 | 2.739.423 | 0 | 0 |
| 2024 | 2.789.756 | 2.789.756 | 0 | 0 |
| 2025 | 2.807.170 | 2.807.170 | 0 | 0 |

“Filas válidas” significa: año/gobierno/tipo esperado, campos de negocio requeridos presentes, medidas finitas representables en NUMERIC(20,2) con formato decimal de hasta dos posiciones y tratamiento permitido de sector/pliego ausentes en locales. No certifica catálogos oficiales completos ni unicidad.

Las cuatro fuentes pasaron el contrato de formato para todas sus filas. Se detectaron **831 META_NOMBRE ausentes o solo espacios**, sin inventar denominaciones: 241, 225, 190 y 175 por ejercicio. No se incluyó el nombre como campo obligatorio de presencia; sí se conservó para el enlace al modelo heredado.

### Importes y conciliación interna

| Año | PIA del archivo | PIM del archivo | Devengado anual = suma de meses | Celdas mensuales negativas |
| --- | --- | --- | --- | --- |
| 2022 | 197.002.269.014,00 | 238.070.181.438,00 | 209.327.391.946,06 | 77.568 |
| 2023 | 214.790.274.052,00 | 249.946.702.466,00 | 223.054.446.794,58 | 87.850 |
| 2024 | 240.806.216.645,00 | 262.058.019.205,00 | 238.893.055.447,28 | 90.200 |
| 2025 | 251.801.045.185,00 | 272.450.859.407,00 | 253.675.294.538,35 | 91.442 |

Los importes de la tabla son **sumas de los archivos físicos antes de exclusiones**, incluidas sus repeticiones. Sirven como controles de transformación, no como cifras nacionales certificadas ni como totales de la futura muestra.

La suma de los doce meses coincide con MONTO_DEVENGADO_ANUAL en cada una de las 10.957.342 filas y en sus totales. El control independiente mediante unnest mantiene la suma y produce exactamente doce observaciones por fila. No se copian PIA/PIM ni otras referencias anuales a esas doce observaciones.

Se conservaron **347.060 celdas mensuales negativas**. Hay ajustes también en otras medidas. No se aplicó ABS, redondeo correctivo, recorte, filtro de positivos ni sustitución por cero. Los negativos pueden afectar ratios; un PIM agregado no positivo debe dar “No calculable”.

Los sectores/pliegos de gobiernos locales aparecen como espacios y no se consideran inválidos. Todos los gobiernos E/R/M están incluidos; los códigos se mantienen como texto con ceros iniciales y tipos de recurso alfanuméricos.

## 4. Unicidad, duplicados y dependencias

El grano candidato comprobado usa año, los 27 códigos presupuestarios, SEC_FUNC, FINALIDAD y META_NOMBRE. Se verificó su agrupación exacta, no una deduplicación probabilística por hash.

| Año | Claves repetidas | Filas afectadas | Grupos exactos | Grupos con importes distintos |
| --- | --- | --- | --- | --- |
| 2022 | 230 | 460 | 1 | 229 |
| 2023 | 194 | 388 | 1 | 193 |
| 2024 | 148 | 296 | 2 | 146 |
| 2025 | 142 | 284 | 10 | 132 |

Los 714 grupos tienen dos filas. En **700**, los importes numéricos difieren aun sin variantes en los demás atributos descriptivos examinados; **14 grupos** son repeticiones exactas de todas las columnas. La evidencia no permite decidir si los grupos monetariamente distintos deben sumarse, sustituirse o representan detalle no publicado. No se tomó esa decisión. Añadir una clave técnica o un número de fila tampoco resolvería la ambigüedad del grano de negocio.

**Política conservadora utilizada solo para evaluar muestreo:** excluir del enlace todos los miembros de una clave repetida, incluso de los duplicados exactos. No deduplicar escogiendo una fila ni agregar importes. Las fuentes y los casos completos permanecen en Parquet/evidencias. Una posible deduplicación futura requiere justificar el significado del registro.

### Población candidata de actividad y unicidad

| Año | Filas activas válidas | Series inequívocas activas | Filas totalmente cero | Activas apartadas por clave repetida |
| --- | --- | --- | --- | --- |
| 2022 | 2.503.456 | 2.503.001 | 117.537 | 455 |
| 2023 | 2.592.048 | 2.591.662 | 147.375 | 386 |
| 2024 | 2.607.309 | 2.607.018 | 182.447 | 291 |
| 2025 | 2.629.070 | 2.628.808 | 178.100 | 262 |

Se definió actividad como al menos una de las 18 medidas distinta de cero, por lo que se conservan ajustes y series con meses cero. No se usa suma neta distinta de cero: movimientos positivos y negativos pueden compensarse.

Las series totalmente cero quedan fuera de esta población de selección propuesta, pero no del archivo auditado. Las exclusiones de actividad y claves repetidas se documentan; no significan que toda fila excluida sea errónea. No se han aplicado todavía reglas de producción.

### Dependencias funcionales

En cada ejercicio, las claves compuestas de entidad, intervención, función, financiamiento y clasificador determinan una sola combinación de denominaciones observadas. Se comprobó también el contexto detallado de meta hacia META_NOMBRE sin variantes.

No son claves suficientes:
- Año/nivel/SEC_EJEC/SEC_FUNC: hay **863, 1.160, 1.077 y 1.336** claves con variantes de contexto, respectivamente.
- Añadiendo FINALIDAD todavía hay **8, 7, 7 y 7** claves con variantes en META/ubicación/intervención/función. No debe utilizarse esa combinación reducida como identidad definitiva.

La propuesta de clave natural de meta detallada contiene **20 componentes**: año + ocho códigos de entidad + cuatro de intervención + tres funcionales + SEC_FUNC + FINALIDAD + META + departamento. En esta población determina el nombre; no se ha demostrado que sea mínima. El grano de hecho debe incluir además financiamiento, clasificador y mes. Los 714 conflictos impiden afirmar que todo el archivo tenga un grano de negocio globalmente único sin exclusiones.

Entre años se observaron ocho claves compuestas de entidad con dos combinaciones de nombres y cinco claves de clasificador con hasta tres. La jerarquía funcional y rubro→fuente no presentaron variantes en los códigos contrastados. No se inventan fechas de vigencia SCD2: registrar nombres observados por fuente/año no prueba la fecha efectiva de un cambio.

## 5. Correspondencias financieras y enlace al snapshot anual

La jerarquía **RUBRO → FUENTE_FINANCIAMIENTO** se cumple sin excepciones en las cuatro fuentes y en su contraste interanual, para los nueve rubros observados.

La transformación ensayada para relacionar con el modelo heredado es explícita:
- Nueva FUENTE_FINANCIAMIENTO corresponde al campo RUBRO del comparativo/snapshot.
- Nuevo RUBRO corresponde al campo FUENTE_FINANCIAMIENTO del comparativo/snapshot.
- TIPO_RECURSO se conserva con su contexto.
- TIPO_ACT_PROY: ACTIVIDAD→3 y PROYECTO→2, valores comprobados en estas fuentes.

Se contrastaron códigos **y nombres de los roles** contra los 114 registros de financiamiento del snapshot:
- **10.953.570 filas** corresponden a tuplas existentes y sus nombres de fuente/rubro coinciden exactamente al invertir los roles.
- **3.772 filas** usan tuplas que no están en la dimensión de la muestra anual; no se consideran errores por esa ausencia. Pueden requerir nuevos registros si se amplía fuera de la cohorte enlazada.
- No se detectaron discordancias de los nombres de esos dos roles en las tuplas coincidentes.

Esto valida la adaptación en el ámbito observado. No constituye una auditoría completa del comparativo original, que solo se recorrió para un caso concreto. Las copias locales de diccionario previamente encontradas estaban vacías y no fueron sustituidas; no se atribuye a ellas una validación inexistente.

### Enlace por clave completa y seis medidas

| Año | Anuales del snapshot | Enlazadas | Conciliadas seis medidas | Diferentes | Sin enlace bajo filtros |
| --- | --- | --- | --- | --- | --- |
| 2022 | 37.500 | 37.373 | 37.334 | 39 | 127 |
| 2023 | 37.500 | 37.352 | 37.297 | 55 | 148 |
| 2024 | 37.500 | 37.330 | 37.330 | 0 | 170 |
| 2025 | 37.500 | 37.288 | 37.246 | 42 | 212 |

Se enlazaron **149.343** observaciones del snapshot bajo la política conservadora. Cada padre enlazado tiene una sola serie mensual en esta cohorte: no hay expansión muchos-a-muchos. Otras **657** observaciones anuales no enlazaron bajo los filtros/mapa; no se concluye que no exista ninguna contraparte posible.

De las enlazadas, **149.207** coinciden en PIA, PIM, certificado, compromiso anual, devengado anual y girado anual. Son la población común conciliada disponible, no una muestra mensual ya seleccionada. El compromiso mensual del hecho anual no está presente en el devengado ancho y no se declaró conciliado con él.

### Diferencias residuales: conocidas, no corregidas

| Año | Series diferentes | Diferencias devengado | Diferencias girado | Delta devengado total (mensual − snapshot) | Máximo absoluto en girado |
| --- | --- | --- | --- | --- | --- |
| 2022 | 39 | 3 | 38 | 17.675,44 | 21.030,90 |
| 2023 | 55 | 7 | 50 | 75.376,91 | 299.470,03 |
| 2024 | 0 | 0 | 0 | No aplica | No aplica |
| 2025 | 42 | 2 | 40 | -16,51 | 16.371,20 |

Son **136 observaciones distintas**: 12 difieren en devengado y 128 en girado, con solapamiento de cuatro casos. PIA, PIM, certificado y compromiso anual coinciden en todas las observaciones enlazadas. Los catálogos guardan cada hecho, KEY_VALUE, clave completa y deltas firmados.

Las diferencias **no se explican por un simple céntimo de redondeo**: el máximo absoluto observado es 299.470,03 en girado de 2023. No se atribuyen automáticamente a errores del MEF ni a fechas de corte; faltan metadatos o comprobaciones específicas de cada caso. Tampoco se ajustaron importes para forzar igualdad. Estas 136 series quedan fuera de la cohorte que concilia las seis medidas.

La igualdad monetaria en una cohorte no certifica cierre oficial ni representatividad nacional. Se mantiene la advertencia de que 2025 es una instantánea con fecha de corte de ejecución no certificada.

## 6. Resolución verificada de los 59.000 de 2024

Con autorización adicional se leyó completo el comparativo original de 8,98 GB, **filtrando únicamente la clave presupuestaria del caso**. Se conservaron tres contrapartes en un pequeño Parquet.

Las tres tienen KEY_VALUE **178D0E452F3066BB9E5F9F0945C9E6E3** y la misma combinación de códigos y META_NOMBRE, pero variantes en las descripciones de subgenérica/específica:

| Contraparte del comparativo | PIM 2023 | PIM 2024 | Devengado 2024 | PIM 2025 |
| --- | ---: | ---: | ---: | ---: |
| Fila tomada en la comparación inicial | 6.750 | 0 | 0 | 0 |
| Contraparte con actividad de 2024 | 0 | **59.000** | **59.000** | 0 |
| Otra contraparte | 0 | 0 | 0 | 48.500 |

Hay **una sola contraparte activa en 2024**. Sus referencias de PIM, certificado, compromiso anual, devengado y girado son 59.000; PIA es 0. Las seis medidas comunes coinciden exactamente con la única contraparte mensual del caso.

**Explicación comprobada:** el enlace inicial tomó una fila cuyo bloque de 2024 estaba inactivo. La otra fila aporta la ejecución de ese ejercicio. No había que corregir importes ni asumir que faltaban 59.000 en el Data Warehouse.

Este caso también demuestra que **KEY_VALUE no identifica de forma única la fila física del CSV ancho**. La extracción anual debe considerar todas las contrapartes y el bloque del ejercicio; no usar un diccionario KEY_VALUE→primera fila. Esto no invalida la unicidad anual del snapshot, verificada con año/KEY_VALUE. No se deducen algoritmos de hash ni vigencias administrativas a partir del caso.

No se auditaron globalmente las claves ni los totales de todo el comparativo: el recorrido adicional tuvo un filtro específico. Los nombres alternativos se conservan como observaciones; no se inventa una historia SCD2.

## 7. Viabilidad y estrategia de 150.000 hechos mensuales

**Viable dentro de la cohorte común conciliada**, con 149.207 series disponibles frente a las 12.500 propuestas.

| Año | Series comunes conciliadas | Entidades disponibles | Gobiernos | Series propuestas | Hechos mensuales propuestos |
| --- | --- | --- | --- | --- | --- |
| 2022 | 37.334 | 2.845 | 3 | 3.125 | 37.500 |
| 2023 | 37.297 | 2.844 | 3 | 3.125 | 37.500 |
| 2024 | 37.330 | 2.845 | 3 | 3.125 | 37.500 |
| 2025 | 37.246 | 2.862 | 3 | 3.125 | 37.500 |

Propuesta pendiente de aprobación:
1. Mantener los 150.000 hechos anuales.
2. Seleccionar 3.125 series por año; cada una aporta sus doce columnas reales, incluidos ceros y negativos: 37.500 hechos mensuales por ejercicio y 150.000 en total.
3. Estratificar por año/gobierno/entidad; la cuota anual alcanza para reservar una serie por cada entidad de la cohorte (entre 2.844 y 2.862). Verificar clasificación y medidas de cobertura antes de aprobar cuotas finales.
4. Ordenar por hash de semilla versionada + fuente/versionado + clave anual canónica; desempatar por clave completa. Repetir la selección con orden de entrada alterado.
5. Preservar mes→año, las seis conciliaciones de la serie y el enlace a su observación anual. No copiar seis presupuestos anuales en doce filas.
6. Mantener fuera de la selección comparada las claves conflictivas y las 136 diferencias hasta resolverlas. Se preservan en auditoría.

La cohorte contiene tres niveles de gobierno y distintos clasificadores. Incluye nueve, ocho, siete y ocho valores de genérica según el año. **No se promete cubrir todos los clasificadores de la población**, ni cada combinación entidad×clasificador. Si se exige otra cobertura, debe revisarse el diseño y quizá usar una cohorte mensual independiente, con avisos analíticos.

No se calcularon ni aplicaron cuotas definitivas, pesos de expansión o una selección de 12.500 series. Los CSV cohorte_disponible contienen todo el catálogo diagnóstico elegible, no los hechos seleccionados para cargar.

Las cuotas equilibradas y los mínimos por entidad favorecen cobertura descriptiva; no demuestran representatividad nacional. Las comparaciones de ejecución usarán exactamente la misma cohorte y denominador positivo: SUM(devengado)/SUM(PIM)*100. No promediar porcentajes ni comparar toda la muestra anual contra una submuestra mensual distinta.

## 8. Recomendaciones para V2, todavía no implementadas

**Dos hechos, sin tercera tabla de gasto automática:**
- Conservar el hecho anual y sus siete dimensiones, SK y medidas como referencia.
- Añadir hecho de devengado mensual al grano del período y combinación presupuestaria detallada, solo para una población de observaciones inequívocas aprobada.
- Utilizar los CSV de gasto con MES_EJE para contrastes o futuras etapas mensuales si se justifican; no duplicar devengado ni generar otra cuota de 150.000 por defecto.

### Dimensiones

Cinco dimensiones no temporales son reutilizables mediante conformidad: entidad, intervención, función, financiamiento y clasificador. Intervención requiere el mapa de tipo texto/código; financiamiento requiere corregir los roles semánticos mediante una adaptación/vista o la copia V2, preservando las SK y el original.

Se recomienda añadir **dimensión de período mensual** y **dimensión de meta detallada**, manteniendo la meta heredada para los anuales. Serían nueve dimensiones en la constelación: las siete existentes más estas dos. El hecho mensual podría referenciar las cinco compartidas, meta detallada y período; año es atributo de conformidad temporal.

La separación de meta evita fabricar SEC_FUNC/FINALIDAD para observaciones antiguas. Su clave natural propuesta usa los veinte componentes comprobados; META_NOMBRE puede ser atributo en las nuevas fuentes, pues la dependencia funcional se cumple. Una alternativa de ocho dimensiones mediante ampliación compatible de la meta en la copia V2 requiere justificar niveles y correspondencias; no debe forzar identidad al detalle.

Conservar nombres alternativos y códigos como texto. Los 831 nombres ausentes deben mostrarse como falta de denominación, sin inventar códigos o historia. Que año/SEC_FUNC/FINALIDAD tengan variantes prueba que hacen falta los contextos adicionales.

### Consultas, carga y pruebas futuras

No unir directamente las filas de ambos hechos. Agregar por separado y alinear resultados por atributos conformados (drill-across). Si se comparan metas, usar solo un nivel común cuya correspondencia esté verificada.

El futuro ETL debe generar dimensiones y hechos en un entorno independiente, con FK, unicidad sobre la población aprobada, controles de contexto, COPY transaccional y manifiestos. Los negativos son válidos; no usar restricciones que los prohíban. Conservar la referencia anual y sus 28 controles.

Antes de cargar: aprobar exclusiones/muestreo, resolver o apartar conflictos, comprobar doce meses por serie, valores exactos antes/después y cero huérfanos. Después: regresión anual, consultas por período, filtros y CSV del dashboard, respaldo y recuperación aislados. Las pruebas anteriores del dashboard no se reejecutaron porque no hubo cambios en él; no se simula una validación de un V2 inexistente.

**No se crearon tablas, migraciones, ETL de producción ni cambios de dashboard.** El diseño queda pendiente de tu aprobación.

## 9. Recursos y ejecución controlada

La memoria interna del motor permaneció en **768 MiB**, sin aumentos respecto del intento detenido. Se mantuvieron dos hilos de DuckDB, afinidad del trabajador a dos procesadores, monitor externo aproximadamente a 1,95 GiB, spill máximo 32 GiB y umbral preventivo de carpeta de 39 GiB. El conteo de espacio fue conservador: incluyó otros artefactos de analisis_ampliacion, no solo spill.

| Fase | Tiempo s | CPU s | Pico memoria MiB | Pico carpeta GiB |
| --- | --- | --- | --- | --- |
| Piloto + integridad 2022 | 61,69 | 70,08 | 192,50 | 0,17 |
| Cuatro ejercicios + contraste interanual | 459,75 | 633,17 | 953,86 | 4,09 |
| Comparativo filtrado: caso 2024 | 30,41 | 27,34 | 815,54 | 0,49 |
| Clasificación de conflictos y financiamiento | 25,57 | 37,98 | 872,43 | 1,15 |
| Catálogo de diferencias | 2,19 | 1,59 | 132,34 | 0,49 |

Las cinco fases terminaron con código 0, sin nuevos agotamientos de memoria. Los tiempos son ejecución medida, excluyendo preparación de scripts y esperas de permisos; suman aproximadamente 9,7 minutos. La lectura adicional autorizada del comparativo duró unos 30 segundos.

El pico global observado fue aproximadamente **954 MiB de memoria incluyendo monitor** y **4,09 GiB de espacio de trabajo**, por debajo de 2 GiB y 40 GiB. Son mediciones periódicas e historial de working set disponible del proceso, no una demostración continua de cada asignación.

El espacio libre se comprobó antes de comenzar. Los temporales permanecen disponibles para trazabilidad/reanudación y no se publicaron. Los archivos de spill del motor se liberaron al cerrar sus conexiones; no se eliminaron manualmente fuentes o artefactos originales.

El Parquet reutilizado de 2022 no se duplicó. La referencia compacta evitó volver a construir las uniones dimensionales grandes durante cada exportación mensual. La auditoría no materializó los 131,5 millones de hechos virtuales, sino solo agregados y enlaces diagnósticos.

## 10. Integridad del proyecto original

El cierre registra:
- 63 archivos de ENTREGA_FINAL con hashes coincidentes con SHA256SUMS.txt.
- Ocho CSV preparados del snapshot con los hashes de manifest.json.
- Recuento de 150.000 hechos en el CSV anual y sus siete FK comprobadas contra las dimensiones preparadas.
- Revisión exacta con Decimal de sus **28 totales anuales** contra el manifiesto.
- Rama main y commit originales sin cambios, árbol Git limpio.
- Tamaño/mtime de las cuatro fuentes mensuales y del comparativo sin cambios; hashes completos de las cuatro mensuales guardados.
- Ningún trabajador o monitor de esta auditoría activo al terminar.

Estas son verificaciones **de archivos y del snapshot preparado**. No se consultó ni modificó la base PostgreSQL en vivo, sus servicios, Docker, volúmenes o credenciales. No se realizó ETL, carga, restauración, commit o push. Los respaldos de origen no fueron objeto de operaciones de escritura.

No se calculó un hash completo nuevo del comparativo original durante la lectura extraordinaria; se registraron sus metadatos y contrapartes filtradas. Los hashes de las fuentes mensuales corresponden al contenido efectivamente auditado.

## 11. Evidencias principales

- evidencias/auditoria_completa.json: resultado poblacional de los cuatro CSV.
- evidencias/resultado_2022.json … resultado_2025.json: calidad, totales, duplicados, dependencias y enlaces.
- evidencias/checkpoint_*.json, consultas.sql, eventos.jsonl: resultados inmediatos y SQL ejecutado.
- evidencias/integridad_2022.json: verificación CSV/Parquet reutilizado.
- evidencias/piloto_aprobado.json: referencia única y piloto del cruce nuevo.
- evidencias/diagnosticos_complementarios.json: clasificación de los 714 conflictos y financiamiento.
- evidencias/discrepancias_2022.json … discrepancias_2025.json: catálogo completo de las 136 diferencias, con deltas y trazabilidad.
- evidencias/caso_59000_resolucion.json: tres contrapartes y conciliación exacta de 2024.
- evidencias/cohorte_disponible_*.csv: catálogos diagnósticos completos, no muestra definitiva.
- evidencias/recursos_*.json, metricas_*.jsonl, cpu_*.json: límites y consumo.
- evidencias/control_preservacion_final.json: integridad de la entrega y fuentes.
- temporal/: proyecciones y conflictos conservados; el Parquet 2022 se referencia desde la auditoría previa.
- scripts/: auditoría y verificadores; no implementación de V2.

## 12. Decisiones pendientes

1. Aprobar dos hechos y conservar el snapshot anual.
2. Aprobar la población conservadora: series activas inequívocas, excluyendo grupos repetidos y diferencias no resueltas para las comparaciones.
3. Aprobar 3.125 series por año, estratos y criterios de cobertura; después ejecutar una selección reproducible todavía no realizada.
4. Aprobar la dimensión de meta detallada separada o una alternativa justificada.
5. Aprobar entorno independiente, DDL, ETL y cambios de dashboard de V2 en una fase futura.

**Conclusión:** auditoría mensual poblacional completada y muestra de 150.000 hechos mensuales viable dentro de una cohorte conciliada de 149.207 series. La fuente completa no tiene unicidad de negocio universal ni todas las fuentes son monetariamente intercambiables; los conflictos y diferencias quedan preservados. El modelo V2 no se implementó y espera aprobación.
