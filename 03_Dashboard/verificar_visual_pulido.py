"""Capturas y CSV reales del pulido, sin modificar el servidor existente."""
import json
import os
from pathlib import Path
from playwright.sync_api import sync_playwright
from datos import ROOT,anual,exportar
def main():
    out=Path(os.environ.get("MEF_EVIDENCIAS",str(ROOT/"evidencias")))/"pulido"
    out.mkdir(parents=True,exist_ok=True)
    result={"capturas":[],"resoluciones":[]}
    with sync_playwright() as p:
        b=p.chromium.launch(channel="chrome",headless=True)
        page=b.new_page(viewport={"width":1440,"height":1100})
        page.goto(os.environ.get("MEF_DASHBOARD_URL","http://127.0.0.1:8501"))
        page.get_by_role("heading",name="Resumen ejecutivo",exact=True).wait_for(timeout=45000)
        page.get_by_test_id("stSidebar").get_by_text("Análisis temporal",exact=True).click()
        page.get_by_role("heading",name="Análisis temporal",exact=True).wait_for()
        table=page.get_by_test_id("stDataFrame").first
        table.wait_for()
        table.screenshot(path=str(out/"tabla_temporal.png"))
        result["capturas"].append("tabla_temporal.png")
        table.evaluate("el => { for (const n of el.querySelectorAll('*')) { if (n.scrollWidth>n.clientWidth+30) n.scrollLeft=n.scrollWidth; } }")
        page.wait_for_timeout(600)
        table.screenshot(path=str(out/"tabla_variaciones.png"))
        result["capturas"].append("tabla_variaciones.png")
        page.get_by_test_id("stSidebar").get_by_text("Metodología y calidad",exact=True).click()
        diagram=page.locator(".esquema-scroll")
        diagram.wait_for(timeout=30000)
        assert diagram.locator("svg rect").count()==8
        assert diagram.locator("svg path[marker-end]").count()==7
        diagram.screenshot(path=str(out/"esquema_estrella.png"))
        result["capturas"].append("esquema_estrella.png")
        coverage=page.locator(".st-key-csv_cobertura").get_by_role("button")
        coverage.wait_for(timeout=30000)
        with page.expect_download() as event:
            coverage.click()
        assert event.value.suggested_filename=="mef_muestra_cobertura.csv"
        assert Path(event.value.path()).read_bytes()==exportar(anual())
        result["csv_descargado_identico"]=True
        for width,height in [(1440,1100),(1024,900),(390,844)]:
            page.set_viewport_size({"width":width,"height":height})
            collapse=page.get_by_test_id("stSidebarCollapseButton").get_by_role("button")
            if width<600 and collapse.count() and collapse.is_visible():
                collapse.click()
            page.wait_for_timeout(600)
            assert not page.evaluate("document.documentElement.scrollWidth>window.innerWidth")
            # El diagrama se desplaza dentro de su propio contenedor, no ensancha la página.
            assert diagram.evaluate("el=>el.clientWidth<=window.innerWidth")
            result["resoluciones"].append({"ancho":width,"alto":height,"sin_desborde":True})
        page.get_by_test_id("stMain").evaluate("el=>el.scrollTop=0")
        page.screenshot(path=str(out/"metodologia_movil.png"))
        result["capturas"].append("metodologia_movil.png")
        b.close()
    result["estado"]="correcto"
    (out/"verificacion_visual_pulido.json").write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(result,ensure_ascii=True))
if __name__=="__main__":
    main()
