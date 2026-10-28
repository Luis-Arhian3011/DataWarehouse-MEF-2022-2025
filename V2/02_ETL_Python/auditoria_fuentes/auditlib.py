from pathlib import Path
import json,time,os,csv,hashlib,sys
from datetime import datetime,timezone
import duckdb
OUT=Path(os.environ["MEF_AUDIT_DIR"]).resolve()
CFG=json.loads((OUT/"config_auditoria.json").read_text(encoding="utf-8"))
ROOT=Path(CFG["root"]);TEMP=OUT/"parquet";EVID=OUT/"evidencias"
MONTHS="ENERO FEBRERO MARZO ABRIL MAYO JUNIO JULIO AGOSTO SEPTIEMBRE OCTUBRE NOVIEMBRE DICIEMBRE".split()
MONTHCOL=["MONTO_DEVENGADO_"+m for m in MONTHS]
ANNUAL=["MONTO_PIA","MONTO_PIM","MONTO_CERTIFICADO_ANUAL","MONTO_COMPROMETIDO_ANUAL","MONTO_DEVENGADO_ANUAL","MONTO_GIRADO_ANUAL"]
MONEY=ANNUAL[:4]+MONTHCOL+ANNUAL[4:]
ENTITY="NIVEL_GOBIERNO SECTOR PLIEGO EJECUTORA SEC_EJEC DEPARTAMENTO_EJECUTORA PROVINCIA_EJECUTORA DISTRITO_EJECUTORA".split()
INTERV="PROGRAMA_PPTO TIPO_ACT_PROY PRODUCTO_PROYECTO ACTIVIDAD_ACCION_OBRA".split()
FUNC="FUNCION DIVISION_FUNCIONAL GRUPO_FUNCIONAL".split()
FIN="FUENTE_FINANCIAMIENTO RUBRO TIPO_RECURSO".split()
CLAS="CATEGORIA_GASTO TIPO_TRANSACCION GENERICA SUBGENERICA SUBGENERICA_DET ESPECIFICA ESPECIFICA_DET".split()
CORE=ENTITY+INTERV+FUNC+["META","DEPARTAMENTO_META"]+FIN+CLAS
GRAIN=["ANO_EJE"]+CORE+["SEC_FUNC","FINALIDAD","META_NOMBRE"]
REQUIRED=["ANO_EJE"]+[c for c in CORE if c not in ("SECTOR","PLIEGO")]+["SEC_FUNC","FINALIDAD"]
REGEX=r"^[+-]?[0-9]+([.][0-9]{1,2})?$"
def q(v):return "'"+str(v).replace("\\","/").replace("'","''")+"'"
def ident(c):return '"'+c.replace('"','""')+'"'
def t(c):return "trim("+ident(c)+")"
def n(c):return "TRY_CAST("+t(c)+" AS DECIMAL(20,2))"
def canon(c,prefix=""):
 v="trim("+prefix+ident(c)+")"
 if c=="TIPO_ACT_PROY":return "CASE "+v+" WHEN 'ACTIVIDAD' THEN '3' WHEN 'PROYECTO' THEN '2' ELSE '__NO_MAP__'||coalesce("+v+",'') END"
 return v
def arr(cols,prefix="",year=False):return "to_json(["+",".join(canon(c,prefix) for c in cols)+"])::VARCHAR"
def save(name,data):
 p=EVID/name
 with p.open("x",encoding="utf-8") as f:json.dump(data,f,ensure_ascii=False,indent=2,default=str)
def event(stage,**kw):
 data={"time_utc":datetime.now(timezone.utc).isoformat(),"stage":stage,**kw}
 with (EVID/"eventos.jsonl").open("a",encoding="utf-8") as f:f.write(json.dumps(data,ensure_ascii=False,default=str)+"\n")

def connect():
 spill=TEMP/"spill";spill.mkdir(exist_ok=True)
 con=duckdb.connect(":memory:",config={"memory_limit":CFG["memory_limit_engine"],"threads":str(CFG["threads"]),"temp_directory":str(spill),"max_temp_directory_size":CFG["max_temp_directory_size"],"preserve_insertion_order":"false"})
 con.execute("SET enable_progress_bar=false")
 con.execute("SET max_execution_time=900000")
 return con
def execute(con,stage,sql,fetch=True):
 event(stage,status="start")
 # Every executed query is saved for reproducibility; no secrets or PostgreSQL DSN.
 with (EVID/"consultas.sql").open("a",encoding="utf-8") as f:f.write("-- "+stage+"\n"+sql+";\n")
 started=time.perf_counter()
 cursor=con.execute(sql)
 result=None
 if fetch:
  names=[x[0] for x in cursor.description];result=[dict(zip(names,row)) for row in cursor.fetchall()]
 save("checkpoint_"+"fuentes"+"_"+stage+".json",{"stage":stage,"seconds":time.perf_counter()-started,"result":result,"copy_receipt":cursor.fetchall() if not fetch else None})
 event(stage,status="done",seconds=time.perf_counter()-started,rows_returned=len(result) if result is not None else None)
 return result
def reader(path):
 # No silent skips, numeric coercions, NULL replacement, or parallel reader.
 with Path(path).open(encoding="utf-8-sig",newline="") as f:header=next(csv.reader(f))
 return "read_csv("+q(path)+",header=true,delim=',',all_varchar=true,nullstr='',force_not_null=["+",".join(q(c) for c in header)+"],parallel=false,strict_mode=true,ignore_errors=false,max_line_size=1048576)"
def stage(con,path,dest,limit=None):
 if dest.exists():raise RuntimeError("Salida ya existe: "+str(dest))
 limitstr=" LIMIT "+str(limit) if limit else ""
 return execute(con,"parquet_"+dest.stem,"COPY (SELECT * FROM "+reader(path)+limitstr+") TO "+q(dest)+" (FORMAT PARQUET,COMPRESSION ZSTD,ROW_GROUP_SIZE 32768)",False)
def relation(path):
 if isinstance(path,(list,tuple)):return "read_parquet(["+",".join(q(p) for p in path)+"])"
 return "read_parquet("+q(path)+")"
def quality(con,path,year,label):
 r=relation(path);exprs=["count(*) filas","count(*) FILTER (WHERE "+t("ANO_EJE")+"<>"+q(year)+" OR ANO_EJE IS NULL) anio_incorrecto","count(*) FILTER (WHERE "+t("NIVEL_GOBIERNO")+" NOT IN ('E','R','M') OR NIVEL_GOBIERNO IS NULL) gobierno_incorrecto","count(*) FILTER (WHERE "+t("TIPO_ACT_PROY")+" NOT IN ('ACTIVIDAD','PROYECTO') OR TIPO_ACT_PROY IS NULL) tipo_no_mapeable"]
 for c in MONEY:
  exprs += ["count(*) FILTER (WHERE NOT coalesce(regexp_full_match("+t(c)+","+q(REGEX)+"),false) OR "+n(c)+" IS NULL) "+ident(c+"_invalidos"),"count(*) FILTER (WHERE "+n(c)+"<0) "+ident(c+"_negativos"),"sum("+n(c)+") "+ident(c+"_suma")]
 for c in REQUIRED+["SECTOR","PLIEGO","META_NOMBRE"]:
  exprs += ["count(*) FILTER (WHERE "+ident(c)+" IS NULL OR "+t(c)+"='') "+ident(c+"_ausente")]
 allvalid=" AND ".join("coalesce(regexp_full_match("+t(c)+","+q(REGEX)+"),false) AND "+n(c)+" IS NOT NULL" for c in MONEY)
 required=" AND ".join(ident(c)+" IS NOT NULL AND "+t(c)+"<>''" for c in REQUIRED)
 yearok=t("ANO_EJE")+"="+q(year)
 gov=t("NIVEL_GOBIERNO")+" IN ('E','R','M')"
 typeok=t("TIPO_ACT_PROY")+" IN ('ACTIVIDAD','PROYECTO')"
 sectorok="("+t("NIVEL_GOBIERNO")+"='M' OR ("+t("SECTOR")+"<>'' AND "+t("PLIEGO")+"<>''))"
 valid=allvalid+" AND "+required+" AND "+yearok+" AND "+gov+" AND "+typeok+" AND "+sectorok
 exprs+=["count(*) FILTER (WHERE "+valid+") filas_validas_formato"]
 monsum="("+ "+".join(n(c) for c in MONTHCOL)+")"
 exprs+=["count(*) FILTER (WHERE "+allvalid+") filas_conciliables","count(*) FILTER (WHERE "+allvalid+" AND "+monsum+"<>"+n("MONTO_DEVENGADO_ANUAL")+") diferencias_meses","sum("+monsum+") suma_12_meses"]
 data=execute(con,label+"_calidad","SELECT "+",".join(exprs)+" FROM "+r)[0]
 data["filtro_valido"]=valid
 data["por_gobierno"]=execute(con,label+"_gobiernos","SELECT "+t("NIVEL_GOBIERNO")+" nivel,count(*) filas,count(DISTINCT "+arr(ENTITY)+") entidades,count(*) FILTER (WHERE "+t("SECTOR")+"='' OR "+t("PLIEGO")+"='') sector_pliego_ausente FROM "+r+" GROUP BY 1 ORDER BY 1")
 return data
def duplicates(con,path,cols,label):
 colsql=",".join(t(c) for c in cols)
 # Exact tuple grouping: no probabilistic hash deduplication.
 grouped="SELECT "+colsql+",count(*) multiplicidad FROM "+relation(path)+" GROUP BY "+colsql
 result=execute(con,label,"SELECT count(*) grupos,coalesce(sum(multiplicidad-1),0) filas_extra,coalesce(sum(CASE WHEN multiplicidad>1 THEN multiplicidad ELSE 0 END),0) filas_en_grupos_repetidos,count(*) FILTER (WHERE multiplicidad>1) grupos_repetidos,max(multiplicidad) multiplicidad_maxima FROM ("+grouped+")")[0]
 return result
def rawduplicates(con,path,cols,label):
 names=",".join(ident(c) for c in cols)
 return execute(con,label,"SELECT count(*) grupos,coalesce(sum(n-1),0) filas_extra,count(*) FILTER (WHERE n>1) grupos_repetidos FROM (SELECT "+names+",count(*) n FROM "+relation(path)+" GROUP BY "+names+")")[0]
def fd(con,path,keys,attrs,label):
 k=",".join(t(c) for c in keys);a=",".join(t(c) for c in attrs)
 grouped="SELECT "+k+",count(*) filas,count(DISTINCT row("+a+")) variantes FROM "+relation(path)+" GROUP BY "+k
 stats=execute(con,label,"SELECT count(*) claves,count(*) FILTER (WHERE variantes>1) claves_con_variantes,max(variantes) max_variantes FROM ("+grouped+")")[0]
 stats["keys"]=keys;stats["attrs"]=attrs
 if stats["claves_con_variantes"]:
  stats["ejemplos"]=execute(con,label+"_ejemplos",grouped+" HAVING count(DISTINCT row("+a+"))>1 LIMIT 5")
 return stats
def checksum(path):
 h=hashlib.sha256()
 with path.open("rb") as f:
  for b in iter(lambda:f.read(8*1024*1024),b""):h.update(b)
 return h.hexdigest()
