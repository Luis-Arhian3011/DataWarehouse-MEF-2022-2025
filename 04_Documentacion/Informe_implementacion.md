> Copia documental de la implementación validada. Las referencias a rutas y estados históricos pertenecen al proyecto original; para ejecutar esta entrega utiliza los README de sus carpetas. Las evidencias seleccionadas están en ../05_Evidencias.

# Implementacion MEF 2022?2025 completada

Base nueva: dw_mef_2022_2025. Contenedor: postgres-db. Rol: luchito.

Creacion y carga realizadas despues de autorizacion expresa. No se modifico la base anterior ni el CSV. No se eliminaron contenedores o volumenes.

## Verificacion real en PostgreSQL

| Tabla | Registros |
| --- | ---: |
| mef.dim_anio | 4 |
| mef.dim_financiamiento | 114 |
| mef.dim_funcion | 356 |
| mef.dim_clasificador_gasto | 476 |
| mef.dim_entidad | 2898 |
| mef.dim_intervencion | 18654 |
| mef.dim_meta | 121305 |
| mef.fact_ejecucion_presupuestaria_anual | 150000 |

150000 claves de origen anual distintas y 150000 granos dimensionales distintos. Siete FK validadas; cero huerfanos; cero contextos de meta incorrectos. La union de las dimensiones conserva 150000 filas. Las 28 sumas anio/medida coinciden exactamente con el manifiesto.

| Anio | Hechos |
| --- | ---: |
| 2022 | 37500 |
| 2023 | 37500 |
| 2024 | 37500 |
| 2025 | 37500 |

| Nivel | Hechos | Entidades |
| --- | ---: | ---: |
| E | 23565 | 401 |
| M | 98105 | 1933 |
| R | 28330 | 564 |

Filas seleccionadas con al menos un importe negativo: 7. Signos preservados.

## Validez y limites de 2025

PIA 2025 del archivo completo: S/ 251801045185.00, igual a Ley 32185 en total, nueve genericas y tres niveles. La repeticion exacta con 2026 esta documentada, pero su causa no es determinable con el archivo. No se certifica de manera independiente la fecha de corte ni el cierre de ejecucion. 2025 se utiliza como instantanea de la fuente para el proyecto academico. Se extraen exclusivamente las medidas _2025; no hay anio 2026 en dimensiones/hechos.

2025 tiene 4943 granos ambiguos y 9886 filas separadas. En los cuatro anios se conservan fuera de la poblacion seleccionada 11658 granos ambiguos y 23316 filas, sin borrarlos de auditoria ni sumarlos automaticamente. La muestra no valida el universo completo.

## Comparaciones y conservacion

Las nueve consultas SQL se ejecutaron correctamente en modo de solo lectura. Incluyen LAG para comparar los cuatro ejercicios. Sumas y variaciones describen las muestras, no gasto nacional completo. Se conservan cuotas y pesos; la muestra tiene 37500 hechos por ejercicio.

Se leyeron nuevamente los conteos y 21 sumas de dw_mef_2022_2024: coinciden exactamente con su manifiesto inicial; conserva 150000 hechos. Los hashes de los archivos de control de implementacion anterior siguen iguales.

## Uso

~~~powershell
docker exec -it postgres-db psql -U luchito -d dw_mef_2022_2025
~~~

Repetir verificacion sin modificar PostgreSQL: python verificar.py, desde esta carpeta. No volver a ejecutar etl.py sobre una base cargada: rechaza objetos existentes y no trunca tablas.

Evidencias actuales: verificacion_postgresql.json, implementacion_completada.json, base_anterior_verificada_sin_cambios.json y consultas_analisis_resultados.txt en evidencias/. Los archivos preparacion.json, estado_pre_autorizacion.json y manifest.json conservan el estado y procedencia anteriores a la carga.
