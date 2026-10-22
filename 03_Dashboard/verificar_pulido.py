"""Comprobaciones adicionales del pulido. Solo lectura y agregados reales."""
import csv
import hashlib
import io
import json
import os
from pathlib import Path
from decimal import Decimal
from datetime import datetime,timezone
import pandas as pd
from pandas.testing import assert_frame_equal
from streamlit.testing.v1 import AppTest
from datos import ROOT,MEASURES,GROUPS,LABELS,anual,agrupado,exportar,relaciones_esquema
from presentacion import formato,tabla_presentada,lectura_serie,lectura_grupos,diagrama_estrella,nombre_corto

def main():
    run=Path(os.environ.get("MEF_EVIDENCIAS",str(ROOT/"evidencias")))/"pulido"
    run.mkdir(parents=True,exist_ok=True)
    results=[]
    def check(label,value):
        if not value: raise AssertionError(label)
        results.append(label)
        print("OK:",label)
    baseline=json.loads((ROOT.parent/"05_Evidencias"/"linea_base_csv.json").read_text(encoding="utf-8"))
    frames={"anual":anual(),**{g:agrupado(g) for g in GROUPS}}
    for name,df in frames.items():
        before=df.copy(deep=True)
        styled=tabla_presentada(df)
        assert_frame_equal(df,before)
        check("Presentación sin mutar agregados: "+name,True)
        data=exportar(df)
        check("CSV idéntico al anterior, incluidos céntimos: "+name,hashlib.sha256(data).hexdigest()==baseline[name])
        rows=list(csv.DictReader(io.StringIO(data.decode("utf-8-sig")),delimiter=";"))
        check("Todos los importes del CSV coinciden: "+name,
            all(Decimal(row[LABELS[m]].replace(",","."))==df.iloc[i][m] for i,row in enumerate(rows) for m in MEASURES))
    check("Miles, céntimos y negativos exactos",formato(Decimal("-1234567.89"))=="-1.234.567,89")
    check("Sin pérdida Decimal en importes grandes",formato(Decimal("999999999999999999.99"))=="999.999.999.999.999.999,99")
    sample=pd.DataFrame({"variacion_pct":[None,Decimal("12.34")],"pim":[Decimal("1234567.89"),Decimal("0.00")]})
    styled=tabla_presentada(sample)
    col=styled.data.columns.get_loc(LABELS["variacion_pct"])
    check("No aplica en celdas sin variación",styled._display_funcs[(0,col)](None)=="No aplica")
    check("Formato monetario aplicado por Styler",styled._display_funcs[(0,styled.data.columns.get_loc(LABELS["pim"]))](sample.pim[0])=="1.234.567,89")
    check("Datos de tabla siguen siendo Decimal",isinstance(styled.data[LABELS["pim"]][0],Decimal))
    temporal=frames["anual"]
    latest=temporal.iloc[-1]
    text=lectura_serie(temporal,["pia","pim","devengado"])
    check("Interpretación temporal procede del agregado real",str(latest.anio) in text and formato(latest.devengado) in text and "muestra" in text)
    for metric in ("pia","pim","devengado","ejecucion_pct"):
        text=lectura_grupos(frames["entidad"],metric)
        top=frames["entidad"].sort_values(metric,ascending=False,kind="stable").iloc[0]
        check("Interpretación de ranking: "+metric,str(top["nombre"]) in text and formato(top[metric]) in text)
    relations=relaciones_esquema()
    check("Siete FK reales validadas hacia PK",len(relations)==7 and all(r["validada"] and r["referencia_pk"] for r in relations))
    diagram=diagrama_estrella(relations)
    check("Diagrama incluye todas las claves y dimensiones",all(r["destino"] in diagram and r["origen"] in diagram and r["referencia"] in diagram for r in relations))
    app=AppTest.from_file(str(ROOT/"app.py"),default_timeout=40).run()
    app.radio(key="navegacion").set_value("Distribución del gasto").run()
    check("Devengado sigue predeterminado",app.selectbox(key="medida_gasto").value=="devengado")
    for perspective in ["Funciones presupuestarias","Fuentes de financiamiento","Genéricas de gasto","Categorías de gasto"]:
        app.radio(key="perspectiva").set_value(perspective).run()
        for measure in ("pia","pim","devengado"):
            app.selectbox(key="medida_gasto").set_value(measure).run()
            check("Selector "+perspective+" / "+measure,not app.error and not app.exception)
    app.radio(key="navegacion").set_value("Análisis por entidad").run()
    app.selectbox(key="metrica").set_value("ejecucion_pct").run()
    spec=json.loads(app.get("plotly_chart")[0].proto.spec)
    hover=spec["data"][0]["hovertemplate"]
    check("Ranking porcentual contextualiza PIM y hechos","PIM:" in hover and "Hechos:" in hover and len(spec["data"][0]["customdata"][0])==3)
    app.toggle(key="detalle_entidades").set_value(True).run()
    check("Tabla permite consultar las siete medidas",not app.error and not app.exception and all(LABELS[m] in app.dataframe[0].value.columns for m in MEASURES))
    app.radio(key="navegacion").set_value("Metodología y calidad").run()
    check("Metodología organizada en cuatro desplegables",len(app.expander)==4 and not app.error and not app.exception)
    import pyarrow as pa
    app.radio(key="navegacion").set_value("An\u00e1lisis temporal").run()
    proto=app.dataframe[0].proto
    check("Placeholder nativo para celdas sin variacion",proto.placeholder=="No aplica")
    arrow=proto.arrow_data if hasattr(proto,"arrow_data") else proto
    display=pa.ipc.open_stream(arrow.styler.display_values).read_all().to_pandas()
    check("Styler serializa No aplica sin modificar el valor nulo",display[LABELS["variacion_pct"]][0]=="No aplica")
    pim=display[LABELS["pim"]][0]
    check("Separadores llegan a la tabla del navegador","," in pim and "." in pim)
    result={"estado":"correcto","fecha_utc":datetime.now(timezone.utc).isoformat(),"pruebas":len(results),"comprobaciones":results,"relaciones_verificadas":relations}
    (run/"verificacion_pulido.json").write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
    print("Pruebas adicionales:",len(results))
if __name__=="__main__":
    main()
