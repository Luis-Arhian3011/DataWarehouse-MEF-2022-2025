from auditlib import *
ANAMES=["pia","pim","certificado","comprometido_anual","devengado","girado"]
def verify_snapshot():
 m=json.loads((ROOT/"02_ETL_Python/datos_preparados/anual/manifest.json").read_text(encoding="utf-8"));checks={}
 for ent in m["files"]:
  p=ROOT/"02_ETL_Python/datos_preparados/anual"/ent["file"];event("hash_snapshot_"+p.stem,status="start")
  h=checksum(p)
  if h!=ent["sha256"]:raise RuntimeError("CSV snapshot modificado: "+p.name)
  checks[p.name]={"sha256":h,"bytes":p.stat().st_size}
 save("snapshot_"+sys.argv[1]+".json",checks)
def build_reference(con):
 dest=Path(CFG["compact_ref"])
 legacy=ROOT/"02_ETL_Python/datos_preparados/anual/datos_carga"
 if not dest.exists():
  aliases=[("entidad","e",ENTITY),("intervencion","i",INTERV),("funcion","u",FUNC),("meta","m",["META","DEPARTAMENTO_META"]),("financiamiento","z",FIN),("clasificador_gasto","c",CLAS)]
  fields=["trim(f.anio_key)"]
  for nm,a,cols in aliases:fields += ["trim("+a+"."+c.lower()+")" for c in cols]
  fields+=["trim(m.meta_nombre)"]
  key="to_json(["+",".join(fields)+"])::VARCHAR"
  joins=[]
  for nm,a,cols in aliases:
   joins+=["JOIN "+reader(legacy/("dim_"+nm+".csv"))+" "+a+" ON f."+nm+"_key="+a+"."+nm+"_key"]
  ref="SELECT f.hecho_key,f.anio_key,f.entidad_key,e.nivel_gobierno nivel,"+key+" legacy_key,"+",".join("CAST(f."+n+" AS DECIMAL(20,2)) a_"+n for n in ANAMES)+" FROM "+reader(legacy/"fact_ejecucion_presupuestaria_anual.csv")+" f "+" ".join(joins)
  execute(con,"construir_referencia_compacta","COPY ("+ref+") TO "+q(dest)+" (FORMAT PARQUET,COMPRESSION ZSTD,ROW_GROUP_SIZE 16384)",False)
 stats=execute(con,"verificar_referencia_compacta","SELECT count(*) filas,count(DISTINCT hecho_key) hechos,count(DISTINCT legacy_key) claves FROM "+relation(dest))[0]
 if any(stats[k]!=150000 for k in ["filas","hechos","claves"]):raise RuntimeError("Referencia anual no unica/completa")
 years=execute(con,"anios_referencia_compacta","SELECT anio_key,count(*) filas FROM "+relation(dest)+" GROUP BY 1 ORDER BY 1")
 if [(str(r["anio_key"]),r["filas"]) for r in years]!=[(str(y),37500) for y in [2022,2023,2024,2025]]:raise RuntimeError("Referencia anual sin cobertura esperada")
 return {"stats":stats,"years":years,"bytes":dest.stat().st_size,"sha256":checksum(dest)}
def source_legacy_key(prefix=""):
 vals=[]
 for c in ["ANO_EJE"]+CORE+["META_NOMBRE"]:
  use={"FUENTE_FINANCIAMIENTO":"RUBRO","RUBRO":"FUENTE_FINANCIAMIENTO"}.get(c,c)
  vals.append(canon(use,prefix))
 return "to_json(["+",".join(vals)+"])::VARCHAR"
def mapping(con,path,year,qdoc,grain,label=None):
 lab=label or str(year)
 active="("+" OR ".join(n(c)+"<>0" for c in MONEY)+")"
 filt=qdoc["filtro_valido"]+" AND "+active
 if grain["grupos_repetidos"]:
  key=arr(GRAIN)
  filt+=" AND "+key+" NOT IN (SELECT "+key+" FROM "+relation(path)+" GROUP BY 1 HAVING count(*)>1)"
 count=execute(con,lab+"_conteo_elegibles","SELECT count(*) filas FROM "+relation(path)+" WHERE "+filt)[0]["filas"]
 projection="SELECT "+source_legacy_key()+" legacy_key,"+arr(GRAIN)+" grano_json,trim(NIVEL_GOBIERNO) nivel,"+",".join(n(c)+" s_"+nm for c,nm in zip(ANNUAL,ANAMES))+" FROM "+relation(path)+" WHERE "+filt
 ref="(SELECT * FROM "+relation(CFG["compact_ref"])+" WHERE anio_key="+q(year)+")"
 joined=" FROM ("+projection+") s LEFT JOIN "+ref+" a ON s.legacy_key=a.legacy_key"
 coverage=execute(con,lab+"_cobertura_compacta","SELECT count(*) filas,count(*) FILTER (WHERE a.hecho_key IS NOT NULL) series_enlazadas"+joined)[0]
 if coverage["filas"]!=count:raise RuntimeError("Multiplicacion o perdida de filas en el enlace")
 dest=TEMP/("correspondencias_"+lab+".parquet")
 select="SELECT s.grano_json,a.hecho_key,a.entidad_key,s.nivel,"+",".join("s.s_"+nm+",a.a_"+nm for nm in ANAMES)
 execute(con,lab+"_guardar_enlaces_compactos","COPY ("+select+joined+" WHERE a.hecho_key IS NOT NULL) TO "+q(dest)+" (FORMAT PARQUET,COMPRESSION ZSTD,ROW_GROUP_SIZE 16384)",False)
 sums=",".join("sum(s_"+nm+") s_"+nm+",max(a_"+nm+") a_"+nm for nm in ANAMES)
 grouped="SELECT hecho_key,max(entidad_key) entidad_key,max(nivel) nivel,count(*) subseries,"+sums+" FROM "+relation(dest)+" GROUP BY hecho_key"
 coherent=" AND ".join("s_"+nm+"=a_"+nm for nm in ANAMES)
 st=["count(*) padres_anuales_enlazados","coalesce(sum(subseries),0) series_mensuales_enlazadas","count(*) FILTER (WHERE subseries>1) padres_con_varias_subseries","count(*) FILTER (WHERE "+coherent+") padres_conciliados_seis_medidas","count(*) FILTER (WHERE "+coherent+" AND subseries=1) padres_conciliados_una_serie","count(DISTINCT entidad_key) FILTER (WHERE "+coherent+" AND subseries=1) entidades_cohorte_una_serie"]
 for nm in ANAMES:st+=["count(*) FILTER (WHERE s_"+nm+"<>a_"+nm+") "+nm+"_padres_diferentes"]
 stats=execute(con,lab+"_conciliacion_compacta","SELECT "+",".join(st)+" FROM ("+grouped+")")[0]
 if stats["series_mensuales_enlazadas"]!=coverage["series_enlazadas"]:raise RuntimeError("Conteo inconsistente al agrupar enlaces")
 gov=execute(con,lab+"_cohorte_gobierno","SELECT nivel,count(*) padres_conciliados_una_serie,count(DISTINCT entidad_key) entidades FROM ("+grouped+") WHERE "+coherent+" AND subseries=1 GROUP BY nivel ORDER BY nivel")
 examples=execute(con,lab+"_discrepancias_compactas","SELECT * FROM ("+grouped+") WHERE NOT ("+coherent+") LIMIT 10") if stats["padres_anuales_enlazados"]!=stats["padres_conciliados_seis_medidas"] else []
 # Persist diagnostic identifiers of the eligible common cohort, not a selected sample.
 execute(con,lab+"_catalogo_cohorte","COPY (SELECT hecho_key,entidad_key,nivel FROM ("+grouped+") WHERE "+coherent+" AND subseries=1) TO "+q(EVID/("cohorte_disponible_"+lab+".csv"))+" (FORMAT CSV,HEADER true)",False)
 return {"series_elegibles_unicas":count,"coverage":coverage,"conciliacion_muestra_anual":stats,"estratos_cohorte":gov,"ejemplos_discrepancias":examples,"enlace":"igualdad exacta de clave canonica completa con META_NOMBRE; financiamiento original invertido explicitamente; referencia unica verificada"}
