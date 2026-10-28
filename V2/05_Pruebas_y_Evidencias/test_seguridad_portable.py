import json,os,sys,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import proyecto,entorno
class SeguridadPortableTests(unittest.TestCase):
    def test_base_original_bloqueada(self):
        with patch.dict(os.environ,{"PGDATABASE":"dw_mef_2022_2025"}):
            with self.assertRaises(ValueError):entorno.configuracion()
    def test_destino_existente_no_se_modifica(self):
        with patch.object(sys,"argv",["proyecto.py","restaurar","--autorizar"]),patch.object(proyecto,"configuracion",return_value={}),patch.object(proyecto,"diagnostic",return_value={"exists":True}),patch.object(proyecto,"owned_container") as docker,patch.object(proyecto,"connection") as connection:
            with self.assertRaises(ValueError):proyecto.main()
            docker.assert_not_called();connection.assert_not_called()
    def test_sin_autorizacion_no_crea(self):
        with patch.object(sys,"argv",["proyecto.py","restaurar"]),patch.object(proyecto,"configuracion",return_value={}),patch.object(proyecto,"diagnostic",return_value={"exists":False}),patch.object(proyecto,"owned_container") as docker:
            with self.assertRaises(ValueError):proyecto.main()
            docker.assert_not_called()
    def test_contenedor_original_rechazado(self):
        cfg={"COMPOSE_PROJECT_NAME":"mef-v2-entrega"}
        from subprocess import CompletedProcess
        outputs=[CompletedProcess([],0,"fakeid\n",""),CompletedProcess([],0,json.dumps([{"Name":"/postgres-db"}]),"")]
        with patch.object(proyecto.subprocess,"run",side_effect=outputs):
            with self.assertRaises(ValueError):proyecto.owned_container(cfg,"dummy")
if __name__=="__main__":unittest.main()
