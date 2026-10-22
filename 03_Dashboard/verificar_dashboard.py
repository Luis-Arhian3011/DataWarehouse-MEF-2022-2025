"""Verificación reproducible de consultas y seis secciones. No escribe en PostgreSQL."""
from pathlib import Path
from decimal import Decimal
from dataclasses import replace
from datetime import datetime, timezone
import json
import os
import csv
import io
from datos import *
from streamlit.testing.v1 import AppTest

def main():
    manifest=json.loads((ROOT.parent/"02_ETL_Python"/"manifest.json").read_text(encoding="utf-8"))
    report={"fecha_utc":datetime.now(timezone.utc).isoformat(),"base":configuracion()["dbname"],"comprobaciones":[]}
    def check(name, condition):
        if not condition:
            raise AssertionError(name)
        report["comprobaciones"].append(name)
        print("OK:",name)
    with conectar() as conn:
        row=conn.execute("SELECT current_database() base,current_setting('transaction_read_only') solo_lectura").fetchone()
        check("Conexión a base oficial y transacción de solo lectura",row["base"]==report["base"] and row["solo_lectura"]=="on")
    df=anual()
    check("Cuatro años, 150000 hechos y 37500 por año",list(df.anio)==[2022,2023,2024,2025] and sum(df.hechos)==150000 and all(df.hechos==37500))
    for expected in manifest["expected_by_year"]:
        row=df[df.anio==expected["anio"]].iloc[0]
        for m in MEASURES:
            check(f"Conciliación exacta {expected['anio']} / {m}",row[m]==Decimal(expected[m]))
    r=resumen()
    check("Ejecución como razón de sumas",abs(r["ejecucion_pct"]-100*r["devengado"]/r["pim"])<Decimal("0.0000000000001"))
    q=calidad()
    check("Unicidad del origen anual y del grano",q["hechos"]==q["claves_origen"]==q["granos"]==150000)
    check("Siete hechos con negativos preservados",q["filas_negativas"]==7)
    fk=consultar("""SELECT count(*) n FROM pg_constraint WHERE conrelid='mef.fact_ejecucion_presupuestaria_anual'::regclass
        AND contype='f' AND convalidated""")[0]["n"]
    check("Siete claves foráneas validadas",fk==7)
    dims=[("anio","anio"),("entidad","entidad"),("intervencion","intervencion"),("funcion","funcion"),
        ("meta","meta"),("financiamiento","financiamiento"),("clasificador_gasto","clasificador_gasto")]
    join=" ".join(f"LEFT JOIN mef.dim_{d} d{i} ON d{i}.{k}_key=f.{k}_key" for i,(d,k) in enumerate(dims))
    nulls=" OR ".join(f"d{i}.{k}_key IS NULL" for i,(d,k) in enumerate(dims))
    check("Sin huérfanos en las siete dimensiones",consultar("SELECT count(*) n FROM mef.fact_ejecucion_presupuestaria_anual f "+join+" WHERE "+nulls)[0]["n"]==0)
    maxrows=0
    for group in GROUPS:
        agg=agrupado(group)
        maxrows=max(maxrows,len(agg))
        check("Conciliación agrupada: "+group,all(sum(agg[m])==r[m] for m in MEASURES) and sum(agg.hechos)==r["hechos"])
    for level in LEVELS:
        sub=resumen(Filtros(niveles=(level,)))
        check("Filtro nivel "+level,sub["hechos"]>0)
    check("Gobiernos locales incluidos",resumen(Filtros(niveles=("M",)))["hechos"]==98105)
    check("Filtro vacío no amplía la selección",resumen(Filtros(anios=()))["hechos"]==0 and resumen(Filtros(entidades=()))["hechos"]==0)
    entity=entidades_disponibles((2022,),("M",))[0]["entidad_key"]
    check("Filtro combinado año/nivel/entidad",resumen(Filtros((2022,),("M",),(entity,)))["entidades"]==1)
    common=entidades_comunes(Filtros())
    check("Cohorte común tiene cuatro años por entidad",all(x["anios"]==4 for x in entidades_disponibles(Filtros().anios,Filtros().niveles) if x["entidad_key"] in common))
    payload=exportar(df).decode("utf-8-sig")
    parsed=list(csv.DictReader(io.StringIO(payload),delimiter=";"))
    check("CSV preserva céntimos exactos",Decimal(parsed[0]["Devengado (S/)"].replace(",","."))==df.iloc[0]["devengado"])
    app=AppTest.from_file(str(ROOT/"app.py"),default_timeout=35).run()
    check("Inicio de la aplicación",not app.exception and not app.error)
    sections=["Resumen ejecutivo","Análisis temporal","Niveles de gobierno","Análisis por entidad","Distribución del gasto","Metodología y calidad"]
    for section in sections:
        app.radio(key="navegacion").set_value(section).run()
        check("Vista: "+section,not app.exception and not app.error and len(app.subheader)>0)
        if section=="Distribución del gasto":
            for perspective in ["Funciones presupuestarias","Fuentes de financiamiento","Genéricas de gasto","Categorías de gasto"]:
                app.radio(key="perspectiva").set_value(perspective).run()
                check("Distribución: "+perspective,not app.exception and not app.error)
        if section=="Análisis por entidad":
            app.text_input(key="busqueda").set_value("zz_sin_resultados_zz").run()
            check("Búsqueda sin coincidencias",any("No hay entidades" in x.value for x in app.info))
            app.text_input(key="busqueda").set_value("").run()
            app.selectbox(key="metrica").set_value("ejecucion_pct").run()
            check("Ranking por ejecución",not app.error and not app.exception)
    app.multiselect(key="anios").set_value([]).run()
    check("Interfaz con filtros vacíos",not app.error and not app.exception and any("no devuelven" in x.value for x in app.info))
    app.multiselect(key="anios").set_value([2025]).run()
    app.multiselect(key="niveles").set_value(["M"]).run()
    check("Interfaz 2025 y gobiernos locales",not app.error and not app.exception and len(app.warning)>0)
    from unittest.mock import patch
    with patch.dict(os.environ,{"MEF_TRANSPORT":"tcp","PGPORT":"1"}):
        st.cache_data.clear()
        failed=AppTest.from_file(str(ROOT/"app.py"),default_timeout=15).run()
        check("Error de conexion controlado sin exponer credenciales",not failed.exception and len(failed.error)>0)
    report.update(estado="correcto",pruebas=len(report["comprobaciones"]),max_filas_agregadas=maxrows,
        totales_anuales=df.to_dict("records"),cohorte_comun_entidades=len(common))
    out=Path(os.environ.get("MEF_EVIDENCIAS",str(ROOT/"evidencias")))
    out.mkdir(exist_ok=True)
    (out/"verificacion_dashboard.json").write_text(json.dumps(report,ensure_ascii=False,indent=2,default=str),encoding="utf-8")
    print(f"Verificación completa: {report['pruebas']} pruebas. Máximo {maxrows} filas agregadas por consulta.")
if __name__=="__main__":
    main()
