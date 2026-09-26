# Testes da aplicação e privacidade (TASK 010, ampliado nas subetapas de
aprimoramento da interface anteriores à TASK 011)

Documento da TASK 010 (FASE 4 do plano em [TASKS.md](TASKS.md)), ampliado em
subetapas locais sucessivas: (a) reorganização da interface em cinco áreas,
com linguagem para professores(as) e profissionais da ONG; (b) storytelling
institucional e painel "Panorama e resultados" (ETAPA B), com as 11
perguntas de negócio, os dez gráficos oficiais e explicações sobre
idade/notas/Pedras/Ponto de Virada; (c) ficha de acompanhamento em "Avaliar
um caso" (calculadoras de defasagem/IAN, relatório em memória — 25/09/2026),
que absorveu e removeu a antiga aba "Plano de acompanhamento"; (d) revisão
de identidade visual (25/09/2026 — ver `docs/identidade_visual.md`): logo
oficial, paleta clara/escura e reconstrução editorial da Início. A
arquitetura final tem **cinco áreas**. Descreve a suíte automatizada criada
para `streamlit_app.py`, `src/inferencia.py` e `src/textos_aplicacao.py`, e o
roteiro de validação manual complementar. Este documento não altera nenhum
artefato congelado, nem o comportamento do modelo; apenas comprova, com
testes e um smoke test real, que o contrato aprovado na TASK 008 continua
respeitado e que a interface cumpre as restrições definidas para cada
subetapa.

## Arquitetura final (cinco áreas)

1. **Início** — abertura editorial, contexto institucional (Associação
   Passos Mágicos e a PEDE como avaliação multidimensional), questão
   central, três caminhos numerados e equipe. Logo oficial, subtítulo do
   projeto e o seletor de aparência claro/escuro ficam no cabeçalho, comum a
   todas as áreas.
2. **Panorama e resultados** — resumo executivo, contexto dos dados, índice
   global das 11 perguntas com seleção direta, capítulos como organização
   secundária, tabelas de números principais e os dez gráficos oficiais.
3. **Avaliar um caso** — ficha de acompanhamento: identificação/idade/sexo
   obrigatórios para completar a ficha (nunca enviados ao modelo), os sete preditores oficiais,
   calculadoras de defasagem/IAN com fórmula oficial confirmada, resultado
   da inferência, próximos passos sugeridos e relatório individual gerado
   somente em memória.
4. **Entenda os indicadores** — glossário dos sete preditores + explicação
   de idade/fase/defasagem, notas/IDA, observação anual/par longitudinal,
   Pedras e Ponto de Virada.
5. **Modelo e limitações** — visão simples e camada técnica (com as curvas
   oficiais do modelo, `reports/curvas_modelagem.png`).

## Fontes públicas utilizadas pelo painel "Panorama e resultados"

Todas lidas em tempo de execução, por caminho relativo, com conferência de
hash para os gráficos (`rastreabilidade.file_matches_sha256` contra
`output_hashes` do próprio `metricas_analises_negocio.json`):

- `reports/metricas_analises_negocio.json` — números das 11 perguntas.
- `reports/figures/01_defasagem.png` … `10_insights.png` — dez gráficos
  oficiais (Q3 e Q4 compartilham `03_associacoes.png`).
- `reports/curvas_modelagem.png` — curvas de precisão-recall e calibração,
  exibidas somente na camada técnica de "Modelo e limitações".

Os relatórios institucionais PEDE 2020/2021/2022 (`DATATHON/`) foram usados
**apenas como fonte conceitual durante a implementação** (nunca lidos pela
aplicação em tempo de execução): explicam a origem da PEDE, a relação
idade/fase/defasagem e os conceitos de Pedra e Ponto de Virada, sem nenhum
número 2020–2022 exibido na interface.

## Distinção entre períodos analíticos

A aplicação nunca mistura, na mesma frase sem qualificação: (a) o panorama
exploratório, que cobre 2022–2024; (b) o desenvolvimento do modelo, na
transição 2022→2023; (c) o teste temporal do modelo, na transição seguinte
2023→2024; e (d) a inferência individual de "Avaliar um caso", sempre feita
com o modelo já congelado, sobre um caso hipotético — nunca uma nova análise
exploratória nem um novo teste. Ver `textos_aplicacao.AVISO_TRES_PERIODOS`.

## 1. Objetivo

Comprovar, com testes automatizados e um roteiro manual, que a aplicação
pública:

- valida corretamente as sete entradas do contrato oficial;
- é compatível com o modelo oficialmente avaliado (schema, classes,
  `predict_proba`, limiar congelado);
- reproduz exatamente a predição do modelo, sem desvio numérico;
- se comporta de forma previsível na interface (mensagens, avisos,
  limitações);
- falha de forma controlada em qualquer situação anômala;
- não expõe, solicita, persiste ou registra nenhum dado pessoal;
- é portátil (independente de `DATATHON/`, `local_data/`,
  `local_recovery/`, do diretório de trabalho atual e do sistema
  operacional).

## 2. Arquivos testados

| Arquivo | Testado por |
| --- | --- |
| `src/inferencia.py` | `tests/test_inferencia_aplicacao.py` (validador, modelo, entradas, predição) e `tests/test_streamlit_app.py` (`PrivacyAndSecurityTests`, junto com os demais módulos, via `PUBLIC_PYTHON_MODULES`) |
| `streamlit_app.py` | `tests/test_streamlit_app.py` (via `streamlit.testing.v1.AppTest` e `PrivacyAndSecurityTests`) |
| `src/textos_aplicacao.py` (novo — módulo público exclusivamente textual/de apresentação, sem lógica de inferência) | `tests/test_streamlit_app.py` (`PrivacyAndSecurityTests`, via `PUBLIC_PYTHON_MODULES`; conteúdo também exercitado indiretamente por `AppTestBehaviorTests`) |
| `.streamlit/config.toml` | `tests/test_streamlit_app.py` (`PortabilityTests`, `PrivacyAndSecurityTests`) |

## 3. Matriz de testes

Contagens confirmadas pelo `unittest` (`python -m unittest tests.test_inferencia_aplicacao`
e `tests.test_streamlit_app`, sem contar `subTest` como método separado —
o `unittest` não os contabiliza individualmente).

| Categoria | Arquivo | Classe | Nº de testes |
| --- | --- | --- | --- |
| Validador público (seis caminhos, artefato ausente, hash/limiar/ordem/`configuracao_sha256` divergentes, schema incompatível) | `test_inferencia_aplicacao.py` | `PublicValidatorTests` | 13 |
| Compatibilidade do modelo (classes, classe positiva, `predict_proba`, ausência de `fit`/`predict`) | `test_inferencia_aplicacao.py` | `ModelCompatibilityTests` | 7 |
| Formato e valores de `predict_proba` | `test_inferencia_aplicacao.py` | `PredictShapeAndValueTests` | 11 |
| Validação de entradas (chaves, tipos, domínio, `NaN`/infinito, payload não dicionário) | `test_inferencia_aplicacao.py` | `InputValidationTests` | 18 |
| Reprodução exata da predição | `test_inferencia_aplicacao.py` | `PredictionReproductionTests` | 1 |
| Comportamento da interface: seis áreas, formulário, resultado, plano de acompanhamento, indicadores, métricas traduzidas, classificação binária, paridade com a inferência oficial (`AppTest`) | `test_streamlit_app.py` | `AppTestBehaviorTests` | 41 |
| Panorama e resultados: conjunto oficial, índice global, acesso direto às 11 perguntas, estrutura completa, números derivados dos artefatos, privacidade objetiva, dez gráficos (com conferência de hash), idade/notas, curvas na camada técnica, erro controlado e portabilidade | `test_streamlit_app.py` | `PanoramaTests` | 31 |
| Privacidade e segurança (AST/texto do código-fonte; cobre `streamlit_app.py`, `src/inferencia.py`, `src/textos_aplicacao.py` e `.streamlit/config.toml`) | `test_streamlit_app.py` | `PrivacyAndSecurityTests` | 19 |
| Portabilidade (inclui confirmação de que `pesquisa_challenger_v2/` não é mais dependência do repositório; item 37 executa a aplicação completa — seis abas, painel e "Avaliar um caso" com exemplo sintético — em uma única cópia pública isolada, em subprocesso, a partir de um diretório de trabalho diferente da cópia) | `test_streamlit_app.py` | `PortabilityTests` | 7 |
| **Total** | | | **285 métodos de teste** (50 em `test_inferencia_aplicacao.py` + 95 em `test_streamlit_app.py` + os demais arquivos da suíte oficial), todos executados individualmente pelo `unittest.TestLoader` |

Todos os testes usam apenas dados sintéticos; nenhum artefato oficial é
alterado (os casos de artefato ausente/adulterado operam sobre cópias em
diretórios temporários, removidas mesmo se o teste falhar).

## 4. Dados sintéticos utilizados

- **Payload de baixo risco:** `ida=6.5, ieg=8.0, iaa=7.0, ips=5.0, ipv=7.5,
  fase_origem="2", defasagem_origem=0` — probabilidade estimada abaixo do
  limiar oficial.
- **Payload de alto risco:** `ida=2.0, ieg=2.0, iaa=2.0, ips=2.0, ipv=2.0,
  fase_origem="3", defasagem_origem=-3` — probabilidade estimada acima do
  limiar oficial.
- **Casos-limite:** texto não numérico (`"abc"`), `"NaN"`/`float("nan")`,
  `"inf"`/`"-inf"`/`float("inf")`, booleanos (`True`/`False`), payload não
  dicionário (`None`, lista, string, número), chaves ausentes/extras, as
  oito categorias de fase (`"0"` a `"7"` mais fora do domínio).
- Nenhum valor corresponde a um registro real do projeto; nenhum RA, nome
  ou identificador aparece em qualquer fixture.

## 5. Roteiro manual

Roteiro para um revisor humano executar localmente. Nenhum passo usa dados
reais.

1. **Iniciar a aplicação:** `.\.venv\Scripts\python.exe -m streamlit run streamlit_app.py`
   (ou `--server.headless true` para verificação sem abrir o navegador).
2. **Conferir a tela inicial:** título, aviso de finalidade educacional,
   explicação do que a probabilidade significa e não significa, formulário
   com sete campos.
3. **Testar exemplo sintético:** clicar em "Preencher exemplo sintético" e
   confirmar que os seis campos numéricos e a fase são preenchidos com
   valores claramente ilustrativos (rotulados como não correspondentes a
   nenhum aluno real).
4. **Testar entrada válida:** preencher os sete campos com valores
   plausíveis e clicar em "Gerar estimativa"; confirmar que aparece uma
   probabilidade em percentual e uma classificação (risco sinalizado ou
   não).
5. **Testar campos numéricos vazios:** deixar todos os campos numéricos em
   branco, escolher uma fase válida e enviar; confirmar que o resultado é
   apresentado normalmente (ausência é aceita e imputada pelo pipeline).
6. **Testar texto inválido:** digitar `"abc"` em um campo numérico e
   enviar; confirmar uma mensagem de erro objetiva citando o campo, sem
   stack trace.
7. **Testar `NaN` e infinito:** digitar `"NaN"`, depois `"inf"`, depois
   `"-inf"` em um campo numérico; confirmar mensagem de erro controlada em
   cada caso, sem stack trace.
8. **Conferir classificação:** repetir o envio válido do passo 4 e
   verificar que a mensagem menciona explicitamente o valor do limiar
   congelado (`0.2670`) e que um resultado abaixo do limiar vem acompanhado
   do aviso de que isso não elimina o risco.
9. **Conferir avisos e limitações:** abrir o expander de limitações e
   confirmar a presença da queda de recall no teste temporal, da
   subestimação de risco, da orientação de supervisão humana e da
   linguagem não causal.
10. **Conferir que nenhum dado é persistido:** encerrar a aplicação (passo
    11) e reabri-la; confirmar que o formulário volta vazio (nada foi
    salvo entre execuções) e que nenhum arquivo novo foi criado no
    repositório.
11. **Encerrar a aplicação:** interromper o processo do Streamlit
    (`Ctrl+C` no terminal, ou finalizar o processo).
12. **Confirmar liberação da porta:** tentar acessar a URL local novamente
    e confirmar que a conexão é recusada.

## 6. Checklist de privacidade

Os testes marcados como "ambos os módulos" cobrem `streamlit_app.py` e
`src/inferencia.py` juntos, via a coleção explícita `PUBLIC_PYTHON_MODULES`
(iterados com `subTest` por módulo).

| Item | Verificado por |
| --- | --- |
| Nenhum campo de RA | `test_nenhum_campo_de_entrada_pede_ra_nome_ou_identificador_pessoal` |
| Nenhum campo de nome | `test_nenhum_campo_de_entrada_pede_ra_nome_ou_identificador_pessoal` |
| Nenhum identificador pessoal (CPF, matrícula, e-mail, telefone, endereço) | `test_nenhum_campo_de_entrada_pede_ra_nome_ou_identificador_pessoal` + `test_contrato_de_campos_nunca_inclui_identificador_pessoal` (contrato de `FEATURES`) |
| Nenhum `file_uploader` | `test_nenhum_file_uploader` (ambos os módulos) |
| Nenhuma referência executável a `DATATHON/`, `local_data/`, `local_recovery/` (menção em docstring explicando a ausência é aceita; literal fora de docstring reprova) | `test_nenhuma_referencia_executavel_a_pastas_privadas` (ambos os módulos), `PublicValidatorTests` (execução real sem essas pastas) |
| Nenhuma persistência de entradas em arquivo (`write_text`/`write_bytes`/`write`/`to_csv`/`to_json`/`dump`, por AST) | `test_nenhuma_persistencia_de_entradas_em_arquivo` (ambos os módulos) |
| Nenhum `open()` em modo de escrita/acréscimo/atualização (`'w'`/`'a'`/`'x'`/`'+'`), por AST | `test_nenhum_open_em_modo_de_escrita_acrescimo_ou_atualizacao` (ambos os módulos) |
| Nenhum banco de dados (`sqlite`, SQLAlchemy, etc.) | `test_nenhum_banco_de_dados` (ambos os módulos) |
| Nenhuma chamada HTTP ou socket externa (`requests`, `httpx`, `urllib`, `socket`) | `test_nenhuma_chamada_http_ou_socket_externa` (ambos os módulos) |
| Nenhum analytics (e estatísticas de uso desativadas no `config.toml`) | `test_nenhum_analytics` (ambos os módulos + `config.toml`) |
| Nenhum log ou `print` de payload | `test_nenhum_logging_ou_print_de_payload` (ambos os módulos) |
| Nenhum `st.exception` | `test_nenhum_st_exception` |
| Nenhum `unsafe_allow_html` | `test_nenhum_unsafe_allow_html` (ambos os módulos) |
| Nenhum cache de dados das entradas (`cache_data`); só cache de recurso (`cache_resource`) | `test_nenhum_cache_de_dados_das_entradas` |
| Nenhum segredo hardcoded (`token`, `password`, `api_key`, `credential`) | `test_nenhum_segredo_hardcoded` (ambos os módulos) |
| Nenhum caminho absoluto Windows ou Unix | `test_nenhum_caminho_absoluto_local` (ambos os módulos) |
| Nenhum hash completo exposto na interface | `test_nenhum_hash_completo_exposto` (ambos os módulos) |
| Exemplos exclusivamente sintéticos e rotulados como tal | `test_exemplo_e_rotulado_como_sintetico` |
| `.streamlit/config.toml`: TOML válido, `gatherUsageStats` desabilitado, sem segredo, sem porta fixa, sem caminho absoluto, sem endpoint externo | `test_config_toml_sem_segredo_endpoint_externo_ou_caminho_absoluto`, `test_configuracao_toml_e_valida_e_sem_porta_fixa` |

## 7. Checklist de acessibilidade básica

| Item | Verificado por |
| --- | --- |
| Título da página presente e descritivo | `test_titulo_presente` |
| Rótulos de texto (não apenas ícones) em todos os campos e botões | `test_exatamente_sete_entradas_preditoras` (rótulos vêm de `textos_aplicacao.INDICADORES`) |
| Texto de ajuda contextual em cada campo numérico e na fase | inspeção manual do passo 2 do roteiro; `INDICADORES[campo]["definicao"/"o_que_informar"/"ausencia"]` compõe o `help=` de todos os `text_input`/`selectbox` |
| Contraste de tema sóbrio e definido explicitamente (não depende do tema padrão do navegador) | `test_configuracao_toml_e_valida_e_sem_porta_fixa` (confere presença de `[theme]`) |
| Mensagens de erro em texto simples, sem depender só de cor | `test_texto_invalido_apresenta_mensagem_controlada` e afins (mensagem textual sempre presente) |
| Nenhum HTML bruto que possa quebrar leitores de tela (`unsafe_allow_html`) | `test_nenhum_unsafe_allow_html` |

Esta checklist cobre acessibilidade básica de estrutura e texto; não
substitui uma auditoria completa de acessibilidade (contraste de cor
calculado, navegação por teclado, leitor de tela real), fora do escopo
desta TASK.

## 8. Procedimento para executar

```powershell
# Somente os testes novos desta TASK
.\.venv\Scripts\python.exe -m unittest tests.test_inferencia_aplicacao tests.test_streamlit_app -v

# Suíte completa (nota: antes do stage dos arquivos desta TASK, a trava de
# arquivos não rastreados de tests/test_notebook_final.py rejeita
# intencionalmente os arquivos novos ainda não commitados — ver seção 11)
.\.venv\Scripts\python.exe -m unittest discover -s tests -p "test_*.py" -v

# Smoke test manual da interface (headless, porta livre à sua escolha)
.\.venv\Scripts\python.exe -m streamlit run streamlit_app.py --server.headless true --server.port 8501
```

## 9. Resultado dos testes

Contagens da TASK 010 original (histórico, não alterado nesta subetapa):

- `tests.test_inferencia_aplicacao` — **50/50 aprovados**, ~0,7 s.
- Nenhum defeito funcional restante naquela TASK: um defeito real foi
  encontrado durante a escrita dos testes (`validate_inputs` aceitava
  `None`/tipos não-`dict` e vazava `TypeError` cru em vez de
  `InputValidationError`) e corrigido de forma mínima e cirúrgica em
  `src/inferencia.py`, com autorização explícita, antes de finalizar a
  suíte — ver relatório da TASK 010 para o detalhe exato da correção.

Contagens da primeira subetapa de aprimoramento da interface (cinco áreas):

- `tests.test_streamlit_app` — 66/66 aprovados (41 `AppTestBehaviorTests` +
  19 `PrivacyAndSecurityTests` + 6 `PortabilityTests`).
- Suíte completa do projeto — 256/256 aprovados, 0 falhas/erros/skips.

Contagens da ETAPA B (storytelling e painel "Panorama e resultados";
contagem real obtida via `unittest.TestLoader`, não estimada):

- `tests.test_streamlit_app` — **92/92 aprovados** (41 `AppTestBehaviorTests`
  + 26 `PanoramaTests` + 19 `PrivacyAndSecurityTests` + 6 `PortabilityTests`),
  ~73-99 s.
- Suíte completa do projeto (`unittest discover -s tests -p "test_*.py"`) —
  **282/282 aprovados**, 0 falhas, 0 erros, 0 skips, ~98-151 s (inclui a
  execução real do notebook público via `nbclient`).
- Nenhum defeito funcional encontrado em `src/inferencia.py` nesta etapa (o
  módulo não foi alterado, conforme restrição do enunciado).
- Durante a escrita dos testes de `PanoramaTests`, quatro casos precisaram
  de correção **na própria suíte de teste** (não na aplicação): (a)
  `AppTest` não expõe uma coleção dedicada para `st.progress`, contornado
  com verificação estrutural do código-fonte; (b) `.options`/`.value` de
  `st.image` no `AppTest` retornam uma referência mascarada
  (`/mock/media/<hash>.png`), não o caminho real — a correspondência
  imagem↔pergunta passou a ser verificada pela legenda acessível
  (`.captions`); (c) alternar capítulo e depois selecionar um número de
  pergunta que só existe em OUTRO capítulo levantava `KeyError` no próprio
  teste (ordem de interação errada no teste, não um defeito da aplicação);
  (d) dois testes herdados da subetapa anterior assumiam cinco abas/sete
  widgets brutos e precisaram ser ajustados para as seis abas atuais e para
  filtrar o novo seletor de pergunta do painel.
- Smoke test real (fora do `AppTest`): `streamlit run --server.headless
  true` iniciou sem erro; `/_stcore/health` respondeu `200 ok`; página
  principal respondeu `200`; carregamento do painel confirmado para a
  primeira pergunta de cada um dos quatro capítulos (com gráfico e resposta
  válidos); inferência do exemplo sintético confirmada de forma
  independente do processo do servidor (probabilidade 0,1636, abaixo do
  limiar 0,2670 — não sinalizado); processo encerrado por completo; porta
  liberada; nenhum processo ou arquivo temporário residual.

Contagens da correção pós-revisão independente (achados da revisão
somente-leitura da ETAPA B, corrigidos nesta rodada; contagem real via
`unittest.TestLoader`):

- `tests.test_streamlit_app` — **95/95 aprovados** (41 `AppTestBehaviorTests`
  + 28 `PanoramaTests` + 19 `PrivacyAndSecurityTests` + 7 `PortabilityTests`),
  ~100-120 s.
- Suíte completa do projeto (`unittest discover -s tests -p "test_*.py"`) —
  **285/285 aprovados**, 0 falhas, 0 erros, 0 skips, ~150-170 s (inclui a
  execução real do notebook público via `nbclient`).
- Correções aplicadas: (a) referência textual a uma aba renomeada
  ("Sobre o modelo" → "Modelo e limitações") em
  `AVISO_ABAIXO_NAO_ELIMINA_RISCO`; (b) o antigo teste-placeholder do item
  33 foi substituído por um teste funcional real, que roda a aplicação
  completa (não uma chamada isolada de função) contra um gráfico oficial
  corrompido; (c) remoção da constante morta `CHAMADA_PARA_AVALIAR`; (d)
  docstring de `streamlit_app.py` corrigida de "cinco" para "seis áreas";
  (e) `EXPLICACAO_PONTO_DE_VIRADA` reescrita para deixar explícitos os dois
  papéis do IPV (panorama exploratório e preditor direto do modelo); (f)
  novo teste (`PortabilityTests.test_item37...`) que roda a aplicação
  completa (seis abas, painel e "Avaliar um caso" com exemplo sintético) em
  uma única cópia pública isolada.
- Durante esta correção, dois defeitos adicionais foram encontrados e
  corrigidos **na própria aplicação/suíte** (não fazem parte da lista de
  achados originais da revisão, mas foram necessários para os novos testes
  funcionarem de forma confiável): (a) `streamlit_app.py` chamava `main()`
  incondicionalmente no nível do módulo; um `import streamlit_app` feito
  fora do ciclo de vida do `AppTest` (padrão já usado por dois testes
  preexistentes) executava `main()` "a seco" e corrompia, para o resto do
  processo, o rastreamento interno de formulários do Streamlit — corrigido
  com a guarda padrão `if __name__ == "__main__": main()` (segura tanto
  para `streamlit run` quanto para `AppTest`, que executam o script sob um
  módulo chamado exatamente `"__main__"`); (b) os novos testes que copiam
  `src/` para um diretório temporário (para rodar a aplicação em
  subprocesso isolado) inicialmente deixavam diretório residual no
  sistema — a causa era o atributo "somente leitura" do Windows,
  herdado da raiz do projeto (dentro do OneDrive) via `shutil.copy2`;
  corrigido trocando para `shutil.copy` (sem preservar atributos) nesses
  pontos específicos, mais uma limpeza defensiva com novas tentativas.

## 10. Limitações da validação

- `streamlit.testing.v1.AppTest` simula o script Python da aplicação e o
  estado dos widgets; não renderiza CSS/HTML real nem testa a experiência
  visual em um navegador de verdade (contraste, responsividade, leitor de
  tela). O smoke test real cobre apenas inicialização, saúde HTTP e
  encerramento — não a interação visual.
- Os testes do validador público usam cópias dos artefatos oficiais atuais;
  não cobrem toda combinação teoricamente possível de adulteração, apenas
  os cenários explicitamente listados no escopo da TASK.
- Não há teste de carga, concorrência entre múltiplas sessões, nem do
  comportamento sob deploy real no Streamlit Community Cloud (isso é
  escopo da TASK 011).
- A checklist de acessibilidade é básica (estrutural/textual); não substitui
  uma auditoria formal de acessibilidade.
- Os testes de portabilidade validam apenas o ambiente Windows local
  disponível nesta sessão; a compatibilidade com Linux é garantida pelo uso
  exclusivo de `pathlib`/caminhos relativos (verificado estaticamente), mas
  não foi executada em uma máquina Linux real nesta TASK.

## 11. Critérios para aprovação da TASK 010 (histórico)

1. `tests/test_inferencia_aplicacao.py` e `tests/test_streamlit_app.py`
   criados e aprovados isoladamente (95/95, 0 falhas/erros/skips, contagem
   da época).
2. Nenhum artefato oficial (`artifacts/`, `reports/`) alterado pelos testes.
3. Nenhum dado privado (`DATATHON/`, `local_data/`, `local_recovery/`)
   acessado pelos testes.
4. Checklist de privacidade (seção 6) integralmente coberta por teste
   automatizado.
5. Smoke test real da interface aprovado (saúde HTTP 200, sem traceback,
   processo encerrado, porta liberada).
6. Qualquer defeito funcional real encontrado durante a criação dos testes
   foi corrigido de forma mínima e documentada (não silenciada nem
   ignorada) — ver seção 9.
7. Após o stage dos cinco arquivos daquela TASK, a suíte completa do
   projeto atingiu 235 testes aprovados, 0 falhas, 0 erros e 0 skips (140
   testes anteriores + 95 novos da TASK 010).

## 12. Critérios para a subetapa de aprimoramento da interface (pré-TASK 011)

1. `tests/test_streamlit_app.py` ampliado e aprovado isoladamente (66/66, 0
   falhas/erros/skips — contagem real via `unittest.TestLoader`).
2. `src/inferencia.py` não foi alterado (nenhum defeito funcional
   comprovado foi encontrado).
3. Nenhum artefato oficial (`artifacts/`, `reports/`) alterado.
4. Nenhum dado privado acessado; `pesquisa_challenger_v2/` (já arquivada
   fora do repositório) confirmada como não-dependência.
5. Cinco áreas da aplicação presentes e navegáveis; sete campos oficiais
   preservados na ordem enviada ao modelo; classificação binária mantida
   pelo limiar congelado (sem faixas de risco arbitrárias).
6. Definições dos indicadores rastreadas a fontes documentais do projeto
   (ver relatório da subetapa para a lista exata por campo).
7. Suíte completa do projeto: **256/256 aprovados**, 0 falhas, 0 erros, 0
   skips (contagem real via `unittest discover`, não estimada) — inclui uma
   adição de uma linha, autorizada explicitamente, a
   `tests/test_notebook_final.py` (`AUTHORIZED_UNTRACKED_FILES`), único
   arquivo fora da lista original de arquivos autorizados que precisou de
   ajuste, por depender de um manifesto de arquivos não rastreados alheio
   ao escopo desta subetapa.
8. Smoke test real aprovado antes e depois do redesenho.

## 13. Critérios para a ETAPA B (storytelling e panorama exploratório)

1. `tests/test_streamlit_app.py` ampliado com a classe `PanoramaTests` e
   aprovado isoladamente (92/92, 0 falhas/erros/skips — contagem real via
   `unittest.TestLoader`).
2. `src/inferencia.py` não foi alterado.
3. Nenhum artefato oficial (`artifacts/`, `reports/`) alterado; os dez
   gráficos e `reports/curvas_modelagem.png` são apenas lidos, com
   conferência de hash contra `output_hashes` de
   `reports/metricas_analises_negocio.json`.
4. A aplicação pública nunca lê nenhum PDF em tempo de execução — os
   relatórios PEDE 2020/2021/2022 foram usados apenas como fonte conceitual
   durante a implementação (confirmado por teste: ausência de `import
   fitz`/`import pypdf` e de qualquer literal `.pdf`/`pede2020`/`pede2021`/
   `pede2022` fora de docstring nos três módulos públicos).
5. Seis áreas presentes e navegáveis; quatro capítulos; onze perguntas,
   mapeadas exatamente aos capítulos definidos; dez gráficos oficiais (Q3 e
   Q4 compartilham `03_associacoes.png`, com aviso explícito na interface).
6. Nenhum número das 11 perguntas duplicado manualmente como literal em
   `src/textos_aplicacao.py` — comprovado ao trocar os valores de entrada
   (JSON sintético) e confirmar que a resposta muda de acordo.
7. Idade e notas (Matemática/Português/Inglês) explicadas na aba "Entenda
   os indicadores", sem serem adicionadas ao formulário de "Avaliar um
   caso" (que permanece com exatamente os sete preditores oficiais).
8. Predição do caso sintético preservada e idêntica à produzida diretamente
   por `inferencia.run_inference` com os mesmos valores (0,1636 de
   probabilidade, abaixo do limiar 0,2670 — não sinalizado).
9. AP, ROC-AUC, Brier e demais métricas técnicas continuam ausentes da
   abertura da aplicação e da "Visão simples"; aparecem somente dentro do
   expander "Detalhes técnicos", junto das curvas oficiais do modelo.
10. Erro controlado (sem caminho local completo nem hash completo na
    mensagem) para gráfico ausente ou com hash divergente do registrado.
11. Suíte completa do projeto: **282/282 aprovados**, 0 falhas, 0 erros, 0
    skips (contagem real via `unittest discover`).
12. Smoke test real aprovado, incluindo o carregamento de uma pergunta de
    cada um dos quatro capítulos e a inferência do exemplo sintético.

Os itens 1 e 11 acima registram as contagens desta etapa no momento em que
ela foi concluída; uma revisão independente somente-leitura, seguida de uma
correção, ampliou a suíte — ver "Contagens da correção pós-revisão
independente" na seção 9 e a seção 14 abaixo para as contagens atuais.

## 14. Critérios para a correção pós-revisão independente

Uma revisão independente e somente-leitura da ETAPA B encontrou um achado
bloqueante (referência textual a uma aba renomeada, visível em todo
resultado de inferência abaixo do limiar) e achados importantes/menores
(teste-placeholder tautológico, código morto, docstring desatualizada,
lacuna de cobertura de portabilidade, imprecisão de conteúdo sobre o papel
do IPV). Esta correção resolveu todos eles:

1. `AVISO_ABAIXO_NAO_ELIMINA_RISCO` não referencia mais "Sobre o modelo";
   referencia "Modelo e limitações", a aba real. Coberto por teste que
   confirma ausência do nome antigo em todos os módulos públicos, que toda
   referência textual a uma aba corresponde a uma das seis abas reais, e
   que o texto renderizado no resultado cita o nome atual.
2. O antigo teste-placeholder do item 33 (`assertTrue(True)`) foi
   substituído por um teste funcional real: aplicação completa executada
   (em subprocesso isolado, sem monkeypatch) contra uma cópia pública com
   um gráfico oficial corrompido, confirmando a mensagem controlada
   efetivamente renderizada na interface, sem traceback, caminho local,
   mensagem interna ou hash completo expostos.
3. `CHAMADA_PARA_AVALIAR` (constante sem nenhum consumidor) removida.
4. Docstring de `streamlit_app.py` corrigida para "seis áreas"; nenhuma
   referência obsoleta a "cinco áreas" ou "Sobre o modelo" resta em
   `streamlit_app.py`, `src/textos_aplicacao.py` ou
   `tests/test_streamlit_app.py` (as únicas ocorrências restantes de
   "cinco áreas"/"Sobre o modelo" nesses arquivos são, respectivamente, uma
   nota histórica sobre a subetapa anterior e as próprias asserções de
   regressão que comprovam a ausência do nome antigo).
5. `EXPLICACAO_PONTO_DE_VIRADA` deixa explícitos os dois papéis do IPV
   (indicador do panorama exploratório e um dos sete preditores diretos do
   modelo), sem alterar a definição institucional de Ponto de Virada nem
   inventar fórmula ou ponto de corte.
6. Novo teste (`PortabilityTests.test_item37...`) executa a aplicação
   completa (seis abas, painel "Panorama e resultados" com uma pergunta
   selecionada, e "Avaliar um caso" com o exemplo sintético submetido) em
   uma única cópia pública isolada, com o processo filho rodando a partir
   de um diretório de trabalho diferente da própria cópia.
7. Suíte completa do projeto: **285/285 aprovados**, 0 falhas, 0 erros, 0
   skips (contagem real via `unittest discover`), nenhum arquivo temporário
   residual, nenhum processo residual após o smoke test.
8. Nenhum artefato oficial, modelo, limiar ou dado privado alterado; nenhum
   dos itens já aprovados na ETAPA B (seis abas, quatro capítulos, onze
   perguntas, dez gráficos, caminhos JSON, arredondamentos, formulário,
   sete preditores, inferência, hashes) foi modificado, exceto a correção
   pontual do texto sobre o IPV descrita no item 5 acima.

## 16. Reconstrução da análise exploratória (auditoria das 11 perguntas)

1. A navegação por capítulo foi substituída por um índice completo e um único
   seletor que oferece diretamente as perguntas 1 a 11. Os quatro capítulos
   continuam visíveis com suas contagens (3, 2, 3 e 3), mas não filtram nem
   escondem o conjunto.
2. Cada cartão passou a conter pergunta oficial, resposta direta, tabela de
   números principais, gráfico, instrução de leitura, observação, significado
   para a ONG, ação prática, limitação, população/período e fonte/chaves exatas.
3. A pergunta 8 passou a incluir 2023. A pergunta 7 escolhe a maior correlação
   em valor absoluto. A pergunta 1 informa a regra objetiva de privacidade e o
   denominador de 2024 sem revelar a célula protegida.
4. `PanoramaTests`: **31/31 aprovados**. `tests.test_streamlit_app`: **98/98
   aprovados**. Suíte completa: **288/288 aprovados**, 0 falhas, 0 erros e 0
   skips, em 155,585 s.
5. Validação em navegador Chromium: perguntas 1 a 11 abertas; índice completo
   confirmado; larguras de 1.440 px e 390 px conferidas. Evidências em
   `reports/validacao_visual/`.

## 17. Aprimoramento da página inicial e do layout geral

1. `st.set_page_config` é a primeira chamada Streamlit e usa exatamente o
   título público, o ícone 🎓 e `layout="wide"`.
2. A Home apresenta hero, contexto, questão central, objetivo, quatro
   entregas, cinco passos de navegação, os cinco integrantes e o aviso ético
   solicitados. A equipe não contém e-mails, cargos, links ou ferramentas.
3. Panorama, formulário, plano, indicadores e modelo usam colunas nativas para
   aproveitar a largura disponível; os sete preditores e sua ordem oficial
   permanecem inalterados.
4. Chrome real validado em 1.920, 1.440, 768 e 390 px: nenhuma largura produziu
   overflow horizontal da página. Em 390 px, cards e formulário empilham e a
   barra de abas mantém a navegação horizontal nativa do Streamlit.
5. Evidências e medições em `reports/validacao_layout/`; relatório detalhado em
   `docs/validacao_layout_inicio.md`.
6. `tests.test_streamlit_app`: **100/100 aprovados** antes do ajuste final da
   ordem mobile; o teste focal do ajuste também foi aprovado.
7. Suíte integral final: **290/290 aprovados**, 0 falhas, 0 erros e 0 skips, em
   117,115 s.
8. Nenhum artefato oficial, limiar, preditor ou caminho de inferência foi
   alterado. Não houve `git add`, commit, push, merge, tag ou deploy.

## 18. Correção de usabilidade da navegação das 11 perguntas

1. O índice global permanece visível e informa “11 perguntas de negócio
   respondidas”, com as onze perguntas oficiais numeradas.
2. Um `st.container(border=True)` apresenta “Explore as 11 perguntas”, a
   orientação de uso, o contador, o capítulo atual e o seletor visível
   “Escolha uma das 11 perguntas”.
3. O seletor tem exatamente onze opções oficiais, numeradas de 1 a 11, e usa a
   chave persistente `panorama_pergunta`.
4. Os botões “← Pergunta anterior” e “Próxima pergunta →” compartilham esse
   estado. O primeiro fica desabilitado na pergunta 1, o segundo na pergunta
   11, e não há navegação circular.
5. Testes interativos simulam avanço 1→2, retorno 2→1 e seleção direta da
   pergunta 11. Também comparam resposta, tabela, legenda do gráfico e capítulo
   com a pergunta selecionada.
6. O cartão analítico usa o número da pergunta como título (`Pergunta 1`,
   `Pergunta 2`, …). “Resposta direta”, “Principais números”, “Gráfico
   correspondente” e as demais seções ficam sem numeração concorrente.
7. `tests.test_streamlit_app`: **105/105 aprovados**. Suíte integral:
   **295/295 aprovados**, 0 falhas, 0 erros e 0 skips, em 134,750 s.
8. Chrome real em 1.440 px e 390 px: seletor e botões visíveis, clique real
   confirmado, controles empilhados no celular e nenhum overflow horizontal.
   Evidências em `reports/validacao_layout/navegacao_*.png` e medições em
   `reports/validacao_layout/validacao_navegacao_perguntas.json`.
9. Dados, respostas, tabelas, gráficos, conclusões, modelo e inferência não
   foram alterados. Não houve `git add`, commit, push ou deploy.

## 19. Camada pública sanitizada v1

1. O Streamlit e o notebook passaram a consumir somente
   `reports/public/perguntas_oficiais_v1.json`, com verificação dos hashes do
   manifesto público e onze figuras exclusivas.
2. Os testes novos cobrem literalidade e ordem das 11 perguntas, schema,
   hashes, supressão primária e complementar, ausência dos quadrantes
   artificiais da Q6, independência dos históricos e congelamento do modelo.
3. `tests.test_streamlit_app`: **105/105 aprovados**; suíte completa:
   **253/253 aprovados**, 0 falhas e 0 erros. Após a agregação publicável de
   2024 na Q1, a suíte foi repetida integralmente em 151,905 s com o mesmo
   resultado.
4. O notebook limpo passou em **8/8 testes** e foi executado integralmente em
   memória com 11 células, sem alterar ou salvar outputs no arquivo público.
5. Smoke visual em Chromium real validou Q1, avanço para Q2, seleção direta de
   Q11, limites dos botões e ausência de overflow ou botões cortados em 1.440
   px e 390 px. Capturas em `reports/validacao_visual_publica/`.
6. O modelo, o limiar, os sete preditores e a inferência oficial permaneceram
   inalterados. Não houve `git add`, commit, push, deploy ou remoção de
   artefatos históricos rastreados.

## 20. Implementação do plano da auditoria comparativa independente (24/09/2026)

Uma auditoria comparativa independente (aplicação local vs. referência
pública de terceiros, documentos oficiais e planilha-base) recomendou uma
estratégia híbrida: manter a metodologia e a prudência estatística da
aplicação local, incorporando a riqueza visual e a estrutura comunicacional
da referência, sem copiar seus erros metodológicos (causalidade,
circularidade, limiares não validados). O plano completo (itens Crítico +
Importante + Desejável) foi avaliado e implementado nesta rodada.

**Achados da auditoria já satisfeitos sem alteração** (confirmados, não
implementados de novo): supressão de 2024 sem `None` cru (Q1/Q6), 11
perguntas independentes, linguagem não causal, circularidade do INDE
explicitada (Q8), validação temporal e AUC corretamente interpretadas (Q9),
distinção Pedra/fase escolar (Q10), pergunta 11 já estruturada como cadeia
evidência → público → ação → prioridade → limitação.

**Alterações implementadas:**

1. **Auditoria de divulgação conjunta** (item crítico da auditoria):
   verificação formal, com script dedicado e nova suíte de regressão
   (`test_auditoria_de_divulgacao_conjunta_entre_perguntas`), de que nenhuma
   combinação de números publicados nas 11 perguntas permite reconstruir a
   célula suprimida do IAN de 2024 (Q1) nem a distribuição de IPP por
   categoria de 2024 (Q6). Nenhuma segunda equação independente foi
   encontrada em nenhuma das 11 perguntas — a supressão permanece robusta.
2. **Gráficos interativos** (`src/graficos_publicos.py`, novo módulo
   público): as 11 perguntas passam a ter pelo menos um gráfico Plotly
   interativo (com tooltip ao passar o cursor), construído em tempo de
   execução a partir dos mesmos números já publicados e com hash conferido
   em `principais_numeros` — nenhum valor duplicado manualmente. Três
   perguntas (6, 7 e 9) ganham um segundo gráfico complementar. O gráfico
   PNG oficial (com hash verificado) permanece disponível, agora dentro de
   um expander "Detalhes técnicos", como artefato de auditoria/
   reprodutibilidade. Paleta categórica/sequencial/status validada pela
   skill `dataviz` (`references/palette.md`), nunca uma cor arbitrária —
   confirmado por teste dedicado. Barra de ferramentas técnica do Plotly
   desativada (`displayModeBar: False`): em telas de celular seus ícones
   ficavam cortados, e o público da aplicação não precisa de ferramentas de
   exploração técnica.
3. **Navegador antes do índice**: a auditoria apontou que o índice longo das
   11 perguntas vinha antes do navegador, prejudicando a primeira leitura.
   Invertido; índice completo e organização por capítulos viraram seções
   recolhíveis.
4. **Célula suprimida sem `None` cru na tabela**: a linha de supressão
   integral da pergunta 6 (IPP por categoria, 2024) exibia o texto literal
   "None" na tabela interativa (`st.dataframe`), embora o relatório em
   markdown já usasse um travessão — achado durante a inspeção visual em
   Chromium real desta própria rodada. Corrigido (`None` → "—" só na cópia
   exibida, nunca na fonte); novo teste de regressão cobre as 11 perguntas,
   não somente a pergunta 6.
5. Um novo teste (`test_item37...`, já existente da rodada anterior) e a
   separação executivo/técnico por pergunta (resposta, gráfico interativo e
   significado na visão principal; gráfico oficial, população e fonte exata
   no expander de detalhes técnicos) cobrem os itens "Importante" de
   separação de conteúdo.
6. **Inspeção visual em Chromium real** desta rodada (reaproveitando
   `scripts/validar_layout_publico.py`): confirmado, em 1.440 px e 390 px,
   ausência de overflow horizontal e ausência de botões cortados — a
   primeira execução após adicionar os gráficos Plotly encontrou botões da
   barra de ferramentas técnica cortados em 390 px (item 2 acima corrigiu
   isso). Captura adicional do cartão com gráfico interativo confirmou
   renderização correta (cores da paleta validada, legenda, rótulos de
   valor, tooltip) em `reports/validacao_visual_publica/`.
7. **Itens do plano intencionalmente não implementados nesta rodada**, com
   justificativa: filtros dinâmicos com supressão automática (Desejável) —
   qualquer filtro que recombine categorias exige sua própria auditoria de
   privacidade antes de ir ao ar, o que é desproporcional para incluir sem
   revisão dedicada; teste de usabilidade com professores e equipe da ONG
   (Desejável) — exige pessoas reais, fora do alcance de um agente
   automatizado; ambos ficam como recomendação para uma rodada futura,
   explicitamente autorizada para esse escopo.
8. Novo arquivo de teste `tests/test_graficos_publicos.py` (7 testes):
   cobre as 11 perguntas produzindo figura válida, fidelidade dos valores
   plotados contra `principais_numeros`, ausência de número de negócio
   hardcoded nas funções de gráfico, paleta validada e ausência de
   dependência de dados privados/históricos.
9. `plotly==6.1.2` adicionado a `requirements.txt` (necessário para o
   deploy no Streamlit Community Cloud da TASK 011, ainda não executada).
10. `tests.test_streamlit_app`: **111/111 aprovados** (era 105/105).
    `tests.test_privacidade_publicacao`: **6/6** (era 5/5, +1 auditoria de
    divulgação conjunta). `tests.test_graficos_publicos`: **7/7** (novo).
    Suíte completa do projeto: **267/267 aprovados**, 0 falhas, 0 erros, 0
    skips, ~127-140 s (inclui execução real do notebook público via
    `nbclient`).
11. Nenhum artefato oficial, modelo, limiar ou dado privado foi alterado.
    Nenhum dos itens já aprovados nas rodadas anteriores (seis abas, quatro
    capítulos, onze perguntas, onze gráficos oficiais, caminhos JSON,
    arredondamentos, formulário, sete preditores, inferência, hashes) foi
    modificado. Não houve `git add`, commit, push, merge, tag ou deploy.

## 21. Ajustes finais restritos — Q1, faixa etária aproximada e ligação da Q9 (24/09/2026)

1. **Q1 por sexo:** a agregação binária `sem defasagem` / `alguma
   defasagem` foi validada nas seis combinações sexo×ano. Todas as doze
   células superam o mínimo de publicação. O gráfico mostra feminino e
   masculino em 2022, 2023 e 2024, denominadores no eixo, percentuais nas
   barras, variação anual em pontos percentuais no tooltip e aviso de que
   `alguma defasagem` reúne moderada e severa. O detalhamento original de
   2023/2024 permanece suprimido.
2. **Faixa etária aproximada:** toda a camada pública usa a denominação
   `faixa etária aproximada`. As fronteiras auditadas são 7–10, 11–13,
   14–16 e 17 anos ou mais. O relatório explica que o cálculo usa apenas
   `ano_referencia - ano_nascimento_padronizado`; sem mês e dia, estudantes
   próximos a 10/11, 13/14 e 16/17 podem pertencer à faixa vizinha.
3. **Ligação da Q9:** `scripts/explorar_equidade_genero_modelo.py` usa a
   chave composta `(RA, ano dos preditores)`. A base longitudinal tem 3.030
   linhas e 3.030 chaves compostas; a coorte de teste tem 311 linhas, todas
   ligadas 1:1, sem ausência, duplicação ou correspondência múltipla.
   Preditores, rótulos e probabilidades foram comparados posição a posição
   com a coorte tabular oficial, com fingerprints posicionais. Todas as
   métricas globais foram reproduzidas exatamente antes dos recortes.
4. **Privacidade da Q9:** cada subgrupo publicável registra total,
   positivos, negativos, alertas, verdadeiros positivos, falsos positivos
   e falsos negativos. Grupos abaixo do limite não divulgam essas células;
   quando falta uma das classes, AP e ROC-AUC aparecem como `não estimável
   para este grupo`, nunca como zero.
5. **Testes:** 36 testes específicos aprovados; suíte completa com **289/289
   aprovados**, sem falhas, erros ou skips. A validação em Chromium real
   passou em 1.440, 768 e 390 px, com três gráficos na Q1, sem overflow,
   botões ou gráfico por sexo cortados. As capturas atualizadas estão em
   `reports/validacao_visual_publica/`.

## 22. Ficha de acompanhamento, identidade visual e calculadoras institucionais (25/09/2026)

Três rodadas sucessivas, todas preservando modelo, limiar, artefatos e os
sete preditores oficiais (`inferencia.FEATURES`), sem alterar a aba
"Panorama e resultados" nem as 11 perguntas de negócio:

1. **Ficha de acompanhamento em "Avaliar um caso"** — identificação/idade/
   sexo obrigatórios na ficha (nunca enviados ao modelo), calculadoras de defasagem e
   IAN, relatório individual em memória, "Próximos passos" integrados ao
   resultado (fim da aba "Plano de acompanhamento"). Suíte: **332/332**.
2. **Identidade visual da Associação Passos Mágicos** — logo oficial local
   (`assets/brand/`), paleta clara/escura extraída do logo e documentada
   (`docs/identidade_visual.md`), alternador nativo "Claro/Escuro", Início
   reconstruída como abertura editorial. Corrigido nesta rodada um problema
   real de contraste no modo escuro (componentes nativos do Streamlit —
   `st.table`, rótulos de widget, `st.metric` — fixavam a cor de texto do
   modo claro). Suíte: **352/352**.
3. **Calculadoras institucionais corrigidas** — releitura completa de
   `DATATHON/PEDE_ Pontos importantes.docx`, incluindo as 10 imagens/tabelas
   incorporadas (não só o texto plano), corrigiu a auditoria anterior:
   IDA (três notas), IAA (Tabela 40, seis perguntas) e INDE (informação
   complementar) têm fórmula oficial confirmada e ganharam calculadora;
   sugestão de fase ideal por idade (nunca automática, sempre confirmada
   pelo usuário); IEG, IPS e IPV continuam sem calculadora (questionários
   sem escala documentada). Ver `docs/auditoria_calculadoras_indicadores.md`
   para a matriz completa com citação de fonte por indicador. Suíte final:
   **390/390 aprovados**, sem falhas, erros ou skips (contagem real via
   `python -m unittest discover -s tests -p "test_*.py"`, com verificação
   linha a linha de que a soma dos 15 arquivos de teste bate com o total
   relatado pelo runner).
4. **Ficha individual completa (rodada final)** — identificação, idade,
   sexo, fase atual e fase ideal confirmada passaram a ser obrigatórios;
   a defasagem é calculada como fase atual menos fase ideal e divergências
   com registro institucional exigem escolha explícita. IDA e IAA não
   completam ausências com zero; as frações oficiais do IAA garantem seis
   respostas A iguais a 10. IPP/IAN/INDE permanecem fora do payload, que
   conserva somente os sete preditores e sua ordem. A validação Chromium
   cobre 1.440, 768 e 390 px nos temas claro e escuro, além dos cenários
   funcionais da ficha, em `scripts/validar_ficha_individual.py`. Suíte
   final: **489/489 aprovados**, sem falhas, erros ou skips (contagem real
   via `python -m unittest discover -s tests -p "test_*.py"`).
5. **Revisão independente (IPP/IPV) e ajustes de UX** — o campo do IPP
   estava só dentro do expander colapsado "INDE (informação complementar)",
   apesar de obrigatório para Alfa–7; passou a ter seção própria, visível,
   em "Engajamento e desenvolvimento". Rótulo do IPV corrigido para "IPV —
   Ponto de Virada institucional" (o texto de ajuda contradizia o texto
   logo abaixo). Notas brutas de Matemática/Português/Inglês passaram a
   validar 0–10 com erro por campo (antes só o IDA calculado bloqueava, sem
   dizer qual nota estava errada). Frases que soavam frágeis ("não é
   possível calculá-lo com segurança aqui") foram reescritas em tom
   institucional neutro. Resumo da ficha ("Dados da ficha"/"Indicadores
   usados na estimativa") passou a ficar dentro de um expander colapsado —
   menos peso técnico na tela para quem avalia a ficha. Contraste
   corrigido no modo escuro para: botões desabilitados (cor de texto fixa
   do modo claro a 40% de opacidade não se adaptava) e o alternador
   Claro/Escuro (opção não selecionada usava cores fixas do BaseWeb).
   A aba "Modelo e limitações" saiu da navegação (decisão de produto): o
   mesmo conteúdo, com o ponto operacional em destaque (não mais os
   números desatualizados do ponto original), passou a ser gerado como
   documento autônomo HTML/PDF por
   `scripts/gerar_relatorio_modelo_e_limitacoes.py`, para uso da equipe
   (ex.: apresentação do modelo). Suíte final: **516/516 aprovados**, sem
   falhas, erros ou skips (contagem real via `python -m unittest discover
   -s tests -p "test_*.py"`).
