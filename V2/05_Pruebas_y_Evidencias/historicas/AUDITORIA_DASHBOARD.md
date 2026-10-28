# Auditoria funcional, visual y analitica del dashboard MEF V2

Fecha de cierre America/Lima: 2026-10-28T14:01:53.210633-05:00

**Dictamen: operativo y consistente en datos; apto para una exposicion guiada, con observaciones que conviene resolver antes de cerrar la entrega y publicar V2. No se implemento ninguna mejora.**

No se detectaron errores de importes, doble conteo o excepciones de la aplicacion en los escenarios ejecutados. Se registran cuatro hallazgos de severidad media y dos de severidad baja. No se detectaron hallazgos altos o criticos dentro del alcance probado.

## 1. Alcance, metodo y protecciones

- Dashboard en http://127.0.0.1:8502. Acceso SQL exclusivo a dw_mef_2022_2025_v2 con transacciones de solo lectura.
- Revision estatica de app.py, datos.py, presentacion.py, estilos, configuracion, pruebas existentes y documentacion.
- SQL independiente, pruebas unitarias, AppTest, Chrome real y capturas de las seis secciones.
- Pruebas existentes ejecutadas sin cambiar sus archivos: se redirigio su salida mediante variables del proceso de auditoria. Las simulaciones de error se aplicaron solo en un proceso AppTest separado, no al servidor activo.
- 23 archivos publicos existentes del dashboard conservaron sus hashes antes/despues. Se excluyeron entorno virtual, caches, logs de ejecucion y contenido secreto del registro. No se recopilaron contrasenas.
- La bateria comprueba 63 hashes originales de ENTREGA_FINAL y el SHA-256 del respaldo V2, sin cambios. Se verifico que la base temporal de restauracion sigue existiendo.
- No se modificaron calculos, codigo del dashboard, PostgreSQL, Docker, CSV, respaldos, ENTREGA_FINAL ni Git. Solo se crearon informes, scripts de auditoria y evidencias en esta carpeta.

## 2. Estado de las seis secciones

| Seccion | Estado funcional | Evidencias y observaciones |
|---|---|---|
| Resumen ejecutivo | Correcto con observaciones | PIA/PIM/devengado/girado coinciden con SQL; ambas coberturas operativas; CSV filtrado correcto. M01, M02 y B01 afectan claridad. |
| Presupuesto anual | Correcto | Cuatro etapas separadas, razon de sumas, PIM no positivo no calculable, porcentaje mayor a 100 sin recorte, tablas y CSV exactos. El formato de importes pequenos merece M01 donde se reutiliza. |
| Evolucion mensual | Correcto con observacion semantica | 48 agregados, doce meses por serie, rango visible y acumulado desde enero correctos. M03 aclara el contador de negativos; B02 recomienda estabilidad cromatica. |
| Comparacion de ejercicios | Correcto | Cohorte de entidades comunes, anos no consecutivos sin variacion fabricada y ausencia de cohorte comun con mensaje. Dos CSV filtrados correctos. Conciliacion anual/mensual independiente sin diferencias. |
| Analisis por dimensiones | Correcto | Cuatro dimensiones y cinco medidas: veinte combinaciones de ranking comprobadas. Nombres completos en tooltips, PIM/hechos contextualizan porcentajes y busqueda vacia informa correctamente. CSV filtrado correcto. |
| Metodologia y calidad | Correcto con documentacion de proyecto pendiente | Matriz bus, granos, muestras, reglas y limites identificados. Control general se distingue del filtro. M04 corresponde al README principal del proyecto, no a una alteracion monetaria de esta vista. |

## 3. Datos y conciliacion

| Control | Resultado |
|---|---:|
| Hechos anuales | 150.000 |
| Hechos mensuales | 150.000 |
| Total de registros de hechos | 300.000 |
| Series vinculadas | 12.500 |
| Periodos calendario | 48 |
| Dimensiones / tablas | 9 / 12 |
| FK validadas / huerfanos | 22 / 0 |

El total 300.000 cuenta registros de dos procesos; no implica sumar las medidas de ambos. La cohorte mensual corresponde solo a 12.500 hechos anuales, no a los 150.000 del anual completo.

| Universo anual | Hechos | PIA | PIM | Devengado | Girado |
|---|---:|---:|---:|---:|---:|
| Completo | 150000 | 15445884249.00 | 14353164025.00 | 12028734393.81 | 11980391377.67 |
| Cohorte vinculada | 12500 | 816994607.00 | 1139183592.00 | 1132814617.38 | 1132343529.30 |

Importes en soles corrientes, punto decimal en esta tabla tecnica. Las cuatro sumas por universo fueron contrastadas con SELECT directo sin uniones a dimensiones y, para cohorte, pertenencia mediante IN a la tabla tecnica.

- 28 controles anuales y 48 mensuales exactos frente a los metadatos del respaldo, ademas de comparaciones con SQL independiente para los filtros.
- No se promedian porcentajes individuales. La division solo se calcula con SUM(PIM)>0; tolerancia de contraste del porcentaje 1e-12. Los importes monetarios se comparan exactamente.
- Caso real de PIM cero: anio 2023, nivel M, entidad 1536, funcion 17, fuente 5; doce hechos, devengado S/ 133.400,40, PIM cero. La interfaz muestra No calculable y el aviso.
- Caso real superior a 100: cohorte 2024; el porcentaje observado se conserva sin recortar. No se atribuye una causa no certificada.
- La muestra completa tiene 49.557 hechos anuales con PIM cero y devengado positivo, por S/ 3.541.333.536,98; el indicador coincide con SQL sin uniones.
- Las conciliaciones agregan cada tabla por separado y luego unen por anio; los doce meses permanecen completos. No se hallo multiplicacion de importes.
- Negativos y ceros se conservan. Gobiernos locales incluidos sin exigir sector/pliego. Financiamiento conformado contrastado con los roles heredados.

## 4. Pruebas ejecutadas y resultados

| Grupo de pruebas | Resultado |
|---|---|
| Bateria existente | 131 comprobaciones satisfactorias; incluye la ejecucion de nueve pruebas unitarias |
| Casos adicionales | 15/15 satisfactorios |
| Rankings: 4 dimensiones x 5 indicadores | 20/20; valores de tooltips coinciden con los agregados ordenados |
| Navegador: 6 secciones x 3 resoluciones | 18/18; 1440x1050, 768x1024 y 390x844 |
| Descargas reales con cinco filtros | 7/7, identicas byte a byte a los agregados filtrados |
| Errores JavaScript | 0 |
| Excepciones Streamlit / errores de conexion en las 18 vistas | 0 |
| Desbordamiento horizontal de pagina en las 18 vistas | 0 |
| Referencias huerfanas | 0 en las 22 FK, verificadas mediante antiuniones |

No se suman estas cifras como si todas fueran pruebas independientes: hay comprobaciones de distinto nivel y escenarios compartidos. Los hallazgos de usabilidad o nomenclatura pueden coexistir con consultas y renderizados correctos.

**Descargas filtradas:** anio 2024, nivel Local, entidad 1931, funcion 10, fuente 5. Se aplicaron los cinco controles reales en Chrome. Se descargaron resumen, anual, mensual, comparacion, conciliacion de comparacion, dimensiones y conciliacion de metodologia. Sus valores, decimales y conjuntos corresponden al filtro, no a la muestra completa. Detalle y SHA-256 de cada descarga: evidencias/auditoria_navegador_ampliada.json.

**Estados especiales:** las seis secciones informan seleccion vacia de anios sin ampliarla; una combinacion sin entidades comunes no fabrica comparaciones; la busqueda inexistente informa; un error de conexion simulado muestra un mensaje controlado sin traceback ni secretos. No se detuvo PostgreSQL ni se alteraron credenciales para esas pruebas.

## 5. Hallazgos por severidad

Media: puede inducir una interpretacion incorrecta o dificultar la entrega; conviene resolver antes de publicacion. Baja: mejora de presentacion sin alterar resultados. No se clasifican redondeos de interfaz como errores del dato original.

### M01 ? Importes no nulos aparecen como S/ 0,00 M en las tarjetas

- Severidad: **Media**. Categoria: Presentacion analitica.
- Hallazgo comprobado: Caso real: 2023, gobierno R, entidad 2680, funcion 10, fuente 1; devengado S/ 4.999,99 se formatea como S/ 0,00 M. Se verifico ademas extremo a extremo un caso de S/ 0,01. Las tablas y CSV conservan el importe exacto.
- Recomendacion, no implementada: Formato adaptativo: soles para importes pequenos y millones solo cuando aporten legibilidad; mostrar tambien importe exacto en ayuda o detalle. No cambiar SUM ni la precision original.
- Evidencia: evidencias/importes_pequenos.json; evidencias/importes_pequenos_escala.json

### M02 ? Una seleccion invalida se retira y amplia el universo sin aviso especifico

- Severidad: **Media**. Categoria: Interaccion de filtros.
- Hallazgo comprobado: Entidad local 2046: 412 hechos y una entidad. Al cambiar gobierno a E, la entidad se retira, el filtro queda vacio y se incluyen 23.565 hechos de 401 entidades nacionales. El SQL es correcto para el filtro final, pero el cambio de alcance no se anuncia expresamente.
- Recomendacion, no implementada: Informar que se retiro una seleccion o preservar un estado sin resultados hasta que el usuario elija otro filtro; evitar una ampliacion silenciosa.
- Evidencia: evidencias/auditoria_adicional.json -> observations.filter_reset

### M03 ? Meses negativos cuenta registros, no meses calendario

- Severidad: **Media**. Categoria: Semantica del indicador.
- Hallazgo comprobado: La tarjeta muestra 324. Son hechos mensuales de series con importe negativo; hay 48 periodos calendario y ninguno tiene devengado agregado negativo en el filtro completo. El conteo SQL es correcto, el nombre es ambiguo.
- Recomendacion, no implementada: Renombrar como Hechos mensuales con importe negativo o Registros mensuales negativos. Mantener el conteo y los importes.
- Evidencia: evidencias/semantica_negativos.json; evidencias/390_3_graficos.png

### M04 ? El README principal de V2 conserva el estado anterior a la implementacion

- Severidad: **Media**. Categoria: Documentacion de entrega.
- Hallazgo comprobado: Declara que no se ha creado ni cargado la base V2, aunque la implementacion, respaldo, restauracion y dashboard ya existen. El README del dashboard si describe su ejecucion actual.
- Recomendacion, no implementada: Preparar una entrada principal actualizada y distinguir los documentos historicos de preparacion de las instrucciones vigentes, antes de publicar V2.
- Evidencia: ../README.md, linea 3; evidencias/observaciones_documentacion_colores.json

### B01 ? No se muestra explicitamente el total de 300.000 hechos

- Severidad: **Baja**. Categoria: Cobertura visible.
- Hallazgo comprobado: Las seis vistas muestran 150.000 hechos anuales y 150.000 mensuales. El total se deduce, pero no hay una cifra explicita de 300.000. No hay error en los conteos.
- Recomendacion, no implementada: Anadir el total de registros como 300.000 hechos, 150.000 por proceso, aclarando que no son 300.000 partidas anuales ni una suma de importes.
- Evidencia: evidencias/auditoria_adicional.json -> observations.explicit_300000_visible

### B02 ? El color de un ejercicio cambia al filtrar otros anios

- Severidad: **Baja**. Categoria: Consistencia visual.
- Hallazgo comprobado: 2024 usa #7B9FF2 al mostrar cuatro anios y #35D6C6 al mostrar solo 2024. La leyenda sigue siendo correcta, pero dificulta comparar capturas o estados de filtro.
- Recomendacion, no implementada: Asignar un color fijo por anio, independiente de la posicion en la seleccion.
- Evidencia: evidencias/observaciones_documentacion_colores.json

## 6. Evaluacion visual

La paleta azul marino/turquesa/dorado, jerarquia de tarjetas, navegacion y estilos son coherentes y adecuados para una exposicion universitaria. No se recomienda reconstruir el dashboard.

- En las capturas de escritorio, tablet y movil, las seis vistas mantienen navegacion y contenido accesibles. Las columnas se apilan en movil y las tablas anchas conservan desplazamiento interno.
- Los titulos y unidades monetarias se identifican en los graficos. La comprobacion geometrica no encontro titulos fuera del SVG en los graficos inspeccionados.
- Las etiquetas largas del ranking se abrevian, con denominacion completa en tooltips. En movil queda menos espacio util para barras; mejorar ese equilibrio seria un pulido opcional, no un fallo funcional demostrado.
- Las tarjetas monetarias usan millones con dos decimales; M01 explica por que esta convencion pierde informacion al filtrar importes pequenos.
- Los porcentajes no se recortan, las advertencias de muestra/cobertura variable y fecha de corte no certificada de 2025 permanecen visibles.
- El color anual cambiante B02 no invalida la leyenda, pero conviene estabilizarlo para comparar estados o capturas.

## 7. Preparacion para la entrega y tareas antes de GitHub

**Orden recomendado, pendiente de autorizacion:**

1. Resolver M01, M02 y M03 mediante ajustes locales de formato, interaccion y etiquetas; no requieren cambiar importes ni reconstruir PostgreSQL.
2. Actualizar la entrada principal de V2 y separar expresamente instrucciones vigentes de evidencias historicas de preparacion (M04).
3. Anadir el total de hechos y estabilizar los colores si se aprueba el pulido (B01/B02).
4. Repetir las pruebas de regresion pertinentes y las descargas filtradas despues de esos cambios; conservar esta auditoria como linea base.
5. Preparar la carpeta/version V2 sin alterar ENTREGA_FINAL ni main; definir claramente que archivos se publicaran. No se creo una rama ni repositorio durante esta auditoria.
6. Revisar .gitignore y el listado exacto a incluir: excluir secrets.toml, .env reales, .venv, caches, logs y temporales. No publicar credenciales aunque el servidor sea local.
7. Definir inclusion del dump validado, su hash y metadatos, mas guia de restauracion portable. No duplicar CSV nacionales o archivos Parquet de auditoria innecesarios.
8. Probar instalacion en un entorno limpio con requirements.txt y restauracion/configuracion de V2 en el entorno acordado; el entorno actual reutiliza paquetes globales. No afirmar recuperacion en otra computadora sin ejecutarla.
9. Revisar licencia/procedencia de datos, README final, capturas definitivas y enlaces relativos, y volver a revisar secretos y tamanos antes de autorizar commit/push.

Estas son tareas propuestas; ninguna fue implementada o publicada. No se requiere cambiar la arquitectura Kimball ni los calculos para corregir los hallazgos encontrados.

## 8. Alcance y limites de la conclusion

- Se probaron escenarios concretos y tres resoluciones, no todas las combinaciones posibles, navegadores ni condiciones de red.
- No se realizo una prueba de carga concurrente ni de despliegue remoto. No se intento una escritura real para demostrar su bloqueo.
- La ordenacion manual por cada cabecera del componente de tabla no se automatizo; si se comprobo el contenido, el orden de los rankings, el formato y las descargas.
- No se repitio la auditoria de los CSV nacionales, ETL ni restauracion. La base temporal permanece conservada.
- Los resultados describen muestras, no inferencia nacional. La conciliacion no certifica la fecha de corte 2025 ni la causa de PIM cero con devengado positivo.

## 9. Evidencias

- BASELINE_DASHBOARD.json y evidencias/PRESERVACION_DASHBOARD.json: 23 archivos preservados, sin cambios.
- evidencias/verificacion_1793211537730909900.json: bateria existente redirigida.
- evidencias/auditoria_adicional.json: casos de PIM, filtros, ausencia de datos y total visible.
- evidencias/auditoria_navegador_ampliada.json y eventos_navegador.jsonl: 18 vistas y siete CSV filtrados.
- evidencias/rankings_20_combinaciones.json: veinte rankings.
- evidencias/integridad_referencial.json: definiciones reales de 22 FK y cero huerfanos.
- evidencias/importes_pequenos*.json, semantica_negativos.json y observaciones_documentacion_colores.json: reproducciones de hallazgos.
- Capturas representativas: evidencias/1440_1_superior.png, evidencias/768_2_graficos.png, evidencias/390_3_graficos.png y evidencias/390_5_graficos.png.

**No se corrigieron hallazgos. Se espera autorizacion antes de modificar el dashboard o la documentacion existente.**
