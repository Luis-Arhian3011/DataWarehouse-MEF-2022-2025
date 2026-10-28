# Inclusiones y exclusiones

Se incluyen los tres SQL definitivos, ETL V2 adaptado, doce CSV preparados con manifiestos, referencia anual compacta Parquet, cohortes auditadas, respaldo personalizado y metadatos, dashboard, nueve dimensiones documentadas, matriz bus, diagrama Mermaid, pruebas y evidencias esenciales.

Los CSV preparados contienen codigos, denominaciones publicas e importes presupuestarios del MEF. Son muestras, no datos personales obtenidos de sistemas privados. No se copiaron credenciales locales, configuraciones privadas ni roles globales con contrasenas. El dump proviene de pg_dump de esta base, no de pg_dumpall.

No se copiaron CSV originales de varios GB, cuatro Parquet crudos auditados de mas de 100 MB, entornos virtuales, caches, bases DuckDB temporales, secretos reales, versiones 2022-2024 ni respaldos repetidos. El Parquet compacto incluido no es un temporal crudo: es un insumo verificado de correspondencia.

Se retienen pequenas salidas de las pruebas de empaquetado en 02_ETL_Python/trabajo y 05_Pruebas_y_Evidencias/ejecuciones. Estan excluidas de Git y del manifiesto principal. No se eliminaron archivos. Las evidencias esenciales resumidas se incluyen fuera de esas carpetas.

El respaldo y los doce CSV preparados estan incluidos en Git por defecto para permitir restauracion y carga preparada. Ninguno alcanza 100 MB. dim_meta.csv supera el umbral de advertencia de 50 MiB: evaluar Git LFS o un Release para futuras versiones si aumenta el historial; no es un bloqueo de 100 MB. No publicar .env ni secrets.toml. No se ha iniciado ni publicado un repositorio en este paquete.
