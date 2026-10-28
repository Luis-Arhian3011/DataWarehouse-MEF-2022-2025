-- Muestra, sin extrapolacion nacional. Cohorte identica, agregaciones independientes.
WITH anual AS (
 SELECT anio_key,count(*) series,sum(pia) pia,sum(pim) pim,sum(devengado) devengado_anual
 FROM mef.v_anual_cohorte_mensual GROUP BY anio_key
), mensual AS (
 SELECT anio_key,count(*) hechos,sum(devengado) devengado_mensual
 FROM mef.fact_devengado_mensual GROUP BY anio_key
)
SELECT a.*,m.hechos,m.devengado_mensual,
 m.devengado_mensual-a.devengado_anual diferencia,
 CASE WHEN a.pim>0 THEN 100*m.devengado_mensual/a.pim END ejecucion
FROM anual a JOIN mensual m USING(anio_key) ORDER BY anio_key;

-- No se incorpora PIM a cada mes: evita multiplicarlo por doce.
SELECT p.anio_key,p.mes,p.mes_nombre,count(*) hechos,sum(m.devengado) devengado,
 sum(sum(m.devengado)) OVER(PARTITION BY p.anio_key ORDER BY p.mes) acumulado
FROM mef.fact_devengado_mensual m JOIN mef.dim_periodo_mensual p USING(periodo_key)
GROUP BY p.anio_key,p.mes,p.mes_nombre ORDER BY p.anio_key,p.mes;

SELECT a.anio_key,e.nivel_gobierno,count(*) hechos,sum(a.devengado) devengado
FROM mef.fact_devengado_mensual a JOIN mef.dim_entidad e USING(entidad_key)
GROUP BY a.anio_key,e.nivel_gobierno ORDER BY 1,2;
