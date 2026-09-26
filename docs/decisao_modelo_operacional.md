# Decisão do modelo operacional

Decisão do grupo formalizada na TASK 008 (FASE 3 do plano em [TASKS.md](TASKS.md)),
a partir da inspeção direta dos artefatos oficiais de modelagem. Este documento
define o contrato que a aplicação Streamlit (TASK 009) deverá seguir; **não
implementa a aplicação**.

## 1. Contexto

A aplicação Streamlit tem finalidade **educacional e demonstrativa**: mostrar,
de forma interativa, como o modelo já avaliado classifica uma transição
aluno-ano hipotética, sem produzir nenhuma nova avaliação estatística. O
modelo em questão — `logistica`, uma regressão logística regularizada — já foi
treinado exclusivamente em 2022→2023 e avaliado uma única vez, de forma
temporal, em 2023→2024 (ver
[relatório de modelagem](../reports/relatorio_modelagem.md) e
[métricas](../reports/metricas_modelagem.json)). É necessário preservar a
correspondência exata entre o artefato que a aplicação carrega e as métricas
que o projeto divulga: qualquer artefato diferente do avaliado tornaria as
métricas oficiais (AP, ROC-AUC, precisão, recall, Brier e seus intervalos)
inválidas para descrever o comportamento real da aplicação.

O [contrato metodológico](contrato_metodologico.md) e o
[registro de decisões](registro_decisoes.md) de 17/09/2026 previam, como plano
futuro, um "modelo final do Streamlit" retreinado com as duas transições
rotuladas ("O modelo final do Streamlit será retreinado futuramente com as
duas transições rotuladas..."). A decisão desta TASK **substitui esse plano
para a presente entrega**: a aplicação usará diretamente o modelo já avaliado,
sem retreinamento algum. Essa mudança de rumo está registrada explicitamente
na seção 3 e na seção 11 abaixo; a atualização formal do registro de decisões
histórico não faz parte do escopo autorizado desta TASK.

## 2. Decisão

- A aplicação Streamlit utilizará **diretamente o modelo oficialmente
  avaliado**, persistido em `artifacts/modelo_avaliado.joblib`.
- **Não haverá retreinamento**, ajuste incremental (`partial_fit`) ou criação
  de um novo modelo nesta entrega.
- A aplicação utilizará o **schema oficial** (`artifacts/schema_modelo.json`)
  como único contrato de entrada e saída — ordem dos preditores, tipos,
  categorias de fase e classe positiva.
- A aplicação utilizará o **limiar congelado** registrado no schema e na
  configuração congelada (`0.26696679375725973`), sem recalibração.
- **Nenhuma substituição silenciosa**: a aplicação deve verificar a
  integridade do artefato (hash) antes de usá-lo e falhar de forma controlada
  se o artefato carregado não corresponder ao registrado.

## 3. Justificativa

- As métricas publicamente divulgadas (seção "Avaliação temporal única" do
  [relatório de modelagem](../reports/relatorio_modelagem.md)) só descrevem o
  comportamento de `artifacts/modelo_avaliado.joblib` com o limiar
  `0.26696679375725973`; usar qualquer outro artefato tornaria essas métricas
  enganosas.
- Evita apresentar ao público o desempenho de um artefato diferente do que
  gerou os números divulgados (risco de "bait and switch" metodológico).
- Preserva a rastreabilidade construída nas TASKs 001–007: hash do modelo,
  hash da configuração congelada e hash do schema continuam verificáveis
  ponta a ponta.
- Respeita a regra permanente de governança do projeto (`docs/TASKS.md`): "É
  proibido reabrir a avaliação temporal, repetir o acesso ao conjunto de teste
  ou recalibrar o limiar congelado."
- Reduz risco metodológico e operacional: retreinar agora, sem um processo de
  validação equivalente ao já realizado (seleção apenas no desenvolvimento,
  congelamento antes do teste, avaliação temporal única), reabriria decisões
  já encerradas e exigiria nova revisão completa de validação antes de poder
  ser usado com a mesma confiança.

## 4. Artefatos oficiais

Caminhos reais, confirmados por inspeção direta dos arquivos (nenhum arquivo
foi copiado ou gerado para este documento):

| Artefato | Caminho | Observação |
| --- | --- | --- |
| Modelo | `artifacts/modelo_avaliado.joblib` | `sklearn.pipeline.Pipeline` com as etapas `preprocessamento` (`ColumnTransformer`) e `modelo` (`LogisticRegression`); `classes_ == [0, 1]`. |
| Schema | `artifacts/schema_modelo.json` | Contrato de colunas, tipos, categorias de fase, classe positiva e limiar. |
| Configuração congelada | `artifacts/configuracao_congelada.json` | Protocolo, hiperparâmetros, hashes de entrada, hash canônico da configuração. |
| Registro da avaliação temporal | `artifacts/avaliacao_temporal.json` | Status `concluida`, timestamps de abertura/conclusão, hashes das saídas oficiais. |
| Métricas | `reports/metricas_modelagem.json` | Métricas OOF e temporais, robustez, calibração, interpretabilidade. |
| Relatório | `reports/relatorio_modelagem.md` | Narrativa e tabelas públicas das métricas. |
| Hash do modelo | `schema_modelo.json.modelo_sha256` = `88098ab093fab4eccda475a340a85dd541ffda936a839ce79c3449a3b02dafab`; confirmado, com o mesmo valor, em `avaliacao_temporal.json.output_hashes["artifacts/modelo_avaliado.joblib"]` | Conferido com `rastreabilidade.file_matches_sha256`. Duas fontes públicas independentes registram o mesmo hash. |
| Hash canônico da configuração | `configuracao_congelada.json.sha256` = `85e1e2cd77fa3555f50553078e7dccb72e03152a4c9bb41e293811e99ac87444` | Recalculável com `modelagem.stable_hash(configuracao["configuracao"])`. |
| Cópias do hash da configuração (chave `configuracao_sha256`) | `schema_modelo.json.configuracao_sha256`, `avaliacao_temporal.json.configuracao_sha256` e `reports/metricas_modelagem.json.configuracao_sha256` | **Três** registros que devem ser idênticos entre si e idênticos ao hash canônico da linha acima. |
| Hash do arquivo do schema | `avaliacao_temporal.json.output_hashes["artifacts/schema_modelo.json"]` = `6df5fa1f9d7aae65e4c5442e03417761a0248dcc161de977fc0a0cd30cce5358` | Hash do arquivo `schema_modelo.json` em si (bytes do JSON), distinto do `modelo_sha256` que esse mesmo arquivo carrega como conteúdo. |
| Código de validação reutilizável | `src/modelagem.py` (`validate_frozen`, `verify_hashes`, `read_json`, `stable_hash`) e `src/rastreabilidade.py` (`sha256_file`, `file_matches_sha256`) | Todas as verificações de `validate_frozen` usam apenas artefatos públicos (ver seção 7) e podem ser reaproveitadas pela aplicação. **`modelagem.validate_artifacts` está fora desta lista — ver seção 7 e a separação obrigatória abaixo.** |

## 5. Contrato de entrada

Sete preditores, **nesta ordem obrigatória** (`schema_modelo.json.colunas`,
idêntica a `preparacao_coortes.FEATURES`):

| # | Campo | Tipo (schema) | Obrigatório | Domínio/restrição comprovada | Ausência |
| --- | --- | --- | --- | --- | --- |
| 1 | `ida` | número anulável | Sim, como coluna do formulário | Numérico finito (a validação oficial só exige tipo numérico e ausência de `inf`; o pipeline **não** impõe um mínimo/máximo). | Aceita ausência: imputada pela **mediana do desenvolvimento**, já embutida no `SimpleImputer` do pipeline. |
| 2 | `ieg` | número anulável | Sim | Numérico finito, sem limite imposto pelo pipeline. | Imputada pela mediana do desenvolvimento. |
| 3 | `iaa` | número anulável | Sim | Numérico finito, sem limite imposto pelo pipeline. | Imputada pela mediana do desenvolvimento. |
| 4 | `ips` | número anulável | Sim | Numérico finito, sem limite imposto pelo pipeline. | Imputada pela mediana do desenvolvimento. |
| 5 | `ipv` | número anulável | Sim | Numérico finito, sem limite imposto pelo pipeline. | Imputada pela mediana do desenvolvimento. |
| 6 | `fase_origem` | string categórica | Sim | Domínio fechado `schema_modelo.json.categorias_fase` = `"0"` a `"7"` (oito categorias, fases 8 e 9 fora do domínio do modelo, conforme o [contrato metodológico](contrato_metodologico.md)). | **Não pode ser nula** (`validate_X` de `src/modelagem.py` recusa `fase_origem` ausente); uma fase fora do domínio **não gera erro no pipeline** — o `OneHotEncoder(handle_unknown="ignore")` a converte silenciosamente em vetor zero. A aplicação deve validar o domínio **antes** de chamar o modelo, para não depender desse comportamento silencioso. |
| 7 | `defasagem_origem` | número anulável | Sim | Numérico finito (inteiro na prática, mas o schema não declara um tipo inteiro estrito nem uma faixa). | Imputada pela mediana do desenvolvimento. |

Restrições adicionais comprovadas no código (`src/modelagem.py:validate_X`),
válidas para todo o conjunto de entrada:

- As sete colunas devem estar presentes **exatamente nesta ordem** — qualquer
  ordem diferente é rejeitada (`"Schema/ordem: somente os sete preditores
  aprovados"`).
- Nenhum campo numérico pode ser `inf`/`-inf`.
- `fase_origem` não pode ser nula.
- Nenhum identificador (RA, nome ou qualquer outro) pode compor a entrada;
  os sete campos acima são a lista fechada.

Não há, em nenhum artefato oficial, uma faixa numérica mínima/máxima
imposta pelo pipeline para `ida`, `ieg`, `iaa`, `ips`, `ipv` ou
`defasagem_origem`; a faixa "0–10" citada na documentação do projeto é uma
faixa operacional **descritiva** dos indicadores originais, não um limite
tecnicamente imposto ao modelo. A aplicação pode optar por alertar o usuário
sobre valores fora dessa faixa operacional usual, mas isso é uma camada de
usabilidade a decidir na TASK 009, não uma restrição do modelo.

**Mensagem esperada para entrada inválida:** a aplicação deve recusar a
inferência e informar objetivamente qual campo falhou (nome do campo e
motivo — ausente, não numérico, `inf`/`-inf`, ou fase fora de `"0"`–`"7"`),
sem tentar corrigir, arredondar ou adivinhar o valor.

## 6. Contrato de saída

- **Probabilidade da classe positiva**: `pipeline.predict_proba(X)[:, 1]`,
  onde `classes_ == [0, 1]` (confirmado no objeto carregado) e a classe
  positiva é `1`, exatamente como registrado em
  `schema_modelo.json.classe_positiva`.
- **Classificação pelo limiar congelado**: risco sinalizado quando
  `probabilidade >= limiar` (`schema_modelo.json.regra_classificacao`); caso
  contrário, sem sinalização de risco.
- **Valor integral do limiar**: `0.26696679375725973`, lido de
  `artifacts/schema_modelo.json` (ou de `configuracao_congelada.json`, que
  deve coincidir) em tempo de execução — nunca reescrito no código da
  aplicação como constante solta.
- **Apresentação arredondada apenas na interface**: qualquer arredondamento
  (por exemplo, exibir a probabilidade com duas ou três casas) deve ocorrer
  somente na camada de exibição; o valor usado para comparar com o limiar
  deve ser o valor de ponto flutuante integral retornado por
  `predict_proba`.
- **Rótulos das classes**: `0` = "sem entrada em defasagem observada no
  destino" (`D_destino >= 0`), `1` = "entrada em defasagem no destino"
  (`D_destino < 0`), exatamente como definido em
  `docs/contrato_metodologico.md` e em `reports/metadados_coortes.json`
  (`cohort_schema.y`). A aplicação não deve usar outros rótulos (como
  "aprovado/reprovado" ou "sucesso/fracasso").
- **Aviso de não causalidade**: a saída deve vir acompanhada de um aviso de
  que a probabilidade é uma associação estatística, não uma relação causal,
  reproduzindo a limitação já registrada em
  `docs/contrato_metodologico.md` ("O modelo será preditivo e observacional.
  Não afirmará causalidade...").
- **Aviso de não substituição de avaliação profissional**: a saída deve
  reproduzir explicitamente que o resultado é apoio à priorização, não
  substitui avaliação pedagógica ou profissional e não decide atendimento ou
  exclusão automaticamente.

## 7. Fluxo de inferência

1. **Inicialização da aplicação**: carregar apenas módulos e artefatos
   públicos; nenhuma leitura de `DATATHON/`, `local_data/` ou
   `local_recovery/`.
2. **Localização portátil da raiz**: localizar a raiz do repositório
   subindo diretórios a partir do arquivo em execução (mesma técnica já usada
   no notebook final — procurar `src/modelagem.py` e `docs/TASKS.md`), sem
   caminhos absolutos.
3. **Validação da existência dos artefatos**: confirmar que os seis
   caminhos públicos existem antes de prosseguir — os cinco artefatos
   necessários à inferência (`artifacts/modelo_avaliado.joblib`,
   `artifacts/schema_modelo.json`, `artifacts/configuracao_congelada.json`,
   `artifacts/avaliacao_temporal.json`, `reports/metricas_modelagem.json`)
   **e** a dependência pública adicional de integridade
   (`docs/contrato_metodologico.md`, exigida por `modelagem.validate_frozen`
   — ver seção 7.1).
4. **Verificação de integridade — validador público** (ver especificação
   completa na seção 7.1): reaproveitar `modelagem.validate_frozen` na
   íntegra — todas as suas verificações usam apenas artefatos públicos — e, em
   seguida, replicar manualmente as poucas verificações de
   `modelagem.validate_artifacts` que também são públicas.
   **`modelagem.validate_artifacts` nunca é chamada pela aplicação**, porque
   uma de suas verificações internas exige hashes de arquivos privados em
   `local_data/` (detalhado na seção 7.1).
5. **Carregamento único e cacheado**: carregar o pipeline com `joblib.load`
   uma única vez por processo (cache do framework da aplicação), nunca a cada
   interação do usuário.
6. **Validação das sete entradas**: aplicar as regras da seção 5 (tipo,
   ausência de `inf`, domínio de `fase_origem`, ordem) antes de montar a
   entrada do modelo.
7. **Construção da entrada na ordem oficial**: montar um `DataFrame` de uma
   linha com exatamente as colunas de `FEATURES`/`schema_modelo.json.colunas`,
   na ordem oficial, com `fase_origem` como `string`.
8. **Execução do método oficial de inferência**: chamar
   `pipeline.predict_proba(X)` — nunca `predict` isoladamente (que aplicaria
   o limiar `0.5` padrão do scikit-learn em vez do limiar congelado) e nunca
   `fit`/`fit_transform`/`partial_fit`.
9. **Extração da probabilidade positiva**: usar a coluna correspondente a
   `classes_ == 1` (posição `[:, 1]` neste pipeline, mas a aplicação deve
   localizar a posição pelo array `classes_` em vez de fixar o índice `1` às
   cegas, para não quebrar silenciosamente se o artefato mudar).
10. **Aplicação do limiar congelado**: comparar a probabilidade extraída ao
    limiar lido do schema (`>=`), sem qualquer ajuste.
11. **Apresentação do resultado**: mostrar probabilidade, classificação e os
    avisos da seção 6.
12. **Descarte da entrada sem persistência**: a entrada do usuário e o
    resultado vivem apenas na sessão da interação; nada é gravado em disco,
    log ou banco de dados.

### 7.1 Validador público (a implementar na TASK 009)

Esta seção corrige e substitui qualquer afirmação anterior sobre o que
`modelagem.validate_frozen` verifica, e define, de forma exaustiva, o
validador que a TASK 009 deve implementar antes de qualquer inferência.

**O que `modelagem.validate_frozen` realmente faz** (inspecionado diretamente
em `src/modelagem.py`, sem inferência a partir do nome da função):

1. Lê `artifacts/configuracao_congelada.json`.
2. Recalcula `modelagem.stable_hash(configuracao["configuracao"])` e exige que
   o resultado seja igual a `configuracao_congelada.json.sha256` (o hash
   canônico); também exige que `configuracao["protocolo"]` seja idêntico à
   constante `PROTOCOL` do código.
3. Confere os hashes históricos de código de `src/modelagem.py` e
   `src/relatorio_modelagem.py` (apenas formato/presença, via
   `validate_historical_code_hashes` — **não** recalcula o hash desses
   arquivos no estado atual).
4. Confere o hash de `docs/contrato_metodologico.md`.
5. Compara as versões de pacotes instaladas no ambiente com
   `configuracao["packages"]`.
6. Lê `artifacts/schema_modelo.json` e confere que
   `schema["configuracao_sha256"]` é igual ao hash canônico, que
   `schema["colunas"]` é igual a `preparacao_coortes.FEATURES` e que
   `schema["limiar"]` é igual a `configuracao["limiar"]`.
7. Confere o hash de `artifacts/modelo_avaliado.joblib` contra
   `schema["modelo_sha256"]`.

**`modelagem.validate_frozen` não lê `artifacts/avaliacao_temporal.json` em
nenhum momento.** A afirmação anterior deste documento, de que
`validate_frozen` confere `configuracao_sha256` entre os três artefatos
(configuração congelada, schema **e avaliação temporal**), estava incorreta e
foi corrigida: a ligação com `avaliacao_temporal.json` **não** é feita por
`validate_frozen`; é o validador público (abaixo) que a faz, separadamente,
com arquivos exclusivamente públicos. Nenhum dos sete passos acima toca
`local_data/`, `local_recovery/` ou `DATATHON/` — por isso a função inteira
pode ser reaproveitada pela aplicação.

**Por que `modelagem.validate_artifacts` é proibida no deploy público:**
`validate_artifacts` chama `validate_frozen` e, logo em seguida, executa
`verify_hashes(root, frozen["configuracao"]["input_hashes"])`. Esses
`input_hashes` (registrados em
`configuracao_congelada.json.configuracao.input_hashes`) são exatamente os
sete arquivos privados de `local_data/`: `local_data/coorte_desenvolvimento.csv`,
`local_data/X_desenvolvimento.csv`, `local_data/y_desenvolvimento.csv`,
`local_data/coorte_teste_temporal.csv`, `local_data/X_teste_temporal.csv`,
`local_data/y_teste_temporal.csv` e `local_data/coortes_modelagem.jsonl`.
Como esses arquivos não são versionados e não existem em um deploy público,
essa chamada falharia (ou, pior, exigiria copiar dados privados para o
ambiente de produção só para satisfazer a validação). Por isso:

> **`modelagem.validate_artifacts` é proibido no deploy público porque
> depende de arquivos privados em `local_data/`.**

- `modelagem.validate_artifacts` **não será chamada pelo Streamlit**, em
  nenhum ambiente (nem localmente, nem no Community Cloud).
- A aplicação publicada **não dependerá** de `DATATHON/`, `local_data/` ou
  `local_recovery/` para inicializar nem para operar.
- A **ausência** dessas três pastas **não pode impedir** a inicialização do
  aplicativo nem a execução de nenhuma inferência.
- Nenhuma validação pública pode tentar acessar coortes, matrizes `X`/`y` ou
  qualquer derivado individual — nem para ler, nem para conferir hash.

**Fluxo completo do validador público.** O validador público utiliza cinco
artefatos necessários à inferência e uma dependência pública adicional de
integridade, `docs/contrato_metodologico.md`, exigida por
`modelagem.validate_frozen`:

- **Cinco artefatos públicos necessários à inferência**:
  `artifacts/modelo_avaliado.joblib`, `artifacts/schema_modelo.json`,
  `artifacts/configuracao_congelada.json`, `artifacts/avaliacao_temporal.json`
  e `reports/metricas_modelagem.json`.
- **Uma dependência pública adicional de integridade**:
  `docs/contrato_metodologico.md`. `modelagem.validate_frozen` lê esse
  arquivo e confere seu hash (`rastreabilidade.file_matches_sha256`) contra
  `configuracao_congelada.json.configuracao.contrato_sha256` — por isso o
  contrato metodológico **precisa existir** no deploy para que a validação
  seja concluída. O arquivo é puramente textual e metodológico, não contém
  nenhum dado privado, e sua presença **não** cria dependência de
  `DATATHON/`, `local_data/` ou `local_recovery/` — ele já é versionado em
  `docs/` como qualquer outro documento público do projeto.

Nenhum outro arquivo é necessário; nenhum deles pertence a `local_data/`,
`local_recovery/` ou `DATATHON/`.

1. **Existência dos seis caminhos públicos**: confirmar que os cinco
   artefatos de inferência e `docs/contrato_metodologico.md` existem antes de
   ler qualquer um deles.
2. **Reaproveitar `modelagem.validate_frozen(root)` por inteiro** — cobre os
   sete passos listados acima (hash canônico, protocolo, código histórico,
   contrato, pacotes, schema, hash do modelo). Nenhuma adaptação é necessária
   porque nada nela depende de dados privados.
3. **Hash portátil do arquivo do schema**: conferir
   `artifacts/schema_modelo.json` com
   `rastreabilidade.file_matches_sha256(schema_path, hash)`, usando
   `hash = avaliacao_temporal.json.output_hashes["artifacts/schema_modelo.json"]`
   (valor oficial atual:
   `6df5fa1f9d7aae65e4c5442e03417761a0248dcc161de977fc0a0cd30cce5358`). Esta é
   uma verificação **distinta** da que `validate_frozen` já faz no passo 7
   acima (que confere o `modelo_sha256` **dentro** do schema contra o
   `.joblib`); aqui se confere o hash do **próprio arquivo** `schema_modelo.json`.
4. **Hash binário exato do modelo**: conferir
   `artifacts/modelo_avaliado.joblib` com
   `rastreabilidade.file_matches_sha256`, usando o hash oficial registrado —
   `schema_modelo.json.modelo_sha256` (já conferido por `validate_frozen`) e,
   como confirmação cruzada independente,
   `avaliacao_temporal.json.output_hashes["artifacts/modelo_avaliado.joblib"]`;
   ambos devem ser iguais a
   `88098ab093fab4eccda475a340a85dd541ffda936a839ce79c3449a3b02dafab`.
5. **Os três registros de `configuracao_sha256`**: carregar e exigir
   igualdade entre exatamente estes três arquivos/chaves —
   `artifacts/schema_modelo.json.configuracao_sha256`,
   `artifacts/avaliacao_temporal.json.configuracao_sha256` e
   `reports/metricas_modelagem.json.configuracao_sha256` (não inventar outras
   chaves ou arquivos). Também exigir que os três sejam iguais ao hash
   canônico `artifacts/configuracao_congelada.json.sha256`.
6. **Recalcular a identificação estável**: chamar
   `modelagem.stable_hash(configuracao_congelada["configuracao"])` (a mesma
   função oficial já usada dentro de `validate_frozen`) e comparar o
   resultado ao `sha256` canônico e aos três registros do passo 5. Este
   recálculo já ocorre dentro de `validate_frozen` (passo 2 acima); o
   validador público não precisa repeti-lo, apenas confirmar que o valor
   retornado por `validate_frozen` foi de fato usado nas comparações do passo 5.
7. **Igualdade do limiar**: comparar, como número (não como texto
   formatado), `artifacts/configuracao_congelada.json.configuracao.limiar`,
   `artifacts/schema_modelo.json.limiar` e
   `reports/metricas_modelagem.json.limiar` — os três devem ser exatamente
   `0.26696679375725973`. Usar o valor de ponto flutuante lido do artefato em
   tempo de execução; nunca um valor alternativo hardcoded no código da
   aplicação.
8. **Compatibilidade entre schema e objeto `joblib`**: após carregar o
   pipeline, confirmar (a) `hasattr(pipeline, "predict_proba")`; (b) que o
   atributo `classes_` do pipeline (exposto a partir da etapa final `modelo`)
   é exatamente `[0, 1]`; e (c) que `schema_modelo.json.classe_positiva == 1`
   está entre os valores de `classes_`. A ordem dos sete preditores já é
   conferida no passo 2 (`validate_frozen` compara `schema["colunas"]` a
   `preparacao_coortes.FEATURES`); o validador público não precisa repetir
   essa comparação, apenas usar a mesma ordem ao montar a entrada (seção 5).
9. **Falha controlada**: qualquer divergência em qualquer um dos passos
   acima deve interromper a inicialização da aplicação com uma mensagem
   objetiva sobre qual verificação falhou — nunca permitir que a aplicação
   sirva inferências com um artefato não verificado.
10. **Proibições explícitas do validador público**: não retreinar; não
    recalibrar o limiar; não regenerar nenhum artefato; não "corrigir" um
    hash divergente reescrevendo o valor esperado; não acessar
    `DATATHON/`, `local_data/` ou `local_recovery/` em nenhuma etapa; não
    usar nenhum fallback silencioso (como prosseguir com um modelo/schema não
    verificado, ou substituir um hash divergente por "verificação
    aproximada").

**Separação obrigatória entre dois tipos de validação neste projeto:**

| | Validação histórica/completa do projeto | Validação pública de inferência |
| --- | --- | --- |
| Função | `modelagem.validate_artifacts` (chama `validate_frozen` internamente) | `modelagem.validate_frozen` + os passos 3–8 acima, implementados na TASK 009 |
| Depende de `local_data/`? | Sim — via `input_hashes` | Não, nunca |
| Onde é usada | Notebook final (TASK 007), verificação de entrega (`src/verificar_entrega.py`), ambiente de desenvolvimento com os dados privados disponíveis | Aplicação Streamlit publicada (TASK 009), em qualquer ambiente, com ou sem os dados privados |
| Pode rodar sem `DATATHON/`/`local_data/`/`local_recovery/`? | Não | Sim — é um requisito |

## 8. Tratamento de erros

| Situação | Comportamento exigido |
| --- | --- |
| Artefato ausente (`.joblib`, schema ou configuração congelada não encontrados) | Falhar de forma controlada com mensagem clara sobre qual arquivo falta; não tentar gerar um substituto. |
| Hash divergente (modelo, schema ou configuração alterados) | Recusar carregar e informar que a integridade do artefato oficial não foi confirmada; não prosseguir com um modelo "parecido". |
| Schema incompatível (colunas, ordem, tipos ou limiar diferentes do esperado pela aplicação) | Recusar a inferência e reportar a divergência; não adaptar a entrada ao schema encontrado. |
| Campo ausente na entrada do usuário | Rejeitar a inferência, indicando o campo específico ausente. |
| Valor inválido (não numérico onde se espera número, texto vazio, etc.) | Rejeitar a inferência, indicando o campo e o motivo. |
| Categoria desconhecida em `fase_origem` (fora de `"0"`–`"7"`) | Rejeitar explicitamente na validação da aplicação, **antes** do `OneHotEncoder`, já que o pipeline por si só apenas geraria um vetor zero sem erro. |
| Erro de carregamento do artefato (arquivo corrompido, versão de `scikit-learn`/`joblib` incompatível) | Capturar a exceção, informar o erro de forma genérica e segura (sem stack trace bruto exposto ao usuário final) e não prosseguir. |
| Saída não finita (`NaN`/`inf` na probabilidade) | Tratar como falha da inferência, nunca exibir um resultado não numérico como se fosse válido. |
| Probabilidade fora de `[0, 1]` | Tratar como falha da inferência (indício de artefato ou entrada corrompidos); não recortar (`clip`) silenciosamente o valor para dentro do intervalo. |

Em nenhum desses casos a aplicação deve treinar, retreinar, recalibrar o
limiar ou "corrigir" o modelo automaticamente; a única ação permitida é
falhar de forma clara e seguramente informativa.

## 9. Privacidade

- Nenhum campo de entrada da aplicação deve ser ou conter RA.
- Nenhum campo de entrada deve ser ou conter nome ou qualquer outro
  identificador pessoal.
- Nenhuma base de dados individual (`DATATHON/`, `local_data/`,
  `local_recovery/`) é carregada pela aplicação em nenhum momento.
- Nenhuma persistência das entradas fornecidas pelo usuário (sem escrita em
  disco, banco de dados ou cache duradouro).
- Nenhum log deve registrar os valores informados pelo usuário nem a
  probabilidade/classificação resultante de uma sessão específica.
- A aplicação usa **somente** os sete preditores do contrato (`ida`, `ieg`,
  `iaa`, `ips`, `ipv`, `fase_origem`, `defasagem_origem`); nenhum campo
  administrativo, cadastral ou demográfico é solicitado.
- Quaisquer exemplos, valores padrão ou casos de demonstração exibidos na
  interface devem ser **exclusivamente sintéticos**, nunca extraídos de
  `local_data/` ou de qualquer registro real de aluno.

## 10. Limitações

A aplicação deve deixar visíveis, de forma acessível ao usuário (não apenas
em documentação técnica), as limitações já registradas na avaliação oficial:

- **Queda de recall no teste temporal**: de 81,7% (OOF, desenvolvimento) para
  40,5% (teste temporal 2023→2024) — uma queda de 41,2 pontos percentuais
  (`reports/metricas_modelagem.json`, `diferenca_temporal_menos_oof.recall`).
- **Subestimação de risco observada**: no teste temporal, a calibração ficou
  acima da diagonal ideal (probabilidade prevista menor que a fração real de
  eventos nas faixas mais baixas), isto é, o modelo tende a **subestimar** o
  risco no ano seguinte.
- **Caráter observacional**: o modelo é preditivo e observacional, não
  diagnóstico.
- **Ausência de inferência causal**: nenhuma associação encontrada pelo
  modelo ou pelas análises de negócio deve ser lida como causa.
- **Finalidade educacional**: a aplicação demonstra o funcionamento do
  modelo avaliado; não é um sistema de produção institucional.
- **Necessidade de supervisão humana**: toda saída exige revisão por equipe
  pedagógica/profissional antes de qualquer ação.
- **Risco de mudança de distribuição**: a população de 2023→2024 já diferiu
  da de 2022→2023 em indicadores como IPS (diferença padronizada relevante,
  ver `reports/relatorio_modelagem.md`, seção "Mudança de distribuição");
  populações futuras podem divergir ainda mais, sem garantia de que o
  desempenho observado se repita.
- **Proibição de decisão automatizada de alto impacto**: a saída não pode
  decidir, por si só, inclusão, exclusão, atendimento ou qualquer ação
  administrativa sobre um aluno real.

## 11. Alternativas consideradas

- **Retreinamento final com as duas transições rotuladas** (a opção
  originalmente prevista no [contrato metodológico](contrato_metodologico.md)
  e no [registro de decisões](registro_decisoes.md) de 17/09/2026). **Não
  adotada nesta entrega** porque exigiria uma nova revisão completa de
  validação (nova seleção, novo congelamento, e — para manter o mesmo padrão
  metodológico do projeto — um novo horizonte de avaliação, já que não
  restaria um terceiro ano reservado para testar esse novo artefato sem
  vazamento), o que está fora do escopo e do prazo desta entrega e romperia a
  correspondência entre o artefato em produção e as métricas já divulgadas.
- **Criação de um modelo operacional separado** (mesmo algoritmo, mas
  ajustado com dados adicionais ou reconfigurado especificamente para a
  aplicação). **Não adotada nesta entrega** pelo mesmo motivo: qualquer
  artefato novo precisaria de identificação própria e de uma avaliação
  independente antes de ser usado, o que não foi realizado.
- **Recalibração do limiar** (por exemplo, buscar um novo ponto de corte a
  partir do desempenho observado no teste temporal). **Não adotada** porque
  violaria diretamente a regra permanente de governança do projeto ("é
  proibido... recalibrar o limiar congelado") e invalidaria a interpretação
  já publicada das métricas oficiais (que dependem do limiar
  `0.26696679375725973` fixado antes da abertura do teste).

## 12. Evolução futura

Um eventual retreinamento futuro (incluindo o "modelo final do Streamlit"
originalmente previsto no contrato metodológico) deverá:

- gerar um **artefato separado**, com nome e caminho próprios (nunca
  sobrescrever `artifacts/modelo_avaliado.joblib`);
- possuir **identificação e versão próprias**, distintas da configuração
  congelada atual (`85e1e2cd77fa3555f50553078e7dccb72e03152a4c9bb41e293811e99ac87444`);
- passar por **nova validação**, com seu próprio processo de seleção,
  congelamento e (quando aplicável) avaliação, documentado de forma
  equivalente ao já feito para o modelo atual;
- **não herdar automaticamente** as métricas oficiais deste modelo avaliado
  — um modelo operacional retreinado precisa de sua própria evidência de
  desempenho, obtida sem vazamento;
- **não substituir silenciosamente** o modelo atual: qualquer substituição
  exige nova decisão explícita e documentada, análoga a esta.

## 13. Critérios de aceite da aplicação (TASK 009)

A implementação da TASK 009 só poderá ser considerada concluída quando:

1. A aplicação carregar exclusivamente
   `artifacts/modelo_avaliado.joblib`, sem qualquer chamada a
   `fit`/`fit_transform`/`partial_fit` em nenhum caminho de código.
2. A aplicação executar o **validador público** da seção 7.1 (reaproveitando
   `modelagem.validate_frozen` por inteiro, mais os passos 3–8 daquela seção)
   antes de qualquer inferência, **sem nunca chamar `modelagem.validate_artifacts`**.
3. A entrada do usuário for validada exatamente pelas regras da seção 5
   (sete campos, ordem oficial, tipos, domínio de `fase_origem`, ausência de
   `inf`) antes de qualquer chamada ao modelo.
4. A inferência usar `predict_proba`, extrair a probabilidade da classe `1`
   localizando a posição por `classes_` (não por índice fixo às cegas) e
   aplicar exatamente o limiar `0.26696679375725973` lido do artefato em
   tempo de execução.
5. A saída exibir probabilidade, classificação, os rótulos corretos das
   classes e os avisos de não causalidade e de não substituição de avaliação
   profissional (seção 6).
6. A interface exibir de forma visível as limitações da seção 10, com pelo
   menos a queda de recall e a subestimação de risco observadas no teste
   temporal.
7. Nenhuma entrada do usuário (nem a probabilidade/classificação resultante)
   for persistida, logada ou reaproveitada entre sessões.
8. Nenhum campo de RA, nome ou identificador pessoal for solicitado ou
   aceito pela interface.
9. Nenhum dos diretórios `DATATHON/`, `local_data/` ou `local_recovery/` for
   lido pela aplicação em nenhuma circunstância, e a ausência deles não
   impedir a inicialização (consequência direta de nunca chamar
   `modelagem.validate_artifacts`, conforme a seção 7.1).
10. Todos os casos da seção 8 (artefato ausente, hash divergente, schema
    incompatível, campo ausente, valor inválido, categoria desconhecida,
    erro de carregamento, saída não finita, probabilidade fora de `[0, 1]`)
    produzirem uma falha controlada e compreensível, sem exceção não tratada
    visível ao usuário e sem tentativa de correção automática do modelo.
11. Nenhum arquivo em `artifacts/` ou `reports/` for alterado, sobrescrito
    ou regenerado pela aplicação.
12. A aplicação funcionar a partir de caminhos relativos à raiz do
    repositório, sem caminho absoluto local embutido, em Windows e em Linux.
