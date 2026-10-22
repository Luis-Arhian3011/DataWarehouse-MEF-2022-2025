"""Configuración local y acceso a Compose; no imprime secretos."""
from pathlib import Path
import os
import re
import subprocess
import json
from decimal import Decimal

ROOT = Path(__file__).resolve().parents[1]
KEYS = ("COMPOSE_PROJECT_NAME","POSTGRES_HOST","POSTGRES_PORT","POSTGRES_USER",
        "POSTGRES_PASSWORD","POSTGRES_DB","MEF_TRANSPORT")

def env_path():
    return Path(os.environ.get("MEF_ENV_FILE",str(ROOT/".env"))).resolve()

def cargar_config(requerir=True):
    path=env_path()
    if requerir and not path.is_file():
        raise RuntimeError("Falta .env. Ejecuta: python scripts/proyecto.py configurar")
    values={}
    if path.is_file():
        for line in path.read_text(encoding="utf-8-sig").splitlines():
            line=line.strip()
            if not line or line.startswith("#"):continue
            key,sep,value=line.partition("=")
            if not sep or key.strip() not in KEYS:
                raise RuntimeError("Configuración .env no admitida; utiliza .env.example.")
            value=value.strip()
            if len(value)>1 and value[0]==value[-1] and value[0] in ("'",'"'):
                value=value[1:-1]
            values[key.strip()]=value
    defaults={"COMPOSE_PROJECT_NAME":"mef2025","POSTGRES_HOST":"127.0.0.1",
        "POSTGRES_PORT":"5433","POSTGRES_USER":"mef_admin",
        "POSTGRES_DB":"dw_mef_2022_2025","MEF_TRANSPORT":"compose"}
    cfg={k:os.environ.get(k,values.get(k,defaults.get(k,""))) for k in KEYS}
    if not re.fullmatch(r"[a-z0-9][a-z0-9_-]{2,50}",cfg["COMPOSE_PROJECT_NAME"]):
        raise RuntimeError("Nombre de proyecto Compose inválido.")
    for k in ("POSTGRES_USER","POSTGRES_DB"):
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{0,62}",cfg[k]):
            raise RuntimeError("Usuario/base deben ser identificadores PostgreSQL simples.")
    if cfg["POSTGRES_DB"] in ("postgres","template0","template1"):
        raise RuntimeError("La base de destino no puede ser una base de mantenimiento.")
    if not cfg["POSTGRES_PORT"].isdigit() or not 1024<=int(cfg["POSTGRES_PORT"])<=65535:
        raise RuntimeError("Puerto PostgreSQL inválido.")
    if requerir and len(cfg["POSTGRES_PASSWORD"])<16:
        raise RuntimeError("Configura una contraseña local de al menos 16 caracteres.")
    return cfg

def proceso_env(cfg):
    env=dict(os.environ)
    env.update(cfg)
    env["PYTHONDONTWRITEBYTECODE"]="1"
    env["PYTHONIOENCODING"]="utf-8"
    return env

def compose_base(cfg):
    return ["docker","compose","--project-directory",str(ROOT),
        "--env-file",str(env_path()),"-p",cfg["COMPOSE_PROJECT_NAME"],
        "-f",str(ROOT/"docker-compose.yml")]

def ejecutar_compose(cfg,args,entrada=None,timeout=300):
    r=subprocess.run(compose_base(cfg)+args,input=entrada,capture_output=True,
                     env=proceso_env(cfg),timeout=timeout)
    if r.returncode:
        # stderr de Compose puede revelar variables del entorno. No se retransmite.
        raise RuntimeError("Docker Compose no completó la operación; código "+str(r.returncode)+". Comprueba Docker, .env y el estado del servicio.")
    return r.stdout.decode("utf-8")

def psql(cfg,sql,base=None,solo_lectura=True):
    opts="-c statement_timeout=30000"
    if solo_lectura:opts+=" -c default_transaction_read_only=on"
    return ejecutar_compose(cfg,["exec","-T","-e","PGOPTIONS="+opts,
        "-e","PGCLIENTENCODING=UTF8","postgres","psql","-X","-q","-At",
        "-v","ON_ERROR_STOP=1","-U",cfg["POSTGRES_USER"],"-d",base or cfg["POSTGRES_DB"]],
        entrada=sql.encode("utf-8"))

def query_json(cfg,sql,base=None):
    return json.loads(psql(cfg,sql,base),parse_float=Decimal)
