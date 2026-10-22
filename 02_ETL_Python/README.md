> Perfil GitHub: este ETL se conserva como código de referencia. Sus ocho CSV preparados quedan fuera de Git; no son necesarios para restaurar el respaldo. Para instalar, utiliza scripts/proyecto.py restaurar, sin repetir el ETL.

# ETL utilizado · Snapshot MEF 2022–2025

Esta es una copia del ETL de carga que produjo dw_mef_2022_2025. Se adaptaron únicamente las rutas al SQL compartido y el nombre de contenedor configurable. No se ejecutó la carga durante la preparación de ENTREGA_FINAL.

## Archivos

- conexion.py: cliente psql a través de Docker. Base fija dw_mef_2022_2025; MEF_CONTAINER selecciona el contenedor, con postgres-db como valor original.
- crear_base.py: crea una base nueva y deja un recibo en evidencias/. Rechaza una base ya existente.
- etl.py: comprueba ocho hashes, rechaza una base con objetos, ejecuta DDL, COPY, secuencias y validaciones en una transacción.
- verificar.py: consulta conteos, siete FK, huérfanos, grano, contexto de meta y 28 sumas; guarda el resultado local.
- manifest.json: columnas, hashes y totales del snapshot. Sus datos monetarios y hashes se conservan; las rutas informativas se adaptaron.
- datos_carga/: las siete dimensiones y los 150.000 hechos en ocho CSV. Se incluyen porque son entradas reales del ETL; no son el CSV nacional original.
- ../01_Base_de_Datos/sql/: SQL reutilizado sin duplicarlo aquí.

Solo usa biblioteca estándar de Python; requirements.txt lo indica. No necesita DuckDB, Pandas ni psycopg para esta etapa de carga. El dashboard sí tiene sus propias dependencias.

## Carga manual alternativa a pg_restore

Únicamente en un contenedor independiente vacío, después de autorización. Crea el contenedor como indica ../01_Base_de_Datos/README.md, pero **no restaures el respaldo**.

```powershell
cd .\02_ETL_Python
$env:MEF_CONTAINER = "postgres-mef-entrega"
python crear_base.py
python etl.py
python verificar.py
```

No usar esta secuencia contra postgres-db ya cargado. No se distribuye un recibo de creación antiguo: lo genera crear_base.py en el destino nuevo. No se mezclan recuperación y ETL; ambos producen el mismo destino mediante rutas alternativas.

## Reglas

Grano anual completo de siete dimensiones; meta conserva contexto y nombre. Se excluyen de la población seleccionada los granos ambiguos documentados, conservados en auditoría externa. Los gobiernos locales se incluyen aunque sector/pliego no estén informados. Importes NUMERIC(20,2), negativos conservados y siete medidas no nulas. No se suman PIA/PIM/etapas entre sí.

La selección es reproducible: semilla MEF_KIMBALL_2022_2025_V1 y 37.500 por año. Los estratos originales son año, NIVEL_GOBIERNO y SEC_EJEC; no equivalen a la clave compuesta de dim_entidad. La tabla de hechos conserva población y cuota de estrato y el hash de selección.

La extracción y selección previas del CSV completo no se vuelven a ejecutar aquí. Véase ../04_Documentacion/FUENTE_Y_REPRODUCCION.md para su procedencia, algoritmos y dependencias históricas.
