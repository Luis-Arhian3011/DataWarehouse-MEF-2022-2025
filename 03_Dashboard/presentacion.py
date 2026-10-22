"""Presentación sin modificar los agregados Decimal ni las exportaciones."""
from html import escape
from textwrap import wrap
from decimal import Decimal
import pandas as pd
from datos import MEASURES, LABELS, LEVELS

def formato(value, decimals=2, ausente="No aplica"):
    if value is None or pd.isna(value):
        return ausente
    return f"{value:,.{decimals}f}".replace(",", "_").replace(".", ",").replace("_", ".")

def tabla_presentada(df):
    visible=df.copy(deep=True)
    if "nivel_gobierno" in visible:
        visible["nivel_gobierno"]=visible["nivel_gobierno"].map(LEVELS).fillna(visible["nivel_gobierno"])
    # Decimal se conserva en la tabla subyacente; Styler cambia solo su representación.
    cols=[m for m in [*MEASURES,"ejecucion_pct","variacion_pct"] if m in visible]
    counts=[m for m in ["hechos","entidades"] if m in visible]
    ordered=[m for m in ["anio","codigo","nombre","sec_ejec","nivel_gobierno","hechos","entidades","pia","pim","devengado","ejecucion_pct","variacion_pct"] if m in visible]
    ordered += [m for m in visible if m not in ordered]
    visible=visible[ordered].rename(columns=LABELS)
    formats={LABELS[m]:formato for m in cols}
    formats.update({LABELS[m]:lambda v:formato(v,0) for m in counts})
    return visible.style.format(formats,na_rep="No aplica")

def nombre_corto(name,width=25):
    lines=wrap(str(name or "Sin denominación"),width=width,break_long_words=True)
    return "<br>".join(escape(x) for x in lines[:2]) + ("…" if len(lines)>2 else "")

def lectura_serie(df,measures):
    metric="devengado" if "devengado" in measures else measures[0]
    valid=df[df[metric].notna()].sort_values("anio")
    if valid.empty:
        return "Lectura de la muestra: no aplica una comparación; no hay valores calculables para este indicador."
    row=valid.iloc[-1]
    if metric in ("ejecucion_pct","variacion_pct"):
        label="La ejecución" if metric=="ejecucion_pct" else "La variación interanual del devengado"
        return f"Lectura de la muestra: {label.lower()} en {int(row['anio'])} es {formato(row[metric])} %. El valor corresponde al subconjunto seleccionado; no describe el total nacional."
    text=f"Lectura de la muestra: en {int(row['anio'])}, el {LABELS[metric].split(' (')[0].lower()} observado es S/ {formato(row[metric])}, con {formato(row['hechos'],0)} hechos y {formato(row['entidades'],0)} entidades."
    if len(valid)>1:
        prev=valid.iloc[-2]
        if row["anio"]-prev["anio"]==1:
            delta=row[metric]-prev[metric]
            text+=f" La diferencia frente a {int(prev['anio'])} es S/ {formato(delta)}; la cobertura de partidas puede variar."
    return text

def lectura_grupos(df,metric):
    valid=df[df[metric].notna()]
    if valid.empty:
        return "Lectura de la muestra: no hay importes calculables en esta selección."
    row=valid.sort_values(metric,ascending=False,kind="stable").iloc[0]
    if metric=="ejecucion_pct":
        return f"Lectura de la muestra: {row['nombre']} figura entre las entidades con mayor porcentaje observado ({formato(row[metric])} %), con PIM de S/ {formato(row['pim'])} y {formato(row['hechos'],0)} hechos. La cobertura parcial impide interpretar este orden como desempeño integral."
    return f"Lectura de la muestra: {row['nombre']} figura entre los grupos con mayor {LABELS[metric].split(' (')[0].lower()} observado: S/ {formato(row[metric])}, en {formato(row['hechos'],0)} hechos. El orden describe únicamente los registros seleccionados."

def diagrama_estrella(relations):
    """SVG accesible generado exclusivamente con nombres y relaciones del catálogo."""
    if len(relations)!=7 or any(not r["validada"] for r in relations):
        raise ValueError("Se requieren siete relaciones validadas.")
    by_table={r["destino"]:r for r in relations}
    order=["dim_anio","dim_entidad","dim_intervencion","dim_funcion","dim_meta","dim_financiamiento","dim_clasificador_gasto"]
    if set(by_table)!=set(order):
        raise ValueError("El esquema no coincide con las siete dimensiones verificadas.")
    positions=[(350,15),(15,165),(15,330),(15,495),(685,165),(685,330),(685,495)]
    svg=['<div class="esquema-scroll" role="region" tabindex="0" aria-label="Esquema estrella: siete relaciones de la tabla de hechos"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 980 625" role="img" aria-labelledby="estrella-titulo"><title id="estrella-titulo">Esquema estrella MEF: claves foráneas reales verificadas en PostgreSQL</title><defs><marker id="punta-fk" markerWidth="8" markerHeight="8" refX="7" refY="3" orient="auto"><path d="M0,0 L0,6 L7,3 z" fill="#39D6C5"/></marker></defs>']
    for table,(x,y) in zip(order,positions):
        r=by_table[table]
        endx=490 if table=="dim_anio" else (x+280 if x<350 else x)
        endy=y+112 if table=="dim_anio" else y+56
        startx=490 if table=="dim_anio" else (360 if x<350 else 620)
        starty=225 if table=="dim_anio" else 335
        svg.append(f'<path d="M {startx},{starty} L {endx},{endy}" stroke="#39D6C5" stroke-width="1.8" fill="none" marker-end="url(#punta-fk)"/>')
    svg.append('<rect x="360" y="225" width="260" height="225" rx="14" fill="#172B3B" stroke="#E7C77C" stroke-width="2"/><g fill="#EDF5FD" font-family="Arial,sans-serif" text-anchor="middle"><text x="490" y="250" font-size="11" fill="#E7C77C">TABLA DE HECHOS · mef</text><text x="490" y="273" font-size="13">fact_ejecucion_</text><text x="490" y="291" font-size="13">presupuestaria_anual</text>')
    for i,r in enumerate(relations):
        svg.append(f'<text x="490" y="{315+i*17}" font-size="11">FK · {escape(r["origen"])}</text>')
    svg.append('</g>')
    for table,(x,y) in zip(order,positions):
        r=by_table[table]
        ref="PK" if r["referencia_pk"] else "Clave única"
        tooltip=f'mef.fact_ejecucion_presupuestaria_anual.{r["origen"]} → {r["esquema_destino"]}.{r["destino"]}.{r["referencia"]}; restricción {r["conname"]}'
        svg.append(f'<g><title>{escape(tooltip)}</title><rect x="{x}" y="{y}" width="280" height="112" rx="12" fill="#102238" stroke="#2D6570"/><text x="{x+140}" y="{y+27}" text-anchor="middle" fill="#91AFC5" font-family="Arial,sans-serif" font-size="11">DIMENSIÓN · {escape(r["esquema_destino"])}</text><text x="{x+140}" y="{y+53}" text-anchor="middle" fill="#39D6C5" font-family="Arial,sans-serif" font-size="14">{escape(table)}</text><text x="{x+140}" y="{y+80}" text-anchor="middle" fill="#E8EFF7" font-family="Arial,sans-serif" font-size="12">{ref} · {escape(r["referencia"])}</text></g>')
    svg.append('</svg></div>')
    return "".join(svg)
