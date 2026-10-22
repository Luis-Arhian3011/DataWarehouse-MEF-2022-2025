# Preparación para GitHub y despliegue independiente

Fecha de cierre: 22 de octubre de 2026. Esta guía corresponde únicamente a ENTREGA_FINAL.

## Dictamen

La copia está preparada para revisión y primer commit. Se ejecutó una restauración completa del respaldo en un entorno Docker local independiente y las comprobaciones resultaron satisfactorias. No se ha publicado, enviado a GitHub ni creado un commit. No se ha probado una computadora distinta.

## Archivos preparados

| Archivo o conjunto | Función |
| --- | --- |
| docker-compose.yml | PostgreSQL 15, volumen propio, puerto configurable y respaldo montado en lectura |
| .env.example | Plantilla pública sin contraseña |
| scripts/entorno.py | Configuración privada y acceso al proyecto Compose |
| scripts/proyecto.py | Configurar, iniciar, restaurar, verificar, abrir dashboard, probar y detener |
| .gitignore / .gitattributes | Exclusiones de secretos y temporales; conservación binaria del respaldo |
| README.md | Pasos concretos para Windows y VS Code |
| 01_Base_de_Datos/README.md | Recuperación segura y condiciones previas |
| 03_Dashboard/datos.py | Transporte Compose adicional y configuración portable; mismas consultas agregadas |
| 03_Dashboard/verificar_dashboard.py | Identifica la base configurada en la evidencia |
| 03_Dashboard/README.md | Inicio mediante el lanzador portable |
| 02_ETL_Python/README.md y FUENTE_Y_REPRODUCCION.md | Distinguen ETL histórico de recuperación desde respaldo |
| 05_Evidencias/github | Auditoría, restauración, pruebas de datos, interfaz, navegador y limpieza |
| SHA256SUMS.txt | Integridad de los archivos seleccionados para Git |

Se conservan SQL, código ETL, manifiesto de conciliación, seis vistas del dashboard, requisitos, diagrama y documentación metodológica. Los ocho CSV preparados siguen en la copia local, pero se excluyen de Git por redundancia: la instalación usa el respaldo. No se incluyen entornos, cachés, configuración privada, CSV original ni informes operativos duplicados. No se eliminaron esos archivos del proyecto.

## Auditoría

Se revisaron los candidatos de Git, los ocho CSV preparados y el contenido SQL del respaldo mediante lectura en flujo. No se detectaron patrones de contraseñas, tokens o claves privadas. Se inspeccionaron 294.459 líneas del contenido del respaldo sin escribir otra copia SQL. Las comprobaciones automatizadas de descripciones no detectaron los patrones personales buscados; esto no certifica la ausencia absoluta de información personal ni una licencia de redistribución.

Las rutas de ejecución se resuelven respecto del repositorio. Algunas evidencias históricas conservan rutas del proyecto como procedencia, sin utilizarlas para conectar o ejecutar. La ubicación privada de la prueba queda excluida de Git.

Ningún archivo seleccionado supera 100 MiB. El mayor es el respaldo de 19.354.326 bytes, aproximadamente 18,46 MiB. No hace falta Git LFS. GitHub bloquea archivos superiores a 100 MiB y advierte sobre archivos superiores a 50 MiB. [Límites oficiales](https://docs.github.com/en/repositories/working-with-files/managing-large-files/about-large-files-on-github).

El archivo .env se genera localmente y no se publica. Compose recibe la contraseña como secreto y la imagen utiliza POSTGRES_PASSWORD_FILE. No se imprime ni se registra su valor. [Secretos Compose](https://docs.docker.com/compose/how-tos/use-secrets/).

## PostgreSQL y recuperación

El respaldo procede de PostgreSQL 15.19 y se restauró con PostgreSQL 15. La etiqueta postgres:15 permite actualizaciones menores de esa versión; no fija un digest inmutable. El usuario inicial predeterminado es mef_admin. No es necesario crear el rol histórico del equipo original.

El comando restaurar verifica el SHA-256, las ocho entradas TABLE DATA, el servicio del proyecto, la versión del cliente y que la base de destino no exista. Crea la base con template0 y ejecuta:

```text
pg_restore --exit-on-error --single-transaction --no-owner --no-privileges -U USUARIO -d BASE /respaldo/mef.dump
```

Estos argumentos se aplican mediante Compose al servicio validado; no son un comando para ejecutar sobre una instalación original. No se usa --clean, no se restaura sobre una base existente y no se eliminan bases ante errores. Los objetos pertenecen al usuario configurado; no se recuperan roles globales ni ACL históricas.

El volumen se llama PROYECTO_pgdata. El lanzador rechaza un volumen homónimo sin las etiquetas esperadas del proyecto. No se montan volúmenes de postgres-db. El puerto local predeterminado es 5433 y puede cambiarse antes de iniciar. Compose escucha solo en 127.0.0.1.

SHA-256 del respaldo, sin regeneración ni modificación:

```text
b9177e726595b4621de32a347e9d56fbbab0bf811e79bdff2be2899923c3c138
```

## Pruebas realmente ejecutadas

- Entorno Python virtual nuevo, con instalación de los requisitos normales y de desarrollo.
- Configuración Compose validada y arranque saludable de PostgreSQL independiente.
- Restauración completa con nuevo propietario mef_admin: ocho tablas, siete dimensiones, siete FK válidas y exactamente 150.000 hechos.
- Cero huérfanos, unicidad del grano y origen, contexto de meta y 28 totales anuales conciliados; 37.500 hechos por año.
- 65 controles del dashboard y 52 del pulido: 117 satisfactorios.
- Dos verificadores de navegador satisfactorios: seis secciones, filtros, gráficos, descarga CSV y presentación en escritorio y pantalla estrecha.
- Nueve consultas analíticas ejecutadas sin errores.
- Conexión TCP de solo lectura al puerto alternativo verificada además del transporte Compose.
- Un segundo intento de restaurar sobre la base existente fue rechazado antes de escribir.
- Conteos y 28 sumas de postgres-db iguales antes y después de la prueba.
- Respaldo conservado con el mismo SHA-256.

Las evidencias detalladas están en [prueba_aislada.json](../05_Evidencias/github/prueba_aislada.json), [restauracion_local.json](../05_Evidencias/github/restauracion_local.json), [verificacion_dashboard.json](../05_Evidencias/github/verificacion_dashboard.json), [verificacion_pulido.json](../05_Evidencias/github/verificacion_pulido.json), [verificacion_navegador.json](../05_Evidencias/github/verificacion_navegador.json) y [auditoria_seguridad.json](../05_Evidencias/github/auditoria_seguridad.json).

La guardia adicional de propiedad del volumen se comprobó contra el volumen real de prueba antes de retirarlo. No se repitieron las pruebas de aplicación por cambios posteriores exclusivamente documentales y de exclusión Git.

## Recursos temporales y limpieza autorizada

Se crearon el proyecto mef2025-prueba-20261022a, contenedor mef2025-prueba-20261022a-postgres-1, volumen mef2025-prueba-20261022a_pgdata y red mef2025-prueba-20261022a_default. Se usaron los puertos 55432 y 8503, una carpeta temporal externa con configuración privada, entorno Python y evidencias de trabajo. No se copiaron nuevamente el respaldo ni los CSV.

Tras guardar las evidencias esenciales y recibir autorización expresa, se retiraron únicamente ese contenedor, volumen y red; se detuvo el servidor de prueba y se eliminó su carpeta temporal. postgres-db permaneció iniciado. No quedan esos recursos de prueba.

## Límites y decisiones pendientes

- Prueba ejecutada en este equipo Windows con Docker Linux y entorno Python nuevo; queda pendiente que el jefe de grupo repita la guía en su computadora.
- Acceso, permisos y publicación del remoto GitHub no se han probado mediante push. El repositorio local se preparó sin alterar historiales previos; no existía uno en esta carpeta.
- No se ha hecho commit ni push. Se requiere autorización para el commit definitivo.
- La auditoría de patrones no sustituye una evaluación jurídica de redistribución de la fuente presupuestaria.
- El dashboard usa un usuario con permisos originales; cada transacción de consulta es de solo lectura. No se creó un rol de servidor con privilegios limitados.
- Los datos son una muestra de 150.000 hechos; no representan el total nacional. La cobertura anual varía y el corte de ejecución de 2025 no está certificado.
- Las evidencias previas al ensayo indicaban correctamente que aún no había restauración completa. Son históricas: el resultado nuevo está en github/restauracion_local.json.

## Comandos para el jefe de grupo

Desde PowerShell, con Git, Docker Desktop y Python 3.11 o superior:

```powershell
git clone https://github.com/Luis-Arhian3011/DataWarehouse-MEF-2022-2025.git
cd DataWarehouse-MEF-2022-2025
python scripts/proyecto.py configurar
python scripts/proyecto.py iniciar
python scripts/proyecto.py restaurar
python scripts/proyecto.py verificar
python -m venv 03_Dashboard/.venv
.\03_Dashboard\.venv\Scripts\python.exe -m pip install -r 03_Dashboard/requirements.txt
.\03_Dashboard\.venv\Scripts\python.exe scripts/proyecto.py dashboard
```

Abrir http://localhost:8501. El clon será posible cuando el propietario publique el repositorio; no se publicó durante esta preparación.

Para detener: Ctrl+C y python scripts/proyecto.py detener. Para volver: iniciar y dashboard, sin repetir restaurar. No se necesita ETL ni descargar el CSV original. Los detalles de configuración, errores y comprobaciones están en el README principal.
