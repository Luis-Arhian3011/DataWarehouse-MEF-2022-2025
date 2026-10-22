-- Debe ejecutarse dentro de la misma transaccion que la carga.
DO $validar$
BEGIN
 IF EXISTS(SELECT 1 FROM mef.dim_anio WHERE anio NOT BETWEEN 2022 AND 2025) OR (SELECT count(*) FROM mef.dim_anio)<>4 THEN RAISE EXCEPTION 'Periodo debe ser exactamente 2022-2025'; END IF;
 IF (SELECT count(*) FROM mef.fact_ejecucion_presupuestaria_anual) <> 150000 THEN
  RAISE EXCEPTION 'La tabla de hechos debe contener exactamente 150000 filas';
 END IF;
 IF EXISTS (SELECT 1 FROM mef.fact_ejecucion_presupuestaria_anual f
JOIN mef.dim_anio a USING(anio_key)
JOIN mef.dim_entidad e USING(entidad_key)
JOIN mef.dim_intervencion i USING(intervencion_key)
JOIN mef.dim_funcion u USING(funcion_key)
JOIN mef.dim_meta m USING(meta_key) WHERE m.anio IS DISTINCT FROM a.anio OR m.clave_natural::jsonb IS DISTINCT FROM
(jsonb_build_array(a.anio::text) || e.clave_natural::jsonb || i.clave_natural::jsonb || u.clave_natural::jsonb ||
 jsonb_build_array(m.meta,m.departamento_meta,m.meta_nombre))) THEN
  RAISE EXCEPTION 'Contexto de meta incompatible con anio/entidad/intervencion/funcion';
 END IF;
 IF EXISTS (
 WITH esperado(anio,hechos,pia,pim,certificado,comprometido_anual,comprometido,devengado,girado) AS (VALUES (2022,37500,7160329078.00,4444957539.00,3117400430.81,2987917276.19,3166518205.05,3051967587.64,3012287406.45),(2023,37500,2452274432.00,2862145499.00,2728618602.90,2618795165.87,2516106901.58,2491634677.99,2488350151.22),(2024,37500,2907341142.00,3494380573.00,3382293746.88,3298710845.74,3296212002.76,3260710447.90,3256666735.87),(2025,37500,2925939597.00,3551680414.00,3462054522.42,3393490905.76,3271586534.89,3224421680.28,3223087084.13)),
 observado AS (SELECT anio_key anio,count(*) hechos,sum(pia) pia,sum(pim) pim,sum(certificado) certificado,sum(comprometido_anual) comprometido_anual,sum(comprometido) comprometido,sum(devengado) devengado,sum(girado) girado FROM mef.fact_ejecucion_presupuestaria_anual GROUP BY anio_key)
 SELECT 1 FROM esperado x FULL JOIN observado y USING(anio)
 WHERE x.hechos IS DISTINCT FROM y.hechos OR x.pia IS DISTINCT FROM y.pia OR x.pim IS DISTINCT FROM y.pim OR x.certificado IS DISTINCT FROM y.certificado OR x.comprometido_anual IS DISTINCT FROM y.comprometido_anual OR x.comprometido IS DISTINCT FROM y.comprometido OR x.devengado IS DISTINCT FROM y.devengado OR x.girado IS DISTINCT FROM y.girado
 ) THEN RAISE EXCEPTION 'Diferencia contra totales exactos de la seleccion auditada'; END IF;
 IF (SELECT count(*) FROM pg_constraint WHERE conrelid='mef.fact_ejecucion_presupuestaria_anual'::regclass AND contype='f' AND convalidated) <> 7 THEN
  RAISE EXCEPTION 'Se requieren siete claves foraneas validadas';
 END IF;
END;
$validar$;
