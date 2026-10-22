"""Observatorio presupuestario MEF · aplicación local de solo lectura."""
from pathlib import Path
from html import escape
from dataclasses import replace
from decimal import Decimal
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from datos import (Filtros, ErrorDatos, LEVELS, LABELS, MEASURES, resumen, anual,
    agrupado, entidades_disponibles, entidades_comunes, calidad, exportar, relaciones_esquema)
from presentacion import formato, tabla_presentada, nombre_corto, lectura_serie, lectura_grupos, diagrama_estrella

st.set_page_config(page_title="MEF · Observatorio presupuestario", page_icon="◈", layout="wide")
st.markdown("<style>" + Path(__file__).with_name("estilos.css").read_text(encoding="utf-8") + "</style>", unsafe_allow_html=True)
COLORS = ["#39D6C5","#E7C77C","#6A9FF5","#B59DE9"]
SECTIONS = ["Resumen ejecutivo","Análisis temporal","Niveles de gobierno","Análisis por entidad","Distribución del gasto","Metodología y calidad"]

def numero(value, decimals=0):
    if value is None or pd.isna(value):
        return "No calculable"
    return f"{value:,.{decimals}f}".replace(",", "_").replace(".", ",").replace("_", ".")

def dinero(value):
    value = Decimal(value)
    if abs(value) >= 1_000_000_000:
        return "S/ " + numero(value / 1_000_000_000, 2) + " mil M"
    return "S/ " + numero(value / 1_000_000, 2) + " M"

def tarjetas(r):
    vals = [
        ("PIA", dinero(r["pia"]), "Presupuesto inicial de apertura"),
        ("PIM", dinero(r["pim"]), "Presupuesto institucional modificado"),
        ("Devengado", dinero(r["devengado"]), "Obligaciones de pago reconocidas"),
        ("Ejecución", numero(r["ejecucion_pct"],2) + (" %" if r["ejecucion_pct"] is not None else ""), "Devengado / PIM agregado"),
        ("Entidades", numero(r["entidades"]), "Claves de entidad distintas"),
    ]
    cards = "".join(f'<div class="kpi"><div class="label">{escape(l)}</div><div class="value">{escape(v)}</div><div class="note">{escape(n)}</div></div>' for l,v,n in vals)
    st.markdown('<div class="kpis">' + cards + '</div>', unsafe_allow_html=True)

def grafico(fig, title, height=360):
    fig.update_layout(title=dict(text=title,font=dict(size=16,family="Arial, sans-serif")), height=height,
        paper_bgcolor="#0E1E30",plot_bgcolor="#0E1E30",font=dict(color="#B9CBDC",family="Arial, sans-serif"),
        margin=dict(l=28,r=25,t=66,b=45),colorway=COLORS,
        legend=dict(orientation="h",y=1.14,x=0),hoverlabel=dict(bgcolor="#183247"),
        separators=",.", hovermode="closest")
    fig.update_xaxes(gridcolor="#20364A",zerolinecolor="#344A5F")
    fig.update_yaxes(gridcolor="#20364A",zerolinecolor="#344A5F",automargin=True)
    st.plotly_chart(fig,width="stretch",theme=None,config={"displayModeBar":False,"scrollZoom":False,"responsive":True})

def tabla(df, key):
    all_measures=st.toggle("Mostrar las siete medidas monetarias",value=False,key=f"detalle_{key}")
    # Esta selección es exclusivamente visual: el CSV siempre exporta el agregado completo.
    display=df if all_measures else df.drop(columns=[m for m in MEASURES if m not in ("pia","pim","devengado")],errors="ignore")
    styled=tabla_presentada(display)
    columns={LABELS[m]:st.column_config.Column(width="medium") for m in MEASURES if m in display}
    if "nombre" in display:
        columns[LABELS["nombre"]]=st.column_config.TextColumn(width="large",help="Denominación completa observada en la dimensión.")
    st.dataframe(styled,hide_index=True,width="stretch",height=min(480,80+len(df)*35),
        column_config=columns,key=f"tabla_{key}",placeholder="No aplica")
    st.caption("Importes en soles: 1.234.567,89. Ordena por encabezado y desplaza la tabla horizontalmente para consultar más columnas. «No aplica» indica ausencia de una comparación válida.")
    st.download_button("Descargar resultados agregados · CSV",exportar(df),
        file_name=f"mef_muestra_{key}.csv",mime="text/csv",key=f"csv_{key}")
    st.caption("CSV con importes originales y céntimos completos; incluye todas las medidas, sin el formato visual de miles.")

def serie(df, measures, title, porcentaje=False):
    fig = go.Figure()
    for i,m in enumerate(measures):
        values = [None if v is None or pd.isna(v) else float(v)/(1 if porcentaje else 1_000_000) for v in df[m]]
        fig.add_trace(go.Scatter(x=df["anio"].astype(str),y=values,name=LABELS[m].split(" (")[0],
            mode="lines+markers",line=dict(width=3,color=COLORS[i]),marker=dict(size=8),
            hovertemplate="%{x}<br>%{y:,.2f}" + (" %" if porcentaje else " M de S/") + "<extra>%{fullData.name}</extra>"))
    fig.update_xaxes(title="Año",type="category")
    fig.update_yaxes(title=LABELS[measures[0]] if porcentaje else "Millones de soles · muestra")
    grafico(fig,title)
    st.caption(lectura_serie(df,measures))

def barras(df,title,measure="devengado",limit=12):
    if df.empty:
        st.info("No hay datos para esta selección.")
        return
    view=df.sort_values(measure,ascending=False,kind="stable").head(limit).iloc[::-1].copy()
    # Posiciones únicas también cuando un código tiene distintas denominaciones observadas.
    axes=[str(i) for i in range(len(view))]
    custom=[[escape(str(row["nombre"])),str(row["codigo"]),formato(row[measure]),
        formato(row["pim"]),formato(row["hechos"],0)] for _,row in view.iterrows()]
    fig=go.Figure(go.Bar(x=[float(x)/1_000_000 for x in view[measure]],y=axes,orientation="h",
        marker_color=COLORS[0],customdata=custom,
        hovertemplate="%{customdata[0]}<br>Código: %{customdata[1]}<br>Importe: S/ %{customdata[2]}<br>PIM: S/ %{customdata[3]}<br>Hechos: %{customdata[4]}<extra></extra>"))
    fig.update_yaxes(tickmode="array",tickvals=axes,ticktext=[nombre_corto(n) for n in view["nombre"]],type="category",tickfont=dict(size=11))
    fig.update_xaxes(title="Millones de soles · " + LABELS[measure].split(" (")[0])
    grafico(fig,title,max(360,min(1250,len(view)*47+110)))
    st.caption(lectura_grupos(df,measure))

def ejecutar():
    with st.sidebar:
        st.markdown('<div class="brand">MEF<span> /</span></div><div class="brand-sub">OBSERVATORIO PRESUPUESTARIO</div>',unsafe_allow_html=True)
        section = st.radio("Explorar",SECTIONS,label_visibility="collapsed",key="navegacion")
        st.divider()
        st.markdown("**Delimitar la muestra**")
        years = tuple(st.multiselect("Años",[2022,2023,2024,2025],default=[2022,2023,2024,2025],key="anios"))
        levels = tuple(st.multiselect("Nivel de gobierno",list(LEVELS),default=list(LEVELS),format_func=LEVELS.get,key="niveles"))
        options = entidades_disponibles(years,levels)
        names = {r["entidad_key"]:f'{r["ejecutora_nombre"] or "Sin denominación"} · {r["sec_ejec"] or "sin SEC_EJEC"} · {r["entidad_key"]}' for r in options}
        if "entidades" in st.session_state:
            st.session_state["entidades"] = [k for k in st.session_state["entidades"] if k in names]
        selected = st.multiselect("Entidades",list(names),format_func=names.get,placeholder="Todas las entidades disponibles",key="entidades")
        st.caption("Escribe para buscar. Sin entidades seleccionadas se incluyen todas las disponibles.")
        st.caption("Los filtros se aplican a las seis secciones; el control de calidad general se identifica por separado.")
        if st.button("Actualizar consultas",width="stretch"):
            st.cache_data.clear()
            st.rerun()
        st.divider()
        st.caption("Solo lectura · PostgreSQL\n\nSoles corrientes · sin expansión estadística")
    filtros = Filtros(years,levels,tuple(selected) if selected else None)
    r = resumen(filtros)
    st.markdown('<div class="hero"><div class="eyebrow">INTELIGENCIA DE NEGOCIOS / PERÚ</div><h1>Ejecución presupuestaria</h1><p>Una mirada analítica al presupuesto público, desde una muestra auditada del Data Warehouse del MEF.</p><span class="pill">2022–2025</span><span class="pill">150.000 hechos en la base</span><span class="pill gold">Muestra · no total nacional</span></div>',unsafe_allow_html=True)
    st.caption(f"VISTA ACTIVA · {section.upper()}   /   {numero(r['hechos'])} hechos · {numero(r['entidades'])} entidades · años: {', '.join(map(str, sorted(years))) or 'ninguno'}")
    st.info("Las sumas describen exclusivamente la muestra filtrada; no son cifras oficiales nacionales. Las diferencias entre años también reflejan cambios en su cobertura.")
    if 2025 in years:
        st.warning("2025: instantánea de la fuente. La fecha de corte de ejecución y el cierre anual no están certificados.")
    st.subheader(section)
    if not r["hechos"]:
        st.info("Los filtros no devuelven datos. Selecciona al menos un año y un nivel de gobierno, o amplía las entidades.")
        return
    if section == SECTIONS[0]:
        tarjetas(r)
        st.caption("M = millones; mil M = miles de millones. PIA, PIM y etapas de ejecución son medidas distintas: no se suman entre sí.")
        data = anual(filtros)
        left,right = st.columns([1.6,1])
        with left:
            serie(data,["pia","pim","devengado"],"Presupuesto y ejecución de la muestra")
        with right:
            serie(data,["ejecucion_pct"],"Ejecución por ejercicio",True)
        with st.expander("Ver importes y cobertura por año"):
            tabla(data,"resumen_anual")
    elif section == SECTIONS[1]:
        st.caption("Las variaciones son descriptivas de la muestra y no miden el crecimiento nacional ni el desempeño integral de las entidades.")
        common = st.checkbox("Comparar solo entidades presentes en todos los años seleccionados",value=True,key="cohorte")
        temporal = filtros
        if common:
            ids = entidades_comunes(filtros)
            temporal = replace(filtros,entidades=ids)
            st.caption(f"Cohorte común: {numero(len(ids))} claves de entidad. La composición de partidas y la cobertura presupuestaria aún pueden variar.")
        data = anual(temporal)
        if data.empty:
            st.info("No hay entidades comunes para los años y filtros elegidos. Amplía los filtros o desactiva la cohorte común.")
            return
        serie(data,["pia","pim","devengado"],"Evolución anual · importes de la muestra")
        left,right = st.columns(2)
        with left:
            serie(data,["ejecucion_pct"],"Ejecución ponderada por PIM",True)
        data = data.copy()
        changes = [None]
        for i in range(1,len(data)):
            prev,cur = data.iloc[i-1],data.iloc[i]
            changes.append(100*(cur["devengado"]-prev["devengado"])/prev["devengado"]
                if cur["anio"]-prev["anio"]==1 and prev["devengado"]>0 else None)
        data["variacion_pct"] = changes
        with right:
            serie(data,["variacion_pct"],"Variación interanual del devengado",True)
        st.caption("La variación se calcula únicamente para años consecutivos y un devengado anterior positivo. El primer año no tiene base de comparación.")
        tabla(data,"temporal")
    elif section == SECTIONS[2]:
        data = agrupado("nivel",filtros)
        data["nombre"] = data["codigo"].map(LEVELS).fillna(data["nombre"])
        left,right=st.columns(2)
        with left:
            barras(data,"PIM por nivel de gobierno","pim")
        with right:
            fig=go.Figure()
            for m,i in [("pim",1),("devengado",0)]:
                fig.add_trace(go.Bar(x=data["nombre"],y=[float(x)/1_000_000 for x in data[m]],name=LABELS[m].split(" (")[0],marker_color=COLORS[i]))
            fig.update_layout(barmode="group")
            fig.update_yaxes(title="Millones de soles · muestra")
            grafico(fig,"Presupuesto frente a devengado")
            st.caption(lectura_grupos(data,"devengado"))
        st.caption("Los gobiernos locales se incluyen aunque sector o pliego estén vacíos. La clasificación utiliza nivel_gobierno de la dimensión entidad.")
        tabla(data,"niveles")
    elif section == SECTIONS[3]:
        data = agrupado("entidad",filtros)
        term=st.text_input("Buscar una entidad por nombre o SEC_EJEC",placeholder="Ejemplo: municipalidad",key="busqueda").strip()
        if term:
            data=data[data["nombre"].fillna("").str.contains(term,case=False,regex=False) | data["sec_ejec"].fillna("").str.contains(term,case=False,regex=False)]
        if data.empty:
            st.info("No hay entidades que coincidan con la búsqueda.")
            return
        left,right=st.columns([2,1])
        with right:
            metric=st.selectbox("Ordenar ranking por",["pim","devengado","ejecucion_pct"],format_func=lambda k:LABELS[k],key="metrica")
            limit=st.slider("Entidades en el gráfico",5,25,10)
            st.caption("Las entidades corresponden a claves naturales compuestas; SEC_EJEC o el nombre por sí solos no definen su identidad. El ranking usa el subconjunto observado.")
        with left:
            if metric=="ejecucion_pct":
                v=data[data[metric].notna()].sort_values(metric,ascending=False).head(limit).iloc[::-1]
                fig=go.Figure(go.Bar(x=[float(x) for x in v[metric]],y=[str(x) for x in v["codigo"]],orientation="h",marker_color=COLORS[1],customdata=[[escape(str(row["nombre"])),formato(row["pim"]),formato(row["hechos"],0)] for _,row in v.iterrows()],hovertemplate="%{customdata[0]}<br>Ejecución: %{x:.2f} %<br>PIM: S/ %{customdata[1]}<br>Hechos: %{customdata[2]}<extra></extra>"))
                fig.update_yaxes(type="category",tickmode="array",tickvals=[str(x) for x in v["codigo"]],ticktext=[nombre_corto(x) for x in v["nombre"]],tickfont=dict(size=11))
                fig.update_xaxes(title="Ejecución de la muestra (%)")
                grafico(fig,"Ranking por ejecución · PIM positivo",max(360,len(v)*47+110))
                st.caption(lectura_grupos(data,metric))
            else:
                barras(data,"Entidades con mayor " + LABELS[metric].split(" (")[0],metric,limit)
        st.caption("Un porcentaje elevado, incluso mayor de 100 %, puede reflejar la cobertura parcial de partidas; no equivale a evaluar toda la entidad. Para comparar entidades específicas, utiliza el filtro lateral.")
        tabla(data.sort_values(metric,ascending=False,na_position="last"),"entidades")
    elif section == SECTIONS[4]:
        choice=st.radio("Perspectiva",["Funciones presupuestarias","Fuentes de financiamiento","Genéricas de gasto","Categorías de gasto"],horizontal=True,key="perspectiva")
        group=dict(zip(["Funciones presupuestarias","Fuentes de financiamiento","Genéricas de gasto","Categorías de gasto"],["funcion","fuente","generica","categoria"]))[choice]
        data=agrupado(group,filtros)
        measure=st.selectbox("Medida presupuestaria",["pia","pim","devengado"],index=2,format_func=lambda k:LABELS[k].split(" (")[0],key="medida_gasto")
        barras(data,choice + " · " + LABELS[measure].split(" (")[0],measure=measure,limit=15)
        st.caption("El gráfico presenta hasta 15 grupos; la tabla y la exportación incluyen todos los grupos del filtro. No se representan importes negativos mediante sectores circulares.")
        tabla(data,"distribucion_"+group)
    else:
        st.markdown("**Resumen metodológico.** Esquema estrella Ralph Kimball: siete dimensiones y un hecho presupuestario anual. Muestra reproducible de 150.000 hechos, 37.500 por año de 2022 a 2025. No se extrapola al universo nacional.")
        st.markdown("**Esquema estrella verificado en PostgreSQL**")
        relations=relaciones_esquema()
        st.markdown(diagrama_estrella(relations),unsafe_allow_html=True)
        st.caption("Las flechas conectan cada FK con la clave referenciada de su dimensión (muchos a uno). Pasa el cursor sobre los nodos para ver la restricción completa. En pantallas pequeñas, desplaza el diagrama horizontalmente.")
        with st.expander("Fuente, selección y granularidad"):
            st.markdown("**Fuente y alcance.** Archivo MEF `comparativo_gastos_2022_2026.csv`, utilizando exclusivamente 2022–2025. Los datos se leen del Data Warehouse; el dashboard no procesa el CSV ni ejecuta el ETL.")
            st.markdown("**Selección reproducible.** 150.000 hechos: 37.500 por año. Selección determinista por hash y cuotas estratificadas por nivel de gobierno y entidad, con semilla `MEF_KIMBALL_2022_2025_V1`. No se extrapolan las sumas al universo ni se aplican pesos de expansión.")
            st.markdown("**Kimball y granularidad.** Un hecho representa una combinación presupuestaria anual validada: entidad, intervención, función, meta, financiamiento y clasificador, además del año. La identidad de meta conserva su nombre y contexto para evitar fusiones incorrectas.")
        with st.expander("Dimensiones y relaciones verificadas"):
            dimensions=pd.DataFrame([
                ["Año","dim_anio","Ejercicio fiscal"],
                ["Entidad","dim_entidad","Nivel de gobierno, ejecutora y ubicación"],
                ["Intervención","dim_intervencion","Programa, producto/proyecto y actividad"],
                ["Función","dim_funcion","Función, división y grupo funcional"],
                ["Meta","dim_meta","Meta y su contexto anual"],
                ["Financiamiento","dim_financiamiento","Fuente, rubro y tipo de recurso"],
                ["Clasificador de gasto","dim_clasificador_gasto","Categoría y clasificación económica"]],
                columns=["Dimensión","Tabla en mef","Contenido"])
            st.dataframe(dimensions,hide_index=True,width="stretch")
            st.dataframe(pd.DataFrame(relations).rename(columns={"origen":"FK en hechos","destino":"Dimensión","referencia":"Clave referenciada","esquema_destino":"Esquema","conname":"Restricción","validada":"Validada","referencia_pk":"Referencia a PK"}),hide_index=True,width="stretch")
        with st.expander("Reglas monetarias, gobiernos locales y ambigüedades"):
            st.markdown("**Reglas monetarias.** Soles corrientes; NUMERIC(20,2) y Decimal preservan los céntimos. Los importes negativos se conservan. PIA, PIM, certificado, comprometidos, devengado y girado son medidas diferentes, no componentes para sumar entre sí. Ejecución = 100 × SUM(devengado) / SUM(PIM), solo con PIM agregado positivo; nunca se promedian porcentajes por fila ni se limita el resultado a 100 %. Los nulos no se convierten silenciosamente en observaciones válidas: la carga validada contiene las siete medidas no nulas.")
            st.markdown("**Gobiernos locales y nombres.** Sector y pliego vacíos no excluyen a los gobiernos locales. Los nombres son denominaciones observadas, con alias conservados; no se inventaron vigencias históricas ni se usa un nombre como clave única.")
            st.markdown("**Ambigüedades.** Los 11.658 granos ambiguos (23.316 filas de 2022–2025) quedaron fuera de la población seleccionada y se conservaron en las evidencias del proceso; no fueron borrados ni sumados automáticamente.")
        with st.expander("Alcance y limitaciones de 2025"):
            st.markdown("**2025.** El PIA del archivo completo fue contrastado durante la validación, pero las sumas del dashboard corresponden a la muestra. Las medidas de 2025 coinciden con las columnas de 2026 en la fuente; se desconoce la causa. Esto no certifica el corte o cierre de ejecución de 2025. No se incluye 2026.")
        q=calidad()
        st.markdown("**Control general de la base · independiente de los filtros**")
        st.success(f"{numero(q['hechos'])} hechos · {numero(q['claves_origen'])} claves de origen únicas · {numero(q['granos'])} granos únicos · {q['filas_negativas']} hechos con algún importe negativo.")
        st.markdown("**Cobertura del filtro actual**")
        tabla(anual(filtros),"cobertura")
        st.caption("Las claves foráneas, la conciliación de las 28 sumas año/medida y la conservación de la base anterior se documentan en 05_Evidencias/implementacion. La auditoría del dashboard se guarda en 05_Evidencias/dashboard.")
    st.markdown('<div class="footer">MEF / Observatorio presupuestario · Proyecto académico · Modelo dimensional Ralph Kimball · Muestra sin extrapolación nacional</div>',unsafe_allow_html=True)

try:
    ejecutar()
except ErrorDatos as exc:
    st.error(str(exc))
    st.info("Inicia postgres-db y revisa las variables PGHOST, PGPORT, PGDATABASE, PGUSER y PGPASSWORD, o .streamlit/secrets.toml.")
except Exception:
    st.error("No se pudo mostrar esta vista. Revisa la configuración y ejecuta verificar_dashboard.py para diagnosticar el entorno.")
