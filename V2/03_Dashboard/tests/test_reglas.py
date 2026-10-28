import csv,io,os,sys,unittest
from pathlib import Path
from decimal import Decimal
from unittest.mock import patch
import pandas as pd
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import datos as d
from presentacion import formato,variaciones,tabla_estilo,ranking

class ReglasTests(unittest.TestCase):
    def test_base_fija(self):
        with patch.dict(os.environ,{"PGDATABASE":"dw_mef_2022_2025"}),patch("datos.psycopg.connect") as connect:
            with self.assertRaises(d.ErrorDatos):d.conectar()
            connect.assert_not_called()
    def test_bloqueo_escritura(self):
        with patch("datos.conectar") as connect:
            with self.assertRaises(d.ErrorDatos):d.consultar("DELETE FROM mef.fact_devengado_mensual")
            connect.assert_not_called()
    def test_grupos_cerrados(self):
        with self.assertRaises(ValueError):d.agrupado("funcion; SELECT 1")
    def test_2026_excluido(self):
        with self.assertRaises(ValueError):d.Filtros(anios=(2026,))
    def test_filtro_vacio_no_amplia(self):
        sql,params=d.condicion(d.Filtros(anios=(),entidades=()))
        self.assertEqual(params[0],[])
        self.assertEqual(params[2],[])
        self.assertIn("ANY",sql)
    def test_formato_decimal(self):
        self.assertEqual(formato(Decimal("-1234567.89")),"-1.234.567,89")
        self.assertEqual(formato(None),"No aplica")
    def test_csv_y_estilo_conservan_valores(self):
        value=Decimal("999999999999999999.99")
        frame=pd.DataFrame({"pim":[value],"devengado":[Decimal("-59000.01")]})
        before=frame.copy(deep=True)
        styled=tabla_estilo(frame)
        pd.testing.assert_frame_equal(frame,before)
        self.assertEqual(styled.data["PIM (S/)"].iloc[0],value)
        row=next(csv.DictReader(io.StringIO(d.exportar(frame).decode("utf-8-sig")),delimiter=";"))
        self.assertEqual(Decimal(row["PIM (S/)"].replace(",",".")),value)
        self.assertEqual(Decimal(row["Devengado (S/)"].replace(",",".")),Decimal("-59000.01"))
    def test_variacion_sin_base_o_salto(self):
        frame=pd.DataFrame({"anio":[2022,2024,2025],"devengado":[Decimal(0),Decimal(100),Decimal(120)]})
        result=variaciones(frame)
        self.assertIsNone(result["variacion_pct"][0])
        self.assertIsNone(result["variacion_pct"][1])
        self.assertEqual(result["variacion_pct"][2],Decimal(20))
    def test_porcentaje_no_se_recorta(self):
        frame=pd.DataFrame({"codigo":[1],"nombre":["Entidad de prueba"],"hechos":[12],"pim":[Decimal(10)],"ejecucion_pct":[Decimal(150)]})
        figure=ranking(frame,"ejecucion_pct")
        self.assertEqual(figure.data[0].x[0],150)
        self.assertIn("PIM",figure.data[0].hovertemplate)
        self.assertIn("Hechos",figure.data[0].hovertemplate)
if __name__=="__main__":unittest.main()
