"""Capa SQL V2: agregados parametrizados, Decimal y transacciones de solo lectura."""
import csv,io,os,tomllib
from pathlib import Path
from dataclasses import dataclass
from decimal import Decimal
import pandas as pd
import psycopg
from psycopg.rows import dict_row
import streamlit as st

ROOT=Path(__file__).resolve().parent
DATABASE="dw_mef_2022_2025_v2"
LEVELS={"E":"Nacional","R":"Regional","M":"Local"}
SCOPES={"total":"Muestra anual completa","cohorte":"Cohorte vinculada al mensual"}
TABLES={"total":"mef.fact_ejecucion_presupuestaria_anual","cohorte":"mef.v_anual_cohorte_mensual"}
MEASURES=("pia","pim","devengado","girado")
LABELS={"anio":"Año","mes":"Mes","mes_nombre":"Nombre del mes","hechos":"Hechos","entidades":"Entidades","pia":"PIA (S/)","pim":"PIM (S/)","devengado":"Devengado (S/)","girado":"Girado (S/)","ejecucion_pct":"Ejecución (%)","variacion_pct":"Variación interanual (%)","codigo":"Código","nombre":"Denominación","sec_ejec":"SEC_EJEC","nivel_gobierno":"Gobierno","negativos":"Meses negativos","acumulado":"Acumulado desde enero (S/)","series":"Series","meses":"Hechos mensuales","devengado_anual":"Devengado anual de cohorte (S/)","devengado_mensual":"Devengado mensual conciliado (S/)","diferencia":"Diferencia (S/)","pim_cero":"Hechos con PIM cero y devengado positivo","dev_pim_cero":"Devengado con PIM cero (S/)","pim_no_positivo":"Hechos con PIM no positivo"}
class ErrorDatos(Exception):pass

def configuracion():
    try:
        file=ROOT/".streamlit/secrets.toml"
        local=tomllib.loads(file.read_text(encoding="utf-8")).get("postgres",{}) if file.exists() else {}
        defaults=dict(host="127.0.0.1",port=5432,dbname=DATABASE,user="",password="")
        mapping=dict(host="PGHOST",port="PGPORT",dbname="PGDATABASE",user="PGUSER",password="PGPASSWORD")
        cfg={key:os.environ.get(env,local.get(key,defaults[key])) for key,env in mapping.items()}
        cfg["port"]=int(cfg["port"])
        if cfg["dbname"]!=DATABASE:
            raise ErrorDatos("Este dashboard permite exclusivamente la base dw_mef_2022_2025_v2.")
        return cfg
    except (OSError,ValueError,tomllib.TOMLDecodeError):
        raise ErrorDatos("Revisa las variables PG* o la configuración privada .streamlit/secrets.toml.") from None

def conectar():
    try:
        connection=psycopg.connect(**configuracion(),connect_timeout=5,row_factory=dict_row,
            options="-c default_transaction_read_only=on -c statement_timeout=15000 -c application_name=dashboard_mef_v2")
        connection.read_only=True
        return connection
    except (psycopg.Error,OSError,ValueError):
        raise ErrorDatos("No se pudo conectar con V2. Comprueba Docker, el puerto y la configuración privada; consulta README.md.") from None

def consultar(statement,params=()):
    if not statement.lstrip().upper().startswith(("SELECT","WITH")):
        raise ErrorDatos("Solo se admiten consultas SELECT de diagnóstico y agregación.")
    try:
        with conectar() as connection:
            with connection.cursor() as cursor:
                cursor.execute(statement,params) if params else cursor.execute(statement)
                return cursor.fetchall()
    except psycopg.Error:
        raise ErrorDatos("La consulta no pudo completarse. Verifica el esquema V2 o actualiza la conexión.") from None

@dataclass(frozen=True)
class Filtros:
    anios:tuple=(2022,2023,2024,2025)
    niveles:tuple=("E","R","M")
    entidades:tuple|None=None
    funciones:tuple|None=None
    fuentes:tuple|None=None
    def __post_init__(self):
        if not set(self.anios)<=set(range(2022,2026)) or not set(self.niveles)<=set(LEVELS):
            raise ValueError("Años o niveles fuera del período permitido.")

JOINS=""" JOIN mef.dim_entidad e ON e.entidad_key=f.entidad_key
 JOIN mef.dim_funcion u ON u.funcion_key=f.funcion_key
 JOIN mef.v_financiamiento_conformado r ON r.financiamiento_key=f.financiamiento_key """
def base(scope):
    if scope not in TABLES:raise ValueError("Cobertura no permitida")
    return " FROM "+TABLES[scope]+" f "+JOINS

def condicion(filters):
    parts=["f.anio_key=ANY(%s::smallint[])","e.nivel_gobierno=ANY(%s::text[])"]
    params=[list(filters.anios),list(filters.niveles)]
    for field,expression,cast in [("entidades","f.entidad_key","bigint"),("funciones","u.funcion","text"),("fuentes","r.fuente_financiamiento","text")]:
        value=getattr(filters,field)
        if value is not None:
            parts.append(expression+"=ANY(%s::"+cast+"[])")
            params.append(list(value))
    return " WHERE "+" AND ".join(parts),tuple(params)

SUMS=", ".join("COALESCE(sum(f."+m+"),0) "+m for m in MEASURES)
METRICS="""count(*) hechos,count(DISTINCT f.entidad_key) entidades,"""+SUMS+""",
 CASE WHEN sum(f.pim)>0 THEN 100*sum(f.devengado)/sum(f.pim) END ejecucion_pct,
 count(*) FILTER(WHERE f.pim=0 AND f.devengado>0) pim_cero,
 COALESCE(sum(f.devengado) FILTER(WHERE f.pim=0 AND f.devengado>0),0) dev_pim_cero,
 count(*) FILTER(WHERE f.pim<=0) pim_no_positivo"""

@st.cache_data(ttl=300,max_entries=128,show_spinner=False)
def resumen(filters=Filtros(),scope="total"):
    where,params=condicion(filters)
    return consultar("SELECT "+METRICS+base(scope)+where,params)[0]

@st.cache_data(ttl=300,max_entries=128,show_spinner=False)
def anual(filters=Filtros(),scope="total"):
    where,params=condicion(filters)
    return pd.DataFrame(consultar("SELECT f.anio_key anio,"+METRICS+base(scope)+where+" GROUP BY f.anio_key ORDER BY f.anio_key",params))

@st.cache_data(ttl=300,max_entries=128,show_spinner=False)
def mensual(filters=Filtros()):
    where,params=condicion(filters)
    statement="""SELECT f.anio_key anio,p.mes,p.mes_nombre,count(*) hechos,
 count(DISTINCT f.hecho_anual_key) series,sum(f.devengado) devengado,
 count(*) FILTER(WHERE f.devengado<0) negativos,
 sum(sum(f.devengado)) OVER(PARTITION BY f.anio_key ORDER BY p.mes) acumulado
 FROM mef.fact_devengado_mensual f """+JOINS+""" JOIN mef.dim_periodo_mensual p ON p.periodo_key=f.periodo_key """+where+""" GROUP BY f.anio_key,p.mes,p.mes_nombre ORDER BY f.anio_key,p.mes"""
    return pd.DataFrame(consultar(statement,params))

GROUPS={
 "entidad":("e.entidad_key codigo,e.ejecutora_nombre nombre,e.sec_ejec,e.nivel_gobierno","e.entidad_key,e.ejecutora_nombre,e.sec_ejec,e.nivel_gobierno"),
 "funcion":("u.funcion codigo,u.funcion_nombre nombre","u.funcion,u.funcion_nombre"),
 "fuente":("r.fuente_financiamiento codigo,r.fuente_financiamiento_nombre nombre","r.fuente_financiamiento,r.fuente_financiamiento_nombre"),
 "nivel":("e.nivel_gobierno codigo,e.nivel_gobierno_nombre nombre","e.nivel_gobierno,e.nivel_gobierno_nombre"),
}
@st.cache_data(ttl=300,max_entries=128,show_spinner=False)
def agrupado(group,filters=Filtros(),scope="total"):
    if group not in GROUPS:raise ValueError("Agrupación no permitida")
    columns,grouping=GROUPS[group]
    where,params=condicion(filters)
    return pd.DataFrame(consultar("SELECT "+columns+","+METRICS+base(scope)+where+" GROUP BY "+grouping+" ORDER BY sum(f.devengado) DESC",params))

@st.cache_data(ttl=300,max_entries=64,show_spinner=False)
def catalogos(anios,niveles):
    where,params=condicion(Filtros(anios,niveles))
    entities=consultar("SELECT e.entidad_key,e.sec_ejec,e.ejecutora_nombre,e.nivel_gobierno,count(*) hechos"+base("total")+where+" GROUP BY e.entidad_key ORDER BY e.ejecutora_nombre,e.entidad_key",params)
    functions=consultar("SELECT u.funcion codigo,string_agg(DISTINCT u.funcion_nombre,' / ' ORDER BY u.funcion_nombre) nombre"+base("total")+where+" GROUP BY u.funcion ORDER BY u.funcion",params)
    sources=consultar("SELECT r.fuente_financiamiento codigo,r.fuente_financiamiento_nombre nombre"+base("total")+where+" GROUP BY 1,2 ORDER BY 1,2",params)
    return dict(entidades=entities,funciones=functions,fuentes=sources)

@st.cache_data(ttl=300,max_entries=128,show_spinner=False)
def entidades_comunes(filters,scope):
    where,params=condicion(filters)
    return tuple(row["entidad_key"] for row in consultar("SELECT f.entidad_key"+base(scope)+where+" GROUP BY f.entidad_key HAVING count(DISTINCT f.anio_key)=%s",params+(len(filters.anios),)))

@st.cache_data(ttl=300,max_entries=128,show_spinner=False)
def conciliacion(filters=Filtros()):
    where,params=condicion(filters)
    a="SELECT f.anio_key anio,count(*) series,sum(f.devengado) devengado_anual"+base("cohorte")+where+" GROUP BY f.anio_key"
    m="SELECT f.anio_key anio,count(*) meses,sum(f.devengado) devengado_mensual FROM mef.fact_devengado_mensual f "+JOINS+where+" GROUP BY f.anio_key"
    statement="""WITH a AS ("""+a+"""),m AS ("""+m+""")
 SELECT COALESCE(a.anio,m.anio) anio,a.series,m.meses,a.devengado_anual,m.devengado_mensual,
 m.devengado_mensual-a.devengado_anual diferencia
 FROM a FULL JOIN m USING(anio) ORDER BY 1"""
    return pd.DataFrame(consultar(statement,params+params))

@st.cache_data(ttl=300,max_entries=8,show_spinner=False)
def calidad():
    return consultar("""SELECT current_database() base,current_setting('transaction_read_only') solo_lectura,
 (SELECT count(*) FROM mef.fact_ejecucion_presupuestaria_anual) hechos_anuales,
 (SELECT count(*) FROM mef.fact_devengado_mensual) hechos_mensuales,
 (SELECT count(*) FROM auditoria.serie_seleccionada) series,
 (SELECT count(*) FROM mef.dim_periodo_mensual) periodos,
 (SELECT count(*) FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE c.relkind='r' AND n.nspname IN ('mef','auditoria')) tablas,
 (SELECT count(*) FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE c.relkind='r' AND n.nspname='mef' AND c.relname LIKE 'dim_%') dimensiones,
 (SELECT count(*) FROM pg_constraint c JOIN pg_namespace n ON n.oid=c.connamespace WHERE c.contype='f' AND n.nspname IN ('mef','auditoria')) fk,
 (SELECT count(*) FROM pg_constraint c JOIN pg_namespace n ON n.oid=c.connamespace WHERE c.contype='f' AND NOT c.convalidated AND n.nspname IN ('mef','auditoria')) fk_sin_validar""")[0]

def exportar(frame):
    output=io.StringIO(newline="")
    writer=csv.writer(output,delimiter=";",lineterminator="\r\n")
    writer.writerow([LABELS.get(c,c) for c in frame.columns])
    for values in frame.itertuples(index=False,name=None):
        writer.writerow(["" if value is None or pd.isna(value) else (format(value,"f").replace(".",",") if isinstance(value,Decimal) else value) for value in values])
    return output.getvalue().encode("utf-8-sig")
