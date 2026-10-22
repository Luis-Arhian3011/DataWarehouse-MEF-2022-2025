> Perfil GitHub: los CSV preparados citados aqu? permanecen en la entrega local, pero se excluyen del repositorio. El clon permite recuperar el snapshot desde el respaldo incluido; no necesita el CSV nacional ni el ETL.

# Fuente y niveles de reproducibilidad

## Archivo de origen

Ubicación conservada fuera de la entrega: C:\DataWarehouse_MEF\datos\comparativo_gastos_2022_2026.csv.

Procedencia declarada del conjunto entregado al proyecto: Ministerio de Economía y Finanzas del Perú. No se conservó una URL exacta de descarga ni una fecha de corte certificada; no se inventan esos metadatos. Las referencias legales del documento de modelo contrastan PIA 2025, pero no sustituyen la procedencia del CSV.

8.468.325 filas, 88 columnas y 8.978.982.720 bytes; UTF-8 con BOM. SHA-256 registrado en la auditoría y manifiesto:

```text
f1d5e01a2d532cbe02694b65496bd322b4e9bff62d6a95c362e2873b8979401c
```

La fuente contiene siete medidas por cada año 2022–2026. Solo se utilizan 2022–2025. Las columnas 2025/2026 coinciden; su causa no se determinó. 2025 es una instantánea con PIA contrastado; no se certifica el corte de ejecución.

No se duplican esos aproximadamente 9 GB en la entrega. La preparación de ENTREGA_FINAL no volvió a procesar ni calcular la huella de ese CSV: reutiliza la evidencia de auditoría previa.

## Flujo utilizado

CSV → normalización de códigos y auditoría en disco → anualización de siete medidas → exclusión documentada de granos ambiguos → cuotas y selección por hash → enriquecimiento dimensional → ocho CSV de carga → PostgreSQL → agregaciones SQL → dashboard.

La precisión se valida con Decimal/DECIMAL, sin float monetario. Los importes negativos no se eliminan. Un grupo anual con siete ceros no aporta importes; la exclusión no cambia los totales. Los gobiernos locales no se descartan por sector/pliego vacío.

Grano: año y combinación completa de dimensiones. La identidad de meta incluye META_NOMBRE y su contexto. Los 11.658 granos ambiguos, 23.316 filas de 2022–2025, no se fusionaron ni sumaron arbitrariamente.

## Selección exacta

Semilla: MEF_KIMBALL_2022_2025_V1. Objetivo: 37.500 hechos por año.

Estratos: año, NIVEL_GOBIERNO y SEC_EJEC. Para cada año, H estratos y N elegibles: uno por estrato, resto proporcional a N_h−1 mediante cociente entero y restos mayores, con desempate por nivel y SEC_EJEC. Dentro del estrato se ordena por SHA-256(semilla + JSON([año_como_texto, grain_json])) y grain_json. Se toman las primeras cuota filas. Se comprobó igualdad al invertir el orden de entrada.

Los estratos no son las claves naturales completas de dim_entidad; la dimensión conserva la identidad compuesta y las denominaciones observadas. ../05_Evidencias/cuotas_seleccion.csv contiene la asignación auditada. Los hechos incluidos conservan hash, cuota y población por estrato.

## Qué se reproduce desde la entrega

1. Restaurar el snapshot con el respaldo incluido, en una instalación independiente.
2. Alternativamente, cargar exactamente los mismos CSV preparados con el ETL original adaptado a rutas relativas; sus ocho hashes y 28 sumas sirven de controles.
3. Ejecutar dashboard, consultas y pruebas sobre esa base.

Los puntos 1 y 2 son rutas alternativas. Ninguno se ejecutó al preparar esta entrega. Las pruebas de esta copia utilizan exclusivamente lecturas de la base existente.

## Volver al CSV completo

El ETL de carga incluido no lee directamente el CSV nacional: sus entradas son los ocho CSV preparados. Para regenerarlos desde la fuente se necesita repetir la auditoría y selección previas en un workspace separado, con el mismo archivo original y huella, almacenamiento temporal en disco y DuckDB 2.0.0, usado en la auditoría.

En el proyecto original se conservan estos artefactos y scripts:
- analisis/validacion_final_20261021_162020: normalización, auditoría, claves y raw en temporal/auditoria.duckdb.
- analisis/validar_2025_y_seleccionar.py y completar_validacion_2022_2025.py: selección y comprobación de 2022–2025.
- analisis/validacion_2022_2025_v1: resultado, cuotas y selección Parquet, además de temporal/revision.duckdb.
- analisis/preparar_postgresql_2022_2025.py: enriquece la selección y exporta los ocho CSV finales.

No se redistribuyen los temporales, scripts de reanudación ni una segunda implementación histórica para simular una extracción independiente que no se ha probado. Si se desea reauditar el CSV, se debe preservar el original y preparar un workspace nuevo, adaptar las salidas y reconstruir las dependencias de auditoría antes de exportar. No ejecutar esos scripts sobre sus salidas existentes; contienen protecciones contra sobrescritura.

**Límite explícito:** esta entrega es autosuficiente para recuperar o cargar el snapshot validado y demostrarlo; no automatiza desde cero una nueva auditoría del CSV completo. Se mantiene esa etapa externa y documentada en lugar de añadir un ETL nuevo no ejecutado.
