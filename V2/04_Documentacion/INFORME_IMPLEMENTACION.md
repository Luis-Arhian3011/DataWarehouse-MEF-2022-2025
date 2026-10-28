# Informe de implementacion controlada ? Data Warehouse MEF V2

Fecha UTC: 2026-10-25T09:07:47.714767+00:00

**Estado: IMPLEMENTADO Y VALIDADO.** Base exclusiva dw_mef_2022_2025_v2, servidor PostgreSQL 15.19 en postgres-db. La implementacion original permanece independiente.

## 1. Verificaciones previas y autorizacion

- Autorizacion explicita del usuario para crear y cargar exclusivamente V2.
- postgres-db activo, identidad de servidor TCP coincidente con Docker: 7697394465128882215. Sin reinicio ni cambios de configuracion.
- La base V2 no existia antes de ejecutar CREATE DATABASE.
- Lote local validado y hashes de preparacion comprobados. 150.000 hechos anuales y 150.000 mensuales.
- Origen cotejado en modo de solo lectura: todas las columnas de sus ocho tablas coinciden con el snapshot protegido; siete FK sin huerfanos y hechos/granos unicos.
- Espacio libre de host antes de cargar: 335.21 GiB. Espacio logico disponible dentro del almacenamiento Docker: 951.81 GiB. El host fisico es el limite efectivo; ambos superaban el margen preventivo de 10 GiB.
- Los dos SQL DDL tienen guardia current_database() contra el nombre V2. Las escrituras del cargador utilizan exclusivamente esa conexion. El origen usa default_transaction_read_only=on. No hay instrucciones destructivas.

## 2. Arquitectura y matriz bus Kimball

Dos procesos a diferente grano, nueve dimensiones y una tabla tecnica sin medidas. Se conserva el anual y se comparte el significado de los catalogos mediante las mismas claves sustitutas.

| Hecho | Anio | Entidad | Intervencion | Funcion | Meta original | Financiamiento | Clasificador | Periodo mensual | Meta detallada |
|---|---|---|---|---|---|---|---|---|---|
| Anual | Directo | Compartida | Compartida | Compartida | Directa | Compartida, vista conformada | Compartida | No aplica | No aplica |
| Mensual | Mediante periodo y contexto | Misma SK | Misma SK | Misma SK | Solo linaje tecnico | Misma SK, vista conformada | Misma SK | Directo | Directa |

Matriz completa y justificacion de las 22 FK: [MATRIZ_BUS_KIMBALL.md](MATRIZ_BUS_KIMBALL.md). Diagrama: [esquema_v2.mmd](esquema_v2.mmd).

- **Grano anual:** anio y combinacion completa de las siete dimensiones originales, con meta contextual; 150.000 observaciones originales conservadas.
- **Grano mensual:** periodo anio-mes, entidad, intervencion, funcion, meta detallada, financiamiento y clasificador. Doce filas por serie.
- Meta detallada incluye SEC_FUNC y FINALIDAD con anio/entidad/intervencion/funcion/META/DEPARTAMENTO_META. No se usa SEC_FUNC aislado como identificador.
- La tabla auditoria.serie_seleccionada garantiza linaje y coherencia de contexto mediante dos FK compuestas. No es un tercer hecho ni un puente para repartir importes.
- La vista v_financiamiento_conformado adapta los roles invertidos de fuente/rubro heredados sin cambiar los miembros originales.
- No se unen hechos a nivel fila para sumar. Las consultas agregan independientemente la misma cohorte; PIA y PIM permanecen anuales.

## 3. Tablas y registros

| Tabla | Registros |
|---|---:|
| auditoria.serie_seleccionada | 12.500 |
| mef.dim_anio | 4 |
| mef.dim_clasificador_gasto | 476 |
| mef.dim_entidad | 2.898 |
| mef.dim_financiamiento | 114 |
| mef.dim_funcion | 356 |
| mef.dim_intervencion | 18.654 |
| mef.dim_meta | 121.305 |
| mef.dim_meta_detallada | 12.477 |
| mef.dim_periodo_mensual | 48 |
| mef.fact_devengado_mensual | 150.000 |
| mef.fact_ejecucion_presupuestaria_anual | 150.000 |

**Total: 12 tablas, 468.832 registros, incluidos exactamente 300.000 registros de hechos.**

Base V2 medida tras validar: 271301991 bytes (258.73 MiB).

## 4. Resultado de cada clave foranea

| Tabla hija | Restriccion | Tabla referenciada | Validada | Huerfanos |
|---|---|---|---|---:|
| auditoria.serie_seleccionada | serie_seleccionada_hecho_anual_key_anio_key_entidad_key_in_fkey | mef.fact_ejecucion_presupuestaria_anual | Si | 0 |
| auditoria.serie_seleccionada | serie_seleccionada_meta_detalle_key_anio_key_entidad_key_i_fkey | mef.dim_meta_detallada | Si | 0 |
| mef.dim_meta_detallada | dim_meta_detallada_anio_key_fkey | mef.dim_anio | Si | 0 |
| mef.dim_meta_detallada | dim_meta_detallada_entidad_key_fkey | mef.dim_entidad | Si | 0 |
| mef.dim_meta_detallada | dim_meta_detallada_funcion_key_fkey | mef.dim_funcion | Si | 0 |
| mef.dim_meta_detallada | dim_meta_detallada_intervencion_key_fkey | mef.dim_intervencion | Si | 0 |
| mef.dim_periodo_mensual | dim_periodo_mensual_anio_key_fkey | mef.dim_anio | Si | 0 |
| mef.fact_devengado_mensual | fact_devengado_mensual_clasificador_gasto_key_fkey | mef.dim_clasificador_gasto | Si | 0 |
| mef.fact_devengado_mensual | fact_devengado_mensual_entidad_key_fkey | mef.dim_entidad | Si | 0 |
| mef.fact_devengado_mensual | fact_devengado_mensual_financiamiento_key_fkey | mef.dim_financiamiento | Si | 0 |
| mef.fact_devengado_mensual | fact_devengado_mensual_funcion_key_fkey | mef.dim_funcion | Si | 0 |
| mef.fact_devengado_mensual | fact_devengado_mensual_hecho_anual_key_anio_key_entidad_ke_fkey | auditoria.serie_seleccionada | Si | 0 |
| mef.fact_devengado_mensual | fact_devengado_mensual_intervencion_key_fkey | mef.dim_intervencion | Si | 0 |
| mef.fact_devengado_mensual | fact_devengado_mensual_meta_detalle_key_anio_key_entidad_k_fkey | mef.dim_meta_detallada | Si | 0 |
| mef.fact_devengado_mensual | fact_devengado_mensual_periodo_key_anio_key_fkey | mef.dim_periodo_mensual | Si | 0 |
| mef.fact_ejecucion_presupuestaria_anual | fact_ejecucion_presupuestaria_anual_anio_key_fkey | mef.dim_anio | Si | 0 |
| mef.fact_ejecucion_presupuestaria_anual | fact_ejecucion_presupuestaria_anual_clasificador_gasto_key_fkey | mef.dim_clasificador_gasto | Si | 0 |
| mef.fact_ejecucion_presupuestaria_anual | fact_ejecucion_presupuestaria_anual_entidad_key_fkey | mef.dim_entidad | Si | 0 |
| mef.fact_ejecucion_presupuestaria_anual | fact_ejecucion_presupuestaria_anual_financiamiento_key_fkey | mef.dim_financiamiento | Si | 0 |
| mef.fact_ejecucion_presupuestaria_anual | fact_ejecucion_presupuestaria_anual_funcion_key_fkey | mef.dim_funcion | Si | 0 |
| mef.fact_ejecucion_presupuestaria_anual | fact_ejecucion_presupuestaria_anual_intervencion_key_fkey | mef.dim_intervencion | Si | 0 |
| mef.fact_ejecucion_presupuestaria_anual | fact_ejecucion_presupuestaria_anual_meta_key_fkey | mef.dim_meta | Si | 0 |

**22/22 FK validadas, cero huerfanos.** Se verificaron las restricciones y sus triggers habilitados, y se ejecutaron antiuniones explicitas sobre todas las columnas de cada relacion, incluidas las compuestas. Las definiciones completas estan en POSTERIORES.json.

## 5. Conciliaciones monetarias

- 28 sumas anuales (siete medidas por cuatro anios) exactas contra el manifiesto.
- 48 sumas mensuales exactas contra el lote.
- 12.500 series con doce periodos distintos y suma mensual exactamente igual al devengado de su observacion anual.
- Las 150.000 filas mensuales se compararon columna por columna con el CSV preparado, ademas de conciliar totales.
- Se conservaron 324 importes mensuales negativos y 124.976 ceros. No se aplicaron ABS, recortes, redondeos correctivos ni eliminaciones.
- Cero granos mensuales duplicados; 3.125 series y 37.500 hechos mensuales por ejercicio.

| Anio | Series | Hechos mensuales | Devengado cohorte anual | Suma mensual | Diferencia |
|---|---:|---:|---:|---:|---:|
| 2022 | 3.125 | 37.500 | 229036151.01 | 229036151.01 | 0.00 |
| 2023 | 3.125 | 37.500 | 305679174.74 | 305679174.74 | 0.00 |
| 2024 | 3.125 | 37.500 | 328251572.29 | 328251572.29 | 0.00 |
| 2025 | 3.125 | 37.500 | 269847719.34 | 269847719.34 | 0.00 |

Importes en soles corrientes, punto decimal. Son sumas de la cohorte seleccionada, no cifras nacionales.

## 6. Comparacion de integridad y protecciones

- Las ocho tablas originales se cotejaron por cada fila y atributo antes de crear y despues de cargar V2. Ambas comparaciones fueron exactas.
- Las ocho tablas copiadas en V2 tambien coinciden integramente con ese snapshot, incluidas claves sustitutas, nombres, JSON e importes.
- La base original conserva 150.000 hechos unicos, siete FK validas y cero huerfanos. Todas las conexiones al origen fueron de solo lectura.
- Los 63 hashes de ENTREGA_FINAL coinciden despues de la carga. Los ocho CSV anuales y el lote mensual conservan sus hashes.
- Identidad, imagen, fecha de inicio, contador de reinicios y montajes de postgres-db iguales antes y despues. No se crearon ni eliminaron contenedores o volumenes.
- No se modificaron respaldos, CSV originales, dashboard, credenciales, rama Git ni repositorio. No se hizo commit o push.

## 7. Tiempos y recursos medidos

- Invocacion completa del cargador: 34.217 segundos, incluyendo revalidacion local, cotejo del origen, creacion, DDL, COPY, controles y COMMIT. No es tiempo puro de COPY.
- Pico RSS medido de cliente Python mas orquestador: 400.25 MiB. No incluye la memoria del servidor PostgreSQL.
- Muestra Docker registrada a 2026-10-25T08:59:39.007095+00:00: 293.3MiB / 7.57GiB de memoria y 0.04% de CPU, para el contenedor completo.
- Aclaracion de metrica: el archivo RECURSOS_CONTENEDOR_DURANTE.json conserva el nombre/etiqueta de fase solicitado al lanzar la consulta, pero su timestamp es posterior al COMMIT. Es una muestra posterior, **no un pico durante la carga**. No se dispone de un pico historico atribuible exclusivamente al servidor V2.
- El pico del cliente estuvo por debajo de 2 GiB. Los datos se transfirieron mediante COPY y cursores por bloques, sin cargar las fuentes nacionales ni repetir su auditoria.

## 8. Pruebas, incidencias y limites

- Diez pruebas unitarias satisfactorias antes y despues de cargar; muestreo determinista, cuotas, decimales, bloqueos de destino y COPY de cadenas vacias. Evidencia final: verificacion_1792919109064949100.json.
- Sintaxis Python y 28 sentencias SQL comprobadas. Los dos scripts DDL y las tres consultas analiticas se ejecutaron realmente en V2 sin errores.
- Las consultas devolvieron cuatro resultados anuales conciliados, 48 periodos y doce grupos anio/nivel de gobierno.
- Se completo la matriz bus antes de cargar; no fue necesario corregir el esquema ni modificar el lote. No hubo fallos de creacion o carga ni reconstrucciones automaticas.
- DDL, COPY y controles se confirmaron en una sola transaccion de V2. La creacion de la base fue una operacion separada. No se provoco deliberadamente un fallo ni se certifica una prueba de recuperacion/rollback por inyeccion de errores.
- Los JSON de validacion local con postgres_executed=false se refieren solo al verificador local; PREVIAS, recibo de carga y POSTERIORES acreditan las operaciones reales de esta fase.

**Observacion de calidad para el dashboard:** la ejecucion agregada de la cohorte es superior a 100 % en 2022-2024. No es un fallo de conciliacion: el anual y el mensual coinciden exactamente. La fuente incluye series con PIM cero y devengado positivo. No se ha certificado la causa de ese estado; no debe inferirse a partir del cociente.

| Anio | Ejecucion agregada de cohorte | Series PIM cero y devengado positivo | Series con PIM negativo |
|---|---:|---:|---:|
| 2022 | 104.16 % | 1048 | 0 |
| 2023 | 106.59 % | 1042 | 0 |
| 2024 | 109.24 % | 990 | 0 |
| 2025 | 81.27 % | 982 | 0 |

El cociente usa SUM(devengado)/SUM(PIM) con PIM agregado positivo. No se promedian porcentajes individuales ni se trunca a 100 %. OBSERVACION_EJECUCION.json cuantifica las series; no aporta una explicacion causal.

## 9. Recomendaciones para Streamlit, sin implementarlas

1. Desarrollar una copia V2 del dashboard con conexion de solo lectura a la nueva base; conservar la version original.
2. Ofrecer vistas Anual original, Cohorte comparable y Mensual, rotulando su cobertura. No combinar todos los hechos anuales con solo el subconjunto mensual para comparaciones.
3. Agregar filtros conformados de anio/mes, entidad, funcion, financiamiento y clasificador; usar periodo para estacionalidad y acumulados, manteniendo negativos.
4. Mantener PIA/PIM como presupuesto anual de cohorte, sin repetirlos por mes. Mostrar por separado el importe de las series con PIM cero y devengado positivo y advertir sobre cocientes mayores a 100 %.
5. Reutilizar la paleta y las seis secciones existentes mediante una ampliacion separada; consultas parametrizadas y agregaciones SQL, no DataFrames de 300.000 hechos.
6. Conservar las advertencias de muestra, composicion variable y fecha de corte de ejecucion 2025 no certificada. Los ceros mensuales son observaciones de fuente; no interpretarlos automaticamente como ausencia de actividad institucional.

## 10. Evidencias y estado operativo

Evidencias de esta ejecucion: evidencias/implementacion_20261025T084833Z/. Incluyen previas, salida/recursos de carga, posteriores, detalle de FK, observacion de ejecucion y muestra del contenedor. El recibo committed=true se conserva en evidencias/carga_20261025T085755901626Z.json.

Los documentos y el manifiesto de preparacion anteriores permanecen intactos como registro de la fase previa; sus frases sobre carga pendiente describen ese momento. Este informe acredita el estado implementado actual.

**Dictamen:** implementacion V2 completada, independiente y validada. No modificar el dashboard ni publicar V2 hasta recibir nuevas instrucciones. No se ha generado un respaldo nuevo de V2 en esta fase.
