-- Todas las sumas describen la muestra seleccionada, no totales nacionales.
-- No sumar etapas entre si ni promediar porcentajes por fila.
-- El porcentaje es del subconjunto y puede superar 100: no representa ejecucion integral de la entidad.

-- 1. Presupuesto y ejecucion por ejercicio.
SELECT a.anio, count(*) hechos, sum(f.pia) pia, sum(f.pim) pim,
       sum(f.devengado) devengado, sum(f.girado) girado,
       round(100*sum(f.devengado)/nullif(sum(f.pim),0),2) ejecucion_muestra_pct
FROM mef.fact_ejecucion_presupuestaria_anual f JOIN mef.dim_anio a USING(anio_key)
GROUP BY a.anio ORDER BY a.anio;

-- 2. Comparacion por nivel de gobierno y ejercicio.
SELECT a.anio,e.nivel_gobierno,e.nivel_gobierno_nombre,
       count(*) hechos,count(DISTINCT e.entidad_key) entidades,sum(f.pim) pim,sum(f.devengado) devengado
FROM mef.fact_ejecucion_presupuestaria_anual f
JOIN mef.dim_anio a USING(anio_key) JOIN mef.dim_entidad e USING(entidad_key)
GROUP BY a.anio,e.nivel_gobierno,e.nivel_gobierno_nombre ORDER BY 1,2;

-- 3. Veinte entidades con mayor devengado dentro de la muestra.
SELECT e.sec_ejec,e.ejecutora_nombre,sum(f.devengado) devengado_muestra
FROM mef.fact_ejecucion_presupuestaria_anual f JOIN mef.dim_entidad e USING(entidad_key)
GROUP BY e.entidad_key,e.sec_ejec,e.ejecutora_nombre ORDER BY devengado_muestra DESC LIMIT 20;

-- 4. Finalidad funcional.
SELECT a.anio,u.funcion,u.funcion_nombre,sum(f.pim) pim,sum(f.devengado) devengado
FROM mef.fact_ejecucion_presupuestaria_anual f
JOIN mef.dim_anio a USING(anio_key) JOIN mef.dim_funcion u USING(funcion_key)
GROUP BY a.anio,u.funcion,u.funcion_nombre ORDER BY 1,devengado DESC;

-- 5. Fuente, rubro y tipo de recurso.
SELECT r.fuente_financiamiento,r.fuente_financiamiento_nombre,r.rubro,r.tipo_recurso,
       sum(f.pim) pim,sum(f.devengado) devengado
FROM mef.fact_ejecucion_presupuestaria_anual f JOIN mef.dim_financiamiento r USING(financiamiento_key)
GROUP BY r.financiamiento_key,r.fuente_financiamiento,r.fuente_financiamiento_nombre,r.rubro,r.tipo_recurso
ORDER BY devengado DESC;

-- 6. Categoria y generica del gasto.
SELECT c.categoria_gasto,c.categoria_gasto_nombre,c.generica,c.generica_nombre,
       sum(f.devengado) devengado
FROM mef.fact_ejecucion_presupuestaria_anual f JOIN mef.dim_clasificador_gasto c USING(clasificador_gasto_key)
GROUP BY c.categoria_gasto,c.categoria_gasto_nombre,c.generica,c.generica_nombre ORDER BY devengado DESC;

-- 7. Metas y ubicacion: conservar la distincion entre metas observadas.
SELECT a.anio,m.meta,m.meta_nombre,m.departamento_meta,m.departamento_meta_nombre,
       sum(f.pim) pim,sum(f.devengado) devengado
FROM mef.fact_ejecucion_presupuestaria_anual f
JOIN mef.dim_anio a USING(anio_key) JOIN mef.dim_meta m USING(meta_key)
GROUP BY m.meta_key,a.anio,m.meta,m.meta_nombre,m.departamento_meta,m.departamento_meta_nombre
ORDER BY devengado DESC LIMIT 30;

-- 8. Filas que contienen ajustes negativos: no aplicar ABS ni reemplazar por cero.
SELECT a.anio,e.sec_ejec,e.ejecutora_nombre,f.key_value,f.pim,f.devengado,f.girado
FROM mef.fact_ejecucion_presupuestaria_anual f
JOIN mef.dim_anio a USING(anio_key) JOIN mef.dim_entidad e USING(entidad_key)
WHERE f.pia<0 OR f.pim<0 OR f.certificado<0 OR f.comprometido_anual<0
   OR f.comprometido<0 OR f.devengado<0 OR f.girado<0
ORDER BY a.anio,e.sec_ejec,f.key_value;

-- 9. Comparacion interanual del subconjunto, no de los totales oficiales.
WITH anuales AS (
 SELECT a.anio,count(*) hechos,sum(f.pia) pia,sum(f.pim) pim,sum(f.devengado) devengado_muestra
 FROM mef.fact_ejecucion_presupuestaria_anual f JOIN mef.dim_anio a USING(anio_key)
 GROUP BY a.anio
), cambios AS (
 SELECT *,lag(devengado_muestra) OVER(ORDER BY anio) anterior FROM anuales
)
SELECT anio,hechos,pia,pim,devengado_muestra,devengado_muestra-anterior diferencia_muestra,
 round(100*(devengado_muestra-anterior)/nullif(anterior,0),2) variacion_muestra_pct
FROM cambios ORDER BY anio;
