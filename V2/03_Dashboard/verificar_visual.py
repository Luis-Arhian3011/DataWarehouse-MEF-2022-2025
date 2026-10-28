"""Prueba de navegador opcional. Chrome local, sin descargar navegadores."""
import hashlib,json,os,time
from pathlib import Path
from urllib.request import urlopen
from playwright.sync_api import sync_playwright
import datos as d
ROOT=Path(__file__).resolve().parent
URL=os.environ.get("MEF_V2_URL","http://127.0.0.1:8502")
def main():
    assert urlopen(URL+"/_stcore/health",timeout=10).status==200
    stamp=str(time.time_ns())
    result=dict(http_health=200,views=[],page_errors=[],screenshots=[],url=URL)
    headings={
        "Resumen ejecutivo":"El presupuesto de la muestra, en perspectiva",
        "Presupuesto anual":"Presupuesto anual y calidad del denominador",
        "Evolución mensual":"Del ejercicio anual a los doce meses",
        "Comparación de ejercicios":"Comparar ejercicios con cobertura explícita",
        "Análisis por dimensiones":"Explorar la composición del presupuesto",
        "Metodología y calidad":"Trazabilidad, método y límites"}
    with sync_playwright() as p:
        browser=p.chromium.launch(channel="chrome",headless=True)
        page=browser.new_page(viewport={"width":1440,"height":1050},device_scale_factor=1)
        page.on("pageerror",lambda error:result["page_errors"].append(str(error)))
        page.goto(URL)
        page.get_by_role("heading",name=headings["Resumen ejecutivo"],exact=True).wait_for(timeout=45000)
        page.locator(".kpi").first.wait_for()
        page.locator("[data-testid=stPlotlyChart] .js-plotly-plot").first.wait_for(timeout=45000)
        for section,heading in headings.items():
            if section!="Resumen ejecutivo":
                page.get_by_test_id("stSidebar").get_by_text(section,exact=True).click()
            page.get_by_role("heading",name=heading,exact=True).wait_for(timeout=30000)
            page.wait_for_timeout(500)
            assert page.get_by_test_id("stException").count()==0
            assert page.get_by_text("La consulta no pudo completarse.",exact=False).count()==0
            assert page.get_by_text("No se pudo conectar con V2.",exact=False).count()==0
            result["views"].append(section)
            if section in ("Resumen ejecutivo","Evolución mensual"):
                name=("escritorio_resumen_" if section=="Resumen ejecutivo" else "escritorio_mensual_")+stamp+".png"
                page.locator("[data-testid=stMain]").evaluate("element => element.scrollTop=0")
                page.screenshot(path=str(ROOT.parent/"05_Pruebas_y_Evidencias/ejecuciones"/name),full_page=True)
                result["screenshots"].append(name)
        # CSV descargado realmente a traves del navegador; comparacion byte a byte.
        page.get_by_test_id("stSidebar").get_by_text("Presupuesto anual",exact=True).click()
        page.get_by_role("heading",name=headings["Presupuesto anual"],exact=True).wait_for()
        button=page.get_by_role("button",name="Descargar agregados · CSV",exact=True)
        with page.expect_download() as event:button.click()
        download=event.value
        data=Path(download.path()).read_bytes()
        fields=["anio","hechos","entidades","pia","pim","devengado","girado","ejecucion_pct"]
        assert data==d.exportar(d.anual()[fields]),"CSV descargado distinto de los agregados Decimal"
        result["csv"]=dict(name=download.suggested_filename,bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),values_exact=True)
        page.get_by_test_id("stSidebar").get_by_text("Resumen ejecutivo",exact=True).click()
        page.get_by_role("heading",name=headings["Resumen ejecutivo"],exact=True).wait_for()
        page.wait_for_timeout(1200)
        collapse=page.get_by_test_id("stSidebarCollapseButton").get_by_role("button")
        if collapse.count() and collapse.is_visible():collapse.click()
        page.set_viewport_size({"width":390,"height":844})
        page.locator("[data-testid=stMain]").evaluate("element => element.scrollTop=0")
        page.wait_for_timeout(1200)
        result["mobile_horizontal_overflow"]=page.evaluate("document.documentElement.scrollWidth > window.innerWidth")
        assert not result["mobile_horizontal_overflow"]
        name="movil_resumen_"+stamp+".png"
        page.screenshot(path=str(ROOT.parent/"05_Pruebas_y_Evidencias/ejecuciones"/name),full_page=True)
        result["screenshots"].append(name)
        assert not result["page_errors"]
        browser.close()
    result["status"]="correcto"
    with (ROOT.parent/"05_Pruebas_y_Evidencias/ejecuciones"/("navegador_"+stamp+".json")).open("x",encoding="utf-8") as stream:
        json.dump(result,stream,ensure_ascii=False,indent=2)
    print(json.dumps(result,ensure_ascii=True))
if __name__=="__main__":main()
