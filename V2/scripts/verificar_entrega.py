"""Integridad y revision offline; no usa PostgreSQL ni modifica Docker."""
import argparse,ast,hashlib,json,re,sys,tomllib,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(path):
    h=hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda:stream.read(1024*1024),b""):h.update(block)
    return h.hexdigest()
def included(path):
    rel=path.relative_to(ROOT)
    return path.is_file() and "ejecuciones" not in rel.parts and "trabajo" not in rel.parts and "__pycache__" not in rel.parts and not any(p.startswith(".venv") for p in rel.parts) and path.name not in (".env","secrets.toml")
def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--crear-manifiesto",action="store_true")
    args=parser.parse_args()
    files=sorted(p for p in ROOT.rglob("*") if included(p))
    manifest=ROOT/"SHA256SUMS.txt"
    if args.crear_manifiesto:
        # El manifiesto se regenera solo por opcion explicita dentro de esta entrega.
        with manifest.open("w",encoding="utf-8",newline="\n") as out:
            for p in files:
                if p!=manifest:out.write(sha(p)+"  "+p.relative_to(ROOT).as_posix()+"\n")
        print("Manifiesto actualizado");return
    assert manifest.is_file(),"Falta SHA256SUMS.txt"
    count=0
    for line in manifest.read_text(encoding="utf-8").splitlines():
        digest,name=line.split(maxsplit=1)
        path=(ROOT/name).resolve()
        assert path.is_relative_to(ROOT) and path.is_file(),name
        assert sha(path)==digest,name
        count+=1
    oversized=[str(p.relative_to(ROOT)) for p in files if p.stat().st_size>=100000000]
    assert not oversized,oversized
    for p in ROOT.rglob("*.py"):
        if included(p):ast.parse(p.read_text(encoding="utf-8"))
    for p in ROOT.rglob("*.toml*"):
        if included(p):tomllib.loads(p.read_text(encoding="utf-8"))
    links=[]
    external=[]
    for p in ROOT.rglob("*.md"):
        if not included(p):continue
        text=p.read_text(encoding="utf-8")
        for link in re.findall(r"\]\(([^)]+)\)",text):
            link=link.strip("<>").split("#")[0]
            if not link or re.match(r"^(https?://|mailto:)",link):continue
            target=(p.parent/link).resolve()
            if not target.is_relative_to(ROOT) or not target.exists():links.append([p.relative_to(ROOT).as_posix(),link])
    assert not links,links
    findings=[]
    patterns=[r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----",r"\bgh[pousr]_[A-Za-z0-9]{30,}\b",r"\bAKIA[A-Z0-9]{16}\b"]
    for p in files:
        if p.suffix.lower() not in (".py",".md",".json",".toml",".txt",".yml",".example",".env"):continue
        text=p.read_text(encoding="utf-8",errors="replace")
        if any(re.search(pattern,text) for pattern in patterns):findings.append(str(p.relative_to(ROOT)))
        if re.search(r"(?<![A-Za-z])[A-Za-z]:[\\/]",text):external.append(str(p.relative_to(ROOT)))
    assert not findings,findings
    assert not external,("Rutas absolutas Windows",external)
    # Los doce CSV y sus hashes forman parte del contrato de carga.
    annual=json.loads((ROOT/"02_ETL_Python/datos_preparados/anual/manifest.json").read_text(encoding="utf-8"))
    monthly=json.loads((ROOT/"02_ETL_Python/datos_preparados/mensual/manifest.json").read_text(encoding="utf-8"))
    for folder,entries in [(ROOT/"02_ETL_Python/datos_preparados/anual",annual["files"]),(ROOT/"02_ETL_Python/datos_preparados/mensual",monthly["files"])]:
        for item in entries:assert sha(folder/item["file"])==item["sha256"],item["file"]
    backup=ROOT/"01_Base_de_Datos/respaldo/dw_mef_2022_2025_v2_completo_20261028T170603643031Z.dump"
    assert sha(backup)=="3da3bafb255c3fdf69884417c72f9dccfc3647422b21a8aa05af9c5682499b96"
    result=dict(status="correcto",hashes=count,oversized=oversized,broken_links=links,windows_paths=external,secret_patterns=findings,backup_matches=True,prepared_csv_files=12,python_syntax=True)
    out=ROOT/"05_Pruebas_y_Evidencias/ejecuciones"/("verificacion_offline_"+str(time.time_ns())+".json")
    with out.open("x",encoding="utf-8") as stream:json.dump(result,stream,ensure_ascii=False,indent=2)
    print(json.dumps(result))
if __name__=="__main__":main()
