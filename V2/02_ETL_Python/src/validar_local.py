import argparse,json
from collections import Counter,defaultdict
from decimal import Decimal
from pathlib import Path
from comun import *

def validate(folder):
    folder=Path(folder)
    manifest=json.loads((folder/"manifest.json").read_text(encoding="utf-8"))
    for f in manifest["annual_files"]:
        require(sha(SNAPSHOT/f["file"])==f["sha256"],"CSV anual modificado")
    for f in manifest["files"]:
        require(sha(folder/f["file"])==f["sha256"],"CSV mensual modificado")
        require(sum(1 for _ in rows(folder/f["file"]))==f["rows"],"Conteo incorrecto")
    dims={}
    for f in manifest["annual_files"][:-1]:
        data={}
        key=f["columns"][0]
        for row in rows(SNAPSHOT/f["file"]):
            require(row[key] not in data,"PK de dimension duplicada")
            data[row[key]]=json.loads(row["clave_natural"]) if "clave_natural" in row else None
        dims[key]=data
    annual_file=manifest["annual_files"][-1]
    totals=defaultdict(lambda:defaultdict(Decimal))
    selection={r["hecho_anual_key"]:r for r in rows(folder/"serie_seleccionada.csv")}
    require(len(selection)==12500,"Series no unicas")
    parents={}
    annual_count=0
    natural_annual=set()
    for row in rows(SNAPSHOT/annual_file["file"]):
        annual_count+=1
        grain=tuple(row[k] for k in CONTEXT)
        require(grain not in natural_annual,"Grano anual duplicado")
        natural_annual.add(grain)
        for key in CONTEXT:
            require(row[key] in dims[key],"Huerfano anual")
        for measure in MEASURES:
            totals[row["anio_key"]][measure]+=money(row[measure])
        if row["hecho_key"] in selection:
            parents[row["hecho_key"]]=row
    require(annual_count==150000 and len(parents)==12500,"Conteos incorrectos")
    for expected in manifest["annual_totals"]:
        for measure in MEASURES:
            require(totals[str(expected["anio"])][measure]==Decimal(expected[measure]),"Total anual distinto")
    detail={r["meta_detalle_key"]:r for r in rows(folder/"dim_meta_detallada.csv")}
    period={r["periodo_key"]:r for r in rows(folder/"dim_periodo_mensual.csv")}
    require(len(period)==48,"Periodos incompletos")
    for row in detail.values():
        nk=[row["anio_key"]]+dims["entidad_key"][row["entidad_key"]]+dims["intervencion_key"][row["intervencion_key"]]+dims["funcion_key"][row["funcion_key"]]+[row[c] for c in ["sec_func","finalidad","meta","departamento_meta"]]
        require(nk==json.loads(row["clave_natural"]),"Clave de meta detallada incorrecta")
    grain_set=set()
    for key,row in selection.items():
        require(all(row[c]==parents[key][c] for c in CONTEXT),"Contexto de serie incorrecto")
        require(row["fuente_grano_json"] not in grain_set,"Grano fuente repetido")
        grain_set.add(row["fuente_grano_json"])
        require(row["meta_detalle_key"] in detail,"Meta ausente")
        d=detail[row["meta_detalle_key"]]
        require(all(d[c]==row[c] for c in CONTEXT[:4]),"Contexto de meta incompatible")
        require(d["meta_nombre"]==dims["meta_key"][row["meta_key"]][-1],"Nombre de meta incompatible")
        entity=dims["entidad_key"][row["entidad_key"]]
        interv=dims["intervencion_key"][row["intervencion_key"]]
        func=dims["funcion_key"][row["funcion_key"]]
        fin=dims["financiamiento_key"][row["financiamiento_key"]]
        clas=dims["clasificador_gasto_key"][row["clasificador_gasto_key"]]
        expected=[row["anio_key"]]+entity+interv+func+[d["meta"],d["departamento_meta"],fin[1],fin[0],fin[2]]+clas+[d["sec_func"],d["finalidad"],d["meta_nombre"]]
        require(expected==json.loads(row["fuente_grano_json"]),"Grano fuente/contexto incompatible")
    counts=Counter()
    sums=defaultdict(Decimal)
    periods=defaultdict(Decimal)
    grains=set()
    seen=set()
    negatives=zeros=0
    total=0
    year_count=Counter()
    government=Counter()
    for row in rows(folder/"fact_devengado_mensual.csv"):
        total+=1
        require(int(row["hecho_mensual_key"])==total,"PK mensual no consecutiva")
        key=row["hecho_anual_key"]
        require(key in selection,"Serie inexistente")
        series=selection[key]
        for c in ["anio_key","entidad_key","intervencion_key","funcion_key","meta_detalle_key","financiamiento_key","clasificador_gasto_key"]:
            require(row[c]==series[c],"Contexto mensual incorrecto")
        require(row["periodo_key"] in period and period[row["periodo_key"]]["anio_key"]==row["anio_key"],"Periodo incompatible")
        grain=tuple(row[c] for c in ["periodo_key","entidad_key","intervencion_key","funcion_key","meta_detalle_key","financiamiento_key","clasificador_gasto_key"])
        require(grain not in grains,"Grano mensual duplicado")
        grains.add(grain)
        pair=(key,row["periodo_key"])
        require(pair not in seen,"Mes repetido")
        seen.add(pair)
        value=money(row["devengado"])
        negatives+=value<0
        zeros+=value==0
        sums[key]+=value
        counts[key]+=1
        periods[row["periodo_key"]]+=value
        year_count[row["anio_key"]]+=1
        government[(row["anio_key"],dims["entidad_key"][row["entidad_key"]][0])]+=1
    require(total==150000,"Hechos mensuales distintos de 150000")
    for key,parent in parents.items():
        require(counts[key]==12 and sums[key]==money(parent["devengado"]),"Conciliacion por serie fallida")
    for p,value in manifest["monthly_totals"].items():
        require(periods[p]==Decimal(value),"Conciliacion mensual fallida")
    require(all(year_count[str(y)]==37500 for y in range(2022,2026)),"Cuotas anuales incorrectas")
    return dict(valid=True,annual_facts=annual_count,monthly_facts=total,series=len(selection),periods=len(period),detailed_metas=len(detail),annual_controls=28,monthly_controls=len(periods),series_reconciled=len(parents),orphans=0,duplicate_grains=0,negative_months=negatives,zero_months=zeros,by_year=dict(year_count),by_government={str(k):v for k,v in government.items()},postgres_executed=False)

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("folder",type=Path)
    print(js(validate(parser.parse_args().folder)))
