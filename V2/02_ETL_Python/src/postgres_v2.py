"""Carga futura: solo una base V2 nueva, nunca la base original."""
import argparse,csv,json,os
from datetime import datetime,timezone
from decimal import Decimal
from pathlib import Path
import psycopg
from psycopg import sql
from comun import *
from validar_local import validate

DB="dw_mef_2022_2025_v2"

def connect(database,readonly=False):
    return psycopg.connect(dbname=database,connect_timeout=5,options="-c statement_timeout=300000 -c default_transaction_read_only="+("on" if readonly else "off"))

def verify(connection,folder):
    manifest=json.loads((folder/"manifest.json").read_text(encoding="utf-8"))
    with connection.cursor() as cur:
        cur.execute("SELECT current_database()")
        require(cur.fetchone()[0]==DB,"Base destino inesperada")
        cur.execute("SELECT count(*) FROM information_schema.tables WHERE table_schema='mef' AND table_type='BASE TABLE'")
        require(cur.fetchone()[0]==11,"Se esperan nueve dimensiones y dos hechos")
        cur.execute("SELECT count(*) FROM pg_constraint c JOIN pg_namespace n ON n.oid=c.connamespace WHERE n.nspname IN ('mef','auditoria') AND c.contype='f'")
        require(cur.fetchone()[0]==22,"Se esperan 22 FK totales")
        for table,count in [("mef.fact_ejecucion_presupuestaria_anual",150000),("mef.fact_devengado_mensual",150000),("auditoria.serie_seleccionada",12500),("mef.dim_periodo_mensual",48)]:
            cur.execute(sql.SQL("SELECT count(*) FROM {}").format(sql.Identifier(*table.split("."))))
            require(cur.fetchone()[0]==count,"Conteo inesperado: "+table)
        cur.execute("""SELECT s.hecho_anual_key FROM auditoria.serie_seleccionada s
          JOIN mef.fact_ejecucion_presupuestaria_anual a ON a.hecho_key=s.hecho_anual_key
          LEFT JOIN mef.fact_devengado_mensual m ON m.hecho_anual_key=s.hecho_anual_key
          GROUP BY s.hecho_anual_key,a.devengado
          HAVING count(m.hecho_mensual_key)<>12 OR count(DISTINCT m.periodo_key)<>12 OR sum(m.devengado)<>a.devengado LIMIT 1""")
        require(cur.fetchone() is None,"Conciliacion por serie fallida")
        cur.execute("SELECT anio_key,count(*) FROM mef.fact_devengado_mensual GROUP BY anio_key")
        require(dict(cur.fetchall())=={y:37500 for y in range(2022,2026)},"Cuotas incorrectas")
        cur.execute("SELECT anio_key,count(*) FROM auditoria.serie_seleccionada GROUP BY anio_key")
        require(dict(cur.fetchall())=={y:3125 for y in range(2022,2026)},"Series incorrectas")
        cur.execute("SELECT anio_key,"+",".join("sum("+m+")" for m in MEASURES)+" FROM mef.fact_ejecucion_presupuestaria_anual GROUP BY anio_key")
        actual={str(row[0]):row[1:] for row in cur.fetchall()}
        for expected in manifest["annual_totals"]:
            require(actual[str(expected["anio"])]==tuple(Decimal(expected[m]) for m in MEASURES),"28 totales anuales no conciliados")
        cur.execute("SELECT periodo_key,sum(devengado) FROM mef.fact_devengado_mensual GROUP BY periodo_key")
        actual={str(p):v for p,v in cur.fetchall()}
        require(actual=={k:Decimal(v) for k,v in manifest["monthly_totals"].items()},"48 controles mensuales no conciliados")
        # Las FK validas y habilitadas impiden huerfanos; detectar su desactivacion.
        cur.execute("""SELECT count(*) FROM pg_constraint c JOIN pg_namespace n ON n.oid=c.connamespace
          WHERE n.nspname IN ('mef','auditoria') AND c.contype='f' AND NOT c.convalidated""")
        require(cur.fetchone()[0]==0,"FK sin validar")
        cur.execute("""SELECT count(*) FROM pg_trigger t JOIN pg_class c ON c.oid=t.tgrelid
          JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname IN ('mef','auditoria')
          AND t.tgisinternal AND t.tgenabled='D'""")
        require(cur.fetchone()[0]==0,"Trigger de integridad desactivado")
    compare_snapshot(connection,manifest)
    return dict(valid=True,annual=150000,monthly=150000,series=12500,foreign_keys=22,annual_totals=28,monthly_totals=48,full_annual_snapshot_equal=True)

def compare_snapshot(connection,manifest):
    # Comparacion completa por columna para conservar exactamente el snapshot anual.
    for item in manifest["annual_files"]:
        table=sql.Identifier(*item["table"].split("."))
        columns=sql.SQL(",").join(map(sql.Identifier,item["columns"]))
        order=sql.Identifier(item["columns"][0])
        with connection.cursor(name="verificar_snapshot") as cur:
            cur.execute(sql.SQL("SELECT {} FROM {} ORDER BY {}").format(columns,table,order))
            iterator=iter(cur)
            for expected in rows(SNAPSHOT/item["file"]):
                observed=next(iterator,None)
                require(observed is not None,"Falta fila anual")
                for column,value in zip(item["columns"],observed):
                    wanted=expected[column]
                    if isinstance(value,(dict,list)):
                        require(value==json.loads(wanted),"JSON anual distinto")
                    elif isinstance(value,Decimal):
                        require(value==money(wanted),"Importe anual distinto")
                    else:
                        require(str(value)==wanted,"Atributo anual distinto: "+column)
            require(next(iterator,None) is None,"Filas anuales adicionales")

def copy_file(cur,table,path,columns):
    names=sql.SQL(",").join(map(sql.Identifier,columns))
    query=sql.SQL("COPY {} ({}) FROM STDIN WITH (FORMAT CSV, HEADER TRUE, FORCE_NOT_NULL ({}))").format(sql.Identifier(*table.split(".")),names,names)
    with cur.copy(query) as copy:
        with path.open("rb") as stream:
            for block in iter(lambda:stream.read(1024*1024),b""):
                copy.write(block)

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("action",choices=["diagnostico","verificar","crear-y-cargar"])
    parser.add_argument("--lote",type=Path,default=ROOT/"datos_preparados/mensual")
    parser.add_argument("--autorizar-creacion-y-carga",action="store_true")
    parser.add_argument("--confirmar")
    args=parser.parse_args()
    folder=args.lote.resolve()
    if args.action=="crear-y-cargar":
        require(args.autorizar_creacion_y_carga and args.confirmar==DB,"Falta autorizacion explicita y confirmacion V2")
    require(os.environ.get("PGDATABASE",DB)==DB,"PGDATABASE debe ser exclusivamente V2")
    if args.action=="verificar":
        with connect(DB,True) as connection:
            print(js(verify(connection,folder)))
        return
    expected_id=os.environ.get("V2_EXPECTED_SERVER_ID","")
    with connect("postgres",True) as connection:
        with connection.cursor() as cur:
            cur.execute("SELECT current_setting('server_version_num')::int,system_identifier::text FROM pg_control_system()")
            version,identifier=cur.fetchone()
            cur.execute("SELECT EXISTS(SELECT 1 FROM pg_database WHERE datname=%s)",[DB])
            exists=cur.fetchone()[0]
        print(js(dict(server_version=version,server_identifier=identifier,target=DB,target_exists=exists,readonly=True)))
    if args.action=="diagnostico":
        return
    require(args.autorizar_creacion_y_carga and args.confirmar==DB,"Falta autorizacion explicita y confirmacion V2")
    require(expected_id and expected_id==identifier,"Debe fijarse V2_EXPECTED_SERVER_ID al servidor diagnosticado")
    require(version//10000==15,"Paquete preparado para PostgreSQL 15; revisar otra version")
    require(not exists,"La base destino ya existe: no se sobrescribe ni se reanuda automaticamente")
    require((folder/"VALIDADO.json").exists(),"Lote sin validacion local")
    validate(folder)
    manifest=json.loads((folder/"manifest.json").read_text(encoding="utf-8"))
    # La carga portable valida los CSV incluidos; no necesita la base anual original.
    with connect("postgres") as connection:
        connection.autocommit=True
        with connection.cursor() as cur:
            cur.execute(sql.SQL("CREATE DATABASE {} TEMPLATE template0 ENCODING 'UTF8'").format(sql.Identifier(DB)))
    # Si falla desde aqui se conserva la base nueva. Nunca DROP ni eliminacion automatica.
    receipt=ROOT.parent/"05_Pruebas_y_Evidencias/ejecuciones"/("carga_"+datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")+".json")
    try:
        with connect(DB) as connection:
            with connection.cursor() as cur:
                cur.execute("SELECT count(*) FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname NOT IN ('pg_catalog','information_schema') AND n.nspname NOT LIKE 'pg_toast%'")
                require(cur.fetchone()[0]==0,"La nueva base no esta vacia")
                for name in ["01_modelo_anual.sql","02_modelo_mensual.sql"]:
                    cur.execute((ROOT.parent/"01_Base_de_Datos/sql"/name).read_text(encoding="utf-8"),prepare=False)
                for item in manifest["annual_files"]:
                    copy_file(cur,item["table"],SNAPSHOT/item["file"],item["columns"])
                table_for={"dim_periodo_mensual.csv":"mef.dim_periodo_mensual","dim_meta_detallada.csv":"mef.dim_meta_detallada","serie_seleccionada.csv":"auditoria.serie_seleccionada","fact_devengado_mensual.csv":"mef.fact_devengado_mensual"}
                for item in manifest["files"]:
                    copy_file(cur,table_for[item["file"]],folder/item["file"],item["columns"])
                for table,key in [("dim_entidad","entidad_key"),("dim_intervencion","intervencion_key"),("dim_funcion","funcion_key"),("dim_meta","meta_key"),("dim_financiamiento","financiamiento_key"),("dim_clasificador_gasto","clasificador_gasto_key"),("fact_ejecucion_presupuestaria_anual","hecho_key"),("dim_meta_detallada","meta_detalle_key"),("fact_devengado_mensual","hecho_mensual_key")]:
                    cur.execute(sql.SQL("SELECT setval(pg_get_serial_sequence(%s,%s),(SELECT max({}) FROM {}),true)").format(sql.Identifier(key),sql.Identifier("mef",table)),["mef."+table,key])
            result=verify(connection,folder)
        save_json(receipt,dict(committed=True,result=result,database=DB))
        print(js(result))
    except Exception as error:
        save_json(receipt,dict(status="requiere_revision_no_reintentar_automaticamente",database=DB,error_type=type(error).__name__,sqlstate=getattr(error,"sqlstate",None)))
        raise RuntimeError("Carga no completada o confirmacion local pendiente. Revisar la base V2; no se ha eliminado nada.") from None

if __name__=="__main__":
    main()
