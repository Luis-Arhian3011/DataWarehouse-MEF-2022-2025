"""Regresion de los seis hallazgos; SQL solo de lectura y comparacion con linea base."""
import argparse,ast,hashlib,json,sys,time
from pathlib import Path
from decimal import Decimal
from streamlit.testing.v1 import AppTest
import datos as d
from presentacion import dinero,YEAR_COLORS,evolucion
ROOT=Path(__file__).resolve().parent

def canonical_frame(frame):
    rows=[{key:(str(value) if isinstance(value,Decimal) else value) for key,value in row.items()} for row in frame.to_dict("records")]
    return sorted(rows,key=lambda row:json.dumps(row,sort_keys=True,ensure_ascii=False))
def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--evidencias",type=Path,required=True)
    args=parser.parse_args();out=args.evidencias.resolve()
    if not out.is_relative_to(ROOT.parent/"05_Pruebas_y_Evidencias"):raise ValueError("Salida fuera de las evidencias del dashboard")
    checks=[]
    def check(name,value,details=None):
        if not value:raise AssertionError(name)
        checks.append(dict(name=name,passed=True,details=details));print("OK: "+name,flush=True)
    baseline=json.loads((out/"BASELINE_RESULTADOS.json").read_text(encoding="utf-8"))
    fixture=json.loads((out/"evidencias/fixture_descargas.json").read_text(encoding="utf-8"))
    selected=d.Filtros(anios=(2024,),niveles=("M",),entidades=(fixture["entidad_key"],),funciones=(fixture["funcion"],),fuentes=(fixture["fuente_financiamiento"],))
    frames={}
    for name,filters in [("global",d.Filtros()),("filtrado",selected)]:
        for scope in d.SCOPES:
            frames[name+"/anual/"+scope]=d.anual(filters,scope)
            for group in d.GROUPS:frames[name+"/"+group+"/"+scope]=d.agrupado(group,filters,scope)
        frames[name+"/mensual"]=d.mensual(filters)
        frames[name+"/conciliacion"]=d.conciliacion(filters)
    for name,frame in frames.items():
        before=baseline[name]
        check("Agregados sin cambios "+name,list(frame.columns)==before["columns"] and canonical_frame(frame)==before["rows"])
        raw=d.exportar(frame)
        # La unica diferencia autorizada del CSV es la etiqueta de la columna negativos.
        normalized=raw.decode("utf-8").replace("Registros mensuales negativos","Meses negativos").encode("utf-8")
        check("CSV original conservado "+name,hashlib.sha256(normalized).hexdigest()==before["csv_sha256"])
    old=ast.parse((out/"antes/dashboard/datos.py").read_text(encoding="utf-8"))
    new=ast.parse((ROOT/"datos.py").read_text(encoding="utf-8"))
    def sql_ast(tree):
        names={"Filtros","base","condicion","resumen","anual","mensual","agrupado","catalogos","entidades_comunes","conciliacion","calidad","exportar","JOINS","SUMS","METRICS","GROUPS"}
        tree.body=[node for node in tree.body if (getattr(node,"name",None) in names or isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id in names for t in node.targets))]
        return ast.dump(tree,include_attributes=False)
    check("Consultas monetarias identicas pese a configuracion portable",sql_ast(old)==sql_ast(new))
    def app():return AppTest.from_file(str(ROOT/"app.py"),default_timeout=40).run()
    def html(at):return "\n".join(x.value for x in at.markdown)
    at=app()
    check("Tres conteos globales explicitos sin duplicar KPI",all(x in html(at) for x in ("150.000 hechos anuales","150.000 hechos mensuales","300.000 hechos en total")) and html(at).count("300.000 hechos en total")==1 and len(at.metric)==3)
    at.multiselect(key="anios").set_value([2024]).run()
    check("Conteos globales no cambian con anio", "300.000 hechos en total" in html(at) and at.metric[1].value=="37.500")
    # Caso real de centimos que se mostraba como cero millones.
    at=app()
    for key,values in [("anios",[2025]),("niveles",["M"]),("entidades",[1545]),("funciones",["15"]),("fuentes",["2"])]:
        at.multiselect(key=key).set_value(values).run()
    check("Centimo real visible sin redondearlo a cero millones","S/ 0,01" in html(at) and not at.exception and not at.error)
    # Retiro total, persistencia y recuperacion al elegir una entidad compatible.
    at=app();at.multiselect(key="entidades").set_value([2046]).run()
    at.multiselect(key="niveles").set_value(["E"]).run()
    check("Filtro incompatible no amplía",not at.exception and not at.error and not at.metric and any("selección vacía" in x.value for x in at.warning))
    at.radio(key="seccion").set_value("Evolución mensual").run()
    check("Bloqueo persiste al cambiar de seccion",not at.dataframe and not at.error and not at.exception and any("No hay series" in x.value for x in at.info))
    at.radio(key="seccion").set_value("Resumen ejecutivo").run()
    at.multiselect(key="niveles").set_value(["M"]).run()
    at.multiselect(key="entidades").set_value([2046]).run()
    check("Seleccion compatible recupera solo su entidad",at.metric[1].value=="412" and at.metric[2].value=="1")
    at.multiselect(key="niveles").set_value(["E"]).run()
    at.button(key="restablecer_entidades").click().run()
    expected=d.resumen(d.Filtros(niveles=("E",)))
    check("Expansion solo por boton explicito",at.metric[1].value==format(expected["hechos"],",.0f").replace(",","."))
    # Reajuste parcial conserva la entidad compatible y avisa.
    national=d.catalogos((2022,2023,2024,2025),("E",))["entidades"][0]["entidad_key"]
    at=app();at.multiselect(key="entidades").set_value([2046,national]).run()
    at.multiselect(key="niveles").set_value(["E"]).run()
    check("Reajuste parcial no elimina la restriccion",at.multiselect(key="entidades").value==[national] and at.metric[2].value=="1" and any("Se retiraron" in x.value for x in at.warning))
    # Los filtros de funcion y fuente tambien conservan vacio restringido si desaparecen.
    from filtros_ui import reajustar_seleccion,filtro_efectivo
    for kind in ("entidades","funciones","fuentes"):
        valid,locked,_=reajustar_seleccion(("fuera",),("dentro",))
        check("Guardia vacia reusable "+kind,filtro_efectivo(valid,locked)==())
    at=app();at.radio(key="seccion").set_value("Evolución mensual").run()
    check("Etiqueta negativa y 324 registros sin alteracion","Registros mensuales negativos" in html(at) and "Meses negativos" not in html(at) and int(d.mensual()["negativos"].sum())==324)
    full=evolucion(d.mensual(),"devengado")
    expected_colors={int(trace.name):trace.line.color for trace in full.data}
    check("Cuatro colores por anio",expected_colors==YEAR_COLORS)
    at.multiselect(key="anios").set_value([2024]).run()
    spec=json.loads(at.get("plotly_chart")[0].proto.spec)
    check("Color de 2024 en mensual filtrado",spec["data"][0]["line"]["color"]==YEAR_COLORS[2024])
    at.radio(key="seccion").set_value("Presupuesto anual").run()
    spec=json.loads(at.get("plotly_chart")[1].proto.spec)
    check("Color de 2024 consistente al cambiar de seccion",spec["data"][0]["marker"]["color"]==[YEAR_COLORS[2024]])
    readme=(ROOT.parent/"README.md").read_text(encoding="utf-8")
    check("README refleja implementacion y recuperacion",all(x in readme for x in ("implementado y validado","150.000","300.000","22","restauración","pg_restore","proyecto.py dashboard","proyecto.py restaurar","--autorizar")) and "no se ha creado ni cargado" not in readme)
    check("Solo lectura y base V2",d.calidad()["base"]==d.DATABASE and d.calidad()["solo_lectura"]=="on")
    result=dict(status="correcto",checks=len(checks),details=checks,monetary_queries_unchanged=True,baseline_outputs=len(frames),databases_modified=False)
    path=ROOT.parent/"05_Pruebas_y_Evidencias/ejecuciones"/("regresion_"+str(time.time_ns())+".json")
    with path.open("x",encoding="utf-8") as f:json.dump(result,f,ensure_ascii=False,indent=2,default=str)
    print("REGRESION: "+str(path),flush=True)
if __name__=="__main__":main()
