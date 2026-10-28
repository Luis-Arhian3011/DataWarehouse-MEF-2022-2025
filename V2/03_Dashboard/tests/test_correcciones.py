import sys,unittest
from pathlib import Path
from decimal import Decimal
import pandas as pd
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from presentacion import dinero,evolucion,YEAR_COLORS
from filtros_ui import reajustar_seleccion,filtro_efectivo

class CorreccionesTests(unittest.TestCase):
    def test_soles_positivos_negativos_y_cero(self):
        for value,expected in [("0","S/ 0,00"),("-0.00","S/ 0,00"),("0.01","S/ 0,01"),("-0.01","S/ -0,01"),("999.99","S/ 999,99"),("-999.99","S/ -999,99")]:
            with self.subTest(value=value):self.assertEqual(dinero(Decimal(value)),expected)
    def test_umbral_miles_millones(self):
        for value,unit in [("1000"," mil"),("1000.01"," mil"),("4999.99"," mil"),("999999.99"," mil"),("1000000"," M"),("1000000.01"," M"),("999999999.99"," M"),("1000000000"," mil M")]:
            for sign in (1,-1):
                amount=Decimal(value)*sign
                with self.subTest(amount=amount):
                    self.assertTrue(dinero(amount).endswith(unit))
                    self.assertNotIn("S/ 0,00",dinero(amount))
    def test_decimal_entrada_no_cambia(self):
        amount=Decimal("4999.99");before=amount.as_tuple()
        self.assertEqual(dinero(amount),"S/ 5,00 mil")
        self.assertEqual(amount.as_tuple(),before)
    def test_retiro_total_bloquea(self):
        valid,locked,removed=reajustar_seleccion((1,),{2,3})
        self.assertEqual((valid,locked,removed),((),True,(1,)))
        self.assertEqual(filtro_efectivo(valid,locked),())
    def test_bloqueo_persiste_tras_otro_rerun(self):
        valid,locked,_=reajustar_seleccion((),{1,2},True)
        self.assertTrue(locked);self.assertEqual(filtro_efectivo(valid,locked),())
    def test_retiro_parcial_conserva_restriccion(self):
        valid,locked,removed=reajustar_seleccion((1,2),{2,3})
        self.assertEqual(valid,(2,));self.assertFalse(locked);self.assertEqual(removed,(1,))
        self.assertEqual(filtro_efectivo(valid,locked),(2,))
    def test_recuperacion_con_seleccion_explicita(self):
        valid,locked,_=reajustar_seleccion((2,),{2,3},True)
        self.assertFalse(locked);self.assertEqual(filtro_efectivo(valid,locked),(2,))
    def test_todas_solo_sin_bloqueo(self):
        self.assertIsNone(filtro_efectivo((),False))
        self.assertEqual(filtro_efectivo((),True),())
    def test_colores_estables_al_filtrar_y_acumular(self):
        frame=pd.DataFrame([dict(anio=y,mes=1,mes_nombre="Enero",devengado=Decimal("1"),acumulado=Decimal("1")) for y in range(2022,2026)])
        for metric in ("devengado","acumulado"):
            whole=evolucion(frame,metric)
            self.assertEqual({int(t.name):t.line.color for t in whole.data},YEAR_COLORS)
            for year in YEAR_COLORS:
                selected=evolucion(frame[frame.anio==year],metric)
                self.assertEqual(selected.data[0].line.color,YEAR_COLORS[year])
    def test_contraste_palette_sobre_fondo(self):
        def luminance(hexcolor):
            rgb=[int(hexcolor[i:i+2],16)/255 for i in (1,3,5)]
            linear=[v/12.92 if v<=0.04045 else ((v+0.055)/1.055)**2.4 for v in rgb]
            return sum(v*w for v,w in zip(linear,(0.2126,0.7152,0.0722)))
        background=luminance("#102236")
        for color in YEAR_COLORS.values():
            self.assertGreater((luminance(color)+0.05)/(background+0.05),3)
if __name__=="__main__":unittest.main()
