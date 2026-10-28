# Diccionario de datos de carga

Columnas y conteos extraidos de los manifiestos reales. Tipos y restricciones definitivos: SQL de 01_Base_de_Datos/sql. Las siete medidas anuales y el devengado mensual son NUMERIC(20,2); no se suman etapas entre si.

## mef.dim_anio

Filas: 4.

`anio_key`, `anio`.

## mef.dim_entidad

Filas: 2898.

`entidad_key`, `clave_natural`, `nivel_gobierno`, `sector`, `pliego`, `ejecutora`, `sec_ejec`, `departamento_ejecutora`, `provincia_ejecutora`, `distrito_ejecutora`, `nivel_gobierno_nombre`, `sector_nombre`, `pliego_nombre`, `ejecutora_nombre`, `departamento_ejecutora_nombre`, `provincia_ejecutora_nombre`, `distrito_ejecutora_nombre`, `nombres_observados`.

## mef.dim_intervencion

Filas: 18654.

`intervencion_key`, `clave_natural`, `programa_ppto`, `tipo_act_proy`, `producto_proyecto`, `actividad_accion_obra`, `programa_ppto_nombre`, `tipo_act_proy_nombre`, `producto_proyecto_nombre`, `actividad_accion_obra_nombre`, `nombres_observados`.

## mef.dim_funcion

Filas: 356.

`funcion_key`, `clave_natural`, `funcion`, `division_funcional`, `grupo_funcional`, `funcion_nombre`, `division_funcional_nombre`, `grupo_funcional_nombre`, `nombres_observados`.

## mef.dim_meta

Filas: 121305.

`meta_key`, `clave_natural`, `anio`, `meta`, `meta_nombre`, `departamento_meta`, `departamento_meta_nombre`, `nombres_observados`.

## mef.dim_financiamiento

Filas: 114.

`financiamiento_key`, `clave_natural`, `fuente_financiamiento`, `rubro`, `tipo_recurso`, `fuente_financiamiento_nombre`, `rubro_nombre`, `tipo_recurso_nombre`, `nombres_observados`.

## mef.dim_clasificador_gasto

Filas: 476.

`clasificador_gasto_key`, `clave_natural`, `categoria_gasto`, `tipo_transaccion`, `generica`, `subgenerica`, `subgenerica_det`, `especifica`, `especifica_det`, `categoria_gasto_nombre`, `generica_nombre`, `subgenerica_nombre`, `subgenerica_det_nombre`, `especifica_nombre`, `especifica_det_nombre`, `nombres_observados`.

## mef.fact_ejecucion_presupuestaria_anual

Filas: 150000.

`hecho_key`, `anio_key`, `entidad_key`, `intervencion_key`, `funcion_key`, `meta_key`, `financiamiento_key`, `clasificador_gasto_key`, `key_value`, `pia`, `pim`, `certificado`, `comprometido_anual`, `comprometido`, `devengado`, `girado`, `hash_seleccion`, `poblacion_estrato`, `cuota_estrato`.

## mef.dim_periodo_mensual

Filas: 48.

`periodo_key`, `anio_key`, `mes`, `mes_nombre`.

## mef.dim_meta_detallada

Filas: 12477.

`meta_detalle_key`, `anio_key`, `entidad_key`, `intervencion_key`, `funcion_key`, `sec_func`, `finalidad`, `meta`, `departamento_meta`, `meta_nombre`, `departamento_meta_nombre`, `clave_natural`.

## auditoria.serie_seleccionada

Filas: 12500.

`hecho_anual_key`, `anio_key`, `entidad_key`, `intervencion_key`, `funcion_key`, `meta_key`, `financiamiento_key`, `clasificador_gasto_key`, `meta_detalle_key`, `fuente_grano_json`, `fuente_sha256`, `semilla`, `prioridad_hash`, `entidad_natural`, `poblacion_estrato`, `cuota_estrato`.

## mef.fact_devengado_mensual

Filas: 150000.

`hecho_mensual_key`, `hecho_anual_key`, `periodo_key`, `anio_key`, `entidad_key`, `intervencion_key`, `funcion_key`, `meta_detalle_key`, `financiamiento_key`, `clasificador_gasto_key`, `devengado`.

Las claves sustitutas se conservan; las claves naturales JSON incluyen el contexto indicado en el modelo. La vista de financiamiento conformado intercambia explicitamente los roles heredados de fuente y rubro. El contador de negativos de interfaz cuenta registros mensuales, no periodos calendario.

[Modelo](MODELO_Y_REGLAS.md) ? [Matriz bus](MATRIZ_BUS_KIMBALL.md).
