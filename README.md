# Tech Challenge Fase 5 — Associação Passos Mágicos

Grupo: Victor, Jônatas, Izadora, Laura e Lucas.

## Sobre o projeto

A Associação Passos Mágicos atua na transformação da vida de crianças e
jovens em situação de vulnerabilidade social por meio da educação. Todos os
anos, a instituição aplica o PEDE (Pesquisa Extensiva do Desenvolvimento
Educacional), uma avaliação multidimensional dos estudantes atendidos — que
reúne indicadores de aprendizagem, engajamento, autoavaliação, aspectos
psicossociais e trajetória escolar.

Este projeto parte da base do PEDE de 2022 a 2024 para responder onze
perguntas de negócio sobre a trajetória dos estudantes e treinar um modelo
que estima o risco de um(a) estudante entrar em defasagem escolar no ano
seguinte, a partir de sete indicadores já usados pela instituição. O
resultado é entregue em três formatos complementares:

- um **notebook** que apresenta a metodologia, os resultados e as
  limitações de forma reproduzível, sem tocar em dados privados;
- uma **aplicação Streamlit** para o dia a dia da equipe pedagógica, com um
  panorama das onze perguntas respondidas e uma ficha para avaliar um caso
  individual;
- um **relatório sobre o modelo e suas limitações**, em HTML/PDF, para
  consulta da equipe e apoio à apresentação.

A aplicação está publicada em
**[datathon-fase5-grupo44.streamlit.app](https://datathon-fase5-grupo44.streamlit.app)**.

## Como rodar localmente

Requer Python 3.12. Os arquivos originais da base (`DATATHON/`) não são
distribuídos neste repositório — sem eles, os passos de auditoria e
preparação abaixo não têm o que ler, mas o notebook, a aplicação e o
relatório do modelo funcionam normalmente a partir dos artefatos já
publicados.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m unittest discover -s tests -p "test_*.py" -v
```

No Linux/macOS, use `.venv/bin/python` no lugar de
`.\.venv\Scripts\python.exe`.

Para abrir a aplicação:

```powershell
.\.venv\Scripts\python.exe -m streamlit run streamlit_app.py
```

Para reproduzir a auditoria e a preparação dos dados a partir dos
originais (exige `DATATHON/` local):

```powershell
.\.venv\Scripts\python.exe src/auditoria_inicial.py
.\.venv\Scripts\python.exe src/preparacao_longitudinal.py
.\.venv\Scripts\python.exe src/preparacao_coortes.py
.\.venv\Scripts\python.exe src/modelagem.py
.\.venv\Scripts\python.exe src/analises_negocio.py
.\.venv\Scripts\python.exe src/verificar_entrega.py
```

Execute a partir da raiz do projeto, nessa ordem: a preparação consome a
base longitudinal já auditada, e a modelagem consome as coortes já
preparadas. O script de modelagem treina e seleciona o modelo apenas sobre
os dados de 2022→2023; a avaliação sobre 2023→2024 acontece uma única vez
e fica registrada — rodar de novo apenas confere os resultados já
gravados, sem reabrir a escolha do modelo ou do limiar.

## O que tem em cada pasta

| Pasta | Conteúdo |
| --- | --- |
| `src/` | Todo o código: preparação dos dados, modelagem, análises de negócio, ficha individual e a lógica da aplicação. |
| `streamlit_app.py` | A aplicação (interface e navegação; a lógica fica em `src/`). |
| `notebooks/` | O notebook público, que lê só a camada de dados agregados em `reports/public/`. |
| `artifacts/` | O modelo treinado, seu schema e a configuração congelada no fim da avaliação. |
| `config/` | A configuração do ponto de atenção usado hoje pela aplicação (ver abaixo). |
| `reports/` | Relatórios e métricas — os agregados em `reports/public/` e `reports/figures/` são as fontes que a aplicação e o notebook usam; `reports/experimental/` guarda a análise que levou à decisão do ponto de atenção. |
| `docs/` | Metodologia, decisões de projeto e o histórico de tarefas do grupo. |
| `tests/` | Suíte de testes automatizados (516 testes na versão atual). |
| `assets/` | Identidade visual usada na aplicação (logo e paleta da Associação Passos Mágicos). |

Os originais da base (`DATATHON/`) e as bases derivadas com identificação
por estudante (`local_data/`, `local_recovery/`) não são versionados —
tudo o que a aplicação e o notebook usam é agregado e público.

## Trabalhando com os dados brutos (local_data/)

Quem tiver `local_data/` localmente (gerado pelos passos de auditoria e
preparação acima) pode ler a base completa assim:

```python
import json
from pathlib import Path

registros = [json.loads(linha) for linha in
             Path("local_data/base_longitudinal.jsonl").read_text(encoding="utf-8").splitlines()]
```

O JSONL é a representação completa e conserva a diferença entre ausência
(`null`) e zero; datas originais mantêm seus tipos Excel/Python, sem
reinterpretação a partir do texto. Nas coortes, os CSV não preservam tipos
categóricos — para obter X com fase categórica e números anuláveis, use
`supervised_matrices` de `src/preparacao_coortes.py` sobre os registros do
JSONL filtrados por `metadados.coorte`.

Algumas regras que a preparação dos dados segue, e que quem for auditar ou
estender o projeto deve conhecer:

- Um registro por linha anual, mesmo quando algum indicador está
  indisponível — nenhuma ligação por nome ou posição da linha, só por RA.
- RA ausente, vazio ou duplicado é sinalizado, nunca descartado
  silenciosamente.
- O IPP não existe em 2022 — isso é estrutural, não um erro de leitura.
  Valores como erro de Excel, "INCLUIR" ou espaço em branco preservam o
  motivo da ausência; nunca viram zero.
- Fases alfanuméricas são extraídas explicitamente; a Fase 9 não tem
  significado atribuído.
- Os oito indicadores ficam na faixa 0–10 sem corte nem arredondamento;
  INDE, Pedra e idade não são "corrigidos" por suposição.
- Quando não há observação no ano seguinte, o desfecho fica como
  desconhecido — a auditoria é descritiva, e o recorte usado pelo modelo
  está definido em `docs/contrato_metodologico.md`.

## O modelo e o ponto de atenção

O modelo foi treinado e avaliado uma única vez, sobre 2022→2023 para
desenvolvimento e 2023→2024 para teste — sem repetir essa avaliação desde
então. Os detalhes de treino, métricas e limitações estão em
`reports/relatorio_modelagem.md` e no relatório
`reports/relatorio_modelo_e_limitacoes.html` (também disponível em PDF).

A aplicação usa esse mesmo modelo, sem retreinar nem recalibrar nada. A
única mudança depois da avaliação original foi na **regra de decisão**:
em vez do limiar que privilegiava sensibilidade nos dados de
desenvolvimento, a aplicação passou a usar um ponto de corte com melhor
equilíbrio entre acertar mais casos reais e não gerar alarmes demais —
escolhido só com dados já conhecidos, nunca olhando o teste na hora de
decidir. Essa decisão está registrada em
`config/ponto_atencao_operacional.json`, com a trilha de análise completa
em `reports/experimental/`. O ponto de corte original continua preservado
e documentado, para quem quiser conferir a avaliação tal como ela foi
feita.

## Privacidade

Nenhum dado individual (nome, RA, data de nascimento) é versionado neste
repositório ou exibido pela aplicação. As análises publicadas usam apenas
números agregados, com supressão de qualquer grupo menor que dez
estudantes. A ficha individual da aplicação não salva, registra nem envia
a nenhum serviço externo os dados que o(a) usuário(a) digita — eles
existem só durante a sessão do navegador.

## Mais detalhes

- Metodologia e definição do problema: `docs/contrato_metodologico.md`
- Decisão de uso do modelo pela aplicação: `docs/decisao_modelo_operacional.md`
- Identidade visual: `docs/identidade_visual.md`
- Roteiro de testes da aplicação: `docs/testes_aplicacao.md`
- Histórico de tarefas do grupo: `docs/TASKS.md`
