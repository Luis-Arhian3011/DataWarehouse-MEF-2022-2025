"""Cliente psql del contenedor existente; no requiere psycopg ni contrasenas en archivos."""
from pathlib import Path
from decimal import Decimal
import subprocess,json,hashlib,os
ROOT=Path(__file__).resolve().parent
M=json.loads((ROOT/"manifest.json").read_text(encoding="utf-8"))
if M["database"]!="dw_mef_2022_2025" or M["container"]!="postgres-db":
    raise RuntimeError("Destino distinto del paquete revisado")
def command(database):
    return ["docker","exec","-i","-e","PGCLIENTENCODING=UTF8",os.environ.get("MEF_CONTAINER",M["container"]),
            "psql","-X","-q","-v","ON_ERROR_STOP=1","-U",M["role"],"-d",database]
def psql(sql,database):
    result=subprocess.run(command(database)+["-At","-c",sql],input=b"",
                          stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    if result.returncode:
        raise RuntimeError(result.stderr.decode("utf-8",errors="replace"))
    return result.stdout.decode("utf-8").strip()
def query_json(sql,database):
    return json.loads(psql(sql,database),parse_float=Decimal)
def checksum(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda:f.read(1024*1024),b""):h.update(block)
    return h.hexdigest()
def write_json(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2,default=str),encoding="utf-8")
