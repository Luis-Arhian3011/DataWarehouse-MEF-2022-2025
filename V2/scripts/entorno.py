"""Configuracion privada portable; nunca imprime contrasenas."""
import os,re,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
DB="dw_mef_2022_2025_v2"

def leer_env(path=None):
    path=Path(path or ROOT/".env")
    values={}
    if path.exists():
        for line in path.read_text(encoding="utf-8-sig").splitlines():
            line=line.strip()
            if not line or line.startswith("#"):continue
            if "=" not in line:raise ValueError("Linea invalida en configuracion privada")
            key,value=line.split("=",1)
            if not re.fullmatch(r"[A-Z][A-Z0-9_]*",key):raise ValueError("Nombre de variable invalido")
            value=value.strip()
            if len(value)>1 and value[0]==value[-1] and value[0] in "\"'":value=value[1:-1]
            values[key]=value
    return values

def configuracion():
    defaults={"PGHOST":"127.0.0.1","PGPORT":"55432","PGDATABASE":DB,"PGUSER":"mef_admin","PGPASSWORD":"","COMPOSE_PROJECT_NAME":"mef-v2-entrega"}
    local=leer_env()
    cfg={key:os.environ.get(key,local.get(key,value)) for key,value in defaults.items()}
    if cfg["PGDATABASE"]!=DB:raise ValueError("Solo se permite dw_mef_2022_2025_v2")
    if not re.fullmatch(r"mef-v2-[a-z0-9_-]+",cfg["COMPOSE_PROJECT_NAME"]):raise ValueError("Proyecto Compose debe comenzar por mef-v2-")
    int(cfg["PGPORT"])
    return cfg

def proceso_env(cfg):
    return {**os.environ,**cfg,"PYTHONDONTWRITEBYTECODE":"1"}

def compose(cfg):
    return ["docker","compose","--project-directory",str(ROOT),"-f",str(ROOT/"docker-compose.yml"),"--project-name",cfg["COMPOSE_PROJECT_NAME"]]
