"""Prueba visual opcional: requiere playwright y Chrome local."""
import json
import os
from pathlib import Path
from urllib.request import urlopen
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parent
OUT=Path(os.environ.get("MEF_EVIDENCIAS",str(ROOT/"evidencias")))
OUT.mkdir(parents=True,exist_ok=True)
def main():
    assert urlopen(os.environ.get("MEF_DASHBOARD_URL","http://127.0.0.1:8501")+"/_stcore/health",timeout=10).status==200
    result={"http_salud":200,"vistas":[],"errores_navegador":[]}
    with sync_playwright() as p:
        browser=p.chromium.launch(channel="chrome",headless=True)
        page=browser.new_page(viewport={"width":1440,"height":1100},device_scale_factor=1)
        page.on("pageerror",lambda e:result["errores_navegador"].append(str(e)))
        page.goto(os.environ.get("MEF_DASHBOARD_URL","http://127.0.0.1:8501"))
        page.get_by_role("heading",name="Resumen ejecutivo",exact=True).wait_for(timeout=45000)
        page.locator(".kpi").first.wait_for()
        page.locator("[data-testid=stPlotlyChart] .js-plotly-plot").first.wait_for(timeout=45000)
        page.locator("[data-testid=stMain]").evaluate("el => el.scrollTop = 0")
        page.screenshot(path=str(OUT/"escritorio_resumen.png"),full_page=True)
        for section in ["Análisis temporal","Niveles de gobierno","Análisis por entidad","Distribución del gasto","Metodología y calidad"]:
            page.get_by_test_id("stSidebar").get_by_text(section,exact=True).click()
            page.get_by_role("heading",name=section,exact=True).wait_for(timeout=30000)
            page.wait_for_timeout(1000)
            assert page.get_by_test_id("stException").count()==0
            assert page.get_by_text("No se pudo mostrar esta vista.",exact=False).count()==0
            result["vistas"].append(section)
        # Comprueba una descarga real desde la tabla agregada de cobertura.
        with page.expect_download() as event:
            page.get_by_role("button",name="Descargar resultados agregados · CSV").click()
        download=event.value
        payload=Path(download.path()).read_bytes()
        assert payload.startswith(b"\xef\xbb\xbf") and len(payload)>100
        result["csv_descargado"]=download.suggested_filename
        result["csv_bytes"]=len(payload)
        page.get_by_test_id("stSidebar").get_by_text("Resumen ejecutivo",exact=True).click()
        page.get_by_role("heading",name="Resumen ejecutivo",exact=True).wait_for()
        page.set_viewport_size({"width":390,"height":844})
        # Colapsar navegación si continúa abierta al cambiar la resolución.
        collapse=page.get_by_test_id("stSidebarCollapseButton").get_by_role("button")
        if collapse.count() and collapse.is_visible():
            collapse.click()
        page.locator("[data-testid=stMain]").evaluate("el => el.scrollTop = 0")
        page.wait_for_timeout(1500)
        page.screenshot(path=str(OUT/"movil_resumen.png"),full_page=True)
        result["movil_desborde_horizontal"]=page.evaluate("document.documentElement.scrollWidth > window.innerWidth")
        assert not result["movil_desborde_horizontal"]
        assert not result["errores_navegador"]
        browser.close()
    result["estado"]="correcto"
    (OUT/"verificacion_navegador.json").write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(result,ensure_ascii=True))
if __name__=="__main__":
    main()
