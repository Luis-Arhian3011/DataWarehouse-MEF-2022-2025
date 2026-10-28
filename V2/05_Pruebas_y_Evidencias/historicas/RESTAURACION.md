# Informe de prueba de restauracion completa ? MEF V2

**Resultado: RESTAURACION COMPLETA SATISFACTORIA Y VALIDADA.**

| Campo | Resultado |
|---|---|
| Base original de referencia | dw_mef_2022_2025_v2, sin modificaciones |
| Base temporal restaurada | dw_mef_v2_prueba_restauracion |
| Servidor | postgres-db, PostgreSQL 15.19 |
| Finalizacion America/Lima | 2026-10-28T12:23:05.764013-05:00 |
| Estado del destino | Conservado; no se eliminara sin autorizacion |
| Tiempo de pg_restore | 7.288 segundos |
| Procedimiento completo | 65.62 segundos |
| Tamano de base restaurada | 254270823 bytes (242.49 MiB) |

## 1. Verificaciones previas

- Se leyo la guia de restauracion generada con el respaldo.
- Docker y postgres-db activos, identidad de sistema PostgreSQL 7697394465128882215 coincidente por TCP.
- La base temporal no existia; se comprobo otra vez inmediatamente antes de crearla. No se sobrescribio ninguna base.
- Respaldo de 22.393.234 bytes presente, SHA-256 coincidente con el registrado:

    3da3bafb255c3fdf69884417c72f9dccfc3647422b21a8aa05af9c5682499b96

- Espacio libre del host antes de probar: 333.99 GiB. Disponible logico en almacenamiento del contenedor: 951.55 GiB. Ambos superaban la reserva exigida de 2 GiB o tres veces el tamano de la base original.
- El V2 original paso los controles contra el lote preparado y se firmaron todas sus tablas. El modelo anual original tambien se cotejo en solo lectura con su snapshot protegido.

## 2. Aislamiento y restauracion ejecutada

La guia antigua proponia un servidor Docker nuevo y otro nombre de destino. La autorizacion actual especifico exclusivamente dw_mef_v2_prueba_restauracion y prohibio modificar contenedores. Se utilizo una base distinta, vacia, creada con TEMPLATE template0 dentro del servidor existente. No se crearon contenedores, redes o volumenes. Esta es una prueba de aislamiento logico entre bases, no una prueba en un servidor ni equipo independiente.

Se ejecuto exclusivamente CREATE DATABASE dw_mef_v2_prueba_restauracion. Se verifico que no tuviera objetos de usuario y se transmitio el dump binario por stdin a pg_restore, sin convertirlo a texto ni copiarlo al contenedor.

Opciones reales:

    pg_restore -U luchito --dbname=dw_mef_v2_prueba_restauracion --no-owner --no-privileges --exit-on-error --single-transaction --verbose

Codigo de salida: 0. La restauracion y sus objetos/datos se confirmaron en una unica transaccion. No se utilizaron --clean ni --create. No hubo reintentos destructivos.

## 3. Tablas y datos restaurados

| Tabla | Filas | Coincidencia completa con V2 |
|---|---:|---|
| auditoria.serie_seleccionada | 12500 | Si |
| mef.dim_anio | 4 | Si |
| mef.dim_clasificador_gasto | 476 | Si |
| mef.dim_entidad | 2898 | Si |
| mef.dim_financiamiento | 114 | Si |
| mef.dim_funcion | 356 | Si |
| mef.dim_intervencion | 18654 | Si |
| mef.dim_meta | 121305 | Si |
| mef.dim_meta_detallada | 12477 | Si |
| mef.dim_periodo_mensual | 48 | Si |
| mef.fact_devengado_mensual | 150000 | Si |
| mef.fact_ejecucion_presupuestaria_anual | 150000 | Si |

**Total: 12 tablas y 468.832 registros: nueve dimensiones, dos hechos con 300.000 registros y una tabla tecnica de 12.500 series.**

## 4. Validacion de integridad y medidas

| Control | Resultado |
|---|---|
| Hechos anuales | 150.000 |
| Hechos mensuales | 150.000 |
| Series conciliadas | 12.500, cada una con doce periodos distintos |
| Periodos mensuales | 48 |
| Cuotas por ejercicio 2022?2025 | 3.125 series y 37.500 meses |
| FK validas y habilitadas | 22 de 22 |
| Referencias huerfanas | 0, mediante antiuniones explicitas para cada FK |
| Granos mensuales distintos | 150.000; sin duplicados |
| Conciliaciones anuales | 28 sumas exactas contra los metadatos del respaldo |
| Conciliaciones mensuales | 48 sumas exactas contra los metadatos del respaldo |
| Suma de meses por serie frente al anual | 12.500 series sin diferencias |
| Meses con importe negativo | 324, conservados |
| Meses con importe cero | 124.976, conservados |

Las FK compuestas se comprobaron con todas sus columnas; no se redujeron a una sola clave. Tambien se comprobaron convalidated y la ausencia de triggers internos deshabilitados.

| Tabla hija | Restriccion | Validada | Huerfanos |
|---|---|---|---:|
| auditoria.serie_seleccionada | serie_seleccionada_hecho_anual_key_anio_key_entidad_key_in_fkey | Si | 0 |
| auditoria.serie_seleccionada | serie_seleccionada_meta_detalle_key_anio_key_entidad_key_i_fkey | Si | 0 |
| mef.dim_meta_detallada | dim_meta_detallada_anio_key_fkey | Si | 0 |
| mef.dim_meta_detallada | dim_meta_detallada_entidad_key_fkey | Si | 0 |
| mef.dim_meta_detallada | dim_meta_detallada_funcion_key_fkey | Si | 0 |
| mef.dim_meta_detallada | dim_meta_detallada_intervencion_key_fkey | Si | 0 |
| mef.dim_periodo_mensual | dim_periodo_mensual_anio_key_fkey | Si | 0 |
| mef.fact_devengado_mensual | fact_devengado_mensual_clasificador_gasto_key_fkey | Si | 0 |
| mef.fact_devengado_mensual | fact_devengado_mensual_entidad_key_fkey | Si | 0 |
| mef.fact_devengado_mensual | fact_devengado_mensual_financiamiento_key_fkey | Si | 0 |
| mef.fact_devengado_mensual | fact_devengado_mensual_funcion_key_fkey | Si | 0 |
| mef.fact_devengado_mensual | fact_devengado_mensual_hecho_anual_key_anio_key_entidad_ke_fkey | Si | 0 |
| mef.fact_devengado_mensual | fact_devengado_mensual_intervencion_key_fkey | Si | 0 |
| mef.fact_devengado_mensual | fact_devengado_mensual_meta_detalle_key_anio_key_entidad_k_fkey | Si | 0 |
| mef.fact_devengado_mensual | fact_devengado_mensual_periodo_key_anio_key_fkey | Si | 0 |
| mef.fact_ejecucion_presupuestaria_anual | fact_ejecucion_presupuestaria_anual_anio_key_fkey | Si | 0 |
| mef.fact_ejecucion_presupuestaria_anual | fact_ejecucion_presupuestaria_anual_clasificador_gasto_key_fkey | Si | 0 |
| mef.fact_ejecucion_presupuestaria_anual | fact_ejecucion_presupuestaria_anual_entidad_key_fkey | Si | 0 |
| mef.fact_ejecucion_presupuestaria_anual | fact_ejecucion_presupuestaria_anual_financiamiento_key_fkey | Si | 0 |
| mef.fact_ejecucion_presupuestaria_anual | fact_ejecucion_presupuestaria_anual_funcion_key_fkey | Si | 0 |
| mef.fact_ejecucion_presupuestaria_anual | fact_ejecucion_presupuestaria_anual_intervencion_key_fkey | Si | 0 |
| mef.fact_ejecucion_presupuestaria_anual | fact_ejecucion_presupuestaria_anual_meta_key_fkey | Si | 0 |

## 5. Comparacion completa con el V2 original

No se compararon solo conteos o totales. Se leyeron todas las columnas de todas las filas mediante cursores por bloques, ordenadas por la PK real de cada tabla. Cada fila se serializo de forma canonica, con Decimal como cadena exacta, y se calculo SHA-256 incremental por tabla. Los doce hashes y conteos coinciden. El metodo criptografico hace despreciable el riesgo de colision; no es una demostracion matematica independiente de SHA-256.

| Objeto comparado | Cantidad | Resultado |
|---|---:|---|
| Tablas y sus contenidos completos | 12 | Identicos |
| Definiciones de columnas | 135 | Identicas |
| Restricciones PK/FK/UNIQUE/CHECK | 81 | Identicas |
| Indices | 37 | Identicos |
| Vistas | 2 | Identicas |
| Secuencias y estados last_value/is_called | 9 | Identicos |

No se detectaron diferencias logicas de estructura o datos. El tamano fisico de una base reconstruida no debe usarse como comparacion de igualdad byte a byte del almacenamiento. Se registra el tamano restaurado, sin exigir que coincida con la distribucion fisica de la base original.

**Alcance de propietarios/permisos:** --no-owner y --no-privileges permiten restaurar sin depender de los roles o ACL archivados. La prueba valida datos, restricciones, indices, vistas y secuencias; no certifica equivalencia de ACL, roles globales o propiedades de base que no se aplican al omitir --create.

## 6. Proteccion del proyecto

- V2 original firmado antes y despues: los doce contenidos y sus definiciones permanecen identicos.
- dw_mef_2022_2025 cotejado antes y despues, siempre en solo lectura: ocho tablas coincidentes con el snapshot, 150.000 hechos unicos y siete FK sin huerfanos.
- 63 hashes protegidos de ENTREGA_FINAL coinciden.
- Respaldo .dump conserva exactamente su SHA-256; no se modificaron los archivos del respaldo.
- Identidad, imagen, inicio, reinicios y montajes de postgres-db iguales antes y despues.
- No se ejecutaron DROP DATABASE, DELETE, TRUNCATE, reinicios, cambios de Docker, eliminacion de archivos o volumenes, ETL, commits ni push.

## 7. Tiempo y recursos consumidos

- pg_restore: 7.288 segundos de tiempo transcurrido.
- Proceso completo, incluidas verificaciones y firmas: 65.62 segundos.
- Pico RSS observado de cliente Python y procesos hijo: 67.25 MiB. No se excedio el limite preventivo de 1,95 GiB.
- 30 muestras del cgroup Docker: pico observado 970.02 MiB de memory.current. Incluye cache y memoria compartida por todo el contenedor; no es memoria exclusiva de la base temporal.
- Incremento de CPU del contenedor entre muestras inmediatamente anterior y posterior a pg_restore: 7.85 segundos de CPU. Incluye cualquier otra actividad concurrente del contenedor.
- No se cargaron los CSV nacionales en memoria ni se generaron copias adicionales del dump.

## 8. Problemas encontrados y soluciones

No hubo errores de restauracion ni diferencias de datos que requirieran correcciones. La adaptacion respecto a la guia fue de alcance: destino con el nombre autorizado y aislamiento por base dentro del servidor existente, sin crear infraestructura Docker.

Los ceros, negativos y estados presupuestarios de la fuente se conservaron; esta prueba de recuperacion no cambia las advertencias analiticas del modelo ni certifica la fecha de corte 2025.

## 9. Evidencias y conclusion

- 01_PREVIAS.json: origen, ausencia del destino, espacio, respaldo y firmas previas.
- 02_BASE_CREADA.json: registro de la unica base creada.
- 03_RESTAURACION.json y pg_restore_salida.txt: comando, codigo 0 y tiempo.
- 04_VALIDACIONES.json: resultados de todas las FK, firmas completas, estructura y protecciones posteriores.
- 05_RECURSOS.json: memoria de cliente y muestras del contenedor.
- RESUMEN_FINAL.json: dictamen consolidado.

**El respaldo ya tiene una prueba real de restauracion completa y satisfactoria en una base nueva del mismo servidor PostgreSQL. No se ha probado en otra computadora o version mayor.**

**La base dw_mef_v2_prueba_restauracion permanece disponible. No se eliminara hasta recibir autorizacion expresa.**
