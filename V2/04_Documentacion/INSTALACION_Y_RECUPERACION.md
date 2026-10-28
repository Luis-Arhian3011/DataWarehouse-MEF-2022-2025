# Instalación, respaldo y recuperación

## Requisitos

Python 3.11+, Docker Desktop con Compose y acceso al motor Docker. Servidor y herramientas PostgreSQL 15; respaldo generado con 15.19. Se recomienda la misma versión mayor. El entorno original probado fue Windows con Python 3.13 y PostgreSQL 15.19.

Crear un entorno Python convencional e instalar requirements.txt. No se incluyen entornos virtuales, navegadores o dependencias binarias de la máquina original.

Copiar .env.example a .env solo si no existe. Completar PGUSER y PGPASSWORD privadamente. No usar contraseñas reales en archivos públicos. Compose usa esas variables para el servidor; la base inicial es postgres y la base V2 se crea después.

## Docker independiente

    docker compose up -d

Proyecto predeterminado mef-v2-entrega, volumen nuevo propio y puerto 55432 enlazado a 127.0.0.1. No se asigna el nombre postgres-db ni se reutilizan volúmenes externos. Si existe una instalación con ese proyecto, revisar su identidad antes de operar. Cambiar PGPORT en .env si está ocupado.

No se ejecutó up durante el empaquetado. No se afirma una instalación nueva satisfactoria sin realizarla.

## Restaurar el respaldo

    .\.venv\Scripts\python.exe -B scripts\proyecto.py diagnostico
    .\.venv\Scripts\python.exe -B scripts\proyecto.py restaurar --autorizar
    .\.venv\Scripts\python.exe -B scripts\proyecto.py verificar

El procedimiento verifica hash, versión, identidad entre TCP y Compose, propiedad del contenedor por el proyecto y ausencia de V2. Rechaza postgres-db. Crea exclusivamente dw_mef_2022_2025_v2 si no existe.

El dump se transmite como binario por stdin, sin tuberías de texto de PowerShell. Opciones: --no-owner --no-privileges --exit-on-error --single-transaction. No usa --clean ni --create. Los propietarios/ACL originales no son un requisito para el rol de destino; esta vía no restaura roles globales ni sus contraseñas.

Si falla, conserva la base nueva y el registro. No elimina, limpia ni reintenta automáticamente. Si el destino ya existe, detenerse y solicitar una decisión: no restaurar encima.

## Verificación esperada

Doce tablas: nueve dimensiones, dos hechos y una tabla técnica. 150.000 hechos anuales, 150.000 mensuales, 12.500 series de doce meses y 48 períodos. Veintidós FK validadas, cero huérfanos y conciliación exacta de 28 sumas anuales, 48 mensuales y suma de meses de cada serie. Se conservan 324 registros negativos y 124.976 ceros mensuales.

La verificación portable coteja también el snapshot anual incluido. El informe histórico de restauración acredita una comparación completa de todas las filas, índices, vistas y secuencias en el servidor original. No es evidencia de que este nuevo flujo Compose haya sido restaurado durante el empaquetado.

## Comprobar o generar un respaldo futuro

El respaldo incluido y su hash son inmutables. Para consultar sus contenidos, utilizar pg_restore --list con un cliente compatible. Esa operación no equivale a restaurar los datos.

Para un respaldo nuevo autorizado en una instalación futura, usar pg_dump --format=custom desde el servicio de ese proyecto, guardando stdout binario en un archivo nuevo y exclusivo. Nunca redirigir un dump binario mediante una tubería de texto de PowerShell, sobrescribir el incluido ni publicar roles globales con contraseñas.

Registrar versión, fecha, tamaño, SHA-256, salida de pg_restore --list y después probar restauración en un destino independiente. No se generó otro respaldo en esta entrega.

[Guía principal](../README.md) · [Prueba histórica real](../05_Pruebas_y_Evidencias/historicas/RESTAURACION.md).
