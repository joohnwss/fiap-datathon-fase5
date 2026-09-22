# Testes da aplicação e privacidade (TASK 010)

Documento da TASK 010 (FASE 4 do plano em [TASKS.md](TASKS.md)). Descreve a
suíte automatizada criada para `streamlit_app.py` e `src/inferencia.py`
(TASK 009) e o roteiro de validação manual complementar. Este documento não
altera nenhum artefato congelado, nem o comportamento da aplicação; apenas
comprova, com testes e um smoke test real, que o contrato aprovado na
TASK 008 é respeitado.

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
| `src/inferencia.py` | `tests/test_inferencia_aplicacao.py` (validador, modelo, entradas, predição) e `tests/test_streamlit_app.py` (`PrivacyAndSecurityTests`, junto com `streamlit_app.py`, via `PUBLIC_PYTHON_MODULES`) |
| `streamlit_app.py` | `tests/test_streamlit_app.py` (via `streamlit.testing.v1.AppTest` e `PrivacyAndSecurityTests`) |
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
| Comportamento da interface (`AppTest`) | `test_streamlit_app.py` | `AppTestBehaviorTests` | 22 |
| Privacidade e segurança (AST/texto do código-fonte; cobre `streamlit_app.py`, `src/inferencia.py` e `.streamlit/config.toml`) | `test_streamlit_app.py` | `PrivacyAndSecurityTests` | 18 |
| Portabilidade | `test_streamlit_app.py` | `PortabilityTests` | 5 |
| **Total** | | | **95 métodos de teste**, todos executados individualmente pelo `unittest` |

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
| Rótulos de texto (não apenas ícones) em todos os campos e botões | `test_exatamente_sete_entradas_preditoras` (rótulos vêm de `CAMPO_ROTULO`) |
| Texto de ajuda contextual em cada campo numérico e na fase | inspeção manual do passo 2 do roteiro; `CAMPO_AJUDA` presente em todos os `text_input` |
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

- `tests.test_inferencia_aplicacao` — **50/50 aprovados**, ~0,7 s.
- `tests.test_streamlit_app` — **45/45 aprovados**, ~16-21 s (inclui a
  sobrecarga de inicializar o `AppTest` a cada cenário).
- Os dois arquivos juntos — **95/95 aprovados**, 0 falhas, 0 erros, 0 skips,
  ~16-20 s.
- Smoke test real (fora do `AppTest`): `streamlit run --server.headless
  true` iniciou sem erro; `/_stcore/health` respondeu `200 ok`; página
  principal respondeu `200`; processo encerrado por completo; porta
  liberada (conexão recusada após o encerramento).
- Nenhum defeito funcional restante: um defeito real foi encontrado durante
  a escrita dos testes (`validate_inputs` aceitava `None`/tipos não-`dict`
  e vazava `TypeError` cru em vez de `InputValidationError`) e corrigido de
  forma mínima e cirúrgica em `src/inferencia.py`, com autorização
  explícita, antes de finalizar a suíte — ver relatório da TASK 010 para o
  detalhe exato da correção.

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

## 11. Critérios para aprovação da TASK 010

1. `tests/test_inferencia_aplicacao.py` e `tests/test_streamlit_app.py`
   criados e aprovados isoladamente (95/95, 0 falhas/erros/skips).
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
7. Após o stage dos cinco arquivos desta TASK (`docs/TASKS.md`,
   `docs/testes_aplicacao.md`, `src/inferencia.py`,
   `tests/test_inferencia_aplicacao.py`, `tests/test_streamlit_app.py`), a
   suíte completa do projeto atinge 235 testes aprovados, 0 falhas, 0 erros
   e 0 skips (140 testes anteriores + 95 novos desta TASK).
