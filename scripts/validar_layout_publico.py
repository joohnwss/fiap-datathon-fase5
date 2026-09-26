"""Smoke test visual do navegador público em desktop, tablet e mobile.

Valida 1.440 px, 768 px e 390 px, checando em cada largura a presença de
gráfico, legenda, tabela de principais números, bloco de conclusão e
ausência de overflow/corte, além da navegação entre perguntas.
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path

from playwright.sync_api import sync_playwright


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "reports" / "validacao_visual_publica"
URL = os.environ.get("STREAMLIT_TEST_URL", "http://127.0.0.1:8507")


def validar_largura(page, largura: int, nome: str) -> dict:
    page.set_viewport_size({"width": largura, "height": 1000})
    page.goto(URL, wait_until="domcontentloaded", timeout=60_000)
    page.get_by_role("tab", name="Panorama e resultados").wait_for(timeout=30_000)
    page.get_by_role("tab", name="Panorama e resultados").click()
    page.get_by_text("Explore as 11 perguntas", exact=True).wait_for(timeout=30_000)
    # Deixa o gráfico Plotly e a tabela terminarem de pintar antes de medir.
    page.locator("div.js-plotly-plot").first.wait_for(timeout=30_000)
    page.wait_for_timeout(1_000)

    overflow = page.evaluate("document.documentElement.scrollWidth > window.innerWidth")
    cortados = page.evaluate(
        """
        [...document.querySelectorAll('button')].filter(el => {
          const r = el.getBoundingClientRect();
          return r.left < -0.5 || r.right > window.innerWidth + 0.5;
        }).map(el => el.innerText)
        """
    )
    tem_grafico = page.locator("div.js-plotly-plot").count() > 0
    tem_tabela = page.get_by_text("Principais números", exact=True).count() > 0
    tem_conclusao = page.get_by_text("Conclusão da análise", exact=True).count() > 0
    tem_tooltip_ativo = page.evaluate(
        "!!document.querySelector('div.js-plotly-plot') && "
        "document.querySelector('div.js-plotly-plot').style.overflow !== undefined"
    )
    graficos_q1 = page.locator("div.js-plotly-plot")
    quantidade_graficos_q1 = graficos_q1.count()
    grafico_sexo = graficos_q1.nth(2)
    grafico_sexo.scroll_into_view_if_needed()
    caixa_grafico = grafico_sexo.bounding_box()
    grafico_sexo_cortado = (
        caixa_grafico is None
        or caixa_grafico["x"] < -0.5
        or caixa_grafico["x"] + caixa_grafico["width"] > largura + 0.5
    )
    grafico_sexo.screenshot(path=str(OUTPUT / f"q1_sexo_{nome}.png"))
    captura = OUTPUT / f"{nome}.png"
    page.screenshot(path=str(captura), full_page=True)
    return {
        "largura": largura, "overflow_horizontal": overflow, "botoes_cortados": cortados,
        "tem_grafico_interativo": tem_grafico, "tem_tabela_principais_numeros": tem_tabela,
        "tem_bloco_conclusao": tem_conclusao, "modebar_plotly_presente_no_dom": tem_tooltip_ativo,
        "quantidade_graficos_q1": quantidade_graficos_q1,
        "grafico_sexo_cortado": grafico_sexo_cortado,
    }


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        executavel = (
            Path.home()
            / "AppData/Local/ms-playwright/chromium-1228/chrome-win64/chrome.exe"
        )
        browser = p.chromium.launch(headless=True, executable_path=str(executavel))
        page = browser.new_page(viewport={"width": 1440, "height": 1000})
        desktop = validar_largura(page, 1440, "desktop_1440")

        texto_q1 = page.locator("body").inner_text()
        assert "46,2%" in texto_q1
        assert "moderada e severa foram reunidas" in texto_q1
        assert "None" not in texto_q1
        assert "Por que esta pergunta importa" in texto_q1
        assert "Conclusão da análise" in texto_q1
        assert page.get_by_text("Pergunta 1 de 11", exact=True).count() >= 1
        assert page.get_by_role("button", name="← Pergunta anterior").is_disabled()
        page.get_by_text("Análises complementares da pergunta 1 (novos recortes)", exact=True).click()
        page.get_by_text(re.compile(r"7 a 10 anos"), exact=False).first.wait_for(timeout=10_000)
        texto_q1_expandido = page.locator("body").inner_text()
        assert "faixa etária aproximada" in texto_q1_expandido
        assert "7 a 10 anos" in texto_q1_expandido
        # Q1: composição anual, média segura do IAN e comparação binária por
        # sexo. O terceiro gráfico precisa exibir os seis sexo×ano, seus
        # denominadores e o aviso de agregação.
        graficos_q1 = page.locator("div.js-plotly-plot")
        assert graficos_q1.count() == 3
        texto_terceiro_grafico = graficos_q1.nth(2).inner_text()
        for trecho in ("F = feminino", "M = masculino", "n=457", "n=403", "n=546", "n=468", "n=623", "n=533"):
            assert trecho in texto_terceiro_grafico, trecho
        assert "moderada e severa" in texto_terceiro_grafico
        page.get_by_role("button", name="Próxima pergunta →").click()
        page.get_by_text("Pergunta 2 de 11", exact=True).first.wait_for(timeout=30_000)
        assert "O desempenho acadêmico médio" in page.locator("body").inner_text()

        seletor = page.get_by_text(
            "Escolha uma das 11 perguntas", exact=True
        ).locator("xpath=ancestor::*[@data-testid='stSelectbox']")
        assert seletor.count() == 1
        assert "Escolha uma das 11 perguntas" in seletor.inner_text()
        seletor.locator("input").click()
        page.get_by_role("option", name=re.compile(r"^11\.")).click()
        page.get_by_text("Pergunta 11 de 11", exact=True).first.wait_for(timeout=30_000)
        assert page.get_by_role("button", name="Próxima pergunta →").is_disabled()

        tablet = validar_largura(page, 768, "tablet_768")
        mobile = validar_largura(page, 390, "mobile_390")
        browser.close()

    resultado = {"desktop": desktop, "tablet_768": tablet, "mobile": mobile}
    print(json.dumps(resultado, ensure_ascii=False))
    for nome, r in resultado.items():
        assert not r["overflow_horizontal"] and not r["botoes_cortados"], (nome, r)
        assert r["tem_grafico_interativo"], (nome, "sem gráfico interativo")
        assert r["tem_tabela_principais_numeros"], (nome, "sem tabela de principais números")
        assert r["tem_bloco_conclusao"], (nome, "sem bloco de conclusão")
        assert r["quantidade_graficos_q1"] == 3, (nome, "Q1 sem os três gráficos")
        assert not r["grafico_sexo_cortado"], (nome, "gráfico por sexo cortado")


if __name__ == "__main__":
    main()
