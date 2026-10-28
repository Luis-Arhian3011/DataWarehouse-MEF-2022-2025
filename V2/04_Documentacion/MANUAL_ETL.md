# ETL: carga preparada y reconstrucción de fuentes

## A. Recuperación desde respaldo

No ejecuta ETL. Es la vía rápida descrita en el README: crea una base nueva y restaura los 300.000 hechos. No requiere los CSV nacionales.

## B. Carga de los doce CSV preparados

Los ocho CSV anuales preservan el modelo y las claves originales. Los cuatro CSV nuevos contienen período, meta detallada, linaje de series y hecho mensual. Todos están incluidos con hashes y manifiestos.

Validación local, sin PostgreSQL:

    .\.venv\Scripts\python.exe -B 02_ETL_Python\src\validar_local.py 02_ETL_Python\datos_preparados\mensual

Carga futura autorizada en destino ausente del entorno Compose:

    .\.venv\Scripts\python.exe -B scripts\proyecto.py cargar-preparados --autorizar

El cargador portable conserva la lógica SQL/COPY, validaciones, claves y precisión; cambia rutas y omite la conexión a la base anual antigua, sustituida por validación de los CSV incluidos. No necesita tener dw_mef_2022_2025 en el servidor nuevo.

DDL, COPY y controles se hacen en una sola transacción después de crear la base. Si hay un error, rollback y conservación de la base nueva. Sin limpieza automática. Esta carga y la restauración son vías alternativas para el mismo destino; no se ejecutan una tras otra.

## C. Reconstruir el mensual cuando estén disponibles los CSV

Entradas externas exactas:

- 2022-Gasto-Devengado.csv
- 2023-Gasto-Devengado.csv
- 2024-Gasto-Devengado.csv
- 2025-Gasto-Devengado-Mensual.csv

Son aproximadamente 10,9 GB en total. No están incluidos ni se descargan. Los hashes esperados se conservan en insumos_auditoria/evidencias/resultado_YYYY.json. Una descarga de otra fecha puede diferir y exige reevaluación; el programa no fuerza la conciliación.

También se requieren el snapshot anual y la referencia compacta, ambos incluidos. La referencia Parquet de 7,7 MB es un insumo seleccionado, no un temporal de DuckDB ni un CSV nacional.

1. Colocar los CSV fuera de la entrega y configurar MEF_FUENTES_DIR en una sesión privada, por ejemplo con Resolve-Path sobre su carpeta local.
2. Ejecutar primero un piloto de 100.000 filas de 2022, con una carpeta de salida que no exista:

       .\.venv\Scripts\python.exe -B 02_ETL_Python\src\auditar_fuentes.py --fuentes $env:MEF_FUENTES_DIR --salida 02_ETL_Python\trabajo\piloto --piloto 100000 --autorizar-lectura

3. Revisar controles, tiempo y recursos. El piloto no permite crear una muestra definitiva.
4. Solo después de aprobar su costo, procesar los ejercicios secuencialmente:

       .\.venv\Scripts\python.exe -B 02_ETL_Python\src\auditar_fuentes.py --fuentes $env:MEF_FUENTES_DIR --salida 02_ETL_Python\trabajo\auditoria --autorizar-lectura

5. Configurar MEF_AUDIT_DIR con Resolve-Path a 02_ETL_Python/trabajo/auditoria, y preparar en un destino nuevo:

       .\.venv\Scripts\python.exe -B 02_ETL_Python\src\ejecutar_controlado.py --salida 02_ETL_Python\datos_preparados\recalculado

El adaptador reutiliza las reglas reales de calidad, duplicados y correspondencia compacta. Contrasta el hash del CSV y el conjunto de padres elegibles con la cohorte auditada entregada. El muestreo usa la semilla MEF_V2_DEVENGADO_2022_2025_V1, 3.125 series por año, cuotas enteras por entidad y doce meses completos. Excluye discrepancias y claves ambiguas; no las deduplica arbitrariamente.

Límites del auditor: DuckDB 768 MiB, dos hilos, máximo aproximado de 1,95 GiB RSS del grupo y 40 GiB de trabajo temporal. Exige al menos 10 GiB libres al empezar y se detiene con menos de 1 GiB. Guarda comprobaciones por ejercicio. El preparador final limita sus propios temporales a 1 GiB. No subir automáticamente límites ante errores.

**No se ejecutó de nuevo este procesamiento costoso durante el empaquetado.** Se adaptaron rutas y entradas/salidas; la lógica fuente proviene de la auditoría exitosa. Su ejecución integral portable continúa pendiente.

## Límite de reconstrucción anual

El comparativo original comparativo_gastos_2022_2026.csv, aproximadamente 8,98 GB, permanece fuera de la entrega. Se utiliza solo 2022–2025. Su ubicación no se incrusta en los programas.

No se encontró un generador disponible que reconstruya desde cero la selección anual original de 150.000 hechos. No se sustituye por una muestra inventada. El anual se reproduce exactamente desde sus ocho CSV preparados. La ruta C reconstruye el mensual apoyándose en ese anual congelado, no toda la selección nacional desde cero.

Para una regeneración anual independiente se necesitan el procedimiento original de selección o una nueva fase de ETL validada y autorizada. Esta limitación no impide restaurar ni cargar los 300.000 hechos del proyecto.

## Tipos y reglas

Códigos conservados como texto; ACTIVIDAD/PROYECTO normalizados según correspondencia auditada. Gobiernos locales conservados con sector/pliego vacíos. Importes Decimal/NUMERIC(20,2), sin ABS o sustitución de negativos. Nulos/formatos inválidos se rechazan.

Las claves naturales incluyen contexto completo; SEC_FUNC aislado no identifica una meta. Financiamiento usa roles explícitos; no relacionar por similitud nominal. No sumar etapas ni hechos anuales y mensuales.

[Modelo](MODELO_Y_REGLAS.md) · [Matriz bus](MATRIZ_BUS_KIMBALL.md) · [README](../README.md).
