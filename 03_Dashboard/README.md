# Dashboard portable

Desde la raíz del repositorio:

```powershell
python -m venv 03_Dashboard/.venv
.\03_Dashboard\.venv\Scripts\python.exe -m pip install -r 03_Dashboard/requirements.txt
.\03_Dashboard\.venv\Scripts\python.exe scripts/proyecto.py dashboard
```

Necesita configurar/iniciar/restaurar previamente el entorno, siguiendo ../README.md. Abre http://localhost:8501. --puerto 8502 permite otro puerto.

El lanzador carga el .env privado y ejecuta Streamlit desde esta carpeta para aplicar el tema. El transporte compose descubre el servicio del proyecto, sin depender del nombre físico del contenedor o del usuario de Windows. MEF_TRANSPORT=tcp usa host/puerto/credenciales de la configuración; docker conserva la compatibilidad local con MEF_CONTAINER.

Las consultas, cálculos, seis secciones y diseño se mantienen. PostgreSQL agrega antes de transferir datos; Pandas recibe agregados. Se usa caché, parámetros escapados/psycopg y transacciones de solo lectura.

```powershell
.\03_Dashboard\.venv\Scripts\python.exe scripts/proyecto.py pruebas
```

Son 117 controles de datos/interfaz. Las pruebas visuales opcionales requieren requirements-dev.txt y Chrome; aceptan MEF_DASHBOARD_URL y MEF_EVIDENCIAS para separar servidor y resultados.

Los importes conservan Decimal para cálculo/CSV, formato de miles en tablas y No aplica para cálculos sin base válida. El ranking porcentual incluye PIM/hechos. Las advertencias muestrales, cobertura variable y corte 2025 no certificado permanecen visibles.
