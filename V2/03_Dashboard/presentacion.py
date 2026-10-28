"""Formato y graficos sin mutar los valores Decimal de las consultas."""
from decimal import Decimal
from html import escape
from textwrap import wrap
import pandas as pd
import plotly.graph_objects as go
from datos import LABELS

COLORS=["#35D6C6","#E7BF72","#7B9FF2","#B69BE8"]
YEAR_COLORS=dict(zip((2022,2023,2024,2025),COLORS))
MONTHS=["Enero","Febrero","Marzo","Abril","Mayo","Junio","Julio","Agosto","Septiembre","Octubre","Noviembre","Diciembre"]

def formato(value,decimals=2):
    if value is None or pd.isna(value):return "No aplica"
    return f"{value:,.{decimals}f}".replace(",","_").replace(".",",").replace("_",".")

def dinero(value):
    value=Decimal(value)
    magnitude=abs(value)
    if value==0:
        return "S/ 0,00"
    for threshold,unit in [(Decimal("1000000000"),"mil M"),(Decimal("1000000"),"M"),(Decimal("1000"),"mil")]:
        if magnitude>=threshold:
            return "S/ "+formato(value/threshold)+" "+unit
    return "S/ "+formato(value)

def tarjetas(values):
    return '<div class="kpis">'+"".join('<div class="kpi"><div class="kpi-label">'+escape(a)+'</div><div class="kpi-value">'+escape(b)+'</div><div class="kpi-note">'+escape(c)+'</div></div>' for a,b,c in values)+'</div>'

def corta(value):
    lines=wrap(str(value or "Sin denominación"),width=27,break_long_words=True)
    return "<br>".join(escape(x) for x in lines[:2])+("…" if len(lines)>2 else "")

def tema(figure,title,height=380):
    figure.update_layout(title=dict(text=title,font=dict(size=17)),height=height,
        paper_bgcolor="#102236",plot_bgcolor="#102236",
        font=dict(family="Arial, sans-serif",color="#CEDCEB",size=12),
        colorway=COLORS,margin=dict(l=25,r=25,t=85,b=45),
        legend=dict(orientation="h",y=1.11,x=0),hoverlabel=dict(bgcolor="#1C354D"),
        separators=",.",dragmode=False)
    figure.update_xaxes(gridcolor="#25394D",zerolinecolor="#43556A",automargin=True)
    figure.update_yaxes(gridcolor="#25394D",zerolinecolor="#43556A",automargin=True)
    return figure

def serie_anual(frame,measures,title):
    figure=go.Figure()
    for index,measure in enumerate(measures):
        figure.add_trace(go.Scatter(x=frame["anio"].astype(str),y=[float(x)/1e6 for x in frame[measure]],name=LABELS[measure].split(" (")[0],mode="lines+markers",line=dict(width=3,color=COLORS[index]),marker=dict(size=8),
            customdata=[[formato(v)] for v in frame[measure]],hovertemplate="%{x}<br>S/ %{customdata[0]}<extra>%{fullData.name}</extra>"))
    figure.update_xaxes(title="Ejercicio",type="category")
    figure.update_yaxes(title="Millones de soles · muestra")
    return tema(figure,title)

def evolucion(frame,measure):
    figure=go.Figure()
    for year,part in frame.groupby("anio",sort=True):
        figure.add_trace(go.Scatter(x=part["mes"],y=[float(v)/1e6 for v in part[measure]],name=str(year),mode="lines+markers",line=dict(width=3,color=YEAR_COLORS[int(year)]),marker=dict(size=6),
            customdata=[[n,formato(v)] for n,v in zip(part["mes_nombre"],part[measure])],
            hovertemplate="%{customdata[0]}<br>S/ %{customdata[1]}<extra>%{fullData.name}</extra>"))
    figure.update_xaxes(tickmode="array",tickvals=list(range(1,13)),ticktext=[m[:3] for m in MONTHS],title="Mes del ejercicio")
    figure.update_yaxes(title="Millones de soles · cohorte mensual")
    return tema(figure,"Devengado mensual" if measure=="devengado" else "Devengado acumulado desde enero")

def ranking(frame,measure,limit=12):
    valid=frame[frame[measure].notna()].sort_values(measure,ascending=False,kind="stable")
    if valid.empty:return None
    top=valid.head(limit).iloc[::-1]
    positions=list(range(len(top)))
    percent=measure=="ejecucion_pct"
    custom=[[str(row["nombre"]),str(row["codigo"]),formato(row[measure]),formato(row["pim"]),formato(row["hechos"],0)] for _,row in top.iterrows()]
    figure=go.Figure(go.Bar(x=[float(v)/(1 if percent else 1e6) for v in top[measure]],y=positions,orientation="h",marker_color=COLORS[1 if percent else 0],customdata=custom,
        hovertemplate="%{customdata[0]}<br>Código: %{customdata[1]}<br>Valor: %{customdata[2]}"+(" %" if percent else " S/")+"<br>PIM: S/ %{customdata[3]}<br>Hechos: %{customdata[4]}<extra></extra>"))
    figure.update_yaxes(tickmode="array",tickvals=positions,ticktext=[corta(n) for n in top["nombre"]],type="category",tickfont=dict(size=11))
    figure.update_xaxes(title="Ejecución (%)" if percent else "Millones de soles")
    return tema(figure,"Ranking de la muestra · "+LABELS[measure],max(400,110+len(top)*49))

def variaciones(frame):
    result=frame.copy(deep=True).sort_values("anio").reset_index(drop=True)
    values=[None]*len(result)
    for i in range(1,len(result)):
        previous,current=result.iloc[i-1],result.iloc[i]
        if int(current["anio"])-int(previous["anio"])==1 and previous["devengado"]>0:
            values[i]=Decimal(100)*(current["devengado"]-previous["devengado"])/previous["devengado"]
    result["variacion_pct"]=pd.Series(values,dtype=object)
    return result

def tabla_estilo(frame):
    copy=frame.copy(deep=True)
    numbers=[c for c in copy if c in ("pia","pim","devengado","girado","ejecucion_pct","variacion_pct","dev_pim_cero","acumulado","devengado_anual","devengado_mensual","diferencia")]
    counts=[c for c in copy if c in ("hechos","entidades","series","meses","negativos","pim_cero","pim_no_positivo")]
    formats={LABELS.get(c,c):formato for c in numbers}
    formats.update({LABELS.get(c,c):lambda v:formato(v,0) for c in counts})
    return copy.rename(columns=LABELS).style.format(formats,na_rep="No aplica")
