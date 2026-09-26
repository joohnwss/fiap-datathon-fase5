"""Smoke/validação visual da ficha individual em Chromium headless."""
from __future__ import annotations

import json
import os
from pathlib import Path

from playwright.sync_api import Page, expect, sync_playwright

URL = os.environ.get("STREAMLIT_TEST_URL", "http://127.0.0.1:8507")
CHROME = Path.home() / "AppData/Local/ms-playwright/chromium-1228/chrome-win64/chrome.exe"


def abrir_ficha(page: Page, largura: int) -> None:
    page.set_viewport_size({"width": largura, "height": 1000})
    page.goto(URL, wait_until="domcontentloaded", timeout=60_000)
    page.get_by_role("tab", name="Avaliar um caso").wait_for(timeout=30_000)
    page.get_by_role("tab", name="Avaliar um caso").click()
    page.get_by_text("Campos marcados com * são obrigatórios", exact=False).wait_for(timeout=30_000)


def selecionar(page: Page, rotulo: str, opcao: str) -> None:
    page.get_by_role("combobox", name=rotulo, exact=True).click()
    opcoes = page.get_by_role("option")
    opcoes.first.wait_for(timeout=10_000)
    codigo = opcao.split()[0]
    for indice, texto in enumerate(opcoes.all_inner_texts()):
        if texto.strip().startswith(codigo):
            opcoes.nth(indice).click()
            page.wait_for_timeout(1_000)
            return
    raise AssertionError(f"Opção {opcao!r} ausente em {opcoes.all_inner_texts()!r}")


def sem_overflow(page: Page) -> bool:
    return not page.evaluate("document.documentElement.scrollWidth > window.innerWidth")


def main() -> None:
    resultados: dict[str, object] = {"viewports": {}, "cenarios": {}}
    erros_console: list[str] = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, executable_path=str(CHROME))
        page = browser.new_page()
        page.on("console", lambda msg: erros_console.append(msg.text) if msg.type == "error" else None)
        page.on("pageerror", lambda erro: erros_console.append(str(erro)))

        for largura in (1440, 768, 390):
            for tema in ("Claro", "Escuro"):
                abrir_ficha(page, largura)
                page.get_by_role("radio", name=tema, exact=True).check(force=True)
                page.wait_for_timeout(500)
                chave = f"{largura}_{tema.lower()}"
                resultados["viewports"][chave] = {
                    "sem_overflow": sem_overflow(page),
                    "botao_desabilitado_vazio": page.get_by_role(
                        "button", name="Gerar estimativa e relatório"
                    ).is_disabled(),
                    "cinco_abas": page.get_by_role("tab").count() == 5,
                }

        abrir_ficha(page, 1440)
        page.get_by_role("textbox", name="Idade em anos completos *").fill("8")
        page.get_by_role("textbox", name="Idade em anos completos *").press("Enter")
        page.wait_for_timeout(1_000)
        corpo = page.locator("body").inner_text()
        resultados["cenarios"]["idade_8"] = "fronteira entre fases" in corpo and "Alfa" in corpo and "Fase 1" in corpo

        page.get_by_role("textbox", name="Idade em anos completos *").fill("14")
        page.get_by_role("textbox", name="Idade em anos completos *").press("Enter")
        page.wait_for_timeout(1_000)
        selecionar(page, "Fase atual *", "2 — Fase 2")
        selecionar(page, "Fase ideal *", "4 — Fase 4")
        page.wait_for_timeout(400)
        resultados["cenarios"]["idade_14_fase_2"] = (
            "Diferença entre a fase atual e a fase ideal: −2" in page.locator("body").inner_text()
            or "Diferença entre a fase atual e a fase ideal: -2" in page.locator("body").inner_text()
        )

        page.get_by_role("radio", name="Quero calcular pelas três notas").check(force=True)
        page.wait_for_timeout(1_000)
        page.get_by_role("textbox", name="Nota de Matemática").fill("0")
        page.get_by_role("textbox", name="Nota de Matemática").press("Enter")
        page.get_by_role("textbox", name="Nota de Português").fill("7,5")
        page.get_by_role("textbox", name="Nota de Português").press("Enter")
        page.get_by_role("textbox", name="Nota de Inglês").fill("7.5")
        page.get_by_role("textbox", name="Nota de Inglês").press("Enter")
        page.wait_for_timeout(1_000)
        resultados["cenarios"]["notas_zero_e_decimais"] = "IDA calculado: 5.00" in page.locator("body").inner_text()

        page.get_by_role("radio", name="Quero calcular pelas 6 perguntas").check(force=True)
        page.wait_for_timeout(400)
        primeira_inicial = page.get_by_role("combobox", name="1. Como se sente consigo mesmo?")
        primeira_inicial.click()
        resultados["cenarios"]["iaa_fase_inicial"] = page.get_by_role("option", name="D", exact=True).count() == 0
        page.keyboard.press("Escape")

        selecionar(page, "Fase atual *", "3 — Fase 3")
        page.wait_for_timeout(400)
        primeira = page.get_by_text("1. Como se sente consigo mesmo?", exact=True).locator(
            "xpath=ancestor::*[@data-testid='stSelectbox']"
        )
        primeira.locator("input").click()
        resultados["cenarios"]["iaa_fase_posterior"] = page.get_by_role("option", name="D", exact=True).count() == 1
        page.keyboard.press("Escape")

        abrir_ficha(page, 1440)
        page.get_by_role("button", name="Preencher exemplo sintético").click()
        gerar = page.get_by_role("button", name="Gerar estimativa e relatório")
        expect(gerar).to_be_enabled(timeout=30_000)
        gerar.click()
        page.get_by_text("Resultado", exact=True).wait_for(timeout=30_000)
        resultados["cenarios"]["ficha_completa_resultado"] = page.get_by_text("Estimativa", exact=True).count() >= 1
        resultados["cenarios"]["relatorio"] = page.get_by_role(
            "button", name="Baixar relatório (.html)"
        ).count() == 1
        resultados["cenarios"]["sem_overflow_resultado"] = sem_overflow(page)

        browser.close()

    resultados["erros_console"] = erros_console
    print(json.dumps(resultados, ensure_ascii=False))
    assert not erros_console, erros_console
    assert all(all(item.values()) for item in resultados["viewports"].values())
    assert all(resultados["cenarios"].values())


if __name__ == "__main__":
    main()
