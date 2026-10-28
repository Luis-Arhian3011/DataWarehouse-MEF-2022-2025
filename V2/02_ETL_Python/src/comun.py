import csv, hashlib, json, re
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG = json.loads((ROOT / "config_fuentes.json").read_text(encoding="utf-8"))
import os
PROJECT = ROOT.parent
SNAPSHOT = Path(os.environ.get("MEF_ANUAL_DIR") or ROOT / CONFIG["annual_snapshot"]).resolve()
AUDIT = Path(os.environ.get("MEF_AUDIT_DIR") or ROOT / CONFIG["audit_work"]).resolve()
REFERENCE = ROOT / CONFIG["reference"]
OLD_AUDIT = AUDIT
MEASURES = "pia pim certificado comprometido_anual comprometido devengado girado".split()
MONTHS = "ENERO FEBRERO MARZO ABRIL MAYO JUNIO JULIO AGOSTO SEPTIEMBRE OCTUBRE NOVIEMBRE DICIEMBRE".split()
ENTITY = "NIVEL_GOBIERNO SECTOR PLIEGO EJECUTORA SEC_EJEC DEPARTAMENTO_EJECUTORA PROVINCIA_EJECUTORA DISTRITO_EJECUTORA".split()
INTERV = "PROGRAMA_PPTO TIPO_ACT_PROY PRODUCTO_PROYECTO ACTIVIDAD_ACCION_OBRA".split()
FUNC = "FUNCION DIVISION_FUNCIONAL GRUPO_FUNCIONAL".split()
FIN = "FUENTE_FINANCIAMIENTO RUBRO TIPO_RECURSO".split()
CLAS = "CATEGORIA_GASTO TIPO_TRANSACCION GENERICA SUBGENERICA SUBGENERICA_DET ESPECIFICA ESPECIFICA_DET".split()
CORE = ENTITY + INTERV + FUNC + ["META", "DEPARTAMENTO_META"] + FIN + CLAS
GRAIN = ["ANO_EJE"] + CORE + ["SEC_FUNC", "FINALIDAD", "META_NOMBRE"]
ANNUAL_SOURCE = ["MONTO_PIA", "MONTO_PIM", "MONTO_CERTIFICADO_ANUAL", "MONTO_COMPROMETIDO_ANUAL", "MONTO_DEVENGADO_ANUAL", "MONTO_GIRADO_ANUAL"]
ANNUAL_TARGET = ["pia", "pim", "certificado", "comprometido_anual", "devengado", "girado"]
CONTEXT = "anio_key entidad_key intervencion_key funcion_key meta_key financiamiento_key clasificador_gasto_key".split()

def require(condition, message):
    if not condition:
        raise ValueError(message)

def js(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))

def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()

def money(text):
    require(isinstance(text, str) and re.fullmatch(r"[+-]?[0-9]+(\.[0-9]{1,2})?", text.strip()), "Importe ausente o no decimal")
    value = Decimal(text.strip())
    require(abs(value) < Decimal("1000000000000000000"), "Importe fuera de NUMERIC(20,2)")
    return value

def rows(path):
    with Path(path).open(encoding="utf-8-sig", newline="") as stream:
        yield from csv.DictReader(stream)

def save_json(path, obj):
    with Path(path).open("x", encoding="utf-8") as stream:
        json.dump(obj, stream, ensure_ascii=False, indent=2, default=str)

def write_csv(path, columns, records):
    with Path(path).open("x", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns)
        writer.writeheader()
        count = 0
        for record in records:
            writer.writerow(record)
            count += 1
    return dict(file=Path(path).name, columns=columns, rows=count, sha256=sha(path))
