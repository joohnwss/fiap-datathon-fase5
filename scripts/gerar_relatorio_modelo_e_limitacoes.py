"""Gera um documento autônomo (HTML + PDF) com o conteúdo que antes vivia na
aba "Modelo e limitações" da aplicação — removida da navegação porque o
conteúdo é técnico demais para a ficha do dia a dia, mas continua útil para
a equipe (ex.: vídeo de apresentação do modelo).

Este script NUNCA treina, recalibra ou altera nenhum artefato oficial —
só LÊ `artifacts/`, `reports/metricas_modelagem.json` e
`config/ponto_atencao_operacional.json`, todos já congelados, e apresenta
o estado ATUAL (ponto operacional em destaque, não o ponto metodológico
original desatualizado que aparecia isoladamente antes).

Uso: `python scripts/gerar_relatorio_modelo_e_limitacoes.py`
Saída: `reports/relatorio_modelo_e_limitacoes.html` e `.pdf`.
"""
from __future__ import annotations

import base64
import html
import re
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))

import inferencia  # noqa: E402
import textos_aplicacao as textos  # noqa: E402

OUT_HTML = ROOT / "reports" / "relatorio_modelo_e_limitacoes.html"
OUT_PDF = ROOT / "reports" / "relatorio_modelo_e_limitacoes.pdf"


def _esc(valor) -> str:
    """Escapa primeiro (segurança), depois converte o `**negrito**` simples
    já usado nos textos internos (todos constantes do projeto, nunca
    entrada do usuário) para `<strong>` — sem isso, os asteriscos apareciam
    literalmente no documento renderizado."""
    escapado = html.escape(str(valor))
    return re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", escapado)


def _imagem_base64(caminho: Path) -> str | None:
    if not caminho.is_file():
        return None
    return base64.b64encode(caminho.read_bytes()).decode("ascii")


def montar_html(contexto: inferencia.ApplicationContext) -> str:
    metricas_teste = contexto.validation.metrics["temporal"]["metricas"]
    metricas_dev = contexto.validation.metrics["oof"]["metricas"]
    ponto_operacional = contexto.operational["metricas_temporais"]["ponto_operacional_adotado"]
    limiar_original = contexto.validation.threshold
    limiar_operacional = contexto.operational["ponto_atencao_operacional"]["limiar"]

    curvas_b64 = _imagem_base64(contexto.root / "reports" / "curvas_modelagem.png")
    bloco_curvas = ""
    if curvas_b64:
        bloco_curvas = (
            f'<img src="data:image/png;base64,{curvas_b64}" alt="Curvas agregadas de '
            'precisão-recall e calibração (teste temporal)" style="max-width:100%;margin-top:1rem;">'
            '<p class="legenda">Curvas agregadas de precisão-recall e calibração (teste temporal).</p>'
        )

    linhas_traducao = "".join(
        f"<li><strong>{_esc(simples)}</strong> <span class='termo'>(termo técnico: {_esc(tecnico)})</span></li>"
        for tecnico, simples in textos.TRADUCOES
    )
    linhas_limitacoes = "".join(f"<li>{_esc(lim)}</li>" for lim in textos.LIMITACOES_MODELO)

    gerado_em = datetime.now().strftime("%d/%m/%Y %H:%M")

    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<title>Modelo e limitações — Datathon Fase 5 (Associação Passos Mágicos)</title>
<style>
body {{ font-family: Arial, Helvetica, sans-serif; margin: 2.2rem; color: #22282C; line-height: 1.5; }}
h1 {{ font-size: 1.5rem; margin-bottom: 0.2rem; }}
h2 {{ font-size: 1.15rem; margin-top: 1.8rem; border-bottom: 0.06rem solid #ccc; padding-bottom: 0.3rem; }}
h3 {{ font-size: 1.02rem; margin-top: 1.2rem; }}
.subtitulo {{ color: #5a6268; margin-top: 0; }}
.grade {{ display: flex; gap: 1.2rem; flex-wrap: wrap; margin-top: 0.8rem; }}
.cartao {{ flex: 1; min-width: 260px; border: 0.06rem solid #E2DDD4; border-radius: 8px; padding: 1rem 1.2rem; }}
.aviso {{ background: #f4f4f4; padding: 0.75rem 1rem; margin-top: 0.75rem; border-left: 0.25rem solid #888; }}
.legenda {{ font-size: 0.85rem; color: #5a6268; }}
.termo {{ color: #5a6268; font-size: 0.9rem; }}
.rodape {{ margin-top: 2.2rem; font-size: 0.8rem; color: #5a6268; border-top: 0.06rem solid #E2DDD4; padding-top: 0.8rem; }}
table {{ border-collapse: collapse; width: 100%; margin-top: 0.6rem; }}
td, th {{ border: 0.06rem solid #ccc; padding: 0.4rem 0.6rem; text-align: left; font-size: 0.92rem; }}
</style>
</head>
<body>
<h1>Modelo e limitações</h1>
<p class="subtitulo">Datathon Fase 5 — Associação Passos Mágicos · gerado em {_esc(gerado_em)}</p>
<p class="aviso">{_esc(textos.AVISO_FINALIDADE_EDUCACIONAL)}</p>

<h2>Visão simples — situação atual (ponto operacional)</h2>
<div class="grade">
  <div class="cartao">
    <p>{_esc(textos.frase_precisao(ponto_operacional["precisao"]))}</p>
    <p>{_esc(textos.frase_recall(ponto_operacional["recall"]))}</p>
    <p><strong>Falsos positivos:</strong> {_esc(textos.EXPLICACAO_FALSO_POSITIVO)}</p>
    <p><strong>Falsos negativos:</strong> {_esc(textos.EXPLICACAO_FALSO_NEGATIVO)}</p>
  </div>
  <div class="cartao">
    <p><strong>Calibração:</strong> {_esc(textos.EXPLICACAO_CALIBRACAO)}</p>
    <p><strong>Teste temporal:</strong> {_esc(textos.EXPLICACAO_TESTE_TEMPORAL)}</p>
    <p>{_esc(textos.EXPLICACAO_TESTE_MAIS_REALISTA)}</p>
  </div>
</div>
<p class="legenda">Estes são os números do ponto de atenção OPERACIONAL, o que a aplicação usa
atualmente para sinalizar casos — não os números do ponto metodológico original (ver comparação
abaixo). O modelo em si não foi retreinado; só o valor de comparação da probabilidade mudou.</p>

<h2>Pontos de atenção: original e operacional</h2>
<div class="grade">
  <div class="cartao">
    <h3>{_esc(textos.TITULO_PONTO_METODOLOGICO_ORIGINAL)}</h3>
    <p>{_esc(textos.texto_ponto_metodologico_original(metricas_teste))}</p>
  </div>
  <div class="cartao">
    <h3>{_esc(textos.TITULO_PONTO_OPERACIONAL_ADOTADO)}</h3>
    <p>{_esc(textos.texto_ponto_operacional_adotado(ponto_operacional))}</p>
  </div>
</div>
<p class="legenda">A acurácia isolada não é um bom argumento a favor de nenhum dos dois pontos — ver
recall e precisão acima. {_esc(textos.AVISO_APROXIMACAO)} {_esc(textos.AVISO_CARATER_OBSERVACIONAL)}</p>

<h2>Detalhes técnicos</h2>
<table>
<tr><th>Modelo</th><td>{_esc(contexto.validation.frozen['configuracao']['algoritmo'])}</td></tr>
<tr><th>Sete preditores (ordem oficial)</th><td>{_esc(', '.join(inferencia.FEATURES))}</td></tr>
<tr><th>Ponto metodológico original (limiar) exato</th><td>{limiar_original:.12f}</td></tr>
<tr><th>Ponto de atenção operacional (limiar) exato</th><td>{limiar_operacional:.12f}</td></tr>
<tr><th>Desenvolvimento (2022→2023)</th>
    <td>AP {metricas_dev['average_precision']:.4f} · ROC-AUC {metricas_dev['roc_auc']:.4f} ·
        Precisão {metricas_dev['precisao']:.4f} · Recall {metricas_dev['recall']:.4f} ·
        Brier {metricas_dev['brier']:.4f}</td></tr>
<tr><th>Teste temporal (2023→2024), ponto original</th>
    <td>AP {metricas_teste['average_precision']:.4f} · ROC-AUC {metricas_teste['roc_auc']:.4f} ·
        Precisão {metricas_teste['precisao']:.4f} · Recall {metricas_teste['recall']:.4f} ·
        Brier {metricas_teste['brier']:.4f}</td></tr>
<tr><th>Teste temporal (2023→2024), ponto operacional</th>
    <td>Precisão {ponto_operacional['precisao']:.4f} · Recall {ponto_operacional['recall']:.4f} ·
        Acurácia {ponto_operacional['acuracia']:.4f} ·
        Acurácia balanceada {ponto_operacional['acuracia_balanceada']:.4f}
        <span class="legenda">(AP/ROC-AUC/Brier não mudam com o ponto de corte — dependem só da
        ordenação das probabilidades, não de onde o corte é feito.)</span></td></tr>
</table>
<p class="legenda">Comparação de recall (queda destacada): desenvolvimento (validação interna)
{metricas_dev['recall']:.4f} → teste temporal, ponto original {metricas_teste['recall']:.4f}
(subestimação observada: probabilidades previstas tenderam a ficar abaixo da fração real de eventos
em todas as faixas de calibração do teste temporal). O ponto operacional, definido só com os dados de
desenvolvimento e aplicado uma única vez ao teste temporal, recupera parte dessa queda
(recall {ponto_operacional['recall']:.4f}) sem qualquer novo treino.</p>
<p class="legenda">Separação temporal: desenvolvimento na transição
{_esc(contexto.validation.schema.get('treino', '2022→2023'))}; teste na transição seguinte
(2023→2024), sem nenhum reajuste do modelo ou do limiar original após o desenvolvimento. O ponto
operacional foi definido em auditoria posterior, exclusivamente com os dados de desenvolvimento.</p>
{bloco_curvas}
<p class="aviso">{_esc(textos.AVISO_FINALIDADE_EDUCACIONAL)}<br>{_esc(textos.AVISO_CARATER_OBSERVACIONAL)}</p>
<h3>Limitações</h3>
<ul>{linhas_limitacoes}</ul>

<h2>Termos técnicos (tradução)</h2>
<ul>{linhas_traducao}</ul>

<p class="rodape">Documento gerado automaticamente a partir dos artefatos oficiais congelados
(`artifacts/`, `reports/metricas_modelagem.json`, `config/ponto_atencao_operacional.json`) — não é
editado manualmente e não deve ser considerado desatualizado enquanto os artefatos não mudarem.
Reexecute `python scripts/gerar_relatorio_modelo_e_limitacoes.py` após qualquer nova decisão
operacional para atualizá-lo.</p>
</body>
</html>"""


def gerar() -> None:
    contexto = inferencia.prepare_application(root=ROOT)
    conteudo = montar_html(contexto)
    OUT_HTML.parent.mkdir(parents=True, exist_ok=True)
    OUT_HTML.write_text(conteudo, encoding="utf-8")

    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            navegador = p.chromium.launch()
            pagina = navegador.new_page()
            pagina.goto(OUT_HTML.resolve().as_uri())
            pagina.pdf(path=str(OUT_PDF), format="A4", margin={"top": "1.5cm", "bottom": "1.5cm",
                                                                "left": "1.5cm", "right": "1.5cm"})
            navegador.close()
        print(f"Gerado: {OUT_HTML} e {OUT_PDF}")
    except Exception as erro:  # noqa: BLE001 — PDF é um extra; o HTML já foi salvo com sucesso.
        print(f"Gerado: {OUT_HTML} (PDF não gerado: {erro})")


if __name__ == "__main__":
    gerar()
