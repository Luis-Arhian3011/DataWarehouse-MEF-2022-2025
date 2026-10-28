# Dashboard MEF V2

Seis vistas: resumen, presupuesto anual, evolución mensual, comparación, dimensiones y metodología/calidad. Código independiente de los proyectos originales; consultas agregadas exclusivamente de solo lectura a dw_mef_2022_2025_v2.

## Ejecutar desde la raíz de la entrega

    .\.venv\Scripts\python.exe -B scripts\proyecto.py dashboard

Abrir http://127.0.0.1:8502. Si ese puerto está ocupado por otra aplicación:

    .\.venv\Scripts\python.exe -B scripts\proyecto.py dashboard --puerto-web 8504

También puede ejecutarse directamente:

    cd 03_Dashboard
    ..\.venv\Scripts\python.exe -m streamlit run app.py --server.address 127.0.0.1 --server.port 8502
    cd ..

La configuración se lee desde variables PG*, secrets.toml local o .env de la raíz, en ese orden. El puerto PostgreSQL por defecto de la entrega es 55432. No copiar secretos de otras instalaciones; usar la plantilla y configuración privada propia.

## Cobertura y reglas

Muestra anual completa: 150.000 hechos. Cohorte anual comparable: 12.500 padres; el mensual tiene 150.000 observaciones, doce por serie. El resumen distingue conteos globales de 300.000 hechos frente a los KPI filtrados.

PIM agregado no positivo: no calculable. Ejecución superior al 100 %: se conserva. No se promedian porcentajes individuales, no se suman etapas ni se combina devengado anual y mensual. Los 324 registros mensuales negativos se conservan.

Las tarjetas adaptan soles, miles y millones; tablas y CSV conservan Decimal. Una selección incompatible se retira con aviso y queda restringida si se vacía: no consulta todas las entidades sin confirmación. Los colores de año permanecen fijos.

El rango de meses afecta solo la vista mensual. El acumulado se calcula desde enero antes de recortar meses visibles. Las opciones de entidad/función/fuente dependen de años y gobierno. La búsqueda de dimensiones restringe solo esa vista.

La muestra no representa automáticamente el gasto nacional. Las partidas y cobertura pueden cambiar entre años. La fecha de corte de ejecución 2025 no está certificada.

## Verificar

    .\.venv\Scripts\python.exe -B 03_Dashboard\verificar_dashboard.py
    .\.venv\Scripts\python.exe -B 03_Dashboard\verificar_correcciones.py --evidencias 05_Pruebas_y_Evidencias\fixtures

Para la prueba visual opcional, instalar requirements-dev.txt, tener Chrome local y la aplicación iniciada:

    .\.venv\Scripts\python.exe -B 03_Dashboard\verificar_visual.py

MEF_V2_URL permite indicar otra URL local si se cambia el puerto web. Las salidas se guardan en 05_Pruebas_y_Evidencias/ejecuciones. La prueba no descarga navegadores.

Conexión limitada a cinco segundos, consultas de quince segundos y caché de cinco minutos con entradas acotadas. Reiniciar Streamlit tras cambiar módulos de Python o configuración. No se cargan hechos completos en Pandas ni se ejecutan ETL o restauraciones desde la interfaz.

[Manual principal](../README.md) · [Pruebas](../05_Pruebas_y_Evidencias/README.md).
