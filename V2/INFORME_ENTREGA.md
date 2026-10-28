# Informe de entrega MEF V2

Fecha: 28 de octubre de 2026. Paquete creado en ENTREGA_FINAL_V2; no publicado.

## Dictamen

La entrega esta preparada para revision y una prueba de instalacion independiente. Incluye las dos vias completas de recuperacion de la seleccion congelada: respaldo y doce CSV preparados. No se afirma que se haya instalado en otra computadora ni ejecutado una nueva restauracion de esta copia portable.

Arquitectura Kimball: nueve dimensiones, dos tablas de hechos y una tabla tecnica de correspondencia; doce tablas, 22 claves foraneas, 150.000 hechos anuales, 150.000 mensuales y 12.500 series completas. Las medidas de ambos hechos nunca deben sumarse entre si. La matriz bus y el diagrama estan en 04_Documentacion.

## Comprobaciones ejecutadas sobre la entrega

| Comprobacion | Resultado |
|---|---|
| Dashboard y SQL independiente, seis secciones, filtros, exportaciones | 131 controles satisfactorios; transacciones de solo lectura |
| Regresion de seis hallazgos, agregados y CSV contra linea base | 66 controles satisfactorios; consultas monetarias sin cambios |
| Unitarias de dashboard / ETL / seguridad portable | 19 / 10 / 4 satisfactorias |
| Doce CSV preparados | 150.000 anuales y 150.000 mensuales; 12.500 series, 48 periodos; duplicados y huerfanos cero |
| Conciliaciones locales | 28 totales anuales y 48 mensuales; 324 registros mensuales negativos conservados |
| Respaldo incluido | SHA-256 identico al validado; pg_restore --list sin errores; doce TABLE DATA y 22 FK |
| Docker Compose | config --quiet correcto con valores ficticios en memoria; no se crearon recursos |
| Reprocesamiento mensual portable | Piloto de diez filas de 2022 correcto; sin lectura poblacional ni seleccion definitiva |
| Originales utilizados | 82 hashes comparados contra el registro previo; todos intactos |

La primera regresion de la copia detecto una omision documental en el README; se corrigio y la repeticion completa termino correctamente. El inicio directo desde la carpeta del dashboard se documento para cargar su tema visual. No se alteraron consultas monetarias, ETL original ni datos.

Se reutilizaron interpretes existentes en modo -B; no se creo un entorno virtual ni se instalo una nueva resolucion de dependencias. Las pruebas de interfaz actuales utilizaron Streamlit AppTest. Las capturas y la prueba real de navegador incluidas son antecedentes de la auditoria anterior, no una nueva inspeccion visual de esta copia.

## Respaldo

Archivo: 01_Base_de_Datos/respaldo/dw_mef_2022_2025_v2_completo_20261028T170603643031Z.dump

Tamano: 22.393.234 bytes. PostgreSQL compatible: 15; servidor de origen 15.19.

SHA-256: 3da3bafb255c3fdf69884417c72f9dccfc3647422b21a8aa05af9c5682499b96

La restauracion completa original en una base independiente del mismo servidor fue satisfactoria y consta en historicas. En este empaquetado solo se comprobo lectura, estructura e integridad del respaldo. El script portable exige destino ausente, autorizacion explicita y contenedor Compose propio; no usa --clean ni elimina bases o volumenes. Sus barreras se comprobaron con pruebas unitarias, no con una nueva restauracion.

## Portabilidad y limites pendientes

- Rutas relativas y variables PG*, configuracion local privada y ejemplos sin credenciales. Puerto Compose por defecto 55432, web 8502; configurable para evitar conflictos.
- SQL, CSV, dump, recursos visuales y fixtures locales incluidos. El manifiesto SHA-256 cubre el contenido principal; el inventario identifica las copias adaptadas y su procedencia.
- No se encontro el generador de la seleccion anual original. El snapshot anual se conserva completo y verificado; regenerarlo desde cero a partir del CSV nacional sigue pendiente. Esto no impide restaurar o cargar los 300.000 hechos preparados.
- El adaptador de fuentes mensuales se probo con un piloto acotado; falta ejecutar su reprocesamiento completo en una nueva instalacion. Las fuentes grandes permanecen fuera del paquete y no se descargan automaticamente.
- Falta probar instalacion desde cero de dependencias, creacion Compose y restauracion de esta copia en otra computadora. Los manuales indican los pasos y la negativa a sobrescribir destinos existentes.
- La revision de seguridad combina inventario, exclusiones y busqueda de patrones; no equivale a una certificacion universal de ausencia de secretos. No se detectaron secretos reales en los archivos preparados.
- Las muestras no estiman el total nacional. Cobertura y partidas varian entre ejercicios; el corte de ejecucion de 2025 no esta certificado.

## Archivos y publicacion

[Arbol completo](ARBOL_ENTREGA.txt), [inventario de archivos](INVENTARIO.csv), [inclusiones y exclusiones](04_Documentacion/INCLUSIONES_Y_EXCLUSIONES.md), [manual principal](README.md).

El inventario registra ruta, bytes, SHA-256, procedencia, funcion y adaptacion. Para evitar autorreferencia, no incluye su propio hash ni el del manifiesto; SHA256SUMS.txt protege el inventario y los demas archivos principales, salvo el propio manifiesto. Los resultados locales regenerables estan excluidos.

Ningun archivo individual supera 100 MB. El mayor, dim_meta.csv, tiene 54.469.802 bytes: GitHub puede advertir por superar 50 MiB. Revisar Git LFS o distribucion por Release si aumenta el tamano o las versiones, conservando hashes e instrucciones. El dump y los doce CSV preparados no estan excluidos accidentalmente.

No se modificaron las bases original, V2 o temporal de restauracion, Docker, respaldos originales, CSV originales ni ENTREGA_FINAL. No hubo ETL de produccion, commits ni push. Solo se crearon/adaptaron archivos dentro de ENTREGA_FINAL_V2. No se crearon recursos Docker ni bases nuevas; no hay recursos nuevos que eliminar.

La publicacion queda pendiente de revision y autorizacion del usuario.

## Volumen del paquete

112 archivos principales, aproximadamente 154,17 MB (147,03 MiB). Incluyendo 36 salidas locales pequenas de comprobacion, la carpeta ocupa aproximadamente 154,34 MB (147,19 MiB). Las cifras son redondeadas; el inventario contiene los tamanos individuales exactos. Ninguna salida local se necesita para restaurar o ejecutar el proyecto. La verificacion final de SHA-256, doce CSV, respaldo, sintaxis, enlaces locales, rutas Windows y patrones de secretos termino correctamente.
