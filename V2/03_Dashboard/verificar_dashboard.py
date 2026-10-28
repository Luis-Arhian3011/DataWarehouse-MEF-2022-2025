"""Verificacion integral V2. Todas las consultas son SELECT en modo solo lectura."""
import csv,io,json,os,subprocess,sys,time,hashlib
from pathlib import Path
from decimal import Decimal
from dataclasses import replace
from datetime import datetime,timezone
import pandas as pd
from streamlit.testing.v1 import AppTest
import datos as d
from presentacion import tabla_estilo

ROOT=Path(__file__).resolve().parent
REPORT=ROOT.parent/"05_Pruebas_y_Evidencias/ejecuciones"
def main():
    started=time.monotonic()
    checks=[]
    def check(label,condition):
        if not condition:raise AssertionError(label)
        checks.append(label);print("OK: "+label,flush=True)
    # SQL independiente: semijoins por FK; no reutiliza builder ni vistas de cohorte.
    def independent(filters,scope,monthly=False):
        params=[list(filters.anios),list(filters.niveles)]
        parts=["f.anio_key=ANY(%s::smallint[])","f.entidad_key IN (SELECT entidad_key FROM mef.dim_entidad WHERE nivel_gobierno=ANY(%s::text[]))"]
        for values,clause in [(filters.entidades,"f.entidad_key=ANY(%s::bigint[])"),(filters.funciones,"f.funcion_key IN (SELECT funcion_key FROM mef.dim_funcion WHERE funcion=ANY(%s::text[]))"),(filters.fuentes,"f.financiamiento_key IN (SELECT financiamiento_key FROM mef.v_financiamiento_conformado WHERE fuente_financiamiento=ANY(%s::text[]))")]:
            if values is not None:
                parts.append(clause);params.append(list(values))
        if not monthly and scope=="cohorte":parts.append("f.hecho_key IN (SELECT hecho_anual_key FROM auditoria.serie_seleccionada)")
        table="mef.fact_devengado_mensual" if monthly else "mef.fact_ejecucion_presupuestaria_anual"
        measures=["devengado"] if monthly else list(d.MEASURES)
        sums=",".join("COALESCE(sum(f."+m+"),0) "+m for m in measures)
        with d.conectar() as connection:
            with connection.cursor() as cur:
                cur.execute("SELECT count(*) hechos,"+sums+" FROM "+table+" f WHERE "+" AND ".join(parts),tuple(params))
                return cur.fetchone()
    quality=d.calidad()
    check("Conexion exclusiva V2 y transaccion de solo lectura",quality["base"]==d.DATABASE and quality["solo_lectura"]=="on")
    check("150000 hechos por proceso, 9 dimensiones, 12 tablas y 22 FK",all(quality[k]==v for k,v in dict(hechos_anuales=150000,hechos_mensuales=150000,dimensiones=9,tablas=12,fk=22,series=12500,periodos=48,fk_sin_validar=0).items()))
    metadata=json.loads((ROOT.parent/"01_Base_de_Datos/respaldo/dw_mef_2022_2025_v2_completo_20261028T170603643031Z.json").read_text())
    annual_order=metadata["annual_measure_order"]
    raw=d.consultar("SELECT anio_key,"+",".join("sum("+m+") "+m for m in annual_order)+" FROM mef.fact_ejecucion_presupuestaria_anual GROUP BY anio_key ORDER BY 1")
    check("28 sumas anuales contra respaldo",len(raw)==4 and all([row["anio_key"]]+[str(row[m]) for m in annual_order]==expected for row,expected in zip(raw,metadata["annual_totals"])))
    actual_months=d.mensual()
    check("48 controles mensuales contra respaldo",[(int(r.anio)*100+int(r.mes),str(r.devengado)) for r in actual_months.itertuples()]==[tuple(x) for x in metadata["monthly_totals"]])
    sample=d.consultar("""SELECT f.entidad_key,u.funcion,r.fuente_financiamiento,count(*) hechos
      FROM mef.fact_devengado_mensual f JOIN mef.dim_entidad e USING(entidad_key)
      JOIN mef.dim_funcion u USING(funcion_key) JOIN mef.v_financiamiento_conformado r USING(financiamiento_key)
      WHERE f.anio_key=2024 AND e.nivel_gobierno='M'
      GROUP BY 1,2,3 ORDER BY 4 DESC LIMIT 1""")[0]
    cases=[
        ("completo",d.Filtros()),("un_anio",d.Filtros(anios=(2022,))),
        ("local_2024",d.Filtros(anios=(2024,),niveles=("M",))),
        ("entidad",d.Filtros(entidades=(sample["entidad_key"],))),
        ("funcion",d.Filtros(funciones=(sample["funcion"],))),
        ("fuente",d.Filtros(fuentes=(sample["fuente_financiamiento"],))),
        ("combinados",d.Filtros(anios=(2024,),niveles=("M",),entidades=(sample["entidad_key"],),funciones=(sample["funcion"],),fuentes=(sample["fuente_financiamiento"],))),
        ("salto_anios",d.Filtros(anios=(2022,2024))),
        ("sin_anios",d.Filtros(anios=())),("sin_gobiernos",d.Filtros(niveles=())),
        ("sin_entidades",d.Filtros(entidades=())),("inexistente",d.Filtros(entidades=(999999999,))),
        ("literal_parametrizado",d.Filtros(fuentes=("1' OR '1'='1",)))]
    for name,filters in cases:
        for scope in d.SCOPES:
            expected=independent(filters,scope)
            observed=d.resumen(filters,scope)
            check("SQL independiente anual "+name+"/"+scope,observed["hechos"]==expected["hechos"] and all(observed[m]==expected[m] for m in d.MEASURES))
            expected_rate=Decimal(100)*observed["devengado"]/observed["pim"] if observed["pim"]>0 else None
            check("Denominador y porcentaje "+name+"/"+scope,(observed["ejecucion_pct"] is None if expected_rate is None else abs(observed["ejecucion_pct"]-expected_rate)<Decimal("1e-12")))
        expected=independent(filters,"cohorte",True);observed=d.mensual(filters)
        check("SQL independiente mensual "+name,(sum(observed["devengado"],Decimal(0)) if not observed.empty else Decimal(0))==expected["devengado"] and (int(observed["hechos"].sum()) if not observed.empty else 0)==expected["hechos"])
        reconciliation=d.conciliacion(filters)
        check("Sin doble conteo "+name,all(r.diferencia==0 and r.meses==12*r.series for r in reconciliation.itertuples()))
    for scope in d.SCOPES:
        summary=d.resumen(scope=scope)
        for group in d.GROUPS:
            frame=d.agrupado(group,scope=scope)
            check("Agrupacion conserva medidas "+group+"/"+scope,all(sum(frame[m],Decimal(0))==summary[m] for m in d.MEASURES) and int(frame["hechos"].sum())==summary["hechos"])
            before=frame.copy(deep=True);tabla_estilo(frame)
            check("Formato no modifica Decimal "+group+"/"+scope,frame.equals(before))
            exported=list(csv.DictReader(io.StringIO(d.exportar(frame).decode("utf-8-sig")),delimiter=";"))
            check("CSV conserva centimos "+group+"/"+scope,len(exported)==len(frame) and all(Decimal(row[d.LABELS[m]].replace(",","."))==frame.iloc[i][m] for i,row in enumerate(exported) for m in d.MEASURES))
    # Roles de fuente/rubro: contraste contra el almacenamiento heredado.
    ro=d.agrupado("fuente")
    observed=sum(ro.loc[ro.codigo=="1","devengado"],Decimal(0))
    expected=d.consultar("SELECT sum(devengado) valor FROM mef.fact_ejecucion_presupuestaria_anual WHERE financiamiento_key IN (SELECT financiamiento_key FROM mef.dim_financiamiento WHERE rubro='1')")[0]["valor"]
    check("Fuente 1 conformada concilia con rubro heredado 1",observed==expected)
    unit=subprocess.run([sys.executable,"-B","-m","unittest","discover","-s",str(ROOT/"tests"),"-v"],capture_output=True,text=True)
    check("Pruebas unitarias de seguridad y presentacion",unit.returncode==0)
    app=AppTest.from_file(str(ROOT/"app.py"),default_timeout=40).run()
    sections=["Resumen ejecutivo","Presupuesto anual","Evolución mensual","Comparación de ejercicios","Análisis por dimensiones","Metodología y calidad"]
    for scope in d.SCOPES:
        app.selectbox(key="scope").set_value(scope).run()
        for section in sections:
            app.radio(key="seccion").set_value(section).run()
            check("AppTest "+section+"/"+scope,not app.exception and not app.error)
    app.radio(key="seccion").set_value("Resumen ejecutivo").run()
    app.multiselect(key="anios").set_value([2024]).run()
    app.multiselect(key="niveles").set_value(["M"]).run()
    app.multiselect(key="entidades").set_value([sample["entidad_key"]]).run()
    app.multiselect(key="funciones").set_value([sample["funcion"]]).run()
    app.multiselect(key="fuentes").set_value([sample["fuente_financiamiento"]]).run()
    filters=cases[6][1];expected=d.resumen(filters,"cohorte")
    check("Filtros combinados de interfaz cambian el KPI",not app.exception and not app.error and app.metric[1].value==f'{expected["hechos"]:,.0f}'.replace(",","." ))
    app.multiselect(key="anios").set_value([]).run()
    check("Interfaz con anios vacios no amplia datos",not app.exception and not app.error and len(app.metric)==0 and any("Selecciona al menos" in x.value for x in app.info))
    # Reiniciar sesion para probar rango mensual sin filtros previos.
    app=AppTest.from_file(str(ROOT/"app.py"),default_timeout=40).run()
    app.radio(key="seccion").set_value("Evolución mensual").run()
    app.slider(key="meses_visibles").set_value((4,6)).run()
    app.radio(key="vista_mensual").set_value("acumulado").run()
    check("Rango mensual y acumulado disponibles",not app.exception and not app.error and len(app.dataframe[0].value)==12)
    check("Acumulado visible conserva enero a marzo",all(row["Acumulado desde enero (S/)"]==actual_months[(actual_months.anio==row["Año"])&(actual_months.mes==row["Mes"])].iloc[0]["acumulado"] for _,row in app.dataframe[0].value.iterrows()))
    app.radio(key="seccion").set_value("Análisis por dimensiones").run()
    for group in d.GROUPS:
        app.selectbox(key="dimension").set_value(group).run()
        app.selectbox(key="indicador").set_value("ejecucion_pct").run()
        check("Ranking porcentual "+group,not app.exception and not app.error)
    app.text_input(key="buscar_dimension").set_value("NO_EXISTE_987654321").run()
    check("Busqueda sin coincidencias clara",not app.exception and not app.error and any("No hay coincidencias" in x.value for x in app.info))
    protected=ROOT.parent;verified=0
    for line in (protected/"SHA256SUMS.txt").read_text(encoding="utf-8-sig").splitlines():
        digest,name=line.split(maxsplit=1)
        actual=hashlib.sha256((protected/name.lstrip("*")).read_bytes()).hexdigest()
        if actual!=digest:raise AssertionError("Archivo entregado cambiado: "+name)
        verified+=1
    check("Archivos del paquete con SHA-256 correcto",verified>0)
    backup=ROOT.parent/"01_Base_de_Datos/respaldo/dw_mef_2022_2025_v2_completo_20261028T170603643031Z.dump"
    check("Respaldo V2 sin cambios",hashlib.sha256(backup.read_bytes()).hexdigest()==metadata["sha256"])
    result=dict(status="correcto",utc=datetime.now(timezone.utc).isoformat(),checks=len(checks),check_names=checks,unit_tests=unit.stdout+unit.stderr,elapsed_seconds=round(time.monotonic()-started,3),quality=quality,protected_hashes_verified=verified,all_queries_read_only=True,databases_modified=False)
    path=REPORT/("verificacion_"+str(time.time_ns())+".json")
    with path.open("x",encoding="utf-8") as stream:json.dump(result,stream,ensure_ascii=False,indent=2,default=str)
    print("EVIDENCIA: "+str(path),flush=True)
if __name__=="__main__":main()
