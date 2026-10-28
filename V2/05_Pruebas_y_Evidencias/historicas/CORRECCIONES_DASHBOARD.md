# Correcciones autorizadas del dashboard MEF V2

**Estado: los seis hallazgos estan corregidos y verificados.** Dashboard activo en http://127.0.0.1:8502.

Cierre America/Lima: 2026-10-28T14:30:43.037167-05:00

Referencia: auditoria_dashboard_20261028T181652Z/INFORME_AUDITORIA.md. Se mantuvo la arquitectura, el diseno existente y las consultas monetarias. No se preparo una publicacion.

## 1. Correcciones por hallazgo

| ID | Correccion | Evidencia de cierre |
|---|---|---|
| M01 | Unidad adaptable por valor absoluto: soles por debajo de 1.000, miles desde 1.000, millones desde 1.000.000 y miles de millones desde 1.000.000.000. Mantiene signo, cero y Decimal. | S/ 0,01 ya es visible como S/ 0,01; S/ 4.999,99 se representa S/ 5,00 mil. Pruebas positivas, negativas, cero y proximas a umbrales. |
| M02 | Selector compatible con aviso. Si desaparece toda la seleccion, conserva () y consulta cero resultados; nunca se convierte implicitamente en None/todas. | Caso entidad 2046: 412 hechos; al cambiar a E queda sin hechos, con advertencia. Recupera la entidad al elegirla otra vez o todas solo por accion explicita. Tambien se verifico retiro parcial. |
| M03 | Registros mensuales negativos sustituye Meses negativos en tarjeta y etiqueta CSV. | Sigue contando 324 hechos; no se altero el SQL ni se interpreta como 324 periodos calendario. |
| M04 | README principal refleja implementacion, 300.000 hechos, nueve dimensiones, 22 FK, respaldo, recuperacion real y dashboard. | Se actualizaron instrucciones de instalacion, restauracion futura segura y ejecucion; no se ejecutaron los comandos de restauracion documentados. |
| B01 | Resumen muestra 150.000 hechos anuales, 150.000 mensuales y 300.000 totales, marcados como conteos globales sin filtros. | Solo un total global, sin agregar nuevas tarjetas duplicadas. Los KPI inferiores conservan sus conteos filtrados. |
| B02 | Colores fijos de ejercicio: 2022 turquesa, 2023 dorado, 2024 azul, 2025 violeta. | Mismos colores al filtrar y en barras de ejecucion. Se mantienen las leyendas por medida y la escala monetaria del mapa de calor. |

Las unidades y el redondeo de tarjetas son exclusivamente de presentacion. Los valores subyacentes, tablas y exportaciones conservan sus Decimal. Las sumas anuales y mensuales no se combinan para calcular indicadores monetarios.

## 2. Archivos modificados

| Archivo | Alcance |
|---|---|
| README.md | Estado real e instrucciones vigentes de V2 |
| dashboard/README.md | Nuevas unidades, seleccion restringida, conteos globales, etiquetas y colores |
| dashboard/app.py | Avisos, bloqueo/recuperacion, etiqueta, total global y colores por ejercicio |
| dashboard/presentacion.py | Formato compacto y mapa fijo de colores anuales |
| dashboard/datos.py | Solo LABELS: nombre visible del contador de negativos |

Archivos nuevos: dashboard/filtros_ui.py, dashboard/tests/test_correcciones.py y dashboard/verificar_correcciones.py. En esta carpeta se conservaron copias previas de los cinco archivos en antes/, los scripts de repeticion, los resultados y las capturas. No se elimino ningun archivo.

## 3. Datos y consultas antes/despues

- Comparacion exacta de 24 conjuntos de agregados: anual completo, cohorte, cuatro agrupaciones, mensual y conciliacion; se probaron tanto el universo global como cinco filtros combinados.
- Los 24 conjuntos conservan todas sus columnas y valores originales. No se utilizaron tolerancias para importes monetarios.
- Se comparo el AST completo de datos.py antes y despues, excluyendo solo la asignacion LABELS: es identico. No cambiaron consultas, parametros, uniones, calculos o configuracion de solo lectura.
- CSV: los contenidos se mantienen identicos. En los dos conjuntos mensuales de la linea base se normalizo el unico encabezado autorizado para comparar hashes; la sustitucion Meses negativos -> Registros mensuales negativos es la unica diferencia de esos CSV.
- Diez archivos SQL/ETL del manifiesto historico conservan su SHA-256. No se ejecutaron ni modificaron ETL, DDL o migraciones.
- Conteos finales: 150.000 hechos anuales y 150.000 mensuales. 12.500 series y 48 periodos; 22 FK validadas y cero huerfanos mediante consultas explicitas de solo lectura.
- La bateria conserva los 28 controles anuales y 48 mensuales exactos, sin duplicar importes de ambos hechos.

## 4. Pruebas ejecutadas

| Grupo | Resultado |
|---|---|
| Bateria existente | 131 comprobaciones satisfactorias |
| Pruebas unitarias ejecutadas por la bateria | 19 satisfactorias: nueve previas y diez nuevas |
| Repeticion de casos de auditoria | 17 satisfactorios: quince casos previos adaptados y dos recuperaciones explicitas |
| Regresion de los seis hallazgos | 66 comprobaciones satisfactorias |
| Navegador real: seis vistas en tres resoluciones | 18/18, a 1440x1050, 768x1024 y 390x844 |
| Descargas reales con cinco filtros | 7/7, exactas contra los agregados filtrados |
| JavaScript / excepciones de Streamlit en ejecucion final | 0 |
| Desbordamiento horizontal de pagina | 0 en las 18 vistas |
| HTTP salud | 200 |

No sumar estas cifras como pruebas independientes: las 131 comprobaciones invocan la bateria unitaria y hay escenarios compartidos entre niveles de prueba.

Se verificaron umbrales y signo de cantidades; retiro total/parcial, persistencia al cambiar de seccion y recuperacion por seleccion o boton; etiqueta con 324 registros; total global invariable al filtrar a un solo anio; colores de 2024 al pasar de mensual a anual; README vigente.

Las siete descargas proceden de las seis secciones (comparacion tiene dos tablas), con anio 2024, gobierno local, entidad 1931, funcion 10 y fuente 5. Los KPI filtrados no se confunden con los totales del encabezado.

Contraste: prueba interna superior a 3:1 de cada color anual frente al fondo #102236 y revision de capturas. No se certifico cumplimiento integral de accesibilidad o todas las deficiencias de vision del color.

## 5. Incidencia de recarga resuelta

El primer intento de navegador encontro una version anterior de presentacion.py en memoria del proceso Streamlit, con YEAR_COLORS todavia ausente. Los procesos nuevos de pruebas ya pasaban. Se identifico por PID/comando el proceso exclusivo de V2 en 8502 y se reinicio solo esa aplicacion. No se reinicio ni reconfiguro Docker o PostgreSQL.

Despues de esa recarga, la revision completa de Chrome termino correctamente. Se conserva incidencia_recarga.json y los nuevos logs. No fue necesario modificar SQL, datos o introducir una solucion alternativa en los calculos.

## 6. Protecciones y limites

- Acceso exclusivo a V2 en modo lectura. No se modificaron dw_mef_2022_2025, dw_mef_2022_2025_v2 o dw_mef_v2_prueba_restauracion. La base temporal sigue existiendo.
- 63 hashes protegidos de ENTREGA_FINAL y el hash del respaldo V2 coinciden en la bateria. No se alteraron respaldos ni CSV originales.
- No hubo cambios de modelo dimensional, ETL, roles, contrasenas, contenedores, volumenes o configuraciones privadas.
- No se realizaron operaciones Git, commits, push ni preparacion de publicacion.
- La documentacion antigua y los manifiestos de fases anteriores se conservaron. Las copias antes/ y este nuevo manifiesto registran expresamente los cambios autorizados; no se reescribieron evidencias historicas para ocultar diferencias.
- No se ejecuto una restauracion nueva ni una instalacion en otra computadora. Las instrucciones de recuperacion son documentacion para acciones futuras autorizadas y rechazan usar las bases protegidas.

## 7. Uso y evidencias

La aplicacion continua disponible en http://127.0.0.1:8502. Para arrancarla desde VS Code cuando no este ejecutandose:

    cd [ORIGEN_LOCAL]\V2_MEF_2022_2025\dashboard
    .\.venv\Scripts\python.exe -m streamlit run app.py --server.port 8502

Repetir la regresion de estas correcciones:

    .\.venv\Scripts\python.exe -B verificar_correcciones.py --evidencias evidencias\correcciones_20261028T191147Z

Evidencias: BASELINE_RESULTADOS.json, ARCHIVOS_ANTES.json, antes/, evidencias/verificacion_*.json, evidencias/regresion_*.json, evidencias/auditoria_adicional.json, evidencias/auditoria_navegador_ampliada.json, evidencias/modelo_etl_preservados.json y evidencias/integridad_final.json.

**Dictamen: cerrados los seis hallazgos autorizados dentro del alcance probado. No se implementaron mejoras adicionales. La publicacion permanece pendiente de instrucciones.**
