"""Operaciones futuras explicitas. No elimina bases, contenedores ni volumenes."""
import argparse,hashlib,json,os,subprocess,sys,time
from pathlib import Path
import psycopg
from psycopg import sql
from entorno import ROOT,DB,configuracion,compose,proceso_env

BACKUP=ROOT/"01_Base_de_Datos/respaldo/dw_mef_2022_2025_v2_completo_20261028T170603643031Z.dump"
EXPECTED="3da3bafb255c3fdf69884417c72f9dccfc3647422b21a8aa05af9c5682499b96"
def require(value,message):
    if not value:raise ValueError(message)
def checksum(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda:f.read(1024*1024),b""):h.update(block)
    return h.hexdigest()
def connection(cfg,dbname=DB,readonly=True):
    return psycopg.connect(host=cfg["PGHOST"],port=int(cfg["PGPORT"]),user=cfg["PGUSER"],password=cfg["PGPASSWORD"],dbname=dbname,connect_timeout=5,
        options="-c default_transaction_read_only="+("on" if readonly else "off")+" -c statement_timeout=300000")
def diagnostic(cfg):
    with connection(cfg,"postgres") as con:
        with con.cursor() as cur:
            cur.execute("SELECT current_setting('server_version_num')::int,system_identifier::text FROM pg_control_system()")
            version,identifier=cur.fetchone()
            cur.execute("SELECT EXISTS(SELECT 1 FROM pg_database WHERE datname=%s)",[DB])
            exists=cur.fetchone()[0]
    return dict(version=version,system_identifier=identifier,database=DB,exists=exists)
def owned_container(cfg,identifier):
    args=compose(cfg)+["ps","--quiet","postgres"]
    result=subprocess.run(args,env=proceso_env(cfg),capture_output=True,text=True,check=True)
    cid=result.stdout.strip()
    require(cid,"No hay un servicio postgres de este proyecto Compose")
    inspect=json.loads(subprocess.run(["docker","inspect",cid],capture_output=True,text=True,check=True).stdout)[0]
    require(inspect["Name"]!="/postgres-db","No se permite restaurar mediante el contenedor original postgres-db")
    require(inspect["Config"]["Labels"].get("com.docker.compose.project")==cfg["COMPOSE_PROJECT_NAME"],"Contenedor de otro proyecto")
    query=compose(cfg)+["exec","-T","postgres","psql","-U",cfg["PGUSER"],"-d","postgres","-X","-At","-v","ON_ERROR_STOP=1","-c","SELECT system_identifier::text FROM pg_control_system()"]
    seen=subprocess.run(query,env=proceso_env(cfg),capture_output=True,text=True,check=True).stdout.strip()
    require(seen==identifier,"TCP y Compose no corresponden al mismo servidor")
def verify(cfg):
    sys.path.insert(0,str(ROOT/"02_ETL_Python/src"))
    import postgres_v2
    with connection(cfg) as con:
        result=postgres_v2.verify(con,ROOT/"02_ETL_Python/datos_preparados/mensual")
        with con.cursor() as cur:
            cur.execute("SELECT count(*) FILTER(WHERE devengado<0),count(*) FILTER(WHERE devengado=0) FROM mef.fact_devengado_mensual")
            require(cur.fetchone()==(324,124976),"Negativos o ceros distintos")
    return result

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("accion",choices=["diagnostico","verificar","restaurar","cargar-preparados","dashboard"])
    parser.add_argument("--autorizar",action="store_true")
    parser.add_argument("--puerto-web",type=int,default=8502)
    args=parser.parse_args()
    cfg=configuracion()
    if args.accion=="dashboard":
        require(1024<=args.puerto_web<=65535,"Puerto web invalido")
        cmd=[sys.executable,"-B","-m","streamlit","run",str(ROOT/"03_Dashboard/app.py"),"--server.address","127.0.0.1","--server.port",str(args.puerto_web)]
        raise SystemExit(subprocess.call(cmd,cwd=ROOT/"03_Dashboard",env=proceso_env(cfg)))
    state=diagnostic(cfg)
    if args.accion=="diagnostico":print(json.dumps(state));return
    if args.accion=="verificar":print(json.dumps(verify(cfg)));return
    require(args.autorizar,"Falta --autorizar para crear y poblar una base nueva")
    require(not state["exists"],"El destino ya existe. No se sobrescribe, no se limpia y no se reintenta automaticamente")
    require(state["version"]//10000==15,"Revisar compatibilidad; paquete preparado para PostgreSQL 15")
    owned_container(cfg,state["system_identifier"])
    require(checksum(BACKUP)==EXPECTED,"SHA-256 del respaldo distinto")
    if args.accion=="cargar-preparados":
        env=proceso_env(cfg);env["V2_EXPECTED_SERVER_ID"]=state["system_identifier"]
        cmd=[sys.executable,"-B",str(ROOT/"02_ETL_Python/src/postgres_v2.py"),"crear-y-cargar","--autorizar-creacion-y-carga","--confirmar",DB]
        raise SystemExit(subprocess.call(cmd,cwd=ROOT/"02_ETL_Python",env=env))
    # La base se crea solo si no existe; cualquier error de concurrencia detiene el proceso.
    with connection(cfg,"postgres",False) as con:
        con.autocommit=True
        con.execute(sql.SQL("CREATE DATABASE {} TEMPLATE template0 ENCODING 'UTF8'").format(sql.Identifier(DB)))
    log=ROOT/"05_Pruebas_y_Evidencias/ejecuciones"/("restauracion_"+str(time.time_ns())+".log")
    cmd=compose(cfg)+["exec","-T","postgres","pg_restore","-U",cfg["PGUSER"],"--dbname="+DB,"--no-owner","--no-privileges","--exit-on-error","--single-transaction","--verbose"]
    with BACKUP.open("rb") as source,log.open("xb") as output:
        result=subprocess.run(cmd,env=proceso_env(cfg),stdin=source,stdout=output,stderr=subprocess.STDOUT)
    require(result.returncode==0,"Restauracion fallida; destino conservado. No reintentar automaticamente. Revisar el registro")
    print(json.dumps(verify(cfg)))

if __name__=="__main__":
    try:main()
    except (ValueError,OSError,psycopg.Error,subprocess.SubprocessError) as error:
        # No DSN, comandos privados, mensajes del servidor o contrasenas.
        print("Operacion detenida ("+type(error).__name__+"). Revise configuracion privada, destino y evidencias. No se elimino ningun recurso.",file=sys.stderr)
        raise SystemExit(1)
