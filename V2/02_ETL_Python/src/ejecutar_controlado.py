"""Monitor externo: detiene el grupo si excede memoria, disco o tiempo."""
import argparse,json,os,subprocess,sys,time
from pathlib import Path
import psutil
from comun import ROOT,save_json,require

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--salida",required=True)
    args=parser.parse_args()
    receipt=ROOT.parent/"05_Pruebas_y_Evidencias/ejecuciones"/("recursos_"+str(time.time_ns())+".json")
    command=[sys.executable,"-B",str(ROOT/"src/preparar_datos.py"),"--salida",args.salida]
    child=subprocess.Popen(command)
    peak=0
    started=time.monotonic()
    reason=None
    try:
        while child.poll() is None:
            processes=[psutil.Process(child.pid)]
            try:
                processes+=processes[0].children(recursive=True)
                rss=sum(p.memory_info().rss for p in processes if p.is_running())+psutil.Process().memory_info().rss
                peak=max(peak,rss)
                disk=sum(p.stat().st_size for p in (ROOT/"trabajo/spill").rglob("*") if p.is_file())
                if rss>int(1.95*1024**3):reason="Memoria superior a 1.95 GiB"
                if disk>1024**3:reason="Temporales superiores a 1 GiB"
                if psutil.disk_usage(str(ROOT)).free<1024**3:reason="Disco libre inferior a 1 GiB"
                if time.monotonic()-started>1800:reason="Tiempo superior a 30 minutos"
                if reason:
                    for p in reversed(processes):
                        if p.is_running():p.terminate()
                    break
            except psutil.NoSuchProcess:
                pass
            time.sleep(0.5)
        code=child.wait()
    finally:
        save_json(receipt,dict(exit_code=child.poll(),reason=reason,peak_rss_bytes=peak,elapsed_seconds=round(time.monotonic()-started,2),command=command,postgres=False))
    require(not reason and code==0,"Preparacion detenida: "+str(reason or code))

if __name__=="__main__":main()
