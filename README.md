# Tech Challenge Fase 5 — Associação Passos Mágicos

Grupo: Victor, Jonatas, Izadora, Laura e Lucas.

## Estado do projeto

Auditoria corrigida e primeira base longitudinal conservadora dos anos 2022–2024,
usando somente `DATATHON/BASE DE DADOS PEDE 2024 - DATATHON.xlsx`.
O [contrato metodológico](docs/contrato_metodologico.md) está aprovado e a
[preparação das coortes](reports/relatorio_coortes_modelagem.md) está concluída.
O treinamento ainda não foi iniciado. O [status do projeto](docs/status_projeto.md)
reúne o marco concluído, as pendências e as instruções para continuidade pelo grupo.
Nenhum modelo foi treinado e nenhuma aplicação, apresentação ou publicação foi criada.

Resultados e pendências: [relatório de preparação](reports/relatorio_preparacao_inicial.md).
Evidência das verificações: [verificação final](reports/verificacao_final.md).
O enunciado completo e as evidências de leitura textual/visual estão documentados em
[evidências documentais](docs/evidencias_documentais.md). Os requisitos finais incluem
análise de negócio, notebook preditivo, GitHub, apresentação, Streamlit Community Cloud
e vídeo de até cinco minutos; essas entregas ficam para rodadas posteriores.

## Execução reproduzível

Requer Python 3.12 e os originais locais. A pasta `DATATHON/` não é distribuída no Git.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m unittest discover -s tests -p "test_*.py" -v
.\.venv\Scripts\python.exe src/auditoria_inicial.py
.\.venv\Scripts\python.exe src/preparacao_longitudinal.py
.\.venv\Scripts\python.exe src/preparacao_coortes.py
.\.venv\Scripts\python.exe src/verificar_entrega.py
```

Execute a partir da raiz do projeto. No Linux/macOS, use `.venv/bin/python`
no lugar de `.\.venv\Scripts\python.exe`. A preparação é independente da execução
prévia da auditoria. As coortes consomem a base longitudinal já preparada;
a verificação final confere as três etapas: use a ordem acima.

Cada execução de auditoria/preparação longitudinal/coortes cria uma cópia datada somente das saídas
que serão regeneradas, em `local_recovery/`. Isso inclui as saídas individuais
locais, quando existentes. Não copia `.venv` nem os originais de `DATATHON/`.

A integridade atual compara os hashes antes/depois da execução e verifica as
saídas e documentos manuais pelos metadados. A comparação histórica é opcional:
usa `historical_baseline`, transportado nos metadados, e indica “não disponível”
quando não há baseline. Nenhuma pasta histórica de recuperação é necessária.
Após clonar o projeto, disponibilize os originais em `DATATHON/`, instale as
dependências e execute os comandos acima para regenerar os dados locais.

Os comandos registrados nos relatórios usam a forma portátil `python src/arquivo.py`;
os metadados públicos usam caminhos relativos e `working_directory` igual a `.`.

Os scripts somente leem `DATATHON`. Registram data/hora UTC real, comando,
versões, hashes de fontes, código, testes e saídas; comparam fontes antes/depois
e, separadamente, o inventário da execução anterior. Nenhum comando faz commit ou push.

## Estrutura e saídas

| Caminho | Conteúdo |
| --- | --- |
| `src/dados_pede.py` | Leitura com tipo Excel e linha física, classificação de conteúdo, extração de fases e derivações conservadoras compartilhadas. |
| `src/auditoria_inicial.py` | Auditoria de todas as linhas/colunas, indicadores, cadastro e transições por RA. |
| `src/preparacao_longitudinal.py` | Grava base individual e relê fonte/saídas para validar a correspondência integral. |
| `src/preparacao_coortes.py` | Prepara as duas transições temporais, separa X/y da auditoria privada e valida elegibilidade, contagens e saídas. |
| `src/rastreabilidade.py` | Cópia de recuperação, inventários, hashes e proteção contra versionamento de dados individuais. |
| `src/relatorios_preparacao.py` | Mapa e relatórios agregados regeneráveis. |
| `src/verificar_entrega.py` | Executa testes e confere hashes, registros, arquivos serializados e exclusões do Git; produz evidência final. |
| `tests/test_auditoria_regressao.py` | Quatro testes existentes preservados. |
| `tests/test_preparacao_regressao.py` | Regressões sobre códigos, erros Excel, tipos após 20 linhas, datas, duplicidades, junções e linha original. |
| `tests/test_portabilidade_regressao.py` | Execução sem recuperação histórica, caminhos públicos, RA fora da primeira coluna, fases de origem e documentos manuais. |
| `tests/test_coortes_regressao.py` | Alvo, ausências, fases, proteção de X, separação temporal, serialização e referências na fonte real quando disponível. |
| `local_data/base_longitudinal.jsonl` | Base completa: valores originais, tipos de cada célula, derivados, qualidade e procedência. Um objeto por registro anual. |
| `local_data/base_longitudinal.csv` | Visão plana derivada. O bloco completo de originais permanece no JSONL. |
| `local_data/auditoria/` | Detalhes individuais de células, cadastro e transições, além do resumo agregado em JSON. |
| `local_data/coorte_{desenvolvimento,teste_temporal}.csv` | Sete preditores e y, somente transições supervisionadas, sem identificadores. |
| `local_data/X_{desenvolvimento,teste_temporal}.csv` e `local_data/y_{desenvolvimento,teste_temporal}.csv` | Matrizes X e alvos y separados, alinhados por posição, sem índice exportado. |
| `local_data/coortes_modelagem.jsonl` | Elegíveis na origem, inclusive alvo desconhecido; blocos separados de chave privada, X, y e metadados de auditoria. |
| `reports/relatorio_coortes_modelagem.md` | Fluxos, exclusões, cobertura, distribuição do alvo e validações agregadas. |
| `reports/metadados_coortes.json` | Schema, critérios, contagens e hashes de entradas, saídas, fontes, código e documentos. |
| `docs/mapa_campos.md` | Mapa de todas as colunas por ano/posição e dicionário dos campos preparados. |
| `reports/relatorio_auditoria_inicial.md` | Auditoria agregada corrigida. |
| `reports/relatorio_preparacao_inicial.md` | Resultado da preparação, contagens de qualidade, validações e pendências. |
| `artifacts_meta.json` | Metadados agregados da auditoria. |
| `reports/metadados_preparacao.json` | Metadados agregados da preparação; exceção explícita ao ignore de JSON em reports. |
| `reports/verificacao_final.md` | Resultado efetivo dos testes e das verificações após geração. |

## Leitura da base

```python
import json
from pathlib import Path

registros = [json.loads(linha) for linha in
             Path("local_data/base_longitudinal.jsonl").read_text(encoding="utf-8").splitlines()]
```

O JSONL é a representação completa e conserva a diferença entre ausência (`null`)
e zero. Datas originais usam ISO junto de seus tipos Excel/Python; o tipo não é
inferido de novo a partir do texto. RA não deve ser convertido automaticamente em número.

Nas coortes, os CSV não preservam tipos categóricos. Para obter X com fase
categórica e números anuláveis, usar `supervised_matrices` de
`src/preparacao_coortes.py` sobre os registros do JSONL filtrados por
`metadados.coorte`. A função exclui y desconhecido e retorna X e y alinhados.
Os CSV de X contêm exclusivamente IDA, IEG, IAA, IPS, IPV, fase e defasagem de
origem; nenhuma chave de auditoria pertence a X. Ausências permanecem vazias
no CSV e `null` no JSONL, sem imputação. Todos esses arquivos são privados.

## Regras de preservação e limites

- Um registro por linha anual, inclusive alunos com indicadores indisponíveis. Nenhuma ligação por nome ou posição da linha.
- RA ausente/vazio e duplicado são sinalizados separadamente; duplicidade bloqueia junções, sem excluir registros silenciosamente.
- IPP ausente em 2022 é estrutural. Erros Excel, INCLUIR, espaços e outros textos conservam os motivos de indisponibilidade; não recebem zero.
- Fases alfanuméricas são extraídas explicitamente; números das séries entre parênteses são ignorados. Fase 9 permanece sem significado atribuído.
- Defasagem registrada, diferença entre códigos de fase e IAN esperado são campos/testes separados. Equivalência curricular entre anos permanece pendente.
- Faixa operacional 0–10 sinaliza os oito indicadores, sem cortar ou arredondar. INDE, pedras e idades não são corrigidos por suposição.
- Ausência de observação futura gera desfecho desconhecido. As transições da auditoria são descritivas; o recorte do futuro modelo está definido no contrato metodológico.
- `phase_origin_counts` conta todos os elegíveis; `phase_origin_found_counts` conta os encontrados no destino, sempre pela fase na origem.
- Os documentos manuais têm hashes conferidos durante as execuções. O histórico de decisões foi mantido, com seção datada para o contrato aprovado; o contrato e o status registram a metodologia vigente e a continuidade.
- Relatórios automáticos são identificados como regeneráveis. O registro substantivo de leitura visual fica separado em `docs/evidencias_documentais.md`.
- Os antigos apontadores `documentacao_revisao.md`, `revisao_auditoria_gerada.md` e `registro_decisoes_gerado.md` foram arquivados em uma pasta datada de `local_recovery/` e deixaram de ser regenerados. Consulte diretamente o mapa, as evidências e os relatórios substantivos.

`DATATHON/`, `local_data/`, `local_recovery/` e `.venv/` são ignoradas pelo Git. Os scripts
verificam isso antes de gravar dados individuais. Documentos públicos contêm
agregados, sem amostras de nomes, RAs ou datas completas de nascimento.

A revisão visual realizada em 15/09/2026 utilizou pypdfium2 5.13.0 e Pillow 12.3.0 para
renderizar PDFs e inspecionar imagens. Essas dependências foram usadas na revisão
documental; não são necessárias para executar auditoria, preparação ou testes.
