import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from comun import money
from muestreo import select
from decimal import Decimal

class SamplingTests(unittest.TestCase):
    def candidates(self):
        return [dict(entity=e,canonical=e+str(i),hecho_key=e+str(i)) for e,n in [("a",10),("b",3),("c",1)] for i in range(n)]
    def test_order(self):
        a=self.candidates()
        self.assertEqual(select(a,8,"seed"),select(list(reversed(a)),8,"seed"))
    def test_quota_and_entities(self):
        result=select(self.candidates(),8,"seed")
        self.assertEqual(len(result),8)
        self.assertEqual({r["entity"] for r in result},{"a","b","c"})
        self.assertEqual(len({r["canonical"] for r in result}),8)
    def test_impossible(self):
        with self.assertRaises(ValueError):select(self.candidates(),2,"seed")
    def test_full(self):
        self.assertEqual(len(select(self.candidates(),14,"seed")),14)
    def test_negative_precision(self):
        self.assertEqual(money("-59000.01"),Decimal("-59000.01"))
    def test_invalid_money(self):
        for value in [None,"","NaN","1.001","1000000000000000000.00","1,23"]:
            with self.subTest(value=value),self.assertRaises(ValueError):money(value)
if __name__=="__main__":unittest.main()
