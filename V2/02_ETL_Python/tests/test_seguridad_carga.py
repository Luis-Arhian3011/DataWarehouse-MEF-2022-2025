import csv,os,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
import postgres_v2
from psycopg import sql

class LoaderSafetyTests(unittest.TestCase):
    def test_reject_original_database_before_connection(self):
        with patch.dict(os.environ,{"PGDATABASE":"dw_mef_2022_2025"}),patch.object(sys,"argv",["postgres_v2.py","diagnostico"]),patch.object(postgres_v2,"connect") as connection:
            with self.assertRaises(ValueError):
                postgres_v2.main()
            connection.assert_not_called()
    def test_reject_creation_without_authorization(self):
        with patch.dict(os.environ,{"PGDATABASE":postgres_v2.DB}),patch.object(sys,"argv",["postgres_v2.py","crear-y-cargar"]),patch.object(postgres_v2,"connect") as connection:
            with self.assertRaises(ValueError):
                postgres_v2.main()
            connection.assert_not_called()
    def test_copy_preserves_bytes_and_empty_text(self):
        class Copy:
            def __enter__(self):return self
            def __exit__(self,*args):pass
            def write(self,data):self.data+=data
            def __init__(self):self.data=b""
        class Cursor:
            def copy(self,query):
                self.query=query.as_string()
                self.result=Copy()
                return self.result
        with tempfile.TemporaryDirectory() as temporary:
            path=Path(temporary)/"text.csv"
            expected=b"sector,pliego\r\n,\r\n"
            path.write_bytes(expected)
            cur=Cursor()
            postgres_v2.copy_file(cur,"mef.dim_entidad",path,["sector","pliego"])
            self.assertEqual(cur.result.data,expected)
            self.assertIn('FORCE_NOT_NULL ("sector","pliego")',cur.query)
    def test_verifier_rejects_other_database(self):
        class Cursor:
            def __enter__(self):return self
            def __exit__(self,*args):pass
            def execute(self,*args):pass
            def fetchone(self):return ("dw_mef_2022_2025",)
        class Connection:
            def cursor(self):return Cursor()
        with self.assertRaises(ValueError):
            postgres_v2.verify(Connection(),postgres_v2.ROOT/"datos_preparados/mensual")

if __name__=="__main__":unittest.main()
