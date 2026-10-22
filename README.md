# Data Warehouse MEF · 2022–2025

Proyecto universitario con PostgreSQL 15, Docker Compose, Python, Streamlit y Plotly. Modelo Ralph Kimball: **150.000 hechos, siete dimensiones, siete FK y seis secciones del dashboard**.

Las cifras son de una **muestra**, no totales oficiales nacionales. La cobertura cambia entre ejercicios. **2025 es una instantánea cuya fecha de corte de ejecución no está certificada.**

## Instalación rápida en Windows

Requisitos: Git, Docker Desktop iniciado en modo contenedores Linux, Docker Compose v2 o posterior y Python 3.11 o superior. No necesitas el CSV original del MEF ni repetir el ETL.

En PowerShell:

```powershell
git clone https://github.com/Luis-Arhian3011/DataWarehouse-MEF-2022-2025.git
cd DataWarehouse-MEF-2022-2025

python scripts/proyecto.py configurar
```

Esto crea **.env privado**, con contraseña aleatoria sin mostrarla. No lo publiques. Revisa .env si necesitas otro puerto; el predeterminado es 5433. No requiere activar un entorno virtual ni cambiar la política de PowerShell.

```powershell
python scripts/proyecto.py iniciar
python scripts/proyecto.py restaurar
python scripts/proyecto.py verificar

python -m venv 03_Dashboard/.venv
.\03_Dashboard\.venv\Scripts\python.exe -m pip install -r 03_Dashboard/requirements.txt
.\03_Dashboard\.venv\Scripts\python.exe scripts/proyecto.py dashboard
```

Abre **http://localhost:8501**. Los comandos se ejecutan desde la raíz del repositorio. En VS Code, abre esa carpeta y selecciona 03_Dashboard/.venv/Scripts/python.exe como intérprete.

**Restaurar es una operación de una sola vez.** El script rechaza una base de destino ya existente, incluso vacía. Para abrir otra vez el proyecto, usa iniciar y dashboard; no repitas restaurar ni ejecutes etl.py.

## Qué hace cada paso

- configurar genera .env a partir de .env.example y no sobrescribe configuraciones existentes.
- iniciar ejecuta Docker Compose y espera un PostgreSQL saludable. El proyecto predeterminado es mef2025; su contenedor y volumen no se llaman postgres-db.
- restaurar verifica SHA-256, versión, servicio y ausencia del destino; crea una base nueva y ejecuta pg_restore en una transacción.
- verificar realiza solo lecturas y comprueba tablas, hechos, claves, huérfanos, contexto de meta y 28 totales exactos.
- dashboard carga la configuración local y conecta al servicio Compose con transacciones de solo lectura.

No se crean recursos automáticamente al clonar o importar módulos. Los scripts no eliminan bases, contenedores o volúmenes.

## Configuración

.env.example no contiene una contraseña real. .env queda fuera de Git.

| Variable | Función | Predeterminado |
| --- | --- | --- |
| COMPOSE_PROJECT_NAME | Prefijo aislado de recursos Compose | mef2025 |
| POSTGRES_HOST | Host para transporte TCP | 127.0.0.1 |
| POSTGRES_PORT | Puerto publicado en el equipo | 5433 |
| POSTGRES_USER | Usuario inicial y propietario restaurado | mef_admin |
| POSTGRES_PASSWORD | Contraseña local generada | Sin valor público |
| POSTGRES_DB | Base objetivo de restauración | dw_mef_2022_2025 |
| MEF_TRANSPORT | Transporte del dashboard | compose |

Compose inicia únicamente la base de mantenimiento postgres. POSTGRES_DB se usa como destino de la restauración; así se puede rechazar su existencia antes de escribir. La contraseña se entrega a la imagen mediante un secreto Compose y POSTGRES_PASSWORD_FILE, no como valor literal en docker-compose.yml.

El volumen pgdata lleva el prefijo del proyecto y no es externo. No se monta ningún volumen de la instalación original. El respaldo se monta **solo para lectura**, sin copiarlo al contenedor.

Para TCP cambia MEF_TRANSPORT=tcp. El lanzador configura PGHOST, PGPORT, PGDATABASE, PGUSER y PGPASSWORD para el proceso del dashboard. También se mantiene el transporte docker legado con MEF_CONTAINER para usos locales, pero **la recuperación utiliza exclusivamente Compose**.

## Recuperación e integridad

Respaldo:
01_Base_de_Datos/respaldo/dw_mef_2022_2025_completo_20261022T182048021354Z.dump

SHA-256:

```text
b9177e726595b4621de32a347e9d56fbbab0bf811e79bdff2be2899923c3c138
```

El script usa PostgreSQL 15 y pg_restore con --exit-on-error, --single-transaction, --no-owner y --no-privileges. Los objetos quedan a nombre del usuario configurado, sin depender del rol histórico luchito ni restaurar roles globales. No usa --clean ni reemplaza bases.

Los controles confirman ocho tablas, siete dimensiones, siete FK, 150.000 hechos únicos, cero huérfanos, cuatro ejercicios con 37.500 hechos y 28 sumas conciliadas contra el manifiesto. Si una carga falla, el script se detiene y conserva la base creada para inspección; no la elimina automáticamente.

Consulta [recuperación](01_Base_de_Datos/README.md) y [estado de pruebas](04_Documentacion/GITHUB_Y_DESPLIEGUE.md).

## Dashboard y pruebas

Con la base restaurada:

```powershell
.\03_Dashboard\.venv\Scripts\python.exe scripts/proyecto.py pruebas
```

Ejecuta 65 controles de datos/interfaz y 52 del pulido. No necesita ejecutar el ETL. La prueba visual opcional requiere requirements-dev.txt y Chrome instalado; sus scripts aceptan MEF_DASHBOARD_URL y MEF_EVIDENCIAS para separar puertos y evidencias.

Las seis secciones son resumen ejecutivo, análisis temporal, niveles de gobierno, entidades, distribución del gasto y metodología/calidad. Mantienen filtros, tablas, CSV, tooltips y diagrama del esquema estrella.

## Errores frecuentes

- **Docker no responde:** inicia Docker Desktop y comprueba docker compose version.
- **Puerto 5433 ocupado:** cambia POSTGRES_PORT en .env antes de iniciar. No detengas PostgreSQL de otras aplicaciones. La conexión Compose no utiliza el puerto del host.
- **Puerto 8501 ocupado:** agrega --puerto 8502 al comando dashboard.
- **La base ya existe:** usa verificar y dashboard; no fuerces otra restauración.
- **Contraseña incorrecta después de editar .env:** la inicialización de PostgreSQL aplica la contraseña al crear el volumen; editar .env no cambia usuarios de un volumen existente. Revisa la configuración original, sin eliminar datos.
- **Falta Streamlit:** instala requirements.txt con el intérprete del entorno virtual y utiliza ese mismo intérprete al ejecutar dashboard.
- **Conexión al contenedor equivocado:** usa el lanzador del repositorio; el modo Compose verifica las etiquetas del proyecto y servicio.
- **Filtros vacíos:** la aplicación muestra un mensaje; no equivale a un error de conexión.

## Detener sin borrar

Ctrl+C termina Streamlit. En otra terminal, desde la raíz:

```powershell
python scripts/proyecto.py detener
```

Esto ejecuta docker compose stop y conserva el volumen. Para volver: iniciar y dashboard. No elimines volúmenes para resolver errores de instalación.

## Contenido publicado

- 01_Base_de_Datos: SQL definitivo y respaldo validado.
- 02_ETL_Python: código histórico y manifiesto, opcionales para estudiar el proceso.
- 03_Dashboard: aplicación, recursos, requisitos y pruebas.
- scripts: configuración, recuperación segura y verificación.
- 04_Documentacion: metodología, procedencia, diagrama y guía de despliegue.
- 05_Evidencias: controles esenciales y resultados de la prueba aislada ejecutada.

Los ocho CSV preparados permanecen en la entrega local, pero **no se publican en Git**: son redundantes para restaurar y ejecutar el dashboard. No se publica el CSV original de aproximadamente 9 GB, entornos, cachés, secretos, logs ni informes operativos duplicados. No hace falta Git LFS para los archivos seleccionados.

Los datos tienen naturaleza presupuestaria institucional. La auditoría busca secretos y patrones de información personal; no sustituye una certificación de licencias o una revisión semántica de todos los textos de la fuente.

## Alcance de las pruebas y límites

El estado preciso se registra en [GITHUB_Y_DESPLIEGUE.md](04_Documentacion/GITHUB_Y_DESPLIEGUE.md). No se afirma haber instalado el proyecto en otra computadora si solo se ha probado localmente.

No se modifican la instalación original, su contenedor postgres-db, sus volúmenes, el ETL ni el CSV de origen. La recuperación permite demostrar el snapshot sin repetir su desarrollo.
