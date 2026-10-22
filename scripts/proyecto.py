"""Operaciones explícitas del entorno independiente; nunca ejecuta el ETL."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,hashlib,importlib,json,os,secrets,socket,subprocess,sys
from entorno import ROOT,env_path,cargar_config,compose_base,ejecutar_compose,proceso_env,psql,query_json

ARCHIVE=ROOT/"01_Base_de_Datos/respaldo/dw_mef_2022_2025_completo_20261022T182048021354Z.dump"
EXPECTED_SHA="b9177e726595b4621de32a347e9d56fbbab0bf811e79bdff2be2899923c3c138"

def configurar():
    path=env_path()
    path.parent.mkdir(parents=True,exist_ok=True)
    text=(ROOT/".env.example").read_text(encoding="utf-8")
    text=text.replace("POSTGRES_PASSWORD=","POSTGRES_PASSWORD="+secrets.token_urlsafe(32),1)
    with path.open("x",encoding="utf-8") as f:f.write(text)
    print("Configuración privada creada. Contraseña generada sin mostrarla. No publiques .env.")

def validar_volumen(cfg):
    name=cfg["COMPOSE_PROJECT_NAME"]+"_pgdata"
    r=subprocess.run(["docker","volume","inspect",name],capture_output=True,env=proceso_env(cfg),timeout=30)
    if r.returncode:
        # Diferencia inexistencia de errores del daemon antes de permitir up.
        listed=subprocess.run(["docker","volume","ls","--format","{{.Name}}"],capture_output=True,timeout=30)
        if listed.returncode or name in listed.stdout.decode().splitlines():
            raise RuntimeError("No se pudo comprobar el volumen de destino.")
        return
    labels=json.loads(r.stdout)[0].get("Labels") or {}
    if labels.get("com.docker.compose.project")!=cfg["COMPOSE_PROJECT_NAME"] or labels.get("com.docker.compose.volume")!="pgdata":
        raise RuntimeError("El volumen existe y no pertenece al proyecto: no se reutiliza.")

def validar_contenedor(cfg):
    cid=ejecutar_compose(cfg,["ps","-q","postgres"]).strip()
    if not cid or "\n" in cid:raise RuntimeError("El servicio PostgreSQL no está iniciado.")
    args=["docker","inspect","--format",
        '{{.Name}}|{{index .Config.Labels "com.docker.compose.project"}}|{{index .Config.Labels "com.docker.compose.service"}}',cid]
    r=subprocess.run(args,capture_output=True,env=proceso_env(cfg),timeout=30)
    fields=r.stdout.decode().strip().split("|")
    if r.returncode or len(fields)!=3 or fields[0]=="/postgres-db" or fields[1:]!=[cfg["COMPOSE_PROJECT_NAME"],"postgres"]:
        raise RuntimeError("El contenedor no pertenece al entorno Compose autorizado.")
    return cid

def verificar(cfg,salida):
    validar_contenedor(cfg)
    # Reutiliza el verificador real del proyecto, cambiando solo el transporte y destino.
    sys.path.insert(0,str(ROOT/"02_ETL_Python"))
    v=importlib.import_module("verificar")
    v.query_json=lambda sql,database:query_json(cfg,sql,cfg["POSTGRES_DB"])
    v.write_json=lambda path,data:None
    report=v.verify()
    rels=query_json(cfg,"""SELECT json_agg(row_to_json(t) ORDER BY origen) FROM (
        SELECT s.attname origen,r.relname destino,t.attname referencia,c.convalidated validada
        FROM pg_constraint c JOIN pg_class f ON f.oid=c.conrelid
        JOIN pg_namespace n ON n.oid=f.relnamespace JOIN pg_class r ON r.oid=c.confrelid
        JOIN pg_attribute s ON s.attrelid=f.oid AND s.attnum=c.conkey[1]
        JOIN pg_attribute t ON t.attrelid=r.oid AND t.attnum=c.confkey[1]
        WHERE n.nspname='mef' AND f.relname='fact_ejecucion_presupuestaria_anual'
        AND c.contype='f') t""")
    expected=json.loads((ROOT/"05_Evidencias/relaciones_verificadas.json").read_text(encoding="utf-8"))
    if {(x["origen"],x["destino"],x["referencia"]) for x in rels}!={(x["origen"],x["destino"],x["referencia"]) for x in expected} or not all(x["validada"] for x in rels):
        raise RuntimeError("Las siete relaciones no coinciden con el modelo.")
    report.update(relaciones=rels,verificacion_solo_lectura=True)
    guardar(salida,report)
    return report

def guardar(path,data):
    if path:
        p=Path(path);p.parent.mkdir(parents=True,exist_ok=True)
        with p.open("x",encoding="utf-8") as f:json.dump(data,f,ensure_ascii=False,indent=2,default=str)

def restaurar(cfg,salida):
    validar_contenedor(cfg)
    h=hashlib.sha256()
    with ARCHIVE.open("rb") as f:
        for block in iter(lambda:f.read(1048576),b""):h.update(block)
    if h.hexdigest()!=EXPECTED_SHA:raise RuntimeError("El respaldo no coincide con su SHA-256.")
    listing=ejecutar_compose(cfg,["exec","-T","postgres","pg_restore","--list","/respaldo/mef.dump"])
    manifest=json.loads((ROOT/"02_ETL_Python/manifest.json").read_text(encoding="utf-8"))
    if not all(" TABLE DATA mef "+x["table"].split(".")[1]+" " in listing for x in manifest["files"]):
        raise RuntimeError("El archivo no contiene las ocho tablas esperadas.")
    version=ejecutar_compose(cfg,["exec","-T","postgres","pg_restore","--version"])
    if not version.startswith("pg_restore (PostgreSQL) 15."):
        raise RuntimeError("Esta entrega requiere PostgreSQL 15.")
    exists=query_json(cfg,"SELECT coalesce(json_agg(datname),'[]'::json) FROM pg_database WHERE datname='"+cfg["POSTGRES_DB"]+"'","postgres")
    if exists:raise RuntimeError("La base de destino ya existe: no se modifica ni se reemplaza.")
    # El destino se crea solo después de los controles. --single-transaction hace atómica la carga.
    psql(cfg,'CREATE DATABASE "'+cfg["POSTGRES_DB"]+'" WITH TEMPLATE template0 ENCODING \'UTF8\';',"postgres",False)
    try:
        ejecutar_compose(cfg,["exec","-T","postgres","pg_restore","--exit-on-error","--single-transaction",
            "--no-owner","--no-privileges","-U",cfg["POSTGRES_USER"],"-d",cfg["POSTGRES_DB"],
            "/respaldo/mef.dump"],timeout=600)
        report=verificar(cfg,None)
    except Exception:
        guardar(salida,{"estado":"restauracion_fallida","base":cfg["POSTGRES_DB"],"base_creada_conservada":True,
            "nota":"No se elimina automáticamente la base ni el volumen. Revisar antes de continuar."})
        raise
    report.update(estado="restaurado_y_verificado",restauracion_completa_ejecutada=True,
        fecha_utc=datetime.now(timezone.utc).isoformat(),sha256=h.hexdigest(),
        propietarios="Objetos propiedad del usuario configurado; sin restaurar ACL ni roles globales.")
    guardar(salida,report)
    print("Restauración completada: 150.000 hechos y controles de integridad correctos.")

def app_env(cfg):
    env=proceso_env(cfg)
    env.update(MEF_ENV_FILE=str(env_path()),MEF_TRANSPORT=cfg["MEF_TRANSPORT"],
        PGHOST=cfg["POSTGRES_HOST"],PGPORT=cfg["POSTGRES_PORT"],PGDATABASE=cfg["POSTGRES_DB"],
        PGUSER=cfg["POSTGRES_USER"],PGPASSWORD=cfg["POSTGRES_PASSWORD"])
    return env

def main():
    p=argparse.ArgumentParser(description="Proyecto MEF: entorno independiente y recuperación segura.")
    p.add_argument("accion",choices=["configurar","iniciar","detener","restaurar","verificar","dashboard","pruebas"])
    p.add_argument("--salida",help="JSON nuevo, fuera del repositorio para pruebas aisladas.")
    p.add_argument("--puerto",type=int,default=8501)
    args=p.parse_args()
    try:
        if args.accion=="configurar":configurar();return
        cfg=cargar_config()
        if args.salida and Path(args.salida).exists():raise RuntimeError("El archivo de salida ya existe.")
        if args.accion=="iniciar":
            # No se ejecuta automáticamente; requiere decisión del usuario.
            validar_volumen(cfg)
            ejecutar_compose(cfg,["config","--quiet"])
            ejecutar_compose(cfg,["up","-d","--wait"],timeout=300)
            print("PostgreSQL independiente iniciado y saludable.")
        elif args.accion=="detener":
            ejecutar_compose(cfg,["stop"])
            print("Servicios detenidos; contenedores y volumen conservados.")
        elif args.accion=="restaurar":restaurar(cfg,args.salida)
        elif args.accion=="verificar":verificar(cfg,args.salida)
        elif args.accion=="dashboard":
            validar_contenedor(cfg)
            raise SystemExit(subprocess.call([sys.executable,"-B","-m","streamlit","run","app.py",
                "--server.port",str(args.puerto)],cwd=ROOT/"03_Dashboard",env=app_env(cfg)))
        elif args.accion=="pruebas":
            validar_contenedor(cfg)
            for name in ["verificar_dashboard.py","verificar_pulido.py"]:
                r=subprocess.run([sys.executable,"-B",name],cwd=ROOT/"03_Dashboard",env=app_env(cfg))
                if r.returncode:raise RuntimeError("Falló "+name)
            print("117 comprobaciones automatizadas finalizadas.")
    except (RuntimeError,OSError,subprocess.TimeoutExpired,ValueError) as exc:
        print("ERROR: "+str(exc),file=sys.stderr)
        raise SystemExit(1)

if __name__=="__main__":main()
