> Documento del diseno validado. Las referencias a una carga futura describen la fase previa; el estado implementado y la recuperacion real figuran en el README y los informes historicos de esta entrega.

# Modelo dimensional V2 y reglas verificables

## Granularidades

**Anual:** fila original por año y combinación completa de entidad, intervención, función, meta contextual, financiamiento y clasificador; el año completa las siete dimensiones. Se conserva la unicidad original y sus 150.000 hechos. KEY_VALUE por sí solo no identifica una fila física del comparativo ancho; la identidad anual utiliza año y contexto, además de las restricciones heredadas.

**Mensual:** mes y combinación de entidad, intervención, función, meta detallada, financiamiento y clasificador. La meta detallada incorpora año, SEC_FUNC, FINALIDAD, META y DEPARTAMENTO_META con entidad/intervención/función completas. No se sustituye esta clave por SEC_FUNC aislado.

Solo devengado pertenece al hecho mensual. PIA, PIM y otras etapas siguen en el anual. Las observaciones mensuales no son porcentajes ni acumulados recalculados: son los doce campos MONTO_DEVENGADO_ENERO…DICIEMBRE de la fuente auditada.

## Correspondencias de dimensiones

| Dimensión | Columnas originales / clave natural |
|---|---|
| Año | ANO_EJE |
| Entidad | NIVEL_GOBIERNO, SECTOR, PLIEGO, EJECUTORA, SEC_EJEC, DEPARTAMENTO_EJECUTORA, PROVINCIA_EJECUTORA, DISTRITO_EJECUTORA |
| Intervención | PROGRAMA_PPTO, TIPO_ACT_PROY, PRODUCTO_PROYECTO, ACTIVIDAD_ACCION_OBRA |
| Función | FUNCION, DIVISION_FUNCIONAL, GRUPO_FUNCIONAL |
| Meta original | Año + entidad + intervención + función + META, DEPARTAMENTO_META, META_NOMBRE |
| Financiamiento | FUENTE_FINANCIAMIENTO, RUBRO, TIPO_RECURSO mediante correspondencia auditada de roles |
| Clasificador | CATEGORIA_GASTO, TIPO_TRANSACCION, GENERICA, SUBGENERICA, SUBGENERICA_DET, ESPECIFICA, ESPECIFICA_DET |
| Período mensual nuevo | ANO_EJE + ordinal 1…12 derivado del nombre exacto del campo mensual |
| Meta detallada nueva | Año + entidad + intervención + función + SEC_FUNC, FINALIDAD, META, DEPARTAMENTO_META |

TIPO_ACT_PROY: ACTIVIDAD→3; PROYECTO→2, correspondencia ya auditada. Claves como cadenas: no perder ceros iniciales. Los nombres son atributos observados; no se inventan vigencias históricas.

La fuente mensual y los campos físicos heredados de financiamiento tienen roles invertidos. Se conserva la dimensión física original y su SK. La vista v_financiamiento_conformado expone FUENTE correcta desde rubro heredado y RUBRO correcto desde fuente heredada, incluyendo nombres. No se unen fuentes por igualdad literal de columnas homónimas. El muestreo usa el orden canónico MEF correcto.

Las seis dimensiones distintas de año se copian sin asignar nuevamente claves sustitutas. dim_meta se mantiene para anual; el mensual usa dim_meta_detallada. La tabla técnica conserva la meta original para asegurar el linaje. No existe una relación analítica muchos-a-muchos entre hechos.

## Relaciones definitivas

Siete FK del hecho anual a las siete dimensiones originales. En la copia V2 se agrega una unicidad contextual del hecho anual para poder referenciarlo sin modificar los datos.

- dim_periodo_mensual.anio_key → dim_anio.
- dim_meta_detallada → dim_anio, dim_entidad, dim_intervencion, dim_funcion.
- auditoria.serie_seleccionada → hecho anual por PK más siete claves de contexto, y → meta detallada por SK más año/entidad/intervención/función.
- fact_devengado_mensual → entidad, intervención, función, financiamiento y clasificador mediante cinco FK simples.
- fact_devengado_mensual → período por (periodo_key,anio_key).
- fact_devengado_mensual → meta detallada por (meta_detalle_key,anio_key,entidad_key,intervencion_key,funcion_key).
- fact_devengado_mensual → tabla técnica por (hecho_anual_key,anio_key,entidad_key,intervencion_key,funcion_key,meta_detalle_key,financiamiento_key,clasificador_gasto_key).

Total propuesto: 22 FK. Las restricciones compuestas impiden mezclar entidades o años válidos pero incompatibles. La tabla técnica no contiene importes y no se usa como una medida ni una tercera tabla de hechos. Sus columnas de población/cuota son metadatos del diseño muestral.

## Selección reproducible exacta

1. Partir exclusivamente de cohorte_disponible_YYYY.csv, selladas por la auditoría: 37.334 / 37.297 / 37.330 / 37.246 series elegibles. Excluyen las 136 discrepancias y todos los casos ambiguos o repetidos pendientes.
2. Vincular cada hecho con referencia_anual.parquet, cuyo hash está fijado en el preparador. El identificador de hash es JSON canónico de 29 componentes: año + entidad(8) + intervención(4) + función(3) + META + DEPARTAMENTO_META + financiamiento(3) + clasificador(7) + META_NOMBRE. Financiamiento usa roles MEF.
3. Estrato por año y entidad natural completa de ocho códigos. Entidades elegibles: 2.845 / 2.844 / 2.845 / 2.862. Asignar una serie por entidad.
4. R=3125−cantidad_entidades. Para cada entidad h, peso Nh−1. Repartir R proporcionalmente por división entera y restos mayores. Empates por JSON canónico de entidad, orden lexicográfico. No usar porcentajes flotantes.
5. SHA-256 UTF-8 de semilla + salto de línea + JSON canónico, sin espacios y con Unicode literal. Semilla: MEF_V2_DEVENGADO_2022_2025_V1. Elegir los primeros qh por hash; empate por clave canónica. Ni número físico de fila ni SK intervienen en la prioridad.
6. Conservar los doce meses, incluyendo ceros y negativos. No muestrear celdas por separado. IDs de salida estables en orden año/clave canónica/mes.
7. Verificar invariancia de selección al invertir el orden de candidatos; guardar población/cuota/hash y grano mensual original para trazabilidad.

La cobertura mínima por entidad favorece entidades pequeñas; no es una muestra autoponderada ni una representación nacional. No se garantiza cobertura de todos los clasificadores. La población de referencia es la intersección conciliada con los 150.000 hechos anuales.

## Controles y tratamientos

- Importes: Decimal exacto y NUMERIC(20,2). Rechazar nulos, no finitos, más de dos decimales y desbordamientos. No redondear para hacer coincidir. No usar ABS.
- Gobiernos locales: sector/pliego vacíos permitidos; son parte de la identidad observada. No rechazar el nivel M ni sustituirlo por nacional. COPY conserva cadenas vacías mediante FORCE_NOT_NULL.
- Nombre de meta ausente: cadena vacía observada; no fabricar un código. SEC_FUNC/FINALIDAD/META/DEPARTAMENTO_META siguen siendo obligatorios.
- Duplicados o ambigüedad: excluir a todos los miembros no resueltos antes del muestreo, nunca elegir arbitrariamente el primero ni sumarlos.
- Diferencia histórica 59.000: evidencia poblacional identificó una única fila activa 2024 dentro de tres filas físicas con igual KEY_VALUE del comparativo; seis importes coinciden. No existe pérdida demostrada de 59.000 en el mensual. No confundir repetición multianual física con duplicado anual.
- Cada serie seleccionada debe tener una sola fila fuente, seis importes anuales comunes coincidentes y suma exacta de doce meses igual al devengado del hecho anual.
- Control local: unicidad de PK/granos, contexto, pertenencia a dimensiones, doce períodos distintos, 28 controles del anual y 48 controles mensuales.
- Control PostgreSQL futuro: restricciones habilitadas y validadas, 22 FK, conteos, cuotas, conciliación por serie, 28+48 controles y comparación completa de las ocho tablas del snapshot anual antes y después.
- JOIN directo entre hechos a nivel fila multiplica medidas. Las consultas entregadas agregan primero cada hecho por año/cohorte y luego unen resultados de cardinalidad uno-a-uno.

## Linaje y límites de evidencia

El Parquet 2022 conserva SHA-256 verificado en la auditoría histórica. Para 2023–2025, los Parquet temporales no tenían un hash histórico sellado: se comprobaron tamaño, número de filas y metadatos de la fuente original sin cambios; se registró su hash actual y se reconciliaron todas las series seleccionadas. Eso no equivale a revalidar criptográficamente cada celda de toda la población original. No se realizó una nueva lectura completa de los CSV.

Los controles monetarios fuente/anual y suma de meses detectan diferencias de total, pero por sí solos no prueban la asignación temporal de cada céntimo; se reutiliza la certificación de conciliación mensual poblacional existente. Mantener las evidencias y no modificar sus Parquet.

La validación de snapshot local no demuestra por sí sola el estado actual de PostgreSQL. El cargador futuro cotejará la base original en solo lectura antes de crear V2. La prueba real de DDL/carga/rollback y rendimiento SQL queda pendiente de aprobación.
