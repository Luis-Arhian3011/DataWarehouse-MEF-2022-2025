"""Reprocesamiento opcional de CSV mensuales. No descarga ni usa PostgreSQL."""
import argparse,csv,hashlib,json,os,shutil,subprocess,sys,time
from pathlib import Path
import psutil
ROOT=Path(__file__).resolve().parents[1]
PACKAGE=ROOT.parent
NAMES={2022:"2022-Gasto-Devengado.csv",2023:"2023-Gasto-Devengado.csv",2024:"2024-Gasto-Devengado.csv",2025:"2025-Gasto-Devengado-Mensual.csv"}
def require(value,message):
    if not value:raise ValueError(message)
def sha(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""):h.update(b)
    return h.hexdigest()
def save(p,value):
    with p.open("x",encoding="utf-8") as f:json.dump(value,f,ensure_ascii=False,indent=2,default=str)
def worker(year,pilot):
    sys.path.insert(0,str(ROOT/"auditoria_fuentes"))
    from auditlib import connect,stage,quality,duplicates,GRAIN,OUT,EVID,CFG
    from mapping import mapping
    expected=json.loads((ROOT/"insumos_auditoria/evidencias"/f"resultado_{year}.json").read_text(encoding="utf-8"))
    source=Path(CFG["sources"][str(year)])
    before=source.stat()
    parquet=OUT/"parquet"/f"fuente_{year}.parquet"
    con=connect()
    stage(con,source,parquet,limit=pilot or None)
    qdoc=quality(con,parquet,year,str(year))
    grain=duplicates(con,parquet,GRAIN,str(year)+"_grano")
    require(qdoc["diferencias_meses"]==0,"Diferencias entre suma mensual y anual")
    correspondence=mapping(con,parquet,year,qdoc,grain)
    con.close()
    if not pilot:
        digest=sha(source)
        require(digest==expected["sha256"],"CSV no coincide con la fuente poblacional auditada; no continuar")
        original=ROOT/"insumos_auditoria/evidencias"/f"cohorte_disponible_{year}.csv"
        current=EVID/f"cohorte_disponible_{year}.csv"
        def keys(path):
            with path.open(encoding="utf-8-sig",newline="") as f:
                return {tuple(sorted(row.items())) for row in csv.DictReader(f)}
        require(keys(current)==keys(original),"La cohorte difiere de la auditada; requiere revision")
    else:digest="PILOTO_NO_VALIDO_PARA_SELECCION"
    after=source.stat()
    require((before.st_size,before.st_mtime_ns)==(after.st_size,after.st_mtime_ns),"Fuente cambio mientras se procesaba")
    save(EVID/f"resultado_{year}.json",dict(year=year,source=str(source),bytes=after.st_size,mtime_ns=after.st_mtime_ns,sha256=digest,parquet_bytes=parquet.stat().st_size,parquet_sha256=sha(parquet),quality=qdoc,grain=grain,correspondence_legacy=correspondence,pilot=bool(pilot)))

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--fuentes",type=Path)
    parser.add_argument("--salida",type=Path,default=ROOT/"trabajo/auditoria")
    parser.add_argument("--autorizar-lectura",action="store_true")
    parser.add_argument("--piloto",type=int,default=0)
    parser.add_argument("--worker",type=int,choices=range(2022,2026))
    args=parser.parse_args()
    if args.worker:
        worker(args.worker,args.piloto);return
    require(args.autorizar_lectura,"Lectura costosa: falta --autorizar-lectura")
    source_dir=Path(args.fuentes or os.environ.get("MEF_FUENTES_DIR") or ROOT/"fuentes_externas").resolve()
    out=args.salida.resolve()
    require(out.is_relative_to(ROOT/"trabajo"),"La salida debe estar dentro de 02_ETL_Python/trabajo")
    require(not out.exists(),"Salida existente: no se sobrescribe")
    require(shutil.disk_usage(ROOT).free>10*1024**3,"Se requieren al menos 10 GiB libres")
    require(args.piloto>=0,"Limite piloto invalido")
    sources={str(y):str(source_dir/n) for y,n in NAMES.items()}
    require(all(Path(p).is_file() for p in sources.values()),"Falta uno de los cuatro CSV mensuales")
    out.mkdir(parents=True)
    (out/"parquet").mkdir();(out/"evidencias").mkdir()
    cfg=dict(root=str(PACKAGE),memory_limit_engine="768MiB",threads=2,max_temp_directory_size="32GiB",compact_ref=str(ROOT/"insumos_auditoria/referencia_anual.parquet"),sources=sources)
    save(out/"config_auditoria.json",cfg)
    env={**os.environ,"MEF_AUDIT_DIR":str(out),"PYTHONDONTWRITEBYTECODE":"1"}
    years=[2022] if args.piloto else list(range(2022,2026))
    peak=0
    for year in years:
        command=[sys.executable,"-B",str(Path(__file__).resolve()),"--worker",str(year),"--piloto",str(args.piloto)]
        process=subprocess.Popen(command,env=env)
        reason=None
        while process.poll() is None:
            try:
                p=psutil.Process(process.pid)
                rss=sum(x.memory_info().rss for x in [p]+p.children(recursive=True))+psutil.Process().memory_info().rss
                peak=max(peak,rss)
                used=sum(x.stat().st_size for x in out.rglob("*") if x.is_file())
                if rss>int(1.95*1024**3):reason="Memoria superior a 1.95 GiB"
                if used>40*1024**3:reason="Temporales superiores a 40 GiB"
                if shutil.disk_usage(ROOT).free<1024**3:reason="Disco libre inferior a 1 GiB"
                if reason:
                    for x in reversed([p]+p.children(recursive=True)):
                        if x.is_running():x.terminate()
                    break
            except psutil.NoSuchProcess:pass
            time.sleep(0.5)
        code=process.wait()
        save(out/"evidencias"/f"recursos_{year}.json",dict(exit_code=code,reason=reason,peak_rss_bytes=peak))
        require(code==0 and reason is None,"Proceso detenido; conservar evidencias y no aumentar limites automaticamente")
    if not args.piloto:
        with (out/"MANIFIESTO_EVIDENCIAS.sha256").open("x",encoding="utf-8") as f:
            for p in sorted((out/"evidencias").glob("*")):
                if p.is_file():f.write(sha(p)+"  "+p.relative_to(out).as_posix()+"\n")
    print("Auditoria local finalizada. "+("Piloto: no permite seleccionar." if args.piloto else "Defina MEF_AUDIT_DIR a esta salida antes de preparar la seleccion."))

if __name__=="__main__":main()
