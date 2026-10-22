"""Carga atomica exclusivamente en la base nueva registrada por crear_base.py."""
from datetime import datetime,timezone
import subprocess,json
from conexion import ROOT,M,command,psql,checksum,write_json
from verificar import verify
def main():
    receipt=ROOT/"evidencias"/"creacion_base.json"
    if not receipt.exists():raise RuntimeError("Falta constancia de creacion de la nueva base autorizada")
    creation=json.loads(receipt.read_text(encoding="utf-8"))
    if creation["created_database"]!=M["database"] or M["database"] in creation["existing_before"]:
        raise RuntimeError("El destino no es una base nueva del paquete")
    # Rechaza cualquier carga sobre una base con objetos de usuario; nunca trunca ni reemplaza.
    count=psql("SELECT count(*) FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname NOT IN ('pg_catalog','information_schema') AND n.nspname NOT LIKE 'pg_%'",M["database"])
    if count!="0":raise RuntimeError("La base contiene objetos: no se modifica; usar verificar.py si ya fue cargada")
    for f in M["files"]:
        if checksum(ROOT/f["file"])!=f["sha256"]:
            raise RuntimeError("Checksum incorrecto: "+f["file"])
    logfile=ROOT/"evidencias"/("carga_"+datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")+".log")
    with logfile.open("wb") as log:
        proc=subprocess.Popen(command(M["database"]),stdin=subprocess.PIPE,stdout=log,stderr=subprocess.STDOUT)
        try:
            def send(s):proc.stdin.write(s.encode("utf-8"))
            send("BEGIN;\nSET LOCAL client_encoding='UTF8';\n")
            send((ROOT.parent/"01_Base_de_Datos"/"sql"/"01_esquema.sql").read_text(encoding="utf-8")+"\n")
            for f in M["files"]:
                columns=",".join('"'+x.replace('"','""')+'"' for x in f["columns"])
                send("COPY "+f["table"]+"("+columns+") FROM STDIN WITH(FORMAT csv,HEADER true,ENCODING 'UTF8');\n")
                last=b""
                with (ROOT/f["file"]).open("rb") as stream:
                    for block in iter(lambda:stream.read(1024*1024),b""):
                        proc.stdin.write(block);last=block[-1:]
                if last!=b"\n":send("\n")
                send("\\.\n")
            for f in M["files"]:
                if f["table"]=="mef.dim_anio":continue
                key="hecho_key" if f["table"].endswith("fact_ejecucion_presupuestaria_anual") else f["table"].split("dim_")[1]+"_key"
                send("SELECT setval(pg_get_serial_sequence('"+f["table"]+"','"+key+"'),(SELECT max("+key+") FROM "+f["table"]+"),true);\n")
            send((ROOT.parent/"01_Base_de_Datos"/"sql"/"02_validaciones.sql").read_text(encoding="utf-8")+"\n")
            for f in M["files"]:send("ANALYZE "+f["table"]+";\n")
            send("COMMIT;\n")
            proc.stdin.close()
            code=proc.wait()
        except Exception:
            if proc.stdin and not proc.stdin.closed:proc.stdin.close()
            proc.wait()
            raise RuntimeError("Carga interrumpida; revisar "+str(logfile))
    if code:raise RuntimeError("PostgreSQL rechazo la transaccion; revisar "+str(logfile))
    report=verify()
    write_json(ROOT/"evidencias"/"carga_resultado.json",
               {"status":"loaded_and_verified","database":M["database"],"fact_rows":report["fact_rows"],
                "logfile":str(logfile),"loaded_at_utc":datetime.now(timezone.utc).isoformat()})
if __name__=="__main__":main()
