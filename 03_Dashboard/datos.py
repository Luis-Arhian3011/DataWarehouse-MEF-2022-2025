"""Consultas agregadas de solo lectura; ninguna fila de hechos sale de PostgreSQL."""
import os
import sys
import json
import subprocess
from decimal import Decimal
from pathlib import Path
import tomllib
from dataclasses import dataclass
import pandas as pd
import psycopg
from psycopg.rows import dict_row
import streamlit as st

ROOT = Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT.parent/"scripts"))
from entorno import env_path, cargar_config, compose_base, proceso_env
MEASURES = ("pia", "pim", "certificado", "comprometido_anual", "comprometido", "devengado", "girado")
LEVELS = {"E": "Gobierno nacional", "R": "Gobiernos regionales", "M": "Gobiernos locales"}
BASE = """ FROM mef.fact_ejecucion_presupuestaria_anual f
JOIN mef.dim_anio a USING(anio_key)
JOIN mef.dim_entidad e USING(entidad_key) """
SUMS = ", ".join(f"COALESCE(SUM(f.{m}),0) AS {m}" for m in MEASURES)
RATE = "CASE WHEN SUM(f.pim)>0 THEN 100*SUM(f.devengado)/SUM(f.pim) END AS ejecucion_pct"
METRICS = f"COUNT(*) AS hechos, COUNT(DISTINCT f.entidad_key) AS entidades, {SUMS}, {RATE}"

class ErrorDatos(Exception):
    """Mensaje seguro para la interfaz, sin DSN ni contraseñas."""

def configuracion():
    path = ROOT / ".streamlit" / "secrets.toml"
    local = tomllib.loads(path.read_text(encoding="utf-8")).get("postgres", {}) if path.exists() else {}
    mapping = {"host": "PGHOST", "port": "PGPORT", "dbname": "PGDATABASE", "user": "PGUSER", "password": "PGPASSWORD"}
    defaults = {"host": "127.0.0.1", "port": 5432, "dbname": "dw_mef_2022_2025", "user": "luchito"}
    try:
        if env_path().exists():
            cfg=cargar_config()
            defaults.update(host=cfg["POSTGRES_HOST"],port=cfg["POSTGRES_PORT"],
                dbname=cfg["POSTGRES_DB"],user=cfg["POSTGRES_USER"],password=cfg["POSTGRES_PASSWORD"])
    except RuntimeError as exc:
        raise ErrorDatos(str(exc)) from None
    config = {k: os.environ.get(env, local.get(k, defaults.get(k, ""))) for k, env in mapping.items()}
    if not config["dbname"]:
        raise ErrorDatos("Configura una base de datos de destino.")
    return config

def transporte():
    path = ROOT / ".streamlit" / "secrets.toml"
    local = tomllib.loads(path.read_text(encoding="utf-8")).get("postgres", {}) if path.exists() else {}
    try:
        default=cargar_config()["MEF_TRANSPORT"] if env_path().exists() else "docker"
    except RuntimeError as exc:
        raise ErrorDatos(str(exc)) from None
    value = os.environ.get("MEF_TRANSPORT", local.get("transport", default))
    if value not in ("tcp", "docker", "compose"):
        raise ErrorDatos("MEF_TRANSPORT debe ser tcp, docker o compose.")
    return value

def consultar_docker(sql, params=()):
    """Variables psql con :'nombre': psql escapa cada valor como literal SQL."""
    config = configuracion()
    command = ["docker", "exec", "-i", "-e",
        "PGOPTIONS=-c default_transaction_read_only=on -c statement_timeout=15000 -c application_name=dashboard_mef",
        "-e", "PGCLIENTENCODING=UTF8", os.environ.get("MEF_CONTAINER", "postgres-db"), "psql", "-X", "-q", "-At",
        "-v", "ON_ERROR_STOP=1", "-U", str(config["user"]), "-d", str(config["dbname"])]
    process_env=None
    if transporte()=="compose":
        compose_cfg=cargar_config()
        command=compose_base(compose_cfg)+["exec","-T","-e",
            "PGOPTIONS=-c default_transaction_read_only=on -c statement_timeout=15000 -c application_name=dashboard_mef",
            "-e","PGCLIENTENCODING=UTF8","postgres","psql","-X","-q","-At",
            "-v","ON_ERROR_STOP=1","-U",str(config["user"]),"-d",str(config["dbname"])]
        process_env=proceso_env(compose_cfg)
    parts = sql.split("%s")
    if len(parts) != len(params)+1:
        raise ErrorDatos("Los parámetros de la consulta no coinciden.")
    query = parts[0]
    for i, value in enumerate(params):
        if isinstance(value, (list, tuple)):
            # Literal de matriz PostgreSQL. psql añade el escape SQL externo.
            value = "{" + ",".join(json.dumps(str(v),ensure_ascii=False) for v in value) + "}"
        else:
            value = str(value)
        command += ["-v", f"param{i}={value}"]
        query += f":'param{i}'" + parts[i+1]
    wrapped = "BEGIN READ ONLY; SELECT COALESCE(json_agg(q),'[]'::json) FROM (" + query + ") q; COMMIT;"
    try:
        result = subprocess.run(command,input=wrapped.encode("utf-8"),capture_output=True,timeout=25,env=process_env)
        if result.returncode:
            raise ErrorDatos("No se pudo consultar postgres-db. Verifica Docker y el esquema mef.")
        return json.loads(result.stdout.decode("utf-8"),parse_float=Decimal)
    except (OSError,subprocess.TimeoutExpired,json.JSONDecodeError):
        raise ErrorDatos("No se pudo acceder al contenedor postgres-db. Inicia Docker Desktop y comprueba el contenedor.") from None

class ConexionDocker:
    """Interfaz mínima de diagnóstico; las consultas siguen siendo de solo lectura."""
    def __enter__(self):
        return self
    def __exit__(self,*args):
        return False
    def execute(self,sql,params=()):
        self.rows=consultar_docker(sql,params)
        return self
    def fetchone(self):
        return self.rows[0] if self.rows else None


def conectar():
    if transporte() in ("docker","compose"):
        return ConexionDocker()
    try:
        return psycopg.connect(**configuracion(), connect_timeout=5, row_factory=dict_row,
            options="-c default_transaction_read_only=on -c statement_timeout=15000 -c application_name=dashboard_mef")
    except (psycopg.Error, OSError, ValueError) as exc:
        raise ErrorDatos("No se pudo conectar con PostgreSQL. Verifica Docker y las credenciales locales; consulta README.md.") from None

def consultar(sql, params=()):
    if transporte() in ("docker","compose"):
        return consultar_docker(sql,params)
    try:
        with conectar() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, params)
                return cur.fetchall()
    except psycopg.Error:
        raise ErrorDatos("No se pudo completar la consulta de solo lectura. Comprueba la conexión y el esquema mef.") from None

@dataclass(frozen=True)
class Filtros:
    anios: tuple = (2022, 2023, 2024, 2025)
    niveles: tuple = ("E", "R", "M")
    entidades: tuple | None = None  # None=todas; ()=ninguna, nunca ampliar un resultado vacío.

def condicion(filtros):
    sql = " WHERE a.anio = ANY(%s) AND e.nivel_gobierno = ANY(%s)"
    params = [list(filtros.anios), list(filtros.niveles)]
    if filtros.entidades is not None:
        sql += " AND f.entidad_key = ANY(%s)"
        params.append(list(filtros.entidades))
    return sql, tuple(params)

@st.cache_data(ttl=300, max_entries=200, show_spinner=False)
def resumen(filtros=Filtros()):
    where, params = condicion(filtros)
    return consultar("SELECT " + METRICS + BASE + where, params)[0]

@st.cache_data(ttl=300, max_entries=200, show_spinner=False)
def anual(filtros=Filtros()):
    where, params = condicion(filtros)
    return pd.DataFrame(consultar("SELECT a.anio, " + METRICS + BASE + where + " GROUP BY a.anio ORDER BY a.anio", params))

@st.cache_data(ttl=300, max_entries=100, show_spinner=False)
def entidades_disponibles(anios, niveles):
    where, params = condicion(Filtros(anios, niveles))
    return consultar("""SELECT e.entidad_key,e.sec_ejec,e.ejecutora_nombre,e.nivel_gobierno,
        e.departamento_ejecutora_nombre,COUNT(*) hechos,COUNT(DISTINCT a.anio) anios""" + BASE + where +
        " GROUP BY e.entidad_key ORDER BY e.ejecutora_nombre,e.entidad_key", params)

@st.cache_data(ttl=300, max_entries=150, show_spinner=False)
def entidades_comunes(filtros):
    where, params = condicion(filtros)
    rows = consultar("SELECT f.entidad_key" + BASE + where +
        " GROUP BY f.entidad_key HAVING COUNT(DISTINCT a.anio) = %s", params + (len(filtros.anios),))
    return tuple(r["entidad_key"] for r in rows)

# Lista cerrada de expresiones SQL: los valores del usuario solo se envían como parámetros.
GROUPS = {
    "nivel": ("e.nivel_gobierno AS codigo, e.nivel_gobierno_nombre AS nombre", "", "e.nivel_gobierno,e.nivel_gobierno_nombre"),
    "entidad": ("e.entidad_key AS codigo,e.sec_ejec,e.ejecutora_nombre AS nombre,e.nivel_gobierno",
        "", "e.entidad_key,e.sec_ejec,e.ejecutora_nombre,e.nivel_gobierno"),
    "funcion": ("u.funcion AS codigo,u.funcion_nombre AS nombre",
        " JOIN mef.dim_funcion u USING(funcion_key) ", "u.funcion,u.funcion_nombre"),
    "fuente": ("r.fuente_financiamiento AS codigo,r.fuente_financiamiento_nombre AS nombre",
        " JOIN mef.dim_financiamiento r USING(financiamiento_key) ", "r.fuente_financiamiento,r.fuente_financiamiento_nombre"),
    "generica": ("c.generica AS codigo,c.generica_nombre AS nombre",
        " JOIN mef.dim_clasificador_gasto c USING(clasificador_gasto_key) ", "c.generica,c.generica_nombre"),
    "categoria": ("c.categoria_gasto AS codigo,c.categoria_gasto_nombre AS nombre",
        " JOIN mef.dim_clasificador_gasto c USING(clasificador_gasto_key) ", "c.categoria_gasto,c.categoria_gasto_nombre"),
}

@st.cache_data(ttl=300, max_entries=200, show_spinner=False)
def agrupado(grupo, filtros=Filtros()):
    cols, join, group = GROUPS[grupo]
    where, params = condicion(filtros)
    return pd.DataFrame(consultar(f"SELECT {cols}, {METRICS}" + BASE + join + where +
        f" GROUP BY {group} ORDER BY SUM(f.devengado) DESC", params))

@st.cache_data(ttl=300, show_spinner=False)
def calidad():
    counts = consultar("""SELECT count(*) hechos,
        count(DISTINCT (anio_key,key_value)) claves_origen,
        count(DISTINCT (anio_key,entidad_key,intervencion_key,funcion_key,meta_key,financiamiento_key,clasificador_gasto_key)) granos,
        count(*) FILTER (WHERE pia<0 OR pim<0 OR certificado<0 OR comprometido_anual<0
                         OR comprometido<0 OR devengado<0 OR girado<0) filas_negativas
        FROM mef.fact_ejecucion_presupuestaria_anual""")[0]
    counts["dimensiones"] = consultar("""SELECT c.table_name AS dimension,
        count(*) FILTER (WHERE tc.constraint_type='FOREIGN KEY') AS claves_foraneas
        FROM information_schema.columns c LEFT JOIN information_schema.table_constraints tc
        ON tc.table_schema=c.table_schema AND tc.table_name=c.table_name AND c.ordinal_position=1
        WHERE c.table_schema='mef' GROUP BY c.table_name ORDER BY c.table_name""")
    return counts

LABELS = {"anio":"Año", "hechos":"Hechos", "entidades":"Entidades", "pia":"PIA (S/)", "pim":"PIM (S/)",
    "certificado":"Certificado (S/)", "comprometido_anual":"Comprometido anual (S/)",
    "comprometido":"Comprometido (S/)", "devengado":"Devengado (S/)", "girado":"Girado (S/)",
    "ejecucion_pct":"Ejecución (%)", "codigo":"Código", "nombre":"Nombre", "sec_ejec":"SEC_EJEC",
    "nivel_gobierno":"Nivel de gobierno", "variacion_pct":"Variación del devengado (%)"}
def exportar(df):
    # Decimal mantiene todos los céntimos; el float se usa exclusivamente en los gráficos.
    out = df.copy()
    for col in [*MEASURES,"ejecucion_pct","variacion_pct"]:
        if col in out:
            out[col] = out[col].map(lambda v: "" if v is None or pd.isna(v) else str(v).replace(".", ","))
    return out.rename(columns=LABELS).to_csv(index=False, sep=";").encode("utf-8-sig")

@st.cache_data(ttl=300, show_spinner=False)
def relaciones_esquema():
    """Solo catálogo PostgreSQL: no modifica consultas ni medidas presupuestarias."""
    return consultar("""SELECT c.conname, s.attname origen, r.relname destino,
        t.attname referencia, nr.nspname esquema_destino, c.convalidated validada,
        EXISTS(SELECT 1 FROM pg_constraint pk WHERE pk.conrelid=c.confrelid
               AND pk.contype='p' AND pk.conkey=c.confkey) referencia_pk
        FROM pg_constraint c
        JOIN pg_class f ON f.oid=c.conrelid JOIN pg_namespace n ON n.oid=f.relnamespace
        JOIN pg_class r ON r.oid=c.confrelid JOIN pg_namespace nr ON nr.oid=r.relnamespace
        JOIN pg_attribute s ON s.attrelid=f.oid AND s.attnum=c.conkey[1]
        JOIN pg_attribute t ON t.attrelid=r.oid AND t.attnum=c.confkey[1]
        WHERE n.nspname='mef' AND f.relname='fact_ejecucion_presupuestaria_anual'
        AND c.contype='f' ORDER BY s.attname""")
