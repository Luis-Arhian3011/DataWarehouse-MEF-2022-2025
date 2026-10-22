"""Verificacion de solo lectura en PostgreSQL; guarda evidencia local."""
from decimal import Decimal
from datetime import datetime,timezone
from conexion import ROOT,M,query_json,write_json
def verify():
    dims=[x for x in M["files"] if not x["table"].endswith("fact_ejecucion_presupuestaria_anual")]
    dimsql=" UNION ALL ".join("SELECT '"+d["table"]+"' name,count(*) AS cantidad FROM "+d["table"] for d in dims)
    money=["pia","pim","certificado","comprometido_anual","comprometido","devengado","girado"]
    joins="""FROM mef.fact_ejecucion_presupuestaria_anual f
    LEFT JOIN mef.dim_anio a USING(anio_key)
    LEFT JOIN mef.dim_entidad e USING(entidad_key)
    LEFT JOIN mef.dim_intervencion i USING(intervencion_key)
    LEFT JOIN mef.dim_funcion u USING(funcion_key)
    LEFT JOIN mef.dim_meta m USING(meta_key)
    LEFT JOIN mef.dim_financiamiento r USING(financiamiento_key)
    LEFT JOIN mef.dim_clasificador_gasto c USING(clasificador_gasto_key)"""
    orphan="a.anio_key IS NULL OR e.entidad_key IS NULL OR i.intervencion_key IS NULL OR u.funcion_key IS NULL OR m.meta_key IS NULL OR r.financiamiento_key IS NULL OR c.clasificador_gasto_key IS NULL"
    mismatch="""m.anio IS DISTINCT FROM a.anio OR m.clave_natural::jsonb IS DISTINCT FROM
    (jsonb_build_array(a.anio::text)||e.clave_natural::jsonb||i.clave_natural::jsonb||u.clave_natural::jsonb||
     jsonb_build_array(m.meta,m.departamento_meta,m.meta_nombre))"""
    grain="anio_key,entidad_key,intervencion_key,funcion_key,meta_key,financiamiento_key,clasificador_gasto_key"
    sql="""SELECT json_build_object(
    'database',current_database(),'role',current_user,'version',version(),
    'fact_rows',(SELECT count(*) FROM mef.fact_ejecucion_presupuestaria_anual),
    'unique_origin',(SELECT count(DISTINCT(anio_key,key_value)) FROM mef.fact_ejecucion_presupuestaria_anual),
    'unique_grain',(SELECT count(DISTINCT("""+grain+""")) FROM mef.fact_ejecucion_presupuestaria_anual),
    'fk_validated',(SELECT count(*) FROM pg_constraint WHERE conrelid='mef.fact_ejecucion_presupuestaria_anual'::regclass AND contype='f' AND convalidated),
    'joined_rows',(SELECT count(*) """+joins+"""),
    'orphans',(SELECT count(*) """+joins+" WHERE "+orphan+"""),
    'meta_context_mismatch',(SELECT count(*) """+joins+" WHERE "+mismatch+"""),
    'dimensions',(SELECT json_object_agg(name,cantidad) FROM ("""+dimsql+""") t),
    'by_year',(SELECT json_agg(row_to_json(t) ORDER BY anio) FROM
      (SELECT anio_key anio,count(*) hechos,"""+",".join("sum("+x+") "+x for x in money)+"""
       FROM mef.fact_ejecucion_presupuestaria_anual GROUP BY anio_key) t),
    'by_level',(SELECT json_agg(row_to_json(t) ORDER BY nivel_gobierno) FROM
       (SELECT e.nivel_gobierno,count(*) hechos,count(DISTINCT e.entidad_key) entidades
        FROM mef.fact_ejecucion_presupuestaria_anual f JOIN mef.dim_entidad e USING(entidad_key)
        GROUP BY e.nivel_gobierno) t),
    'negative_rows',(SELECT count(*) FROM mef.fact_ejecucion_presupuestaria_anual WHERE """+" OR ".join(x+"<0" for x in money)+"""))
    """
    report=query_json(sql,M["database"])
    for key in ["fact_rows","unique_origin","unique_grain","joined_rows"]:
        if report[key]!=150000:raise RuntimeError("Conteo incorrecto: "+key)
    if report["fk_validated"]!=7 or report["orphans"]!=0 or report["meta_context_mismatch"]!=0:
        raise RuntimeError("Error de integridad dimensional")
    for d in M["files"]:
        if d["table"] in report["dimensions"] and report["dimensions"][d["table"]]!=d["rows"]:
            raise RuntimeError("Dimension no coincide: "+d["table"])
    for a,b in zip(report["by_year"],M["expected_by_year"]):
        if a["anio"]!=b["anio"] or a["hechos"]!=b["hechos"]:
            raise RuntimeError("Conteo anual no coincide")
        for key in money:
            if Decimal(str(a[key]))!=Decimal(str(b[key])):
                raise RuntimeError("Diferencia monetaria: "+str(a["anio"])+" "+key)
    if [r["anio"] for r in report["by_year"]]!=[2022,2023,2024,2025] or len(report["by_level"])!=3:
        raise RuntimeError("Cobertura incompleta")
    report["status"]="verified"
    report["checked_at_utc"]=datetime.now(timezone.utc).isoformat()
    write_json(ROOT/"evidencias"/"verificacion_postgresql.json",report)
    print("VERIFICADO: 150000 hechos, siete FK, cero huerfanos, importes exactos")
    return report
if __name__=="__main__":verify()
