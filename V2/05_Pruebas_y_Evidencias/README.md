# Pruebas y evidencias

- historicas/: implementación, restauración completa real y auditoría/correcciones del dashboard original. Son antecedentes del proyecto, no certificación de una instalación nueva.
- fixtures/: agregados y fuente previa necesarios para repetir la regresión de presentación y consultas.
- capturas/: dos vistas finales representativas; sin credenciales.
- ejecuciones/: resultados de las pruebas efectuadas sobre esta entrega. Se excluye de Git por ser salida local.
- COPIAS_ORIGINALES.json: hash de origen y hash al copiar cada componente. Las adaptaciones posteriores están identificadas en el inventario final.

No se copiaron entornos virtuales, archivos secretos, bases temporales DuckDB, logs de operación originales, snapshots obsoletos de interfaz ni todas las capturas redundantes.

## Pruebas sin cambiar bases

    .\.venv\Scripts\python.exe -B scripts\verificar_entrega.py
    .\.venv\Scripts\python.exe -B -m unittest discover -s 03_Dashboard\tests -v
    .\.venv\Scripts\python.exe -B -m unittest discover -s 02_ETL_Python\tests -v
    .\.venv\Scripts\python.exe -B -m unittest discover -s 05_Pruebas_y_Evidencias -p test_seguridad_portable.py -v
    .\.venv\Scripts\python.exe -B 02_ETL_Python\src\validar_local.py 02_ETL_Python\datos_preparados\mensual

Con configuración privada y V2 accesible, solo lectura:

    .\.venv\Scripts\python.exe -B 03_Dashboard\verificar_dashboard.py
    .\.venv\Scripts\python.exe -B 03_Dashboard\verificar_correcciones.py --evidencias 05_Pruebas_y_Evidencias\fixtures
    .\.venv\Scripts\python.exe -B scripts\proyecto.py verificar

Las rutas y controles de la copia se adaptaron al paquete. El control que antes cotejaba 63 archivos de ENTREGA_FINAL ahora coteja SHA256SUMS.txt de esta entrega: no necesita la carpeta original.

Los resultados realmente ejecutados se detallan en [INFORME_ENTREGA.md](../INFORME_ENTREGA.md). No interpretar un análisis sintáctico, un hash o pg_restore --list como una nueva prueba completa de restauración.
