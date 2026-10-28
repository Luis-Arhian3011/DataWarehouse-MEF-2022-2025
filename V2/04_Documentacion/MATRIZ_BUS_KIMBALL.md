# Matriz bus de Kimball — V2

| Proceso / hecho | Año | Entidad | Intervención | Función | Meta original | Financiamiento conformado | Clasificador | Período mensual | Meta detallada |
|---|---|---|---|---|---|---|---|---|---|
| Ejecución presupuestaria anual | Directo | Directo | Directo | Directo | Directo | Directo, misma SK | Directo | No aplica | No aplica |
| Devengado mensual | Contexto y período | Directo, misma SK | Directo, misma SK | Directo, misma SK | Linaje técnico de la serie, sin unión analítica entre hechos | Directo, misma SK | Directo, misma SK | Directo | Directo |

El año se conserva como contexto verificable del mensual y se conforma con dim_anio mediante dim_periodo_mensual; ambas filas pertenecen al mismo año por FK compuesta.

dim_meta se conserva intacta para el anual. dim_meta_detallada incorpora SEC_FUNC y FINALIDAD con año, entidad, intervención, función, META y DEPARTAMENTO_META. No son dimensiones intercambiables. El linaje técnico referencia ambas granularidades y no autoriza unir las dos tablas de hechos a nivel fila.

Las cinco dimensiones directamente compartidas por ambos hechos (entidad, intervención, función, financiamiento, clasificador) utilizan exactamente las mismas claves sustitutas y miembros. Año es compartido mediante el calendario. Se reutilizan los siete catálogos originales; meta original solo participa en el proceso anual y en el control de linaje.

Financiamiento: el almacenamiento heredado conserva los roles invertidos observados en la fuente original. Ambos procesos deben presentar códigos y nombres mediante v_financiamiento_conformado, cuya correspondencia fue auditada contra la fuente mensual. No se cambian claves ni valores originales.

## Grano de los hechos

- Anual: año y combinación única de las siete dimensiones originales, conservando la meta contextual y el identificador anual original.
- Mensual: período año-mes, entidad, intervención, función, meta detallada, financiamiento y clasificador. Una sola fila por serie seleccionada y mes. Doce meses completos por serie.

Las siete medidas anuales no son una suma de etapas entre sí. El mensual contiene únicamente devengado del mes, con negativos y ceros conservados. Para comparar, agregar cada hecho independientemente y usar la misma cohorte anual seleccionada. Nunca sumar devengado anual y mensual ni repetir PIA/PIM doce veces.

## Justificación de las 22 FK

| Tabla hija | FK | Necesidad |
|---|---:|---|
| fact_ejecucion_presupuestaria_anual | 7 | Integridad de las siete dimensiones originales |
| dim_periodo_mensual | 1 | Año del calendario conformado |
| dim_meta_detallada | 4 | Identidad contextual válida de año, entidad, intervención y función |
| auditoria.serie_seleccionada | 2 compuestas | Referencia exacta al hecho anual y a la meta detallada del mismo contexto |
| fact_devengado_mensual | 8 | Cinco catálogos compartidos, período/año, meta/contexto y serie/contexto |
| **Total** | **22** | Integridad referencial y coherencia de contexto |

Varias columnas aparecen en más de una FK porque una clave existente por separado no prueba que la combinación pertenezca a la misma serie. Las restricciones compuestas impiden mezclar años, entidades o metas válidos pero incompatibles. No son relaciones muchos-a-muchos ni puentes que repartan importes. La tabla de auditoría no contiene medidas.
