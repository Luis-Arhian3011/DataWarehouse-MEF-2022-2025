# Data Warehouse MEF 2022–2025 V2

Estado: implementado y validado en el proyecto de origen. La nueva instalacion portable aun no se ha restaurado ni probado en otra computadora.

Entrega universitaria de Inteligencia de Negocios, con PostgreSQL 15, Python, Streamlit y metodología dimensional de Ralph Kimball.

| Componente | Contenido |
|---|---|
| Hecho anual | 150.000 observaciones, siete medidas presupuestarias |
| Hecho mensual | 150.000 registros; doce meses de 12.500 series conciliadas |
| Total de hechos | 300.000 registros de dos procesos; no se suman sus importes entre sí |
| Dimensiones / tablas / FK | Nueve / doce / veintidós |
| Período | 2022–2025; 2026 excluido |
| Recuperación rápida | Respaldo personalizado PostgreSQL validado |
| Dashboard | Seis secciones y conexión exclusiva de solo lectura a V2 |

**Son muestras, no cifras nacionales.** No hay pesos ni extrapolación. La ejecución 2025 corresponde a una instantánea cuya fecha de corte no está certificada.

## Empezar: restaurar y abrir el dashboard

Se requiere Git o una copia de esta carpeta, Docker Desktop con Compose y Python 3.11 o posterior. Los comandos siguientes son para PowerShell, situándose dentro de ENTREGA_FINAL_V2.

    python -m venv .venv
    .\.venv\Scripts\python.exe -m pip install -r requirements.txt
    Copy-Item .env.example .env

Crear .env solo si no existe. Completar PGUSER y PGPASSWORD localmente, sin compartirlos. La contraseña de ejemplo está vacía y Compose se negará a iniciar hasta configurarla. No publicar .env ni secrets.toml.

    docker compose up -d
    .\.venv\Scripts\python.exe -B scripts\proyecto.py diagnostico
    .\.venv\Scripts\python.exe -B scripts\proyecto.py restaurar --autorizar
    .\.venv\Scripts\python.exe -B scripts\proyecto.py verificar
    .\.venv\Scripts\python.exe -B scripts\proyecto.py dashboard

Abrir http://127.0.0.1:8502. En VS Code seleccionar el intérprete .venv\Scripts\python.exe. No es necesario activar el entorno ni cambiar políticas de ejecución.

**Estos comandos no se ejecutaron durante el empaquetado.** Preparan una instalación nueva. La base de destino debe estar ausente: si dw_mef_2022_2025_v2 ya existe, la restauración se detiene sin limpiarla ni sobrescribirla.

Compose usa un proyecto separado mef-v2-entrega, sin container_name y con volumen propio. No referencia postgres-db ni sus volúmenes. El puerto publicado por defecto es 55432; puede cambiarse en .env. No se modifica el PostgreSQL local de Windows en 5432.

Para detener el dashboard iniciado en tu terminal, Ctrl+C. Para detener el entorno de esta entrega sin eliminar datos:

    docker compose stop

Para volver a iniciarlo: docker compose start. No se incluyen comandos de eliminación de volúmenes.

## Tres vías distintas de reproducción

1. **Restaurar el respaldo:** vía recomendada para demostrar el proyecto; no requiere CSV ni ETL.
2. **Cargar los doce CSV preparados:** reproduce la selección exacta y el modelo desde archivos locales, sin fuentes de varios GB. En una instalación nueva y con destino ausente:

       .\.venv\Scripts\python.exe -B scripts\proyecto.py cargar-preparados --autorizar

   No ejecutar esta vía después de restaurar: ambas crean la misma base y son alternativas.
3. **Reprocesar las fuentes mensuales:** utiliza los cuatro CSV oficiales suministrados por separado, la muestra anual congelada y las reglas auditadas. Exige autorización explícita de lectura, piloto y espacio temporal. Véase [Manual ETL](04_Documentacion/MANUAL_ETL.md).

**Límite importante:** no se encontró el generador original de la selección anual en los archivos disponibles. Se entrega su snapshot validado íntegro, que permite reproducir exactamente los 300.000 hechos mediante carga preparada o respaldo. No se afirma que pueda regenerarse automáticamente esa selección anual desde el CSV nacional partiendo de cero. El reprocesamiento mensual portable se preparó, pero no se volvió a ejecutar sobre fuentes de varios GB durante esta entrega.

## Organización

- [Base de datos y recuperación](04_Documentacion/INSTALACION_Y_RECUPERACION.md): SQL y respaldo en 01_Base_de_Datos.
- [ETL y fuentes](04_Documentacion/MANUAL_ETL.md): código, doce CSV preparados e insumos compactos en 02_ETL_Python.
- [Dashboard](03_Dashboard/README.md): Streamlit, Plotly, filtros y exportaciones.
- [Modelo dimensional](04_Documentacion/MODELO_Y_REGLAS.md), [matriz bus](04_Documentacion/MATRIZ_BUS_KIMBALL.md) y [diagrama](04_Documentacion/esquema_v2.mmd).
- [Diccionario de datos](04_Documentacion/DICCIONARIO_DATOS.md).
- [Pruebas y evidencia](05_Pruebas_y_Evidencias/README.md).
- [Informe del paquete](INFORME_ENTREGA.md), [inventario](INVENTARIO.csv) y SHA256SUMS.txt.

## Reglas analíticas

- El anual completo y la cohorte mensual son universos diferentes. Las conciliaciones usan solo los 12.500 padres anuales vinculados.
- PIA, PIM y etapas de ejecución son medidas distintas; no se suman entre sí ni se repiten por mes.
- Ejecución = 100 × SUM(devengado) / SUM(PIM), con PIM agregado positivo. No se promedian porcentajes de filas ni se trunca el resultado a 100 %.
- PIM cero con devengado positivo, ceros y negativos se conservan. Gobiernos locales incluidos aunque falten sector o pliego.
- Fuente y rubro se presentan mediante la vista conformada auditada. No se supone equivalencia por nombres parecidos.
- Decimal se conserva en cálculos y CSV; las tarjetas redondean solo la presentación.
- Las entidades compartidas entre ejercicios no garantizan partidas o cobertura monetaria idénticas.
- Soles corrientes, sin ajuste por inflación. Las diferencias de la muestra no estiman crecimiento nacional.

## Fuente y antecedentes

CSV del Ministerio de Economía y Finanzas del Perú, obtenidos a través del portal de datos abiertos:

- [Presupuesto y ejecución de gasto](https://www.datosabiertos.gob.pe/dataset/presupuesto-y-ejecuci%C3%B3n-de-gasto).
- [Devengado mensual](https://www.datosabiertos.gob.pe/dataset/presupuesto-y-ejecuci%C3%B3n-de-gasto-%E2%80%93-devengado-mensual).

Los CSV originales permanecen fuera de esta entrega. Nombres y hashes de las fuentes mensuales auditadas se conservan en los insumos de 02_ETL_Python. No se descarga ninguna fuente automáticamente.

La implementación original se validó, respaldó y restauró completamente en otra base del mismo servidor. Eso no es una prueba en otra computadora. La copia portable se revisó con las pruebas registradas en el informe; no se ejecutó aquí una nueva restauración, ETL de producción ni creación de recursos Docker.

## Comprobaciones

    .\.venv\Scripts\python.exe -B scripts\verificar_entrega.py
    .\.venv\Scripts\python.exe -B 02_ETL_Python\src\validar_local.py 02_ETL_Python\datos_preparados\mensual
    .\.venv\Scripts\python.exe -B 03_Dashboard\verificar_dashboard.py

La última prueba necesita V2 accesible y configuración privada. Las dos primeras no modifican PostgreSQL.

No hay credenciales reales en la entrega. No se creó repositorio Git ni se realizó commit/push. La publicación requiere revisión y autorización posteriores.

El procedimiento de recuperacion utiliza pg_restore con parada ante errores, sin --clean. La arquitectura contiene 9 dimensiones, 12 tablas y 22 claves foraneas.
