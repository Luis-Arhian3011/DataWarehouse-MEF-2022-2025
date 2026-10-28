"""Preparacion local exclusivamente; no importa psycopg ni abre conexiones PostgreSQL."""
import argparse, csv, hashlib, json, shutil, time
from collections import Counter, defaultdict
from decimal import Decimal
from pathlib import Path
import duckdb
from comun import *
from muestreo import select

def expression(column):
    if column == "TIPO_ACT_PROY":
        return """CASE trim("TIPO_ACT_PROY") WHEN 'ACTIVIDAD' THEN '3' WHEN 'PROYECTO' THEN '2' ELSE trim("TIPO_ACT_PROY") END"""
    return 'trim("' + column + '")'

def prepare(destination):
    start = time.monotonic()
    destination = destination.resolve()
    require(destination.is_relative_to(ROOT / "datos_preparados"), "Salida fuera de V2/datos_preparados")
    require(not destination.exists(), "La salida ya existe; no se sobrescribe")
    require(shutil.disk_usage(ROOT).free >= 2 * 1024**3, "Menos de 2 GiB libres")
    destination.mkdir()
    baseline = json.loads((SNAPSHOT / "manifest.json").read_text(encoding="utf-8"))
    for f in baseline["files"]:
        require(sha(SNAPSHOT / f["file"]) == f["sha256"], "Snapshot anual modificado: " + f["table"])
    # Evidencias selladas de la auditoria: no se leen los CSV originales completos.
    seals = {}
    for line in (AUDIT / "MANIFIESTO_EVIDENCIAS.sha256").read_text(encoding="utf-8").splitlines():
        if line.strip():
            digest, name = line.split(maxsplit=1)
            seals[name.lstrip("*").replace("\\", "/")] = digest
    for year in range(2022, 2026):
        p = AUDIT / "evidencias" / f"cohorte_disponible_{year}.csv"
        require(sha(p) == seals["evidencias/" + p.name], "Cohorte no coincide con sello")
    reference = REFERENCE
    require(sha(reference) == "70d6446170e7b4d6084b2823f09b7052c316e352aaa541956d74d1e7b8895da3", "Referencia anual alterada")
    db = duckdb.connect()
    db.execute("SET memory_limit='768MiB'")
    db.execute("SET threads=2")
    db.execute("SET max_temp_directory_size='1GiB'")
    db.execute("SET temp_directory=?", [str(ROOT / "trabajo/spill")])
    db.read_parquet(str(reference)).create_view("referencia")
    selected = []
    for year in range(2022, 2026):
        allowed = {r["hecho_key"]: r for r in rows(AUDIT / "evidencias" / f"cohorte_disponible_{year}.csv")}
        candidates = []
        for key, entity_key, legacy in db.execute("SELECT hecho_key,entidad_key,legacy_key FROM referencia WHERE anio_key=?", [str(year)]).fetchall():
            if str(key) not in allowed:
                continue
            parts = json.loads(legacy)
            canonical = parts.copy()
            canonical[18], canonical[19] = parts[19], parts[18]
            require(str(entity_key) == allowed[str(key)]["entidad_key"], "Entidad incoherente")
            candidates.append(dict(hecho_key=str(key), legacy=legacy, canonical=js(canonical), entity=js(parts[1:9]), year=year))
        chosen = select(candidates, CONFIG["series_per_year"], CONFIG["seed"])
        reverse = select(list(reversed(candidates)), CONFIG["series_per_year"], CONFIG["seed"])
        require([r["hecho_key"] for r in chosen] == [r["hecho_key"] for r in reverse], "Seleccion depende del orden")
        selected.extend(chosen)
        save_json(destination / f"seleccion_{year}.json", dict(population=len(candidates), entities=len(allowed and {r["entity"] for r in candidates}), selected=len(chosen), order_invariance=True))
        print(f"{year}: seleccionadas {len(chosen)} series", flush=True)
    del candidates, allowed, reverse
    parents = {}
    ids = {r["hecho_key"] for r in selected}
    annual_totals = defaultdict(lambda: defaultdict(Decimal))
    annual_file = next(f for f in baseline["files"] if f["table"].endswith("fact_ejecucion_presupuestaria_anual"))
    count = 0
    previous = 0
    for row in rows(SNAPSHOT / annual_file["file"]):
        require(int(row["hecho_key"]) > previous, "PK anual fuera de orden o repetida")
        previous = int(row["hecho_key"])
        count += 1
        for measure in MEASURES:
            annual_totals[row["anio_key"]][measure] += money(row[measure])
        if row["hecho_key"] in ids:
            parents[row["hecho_key"]] = row
    require(count == 150000 and len(parents) == 12500, "Conteos anuales incorrectos")
    for expected in baseline["expected_by_year"]:
        for measure in MEASURES:
            require(annual_totals[str(expected["anio"])][measure] == Decimal(expected[measure]), "Total anual alterado")
    period_rows = [dict(periodo_key=y*100+m, anio_key=y, mes=m, mes_nombre=name.capitalize()) for y in range(2022,2026) for m,name in enumerate(MONTHS,1)]
    output = [write_csv(destination / "dim_periodo_mensual.csv", list(period_rows[0]), period_rows)]
    details, detail_index, series = [], {}, []
    monthly_path = destination / "fact_devengado_mensual.csv"
    monthly_columns = ["hecho_mensual_key", "hecho_anual_key", "periodo_key", "anio_key", "entidad_key", "intervencion_key", "funcion_key", "meta_detalle_key", "financiamiento_key", "clasificador_gasto_key", "devengado"]
    controls, provenance = {}, []
    counter = 0
    legacy_columns = ["ANO_EJE"] + CORE + ["META_NOMBRE"]
    expressions = [expression(c) for c in legacy_columns]
    expressions[18], expressions[19] = expressions[19], expressions[18]
    legacy_expression = "CAST(to_json(list_value(" + ",".join(expressions) + ")) AS VARCHAR)"
    with monthly_path.open("x", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=monthly_columns)
        writer.writeheader()
        for year in range(2022,2026):
            result = json.loads((AUDIT / "evidencias" / f"resultado_{year}.json").read_text(encoding="utf-8"))
            source = Path(result["source"])
            require(source.stat().st_size == result["bytes"] and source.stat().st_mtime_ns == result["mtime_ns"], "Fuente original cambiada")
            parquet = AUDIT / "parquet" / f"fuente_{year}.parquet"
            current_hash = sha(parquet)
            require(current_hash == result["parquet_sha256"], "Parquet no coincide con el recibo de la auditoria actual")
            require(parquet.stat().st_size == result["parquet_bytes"], "Tamano Parquet modificado")
            require(db.execute("SELECT count(*) FROM read_parquet(?)", [str(parquet)]).fetchone()[0] == result["quality"]["filas"], "Parquet incompleto")
            db.execute("CREATE OR REPLACE TABLE elegidas(legacy VARCHAR PRIMARY KEY,hecho_key VARCHAR)")
            year_selected = [r for r in selected if r["year"] == year]
            db.executemany("INSERT INTO elegidas VALUES (?,?)", [(r["legacy"],r["hecho_key"]) for r in year_selected])
            db.read_parquet(str(parquet)).create_view("fuente", replace=True)
            # Una sola union con 3125 claves verificadas; no cadena de dimensiones.
            cursor = db.execute("SELECT e.hecho_key,s.* FROM fuente s JOIN elegidas e ON " + legacy_expression + "=e.legacy")
            columns = [d[0] for d in cursor.description]
            extracted = {}
            for values in cursor.fetchall():
                raw = dict(zip(columns, values))
                key = str(raw.pop("hecho_key"))
                require(key not in extracted, "Mas de una fila fuente para una serie; detener sin deduplicar")
                extracted[key] = {k: (v.strip() if isinstance(v,str) else v) for k,v in raw.items()}
            require(len(extracted) == 3125, "Faltan series fuente")
            month_totals = defaultdict(Decimal)
            for selection in year_selected:
                key = selection["hecho_key"]
                raw, parent = extracted[key], parents[key]
                for a,b in zip(ANNUAL_SOURCE, ANNUAL_TARGET):
                    require(money(raw[a]) == money(parent[b]), "Conciliacion fuente/anual fallida: " + key + "/" + a)
                values = [money(raw["MONTO_DEVENGADO_" + month]) for month in MONTHS]
                require(sum(values) == money(parent["devengado"]), "Suma mensual distinta del anual")
                detail_parts = [str(year)] + [raw[c] for c in ENTITY + INTERV + FUNC] + [raw[c] for c in ["SEC_FUNC","FINALIDAD","META","DEPARTAMENTO_META"]]
                detail_parts[10] = {"ACTIVIDAD":"3", "PROYECTO":"2"}.get(detail_parts[10],detail_parts[10])
                natural = js(detail_parts)
                if natural not in detail_index:
                    detail_index[natural] = len(details)+1
                    detail = dict(meta_detalle_key=len(details)+1, **{c:parent[c] for c in CONTEXT[:4]}, sec_func=raw["SEC_FUNC"],finalidad=raw["FINALIDAD"],meta=raw["META"],departamento_meta=raw["DEPARTAMENTO_META"],meta_nombre=raw["META_NOMBRE"] or "",departamento_meta_nombre=raw["DEPARTAMENTO_META_NOMBRE"] or "",clave_natural=natural)
                    details.append(detail)
                detail_id = detail_index[natural]
                grain = [({"ACTIVIDAD":"3","PROYECTO":"2"}.get(raw[c],raw[c]) if c=="TIPO_ACT_PROY" else raw[c]) for c in GRAIN]
                series.append(dict(hecho_anual_key=key, **{c:parent[c] for c in CONTEXT},meta_detalle_key=detail_id,fuente_grano_json=js(grain),fuente_sha256=result["sha256"],semilla=CONFIG["seed"],prioridad_hash=selection["priority"],entidad_natural=selection["entity"],poblacion_estrato=selection["population"],cuota_estrato=selection["quota"]))
                for month,value in enumerate(values,1):
                    counter += 1
                    record = dict(hecho_mensual_key=counter,hecho_anual_key=key,periodo_key=year*100+month,**{c:parent[c] for c in CONTEXT if c!="meta_key"},meta_detalle_key=detail_id,devengado=format(value,".2f"))
                    writer.writerow(record)
                    month_totals[str(year*100+month)] += value
            controls.update(month_totals)
            provenance.append(dict(year=year,source_sha256=result["sha256"],parquet_sha256=current_hash,parquet_historic_hash_verified=False,source_stat_unchanged=True,matched=3125))
            save_json(destination / f"extraccion_{year}.json",dict(year=year,monthly_rows=37500,totals=month_totals,source=provenance[-1]))
            print(f"{year}: 37500 meses conciliados", flush=True)
    output.extend([write_csv(destination / "dim_meta_detallada.csv",list(details[0]),details),write_csv(destination / "serie_seleccionada.csv",list(series[0]),series)])
    output.append(dict(file=monthly_path.name,columns=monthly_columns,rows=counter,sha256=sha(monthly_path)))
    manifest = dict(state="preparado_pendiente_verificacion",database=CONFIG["database"],seed=CONFIG["seed"],files=output,annual_files=baseline["files"],annual_totals=baseline["expected_by_year"],monthly_totals=controls,provenance=provenance,elapsed_seconds=round(time.monotonic()-start,2))
    save_json(destination / "manifest.json",manifest)
    from validar_local import validate
    report = validate(destination)
    save_json(destination / "VALIDADO.json",report)
    print(js(report),flush=True)
    db.close()

if __name__ == "__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--salida",type=Path,required=True)
    prepare(parser.parse_args().salida)
