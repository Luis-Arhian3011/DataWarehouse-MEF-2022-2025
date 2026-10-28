"""Observatorio MEF V2: seis vistas y consultas agregadas de solo lectura."""
from pathlib import Path
from dataclasses import replace
from decimal import Decimal
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import datos as d
from filtros_ui import reajustar_seleccion,filtro_efectivo
from presentacion import YEAR_COLORS,COLORS,MONTHS,formato,dinero,tarjetas,tema,serie_anual,evolucion,ranking,variaciones,tabla_estilo

ROOT=Path(__file__).resolve().parent
SECTIONS=["Resumen ejecutivo","Presupuesto anual","Evolución mensual","Comparación de ejercicios","Análisis por dimensiones","Metodología y calidad"]
st.set_page_config(page_title="MEF V2 · Observatorio presupuestario",page_icon="◈",layout="wide")
st.markdown("<style>"+(ROOT/"estilos.css").read_text(encoding="utf-8")+"</style>",unsafe_allow_html=True)

def plot(figure):
    st.plotly_chart(figure,width="stretch",theme=None,config={"displayModeBar":False,"responsive":True,"locale":"es"})

def tabla(frame,key):
    if frame.empty:
        st.info("No hay resultados para estos filtros.");return
    st.dataframe(tabla_estilo(frame),hide_index=True,width="stretch",height=min(480,85+len(frame)*35),
        column_config={"Denominación":st.column_config.TextColumn(width="large")},
        placeholder="No aplica",key="tabla_"+key)
    st.caption("Soles con miles y dos decimales. Ordena por encabezado y desplaza horizontalmente para consultar más columnas.")
    st.download_button("Descargar agregados · CSV",d.exportar(frame),file_name="mef_v2_"+key+".csv",mime="text/csv",key="csv_"+key)
    st.caption("CSV: punto y coma, coma decimal y UTF-8 para Excel. Conserva los valores Decimal originales.")

def anual_visible(frame,variation=False):
    columns=["anio","hechos","entidades","pia","pim","devengado","girado","ejecucion_pct"]
    if variation:columns+=["variacion_pct"]
    return frame[[c for c in columns if c in frame]]

def lectura_anual(frame):
    if not frame.empty:
        last=frame.sort_values("anio").iloc[-1]
        st.caption(f"Lectura de la muestra: en {int(last['anio'])}, el devengado es S/ {formato(last['devengado'])}, en {formato(last['hechos'],0)} hechos de {formato(last['entidades'],0)} entidades. La cobertura de partidas puede variar entre años.")

def advertencia_pim(summary):
    if summary["pim_cero"]:
        st.warning(f"Hay {formato(summary['pim_cero'],0)} hechos con PIM cero y devengado positivo: S/ {formato(summary['dev_pim_cero'])}. Es el estado observado en la fuente; no se corrige ni se interpreta como desempeño institucional.")
    value=summary["ejecucion_pct"]
    if value is None:st.info("Ejecución no calculable: el PIM agregado debe ser positivo.")
    elif value>100:st.caption("Ejecución superior al 100 %: se conserva el cociente observado, sin recortarlo ni atribuirle una causa no comprobada.")

def ejecucion(frame):
    fig=go.Figure(go.Bar(x=frame["anio"].astype(str),y=[None if v is None else float(v) for v in frame["ejecucion_pct"]],
        marker_color=[YEAR_COLORS[int(year)] for year in frame["anio"]],customdata=[[formato(v)] for v in frame["pim"]],
        hovertemplate="%{x}<br>Ejecución: %{y:.2f} %<br>PIM: S/ %{customdata[0]}<extra></extra>"))
    fig.add_hline(y=100,line_dash="dot",line_color="#8CA3B9")
    fig.update_yaxes(title="100 × devengado / PIM agregado")
    fig.update_xaxes(type="category",title="Ejercicio")
    return tema(fig,"Ejecución observada · PIM agregado positivo")

def liberar_filtro(key):
    st.session_state[key]=[]
    st.session_state["_bloqueado_"+key]=False

def selector_compatible(label,options,key,placeholder,reset_label):
    lock_key="_bloqueado_"+key
    valid,locked,removed=reajustar_seleccion(tuple(st.session_state.get(key,())),options,st.session_state.get(lock_key,False))
    if removed:
        st.session_state[key]=list(valid)
        st.warning(f"Se retiraron {len(removed)} selecciones de {label.lower()} que ya no son compatibles con los ejercicios y gobiernos elegidos.")
    st.session_state[lock_key]=locked
    selected=st.multiselect(label,list(options),format_func=options.get,placeholder=placeholder,key=key)
    if selected:
        st.session_state[lock_key]=False
    if st.session_state[lock_key]:
        st.warning(f"{label}: selección vacía tras el reajuste. No se incluyen todas las opciones. Elige una compatible o confirma explícitamente el alcance.")
        st.button(reset_label,key="restablecer_"+key,on_click=liberar_filtro,args=(key,))
    return filtro_efectivo(selected,st.session_state[lock_key])

def filtros():
    with st.sidebar:
        st.markdown('<div class="brand">MEF<span> / V2</span></div><div class="brand-sub">OBSERVATORIO PRESUPUESTARIO</div>',unsafe_allow_html=True)
        section=st.radio("Navegación",SECTIONS,key="seccion",label_visibility="collapsed")
        st.divider()
        scope=st.selectbox("Cobertura anual",list(d.SCOPES),format_func=d.SCOPES.get,key="scope")
        st.caption("El mensual siempre representa las 12.500 series vinculadas, no todos los hechos anuales.")
        years=tuple(st.multiselect("Ejercicios",[2022,2023,2024,2025],default=[2022,2023,2024,2025],key="anios"))
        levels=tuple(st.multiselect("Nivel de gobierno",list(d.LEVELS),default=list(d.LEVELS),format_func=d.LEVELS.get,key="niveles"))
        cats=d.catalogos(years,levels)
        names={r["entidad_key"]:f'{r["ejecutora_nombre"] or "Sin denominación"} · {r["sec_ejec"]} · {d.LEVELS[r["nivel_gobierno"]]} · #{r["entidad_key"]}' for r in cats["entidades"]}
        entity=selector_compatible("Entidades",names,"entidades","Todas · escribe para buscar","Usar todas las entidades")
        fn={r["codigo"]:r["codigo"]+" · "+r["nombre"] for r in cats["funciones"]}
        sn={r["codigo"]:r["codigo"]+" · "+r["nombre"] for r in cats["fuentes"]}
        functions=selector_compatible("Funciones",fn,"funciones","Todas las funciones","Usar todas las funciones")
        sources=selector_compatible("Fuentes de financiamiento",sn,"fuentes","Todas las fuentes","Usar todas las fuentes")
        st.caption("Sin selección inicial se incluyen todas las opciones. Una selección retirada queda restringida hasta elegir otra o pulsar «Usar todas…». Vaciar años o gobiernos devuelve cero datos.")
        if st.button("Actualizar consultas",width="stretch"):
            st.cache_data.clear();st.rerun()
        st.divider()
        st.caption("Solo lectura · PostgreSQL V2\n\nSoles corrientes · sin extrapolación nacional")
    return section,scope,d.Filtros(years,levels,entity,functions,sources)

def resumen(filters,scope,summary):
    st.subheader("El presupuesto de la muestra, en perspectiva")
    st.markdown(tarjetas([(label,dinero(summary[key]),description) for label,key,description in [
        ("PIA","pia","Presupuesto inicial de apertura"),("PIM","pim","Presupuesto institucional modificado"),
        ("Devengado","devengado","Obligaciones reconocidas"),("Girado","girado","Etapa de giro registrada")]]),unsafe_allow_html=True)
    a,b,c=st.columns(3)
    a.metric("Ejecución",formato(summary["ejecucion_pct"])+" %" if summary["ejecucion_pct"] is not None else "No calculable")
    b.metric("Hechos anuales del filtro",formato(summary["hechos"],0));c.metric("Entidades del filtro",formato(summary["entidades"],0))
    advertencia_pim(summary)
    years=d.anual(filters,scope);monthly=d.mensual(filters)
    left,right=st.columns(2)
    with left:plot(serie_anual(years,["pia","pim","devengado"],"Trayectoria anual · "+d.SCOPES[scope]))
    with right:
        if monthly.empty:st.info("El filtro no tiene series en la cohorte mensual.")
        else:plot(evolucion(monthly,"devengado"))
    lectura_anual(years)
    st.caption("Cada gráfico señala su universo. Con muestra anual completa, sus totales no son directamente comparables con la cohorte mensual.")
    with st.expander("Consultar los agregados anuales"):tabla(anual_visible(years),"resumen")

def presupuesto(filters,scope,summary):
    st.subheader("Presupuesto anual y calidad del denominador")
    frame=d.anual(filters,scope)
    plot(serie_anual(frame,list(d.MEASURES),"PIA, PIM, devengado y girado · muestra"))
    lectura_anual(frame)
    left,right=st.columns([1.5,1])
    with left:plot(ejecucion(frame))
    with right:
        st.markdown("#### Leer el porcentaje con contexto")
        st.markdown("**100 × SUM(devengado) / SUM(PIM)** cuando el PIM agregado es positivo. No se promedian porcentajes individuales.")
        st.metric("Hechos con PIM no positivo",formato(summary["pim_no_positivo"],0))
        st.metric("Devengado con PIM cero",dinero(summary["dev_pim_cero"]))
        st.caption("Las etapas presupuestarias no se suman entre sí. Los importes negativos permanecen en las sumas.")
    advertencia_pim(summary)
    tabla(anual_visible(frame),"anual")

def meses(filters):
    st.subheader("Del ejercicio anual a los doce meses")
    st.caption("Universo exclusivo: cohorte mensual vinculada a 12.500 observaciones anuales. La cobertura anual lateral no amplía este universo.")
    frame=d.mensual(filters)
    if frame.empty:st.info("No hay series mensuales para los filtros elegidos.");return
    left,right=st.columns([2,1])
    with left:interval=st.slider("Meses visibles",1,12,(1,12),key="meses_visibles")
    with right:measure=st.radio("Vista mensual",["devengado","acumulado"],format_func=lambda x:"Del mes" if x=="devengado" else "Acumulado desde enero",horizontal=True,key="vista_mensual")
    view=frame[frame["mes"].between(*interval)]
    st.markdown(tarjetas([("Devengado del período",dinero(sum(view["devengado"],Decimal(0))),"Suma de meses visibles, no de acumulados"),
        ("Hechos mensuales",formato(view["hechos"].sum(),0),"Incluye importes cero"),
        ("Registros mensuales negativos",formato(view["negativos"].sum(),0),"Conservados en la fuente"),
        ("Ejercicios",str(view["anio"].nunique()),"Cobertura del filtro")]),unsafe_allow_html=True)
    plot(evolucion(view,measure))
    st.caption("El acumulado se calcula en SQL desde enero, antes de limitar los meses visibles. El rango de meses no modifica los indicadores anuales.")
    matrix=view.pivot(index="anio",columns="mes",values="devengado")
    figure=go.Figure(go.Heatmap(z=[[float(v)/1e6 for v in row] for row in matrix.to_numpy()],x=[MONTHS[int(m)-1][:3] for m in matrix.columns],y=[str(y) for y in matrix.index],
        colorscale=[[0,"#E7BF72"],[0.5,"#1B354C"],[1,"#35D6C6"]],zmid=0,colorbar=dict(title="M de S/"),
        hovertemplate="Año %{y} · %{x}<br>%{z:.2f} M de S/<extra></extra>"))
    plot(tema(figure,"Mapa mensual · devengado del mes",310))
    top=view.loc[view["devengado"].idxmax()]
    st.caption(f"Lectura de la muestra: el mayor agregado mensual visible corresponde a {top['mes_nombre'].lower()} de {int(top['anio'])}: S/ {formato(top['devengado'])}. No describe la estacionalidad nacional.")
    tabla(view,"mensual")

def comparar(filters,scope):
    st.subheader("Comparar ejercicios con cobertura explícita")
    common=st.toggle("Limitar a entidades presentes en todos los años elegidos",value=True,key="entidades_comunes")
    active=filters
    if common:
        keys=d.entidades_comunes(filters,scope);active=replace(filters,entidades=keys)
        st.caption(f"Cohorte común: {formato(len(keys),0)} entidades. Compartir entidades no garantiza idénticas partidas ni cobertura monetaria.")
    frame=d.anual(active,scope)
    if frame.empty:st.info("No hay entidades comunes. Amplía los filtros o desactiva la opción.");return
    frame=variaciones(frame)
    left,right=st.columns(2)
    with left:plot(serie_anual(frame,["devengado","girado"],"Devengado y girado por ejercicio"))
    with right:plot(ejecucion(frame))
    lectura_anual(frame)
    st.caption("La variación requiere años consecutivos y devengado anterior positivo. El primer año y los saltos de ejercicio muestran «No aplica».")
    tabla(anual_visible(frame,True),"comparacion")
    st.markdown("#### Conciliación anual ↔ mensual · misma cohorte")
    st.caption("Se agregan los hechos por separado y después se unen por año. El control usa doce meses completos y solo las series vinculadas.")
    reconciliation=d.conciliacion(active)
    if reconciliation.empty:st.info("El filtro no contiene series vinculadas al mensual.")
    else:
        passed=all(row.diferencia==0 and row.meses==12*row.series for row in reconciliation.itertuples())
        if passed:st.success("Conciliación exacta: sin diferencias de importe ni multiplicación de filas.")
        else:st.error("La conciliación no coincide. Revisar los datos antes de interpretarlos.")
        tabla(reconciliation,"conciliacion")

def dimensiones(filters,scope):
    st.subheader("Explorar la composición del presupuesto")
    group=st.selectbox("Dimensión",["entidad","funcion","fuente","nivel"],format_func={"entidad":"Entidad","funcion":"Función presupuestaria","fuente":"Fuente de financiamiento","nivel":"Nivel de gobierno"}.get,key="dimension")
    frame=d.agrupado(group,filters,scope)
    if frame.empty:st.info("No hay datos para esta dimensión.");return
    left,right=st.columns([2,1])
    with right:
        measure=st.selectbox("Indicador del ranking",["devengado","pim","pia","girado","ejecucion_pct"],format_func=d.LABELS.get,key="indicador")
        limit=st.slider("Grupos visibles",5,20,10,key="limite")
        search=st.text_input("Buscar denominación o código",key="buscar_dimension").strip()
        st.caption("La búsqueda solo restringe el gráfico y la tabla de esta sección.")
    if search:frame=frame[frame["nombre"].fillna("").str.contains(search,case=False,regex=False)|frame["codigo"].astype(str).str.contains(search,case=False,regex=False)]
    if frame.empty:st.info("No hay coincidencias para la búsqueda.");return
    with left:
        figure=ranking(frame,measure,limit)
        if figure is None:st.info("No hay porcentajes calculables: PIM agregado no positivo.")
        else:plot(figure)
    valid=frame[frame[measure].notna()]
    if not valid.empty:
        first=valid.sort_values(measure,ascending=False,kind="stable").iloc[0]
        st.caption(f"Lectura de la muestra: {first['nombre']} encabeza este orden por {d.LABELS[measure].lower()}, con PIM de S/ {formato(first['pim'])} y {formato(first['hechos'],0)} hechos. No es una clasificación del desempeño integral.")
    if group=="fuente":st.caption("Códigos y nombres de v_financiamiento_conformado: roles MEF auditados para fuente y rubro.")
    if group=="nivel":st.caption("Gobiernos locales incluidos aunque sector o pliego estén vacíos.")
    columns=["codigo","nombre"]+[c for c in ("sec_ejec","nivel_gobierno") if c in frame]+["hechos","pia","pim","devengado","girado","ejecucion_pct"]
    tabla(frame[columns],"dimensiones")

def metodologia(filters):
    st.subheader("Trazabilidad, método y límites")
    quality=d.calidad()
    st.markdown(tarjetas([("Hechos anuales",formato(quality["hechos_anuales"],0),"Muestra original preservada"),
        ("Hechos mensuales",formato(quality["hechos_mensuales"],0),"Doce meses por serie"),
        ("Dimensiones",str(quality["dimensiones"]),"Catálogos y detalle"),
        ("Claves foráneas",str(quality["fk"]),"Relaciones declaradas")]),unsafe_allow_html=True)
    st.caption("Control general de la base completa, independiente del filtro. El catálogo mostrado no vuelve a auditar huérfanos o todas las filas.")
    if quality["base"]==d.DATABASE and quality["solo_lectura"]=="on" and quality["fk_sin_validar"]==0:st.success("Conexión V2 de solo lectura; FK declaradas validadas en el catálogo.")
    st.warning("Muestras sin extrapolación nacional. La composición de las partidas y cobertura monetaria cambian entre años. La ejecución 2025 tiene fecha de corte no certificada.")
    st.markdown("**Fuente:** CSV del Ministerio de Economía y Finanzas del Perú, auditados en el proyecto. **Método:** Ralph Kimball; dos procesos con granos explícitos, dimensiones compartidas y linaje.")
    with st.expander("Modelo dimensional y matriz bus"):
        bus=pd.DataFrame([["Anual","Año","Sí","Sí","Sí","Original","Conformado","Sí","No"],["Mensual","Período + año","Misma SK","Misma SK","Misma SK","Detallada","Misma SK","Misma SK","Sí"]],
            columns=["Proceso","Tiempo","Entidad","Intervención","Función","Meta","Financiamiento","Clasificador","Período mensual"])
        st.dataframe(bus,hide_index=True,width="stretch")
        st.markdown("**Grano anual:** año y combinación completa de siete dimensiones. **Grano mensual:** período año-mes, entidad, intervención, función, meta detallada, financiamiento y clasificador.")
        st.markdown("Meta detallada añade SEC_FUNC y FINALIDAD con su contexto. La tabla técnica de 12.500 series conserva el linaje; no es un tercer hecho. V2 tiene nueve dimensiones y doce tablas.")
    with st.expander("Selección reproducible y cobertura"):
        st.markdown("3.125 series por ejercicio y doce meses por serie. Selección SHA-256 con semilla fija, cuota mínima por entidad y restos mayores sobre la población conciliada. Se excluyeron 136 discrepancias y claves ambiguas sin resolver.")
        st.markdown("No se aplican pesos. Las 150.000 filas mensuales corresponden a 12.500 hechos anuales, no a toda la muestra anual. Entidades comunes no garantizan partidas idénticas.")
    with st.expander("Importes, porcentajes y financiamiento"):
        st.markdown("Decimal se conserva para conciliación y CSV. Float se usa solo al representar gráficos. Las etapas presupuestarias no se suman entre sí.")
        st.markdown("Ejecución = 100 × SUM(devengado) / SUM(PIM), si PIM agregado > 0. PIM no positivo: no calculable. PIM cero con devengado positivo y porcentajes superiores a 100 % se muestran sin correcciones; la causa no está certificada.")
        st.markdown("Se conservan negativos, ceros y gobiernos locales sin sector/pliego. La vista conformada adapta los roles invertidos del almacenamiento heredado de financiamiento.")
    with st.expander("Evidencias y recuperación"):
        st.markdown("El proyecto tiene implementación, respaldo SHA-256 y restauración completa validada en otra base del mismo servidor. No equivale a probar otra computadora. El dashboard no ejecuta ETL ni restauraciones.")
        st.markdown("Las pruebas del dashboard se documentan en evidencias/INFORME_PRUEBAS.md. El control general de catálogo no sustituye esas validaciones.")
    st.markdown("#### Conciliación del filtro actual · doce meses")
    tabla(d.conciliacion(filters),"calidad_filtro")

def main():
    section,scope,filters=filtros()
    count_badges='<span class="pill">150.000 hechos anuales</span><span class="pill">150.000 hechos mensuales</span>'
    if section==SECTIONS[0]:
        global_counts=d.calidad()
        annual_count=global_counts["hechos_anuales"]
        monthly_count=global_counts["hechos_mensuales"]
        count_badges=(f'<span class="pill">{formato(annual_count,0)} hechos anuales</span>'
                      f'<span class="pill">{formato(monthly_count,0)} hechos mensuales</span>'
                      f'<span class="pill">{formato(annual_count+monthly_count,0)} hechos en total</span>')
    st.markdown(f'<div class="hero"><div class="eyebrow">INTELIGENCIA DE NEGOCIOS / PERÚ</div><h1>Observatorio presupuestario</h1><p>Ejecución anual y trayectoria mensual desde un Data Warehouse auditado.</p><span class="pill">2022–2025</span>{count_badges}<span class="pill gold">Muestra · no total nacional</span></div>',unsafe_allow_html=True)
    if section==SECTIONS[0]:
        st.caption("Conteos del encabezado: globales de la base completa, sin filtros. Los importes y conteos de los KPI inferiores corresponden al filtro activo; los importes anuales y mensuales nunca se suman.")
    st.caption("VISTA · "+section.upper()+"   /   Cobertura anual: "+d.SCOPES[scope])
    st.info("Cifras de la muestra filtrada, no del gasto público nacional. El mensual es una cohorte vinculada; no se suma al devengado anual.")
    if 2025 in filters.anios:st.caption("2025 · instantánea de la fuente; fecha de corte de ejecución no certificada.")
    if not filters.anios or not filters.niveles:st.info("Selecciona al menos un ejercicio y un nivel de gobierno. No se amplía automáticamente el filtro.");return
    if section==SECTIONS[5]:metodologia(filters);return
    if section==SECTIONS[2]:meses(filters);return
    summary=d.resumen(filters,scope)
    if summary["hechos"]==0:st.info("No hay hechos anuales para estos filtros. Amplía la selección.");return
    if section==SECTIONS[0]:resumen(filters,scope,summary)
    elif section==SECTIONS[1]:presupuesto(filters,scope,summary)
    elif section==SECTIONS[3]:comparar(filters,scope)
    elif section==SECTIONS[4]:dimensiones(filters,scope)

try:main()
except d.ErrorDatos as error:
    st.error(str(error));st.info("Revisa la conexión privada indicada en README.md. La aplicación no modifica la base.")
