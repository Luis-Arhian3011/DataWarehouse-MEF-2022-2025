# Recuperación con Docker Compose

La instalación recomendada está en el [README principal](../README.md). No ejecutes los SQL de creación ni el ETL para recuperar el respaldo.

## Archivo

respaldo/dw_mef_2022_2025_completo_20261022T182048021354Z.dump, PostgreSQL custom, 19.354.326 bytes.

SHA-256:
b9177e726595b4621de32a347e9d56fbbab0bf811e79bdff2be2899923c3c138

Compose lo monta en /respaldo/mef.dump con acceso de solo lectura. scripts/proyecto.py comprueba su hash antes de escribir en una base.

## Comandos desde la raíz

```powershell
python scripts/proyecto.py configurar
python scripts/proyecto.py iniciar
python scripts/proyecto.py restaurar
python scripts/proyecto.py verificar
```

Solo configura y restaura una vez por instalación nueva. Nunca reutilices el contenedor original postgres-db como destino. Compose utiliza nombres y volumen propios, basados en COMPOSE_PROJECT_NAME.

## Controles previos

El script comprueba que el servicio pertenezca al proyecto Compose configurado; rechaza explícitamente un contenedor llamado postgres-db. Valida el archivo, PostgreSQL 15, las ocho entradas de datos y que el nombre de destino no exista.

Crea una base nueva y ejecuta el equivalente a:

```text
pg_restore --exit-on-error --single-transaction --no-owner --no-privileges -U USUARIO -d BASE /respaldo/mef.dump
```

No usa --create porque ya creó y controló el destino. No utiliza --clean. Si alguien crea la base entre la comprobación y CREATE DATABASE, PostgreSQL rechaza la creación y el script se detiene antes de restaurar.

No se restauran roles globales o ACL históricas. El rol inicial configurado es el propietario de los objetos restaurados. La aplicación fuerza sesiones de solo lectura.

## Validaciones posteriores

Se reutiliza el verificador del modelo para contar 150.000 hechos, siete dimensiones, claves únicas, siete FK validadas, cero huérfanos, contexto de meta correcto y 28 totales monetarios exactos. Se comparan además las siete relaciones con sus nombres de columnas y dimensiones reales.

verificar usa únicamente SELECT. Se pueden guardar resultados en un archivo JSON nuevo mediante --salida RUTA, preferiblemente fuera del repositorio. El comando no sobrescribe ese archivo si ya existe.

Si una restauración falla, conserva la base para diagnóstico. No hay limpieza ni reintentos destructivos automáticos.

## SQL histórico

sql/ conserva cuatro archivos definitivos: creación de base, esquema estrella, validaciones del ETL y nueve consultas analíticas. Sus importes y relaciones no se cambiaron para Compose. El rol luchito del SQL de creación corresponde al entorno original; la ruta de recuperación usa --no-owner para no exigirlo.

El informe [de despliegue](../04_Documentacion/GITHUB_Y_DESPLIEGUE.md) distingue la validación de estructura/lectura del respaldo y cualquier prueba de restauración completa realmente ejecutada.
