"""Ejecutar solo despues de autorizacion explicita para crear la base nueva."""
from datetime import datetime,timezone
from conexion import ROOT,M,psql,query_json,write_json
def main():
    before=query_json("SELECT json_agg(datname ORDER BY datname) FROM pg_database WHERE NOT datistemplate","postgres")
    if M["database"] in before:
        raise RuntimeError("La base ya existe: no se modifica ni reemplaza")
    can_create=psql("SELECT rolsuper OR rolcreatedb FROM pg_roles WHERE rolname=current_user","postgres")
    if can_create!="t":raise RuntimeError("El rol no tiene permiso CREATE DATABASE")
    sql=(ROOT.parent/"01_Base_de_Datos"/"sql"/"00_crear_base.sql").read_text(encoding="utf-8")
    psql(sql,"postgres")
    info=query_json("SELECT json_build_object('database',current_database(),'role',current_user,'version',version())",M["database"])
    write_json(ROOT/"evidencias"/"creacion_base.json",
               {"created_database":M["database"],"existing_before":before,"connection":info,
                "created_at_utc":datetime.now(timezone.utc).isoformat()})
    print("Base nueva creada: "+M["database"])
if __name__=="__main__":main()
