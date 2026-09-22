# Plano de TASKs — FIAP Datathon Fase 5

## Objetivo geral

Concluir e publicar o projeto FIAP Datathon Fase 5 de forma reproduzível, auditável e segura, preservando a metodologia e os resultados já congelados, transformando-os em notebook, aplicação e comunicação final sem reabrir decisões estatísticas encerradas. O planejamento compreende sete fases e 17 TASKs, numeradas de 000 a 016.

Referências de controle:

- branch de trabalho: `feat/notebook-final`;
- baseline original: commit `265434d`, tag `v0.4-analises-negocio`;
- correção de portabilidade: commit verificado `cd2f97d`;
- suíte de regressão: 79 testes aprovados;
- artefatos de modelagem, métricas, limiar e avaliação temporal: congelados.

## Regras de governança

### Estados

- **DONE:** concluída, validada, com evidência objetiva e versionada.
- **IMPLEMENTED:** implementada e validada localmente, aguardando revisão ou commit.
- **READY:** escopo e dependências permitem início imediato.
- **DRAFT:** escopo ainda sujeito a decisão.
- **BLOCKED:** não pode começar ou terminar enquanto outra TASK indicada estiver pendente.

### Responsabilidade e revisão

Cada TASK deve ter um único executor responsável. Quando possível, deve haver um revisor independente, diferente do executor. A ausência de autoria histórica documentada não deve ser preenchida por suposição; nesses casos, o executor é registrado como **trabalho consolidado anteriormente**.

### Restrições permanentes

- É proibido reabrir a avaliação temporal, repetir o acesso ao conjunto de teste ou recalibrar o limiar congelado.
- É proibido alterar resultados congelados para acomodar notebook, aplicação, documentação ou apresentação.
- É proibido versionar `DATATHON/`, `local_data/`, `local_recovery/` e `.venv/`.
- Dados individuais ou identificadores pessoais não podem aparecer em artefatos públicos, logs, capturas, aplicação ou apresentação.
- Mudanças devem preservar rastreabilidade, separação temporal e verificações de integridade existentes.

## FASE 0 — Governança

### TASK 000 — Organização e controle do projeto

- **Estado:** DONE.
- **Objetivo:** manter uma fonte única para estados, dependências, responsabilidades, evidências e caminho crítico do trabalho restante.
- **Dependências:** nenhuma.
- **Entregáveis:** `docs/TASKS.md` atualizado; tabela-resumo; caminho crítico; checklist de mudança de estado.
- **Critérios de aceite:** todas as TASKs 000–016 registradas; estados e dependências coerentes; próxima TASK explicitada; documento aprovado e versionado para chegar a DONE.
- **Restrições importantes:** não substituir evidências técnicas; não atribuir autoria sem documentação; não alterar arquivos de produto nesta TASK.
- **Executor:** Jônatas Silva.
- **Revisor:** GPT/Codex — revisão documental assistida em 21/09/2026.
- **Evidências de conclusão:** Documento revisado em 21/09/2026 e versionado no commit de conclusão desta TASK.

## FASE 1 — Dados e metodologia

### TASK 001 — Auditoria e integridade das fontes

- **Estado:** DONE.
- **Objetivo:** auditar a integridade das 13 fontes privadas, preservando os originais, sua rastreabilidade e sua proteção.
- **Dependências:** nenhuma.
- **Entregáveis:** inventário das 13 fontes; hashes SHA-256; registros de preservação dos originais; rastreabilidade; mecanismos de proteção das fontes privadas; relatório de auditoria.
- **Critérios de aceite:** 13 fontes identificadas; hashes binários conferidos; originais preservados; associação com a origem validada; rastreabilidade documentada; nenhum dado privado versionado.
- **Restrições importantes:** fontes privadas são somente leitura; comparação binária exata; proibição de publicar dados individuais.
- **Executor:** trabalho consolidado anteriormente.
- **Revisor:** não identificado documentalmente.
- **Evidências de conclusão:** baseline `265434d`; tag `v0.4-analises-negocio`; inventários, relatórios e testes de auditoria versionados.

### TASK 002 — Preparação longitudinal

- **Estado:** DONE.
- **Objetivo:** consolidar os dados de 2022, 2023 e 2024 em uma base longitudinal validada e adequada às análises.
- **Dependências:** TASK 001.
- **Entregáveis:** consolidação de 2022, 2023 e 2024; schemas e campos padronizados; tratamentos necessários à análise; base derivada privada; metadados e relatórios da preparação.
- **Critérios de aceite:** 3.030 registros conferidos; schemas e campos conciliados com as fontes; ausências não convertidas indevidamente em zero; duplicidades e estados de RA tratados; testes aprovados.
- **Restrições importantes:** derivados individuais permanecem fora do Git; nenhuma imputação ou correção silenciosa da origem.
- **Executor:** trabalho consolidado anteriormente.
- **Revisor:** não identificado documentalmente.
- **Evidências de conclusão:** código, metadados, relatório e testes presentes no baseline versionado.

### TASK 003 — Contrato metodológico e coortes temporais

- **Estado:** DONE.
- **Objetivo:** definir o problema, a variável-alvo, os sete preditores e as regras metodológicas das coortes de desenvolvimento e teste temporal.
- **Dependências:** TASKs 001 e 002.
- **Entregáveis:** contrato metodológico; definição da variável-alvo e dos sete preditores; coortes de desenvolvimento e teste temporal; regras metodológicas congeladas; metadados de geração e validação.
- **Critérios de aceite:** problema e alvo documentados; sete preditores fechados; prevenção de vazamento temporal validada; contagens de referência conferidas; hashes das coortes registrados; regras congeladas.
- **Restrições importantes:** não incorporar identificadores ou variáveis futuras; não acessar antecipadamente o teste temporal.
- **Executor:** trabalho consolidado anteriormente.
- **Revisor:** não identificado documentalmente.
- **Evidências de conclusão:** contrato, metadados de coortes e testes de regressão versionados no baseline.

## FASE 2 — Modelagem e análises

### TASK 004 — Modelagem e avaliação temporal

- **Estado:** DONE.
- **Objetivo:** treinar e selecionar o modelo no desenvolvimento, congelar configuração e limiar e realizar uma única avaliação temporal.
- **Dependências:** TASK 003.
- **Entregáveis:** modelo avaliado; configuração congelada; schema; limiar; métricas OOF e temporais; análises de robustez, calibração, equidade e erros; artefatos e limitações documentados.
- **Critérios de aceite:** treinamento e seleção restritos ao desenvolvimento; configuração congelada antes do teste; avaliação temporal única; modelo e entradas com hashes conferidos; métricas, robustez, calibração, equidade e erros validados; limitações explícitas.
- **Restrições importantes:** não reabrir o teste temporal; não retreinar o modelo oficial; não recalibrar ou substituir o limiar; não regenerar artefatos congelados.
- **Executor:** trabalho consolidado anteriormente.
- **Revisor:** não identificado documentalmente.
- **Evidências de conclusão:** artefatos, métricas e avaliação temporal congelados; baseline `265434d`; suíte de regressão aprovada.

### TASK 005 — Análises e perguntas de negócio

- **Estado:** DONE.
- **Objetivo:** responder às 11 perguntas de negócio, produzir dez gráficos agregados e consolidar as principais conclusões com proteção da privacidade.
- **Dependências:** TASKs 002 e 004.
- **Entregáveis:** respostas às 11 perguntas; dez gráficos agregados; principais conclusões; relatório de análises; métricas estruturadas; verificações de privacidade, relatórios e artefatos.
- **Critérios de aceite:** 11 perguntas respondidas; dez figuras válidas; conclusões sustentadas; resultados agregados; ausência de identificadores pessoais; nenhuma chamada de treino; relatórios e artefatos validados contra as métricas oficiais.
- **Restrições importantes:** não expor indivíduos; não reinterpretar associações como causalidade; não modificar o modelo oficial.
- **Executor:** trabalho consolidado anteriormente.
- **Revisor:** não identificado documentalmente.
- **Evidências de conclusão:** tag `v0.4-analises-negocio`, relatórios e testes versionados.

## FASE 3 — Reprodutibilidade e uso operacional

### TASK 006 — Portabilidade dos hashes LF/CRLF

- **Estado:** DONE.
- **Objetivo:** permitir validação portátil de arquivos textuais entre LF e CRLF sem relaxar a integridade do conteúdo ou dos binários.
- **Dependências:** TASKs 001–005.
- **Entregáveis:** comparação centralizada de hashes; integração nas validações; testes de regressão de portabilidade e proveniência histórica.
- **Critérios de aceite:** SHA-256 binário preservado; somente extensões textuais autorizadas toleram LF/CRLF; mudanças reais e binárias falham; 79 testes aprovados.
- **Restrições importantes:** não atualizar hashes ou artefatos congelados; fontes privadas permanecem com igualdade binária exata.
- **Executor:** trabalho consolidado anteriormente.
- **Revisor:** não identificado documentalmente.
- **Evidências de conclusão:** commit verificado `cd2f97d`; suíte com 79 testes aprovada.

### TASK 007 — Notebook final reproduzível

- **Estado:** DONE.
- **Objetivo:** criar o notebook final como narrativa reproduzível dos dados, metodologia, resultados congelados e conclusões, sem repetir a avaliação temporal.
- **Dependências:** TASKs 001–006.
- **Entregáveis:** notebook executável; instruções de execução; células de validação de ambiente e integridade; visualizações e conclusões alinhadas aos resultados oficiais.
- **Critérios de aceite:** execução limpa em ambiente documentado; resultados consistentes com artefatos congelados; ausência de caminhos absolutos e dados pessoais; notebook sem retreino ou recalibração oficial.
- **Restrições importantes:** consumir artefatos existentes; não reabrir teste temporal; não alterar limiar, métricas ou modelo; não embutir dados privados.
- **Executor:** Jônatas Silva — implementação assistida por Claude.
- **Revisor:** GPT/Codex — revisão técnica independente em 22/09/2026.
- **Evidências de conclusão:** notebook criado em `notebooks/datathon_fase5.ipynb`, com 22 seções e 86 células (57 Markdown e 29 de código); execução integral aprovada; execução pública automatizada sem `DATATHON/`, `local_data/` e `local_recovery/` aprovada; modelo, sete preditores, limiar e métricas conferidos diretamente contra os artefatos oficiais; 11 respostas de negócio conferidas; dez gráficos agregados e as curvas oficiais validados por hash; ausência de treinamento, reavaliação e recalibração confirmada por análise AST das células de código; privacidade, caminhos portáveis e ausência de dados individuais validadas; 61 testes específicos do notebook aprovados em `tests/test_notebook_final.py`; 140 testes totais aprovados na suíte completa, com zero falhas, zero erros e zero skips; instalação reproduzível a partir do `requirements.txt` principal, que agora também inclui `notebooks/requirements-notebook.txt`; revisão independente com parecer **APPROVED**; nenhum artefato congelado alterado; versionado no commit de conclusão desta TASK.

### TASK 008 — Definição do artefato operacional

- **Estado:** DONE.
- **Objetivo:** decidir qual artefato e fluxo de inferência serão usados pela aplicação sem confundir demonstração operacional com nova avaliação do modelo.
- **Dependências:** TASK 007 e decisão explícita de produto.
- **Entregáveis:** decisão arquitetural registrada; contrato de entrada e saída; estratégia de carregamento; tratamento de erros e limitações.
- **Critérios de aceite:** alternativa escolhida e justificada; compatibilidade com schema e limiar congelados; riscos de privacidade e operação documentados; aprovação antes da implementação da aplicação.
- **Restrições importantes:** não substituir, sobrescrever ou confundir o modelo oficialmente avaliado com eventual artefato operacional; qualquer retreinamento operacional somente poderá ocorrer após decisão explícita, deverá gerar artefato separado e não poderá herdar as métricas da avaliação temporal oficial; não alterar schema ou limiar; não usar o teste temporal como dado operacional.
- **Executor:** Jônatas Silva — implementação assistida por Claude.
- **Revisor:** GPT/Codex — revisão técnica independente em 22/09/2026.
- **Evidências de conclusão:** decisão documentada em `docs/decisao_modelo_operacional.md` — utilização direta do modelo oficialmente avaliado (`artifacts/modelo_avaliado.joblib`), sem retreinamento nem recalibração; contrato dos sete preditores definido na ordem oficial; classe positiva e `predict_proba` conferidos contra o objeto `joblib` real; limiar congelado (`0.26696679375725973`) preservado como única regra de decisão; validador público definido (reaproveitando `modelagem.validate_frozen` por inteiro); cinco artefatos públicos de inferência identificados (`artifacts/modelo_avaliado.joblib`, `artifacts/schema_modelo.json`, `artifacts/configuracao_congelada.json`, `artifacts/avaliacao_temporal.json`, `reports/metricas_modelagem.json`); `docs/contrato_metodologico.md` registrado como dependência pública adicional de integridade; `modelagem.validate_artifacts` explicitamente proibida no deploy público por depender de hashes privados em `local_data/`; ausência de dependência de `DATATHON/`, `local_data/` e `local_recovery/` confirmada; tratamento de erros, privacidade e limitações documentados; revisão independente com parecer **APPROVED**; versionado no commit de conclusão desta TASK.

## FASE 4 — Aplicação e publicação

### TASK 009 — Aplicação Streamlit

- **Estado:** DONE.
- **Objetivo:** implementar uma interface Streamlit clara e segura para demonstração do artefato operacional aprovado.
- **Dependências:** TASK 008.
- **Entregáveis:** aplicação Streamlit; fluxo de entrada e resultado; mensagens de validação; instruções locais.
- **Critérios de aceite:** aplicação inicia sem erro; respeita contrato operacional; resultados determinísticos; interface não expõe dados privados; limitações visíveis.
- **Restrições importantes:** implementar somente a decisão da TASK 008; não recalibrar, retreinar ou alterar resultados congelados.
- **Executor:** Jônatas Silva — implementação assistida por Claude.
- **Revisor:** GPT/Codex — revisão técnica independente em 22/09/2026.
- **Evidências de conclusão:** aplicação criada em `streamlit_app.py`, com módulo de inferência independente (sem dependência de Streamlit) em `src/inferencia.py`; Streamlit com versão fixada (`streamlit==1.64.0`) em `requirements.txt`, sem alterar nenhuma dependência já congelada; configuração pública em `.streamlit/config.toml` (tema sóbrio, estatísticas de uso desativadas, sem porta fixa). Modelo oficialmente avaliado (`artifacts/modelo_avaliado.joblib`) carregado sem retreinamento; validador público dos seis caminhos implementado (reaproveitando `modelagem.validate_frozen` por inteiro); `modelagem.validate_artifacts` explicitamente proibida e nunca chamada; ausência de dependência de `DATATHON/`, `local_data/` e `local_recovery/` confirmada. Os sete preditores são validados na ordem oficial; chaves ausentes e chaves extras no payload são rejeitadas (`InputValidationError`); valores numéricos ausentes só são aceitos quando a chave correspondente está presente no payload; a classe positiva é validada como o inteiro `1` (tipo estrito, rejeitando `bool`/`str`/`float`); o retorno de `predict_proba` é validado quanto a formato, número de classes e probabilidades finitas em `[0, 1]`; o limiar congelado (`0.26696679375725973`) é lido dos artefatos e aplicado sem ajuste. Nenhuma entrada do usuário é persistida, logada ou reaproveitada entre sessões; a interface usa linguagem não causal e exibe as limitações oficiais (queda de recall no teste temporal, subestimação de risco, necessidade de supervisão humana). Inferências com dados inteiramente sintéticos aprovadas (probabilidade em `[0, 1]`, classificação coerente com o limiar); casos adversariais sintéticos (chaves ausentes/extras, classe positiva inválida, formatos inválidos de `predict_proba`) corretamente rejeitados com `PublicValidationError`/`InputValidationError`, sem vazar mensagens internas. Smoke test headless aprovado: inicialização sem erro, endpoint `/_stcore/health` com HTTP 200 (`ok`), página principal com HTTP 200 sem indício de traceback, processo encerrado por completo ao final. Revisão independente com parecer **APPROVED**; versionado no commit de conclusão desta TASK.

### TASK 010 — Testes da aplicação e privacidade

- **Estado:** READY.
- **Objetivo:** validar comportamento funcional, falhas controladas, privacidade e aderência ao contrato da aplicação.
- **Dependências:** TASK 009.
- **Entregáveis:** testes automatizados e roteiro manual; casos válidos e inválidos; verificação de privacidade; relatório de resultados.
- **Critérios de aceite:** testes aprovados; entradas inválidas bloqueadas; nenhuma informação pessoal exposta; saídas coerentes com o modelo congelado; falhas sem vazamento de dados.
- **Restrições importantes:** usar dados sintéticos ou agregados nos testes públicos; não registrar entradas sensíveis.
- **Executor:** a designar.
- **Revisor:** a designar, preferencialmente independente.
- **Evidências de conclusão:** a produzir: log dos testes, checklist de privacidade e revisão independente.

### TASK 011 — Deploy no Streamlit Community Cloud

- **Estado:** BLOCKED pela TASK 010.
- **Objetivo:** publicar a aplicação validada em ambiente acessível e reproduzível.
- **Dependências:** TASK 010.
- **Entregáveis:** aplicação publicada; configuração mínima de deploy; URL; procedimento de atualização e rollback.
- **Critérios de aceite:** deploy acessível; dependências instaladas; smoke test aprovado; nenhum dado privado ou segredo no repositório; documentação da URL e versão.
- **Restrições importantes:** não enviar diretórios privados; segredos somente no mecanismo seguro da plataforma; fixar versões necessárias.
- **Executor:** a designar.
- **Revisor:** a designar, preferencialmente independente.
- **Evidências de conclusão:** a produzir: URL pública, versão implantada, captura ou registro do smoke test.

## FASE 5 — Documentação e apresentação

### TASK 012 — Documentação final

- **Estado:** BLOCKED pelas TASKs 007 e 011.
- **Objetivo:** consolidar instruções, arquitetura, metodologia, resultados, aplicação e limitações para avaliação e reprodução.
- **Dependências:** TASKs 007 e 011.
- **Entregáveis:** documentação final; guia de execução; referência ao notebook e aplicação; limitações e considerações éticas.
- **Critérios de aceite:** instruções testadas; links válidos; resultados coerentes; distinção clara entre análise, avaliação congelada e uso demonstrativo.
- **Restrições importantes:** não alterar evidências congeladas; não incluir caminhos locais, dados privados ou afirmações não sustentadas.
- **Executor:** a designar.
- **Revisor:** a designar, preferencialmente independente.
- **Evidências de conclusão:** a produzir: revisão documental, links conferidos e checklist de reprodução.

### TASK 013 — Apresentação gerencial

- **Estado:** DRAFT.
- **Objetivo:** sintetizar problema, método, resultados, impacto, limitações e demonstração para público gerencial.
- **Dependências:** TASK 012.
- **Entregáveis:** apresentação com narrativa executiva; gráficos essenciais; mensagens-chave; referências às limitações.
- **Critérios de aceite:** narrativa compreensível; números idênticos aos artefatos oficiais; visual legível; tempo compatível com o vídeo; revisão de privacidade.
- **Restrições importantes:** não selecionar métricas novas; não exagerar causalidade ou desempenho; não mostrar dados individuais.
- **Executor:** a designar.
- **Revisor:** a designar, preferencialmente independente.
- **Evidências de conclusão:** a produzir: arquivo versionado, conferência numérica e aprovação da narrativa.

### TASK 014 — Material dividido entre os cinco integrantes

- **Estado:** BLOCKED pela TASK 013.
- **Objetivo:** preparar o material que servirá de base para os cinco integrantes gravarem o vídeo.
- **Dependências:** TASK 013.
- **Entregáveis:** roteiro completo; divisão do conteúdo entre cinco integrantes; fala sugerida para cada integrante; ordem de participação; indicação dos slides, gráficos, notebook ou telas apresentados por cada pessoa; estimativa do tempo de cada participação; transições entre as falas; conferência do limite total de duração exigido no enunciado.
- **Critérios de aceite:** cinco participações claramente delimitadas; todas as falas associadas ao apoio visual correspondente; transições coerentes; soma das participações respeitando o limite total de até cinco minutos; números conferidos contra os artefatos oficiais.
- **Restrições importantes:** não improvisar números; não revelar ambiente local, segredos ou informações pessoais; limitar o escopo à preparação do material dos integrantes.
- **Executor:** a designar.
- **Revisor:** a designar, preferencialmente independente.
- **Evidências de conclusão:** a produzir: roteiro revisado, matriz de divisão por integrante e conferência documentada da duração.

## FASE 6 — Revisão e encerramento

### TASK 015 — Revisão final da entrega

- **Estado:** BLOCKED.
- **Objetivo:** verificar integralmente código, notebook, aplicação, documentação, apresentação, material dos integrantes, privacidade, rastreabilidade e reprodutibilidade antes da publicação final.
- **Dependências:** TASK 014 e todas as TASKs anteriores aplicáveis.
- **Entregáveis:** checklist final; execução completa dos testes; inventário de arquivos; revisão de links, privacidade e artefatos congelados.
- **Critérios de aceite:** suíte integral aprovada; nenhum arquivo privado versionado; nenhuma alteração indevida em congelados; links funcionais; estados e evidências atualizados.
- **Restrições importantes:** a revisão não pode corrigir silenciosamente resultados; achados devem retornar à TASK responsável.
- **Executor:** a designar.
- **Revisor:** a designar, obrigatoriamente independente quando possível.
- **Evidências de conclusão:** a produzir: log final, `git status`, diff revisado, inventário e aprovação formal.

### TASK 016 — Publicação e versionamento final

- **Estado:** BLOCKED pela TASK 015.
- **Objetivo:** publicar a versão aprovada, integrar a branch e criar a referência final de entrega.
- **Dependências:** TASK 015 em DONE.
- **Entregáveis:** commits finais revisados; merge autorizado; tag final; links definitivos de repositório, aplicação e vídeo.
- **Critérios de aceite:** revisão final aprovada; worktree limpo; histórico coerente; tag apontando para o commit aprovado; links conferidos após publicação.
- **Restrições importantes:** nenhum merge ou tag antes da TASK 015; não versionar dados privados, ambientes ou recuperações locais; evitar reescrita destrutiva do histórico.
- **Executor:** a designar.
- **Revisor:** a designar, independente do executor.
- **Evidências de conclusão:** a produzir: hash do merge, tag final, URLs verificadas e registro da aprovação.

## Tabela-resumo

| TASK | Fase | Título | Estado | Dependência principal |
| --- | --- | --- | --- | --- |
| 000 | 0 | Organização e controle do projeto | DONE | — |
| 001 | 1 | Auditoria e integridade das fontes | DONE | — |
| 002 | 1 | Preparação longitudinal | DONE | 001 |
| 003 | 1 | Contrato metodológico e coortes temporais | DONE | 001, 002 |
| 004 | 2 | Modelagem e avaliação temporal | DONE | 003 |
| 005 | 2 | Análises e perguntas de negócio | DONE | 002, 004 |
| 006 | 3 | Portabilidade dos hashes LF/CRLF | DONE | 001–005 |
| 007 | 3 | Notebook final reproduzível | DONE | 001–006 |
| 008 | 3 | Definição do artefato operacional | DONE | 007 e decisão de produto |
| 009 | 4 | Aplicação Streamlit | DONE | 008 |
| 010 | 4 | Testes da aplicação e privacidade | READY | 009 |
| 011 | 4 | Deploy no Streamlit Community Cloud | BLOCKED | 010 |
| 012 | 5 | Documentação final | BLOCKED | 007, 011 |
| 013 | 5 | Apresentação gerencial | DRAFT | 012 |
| 014 | 5 | Material dividido entre os cinco integrantes | BLOCKED | 013 |
| 015 | 6 | Revisão final da entrega | BLOCKED | 014 e anteriores aplicáveis |
| 016 | 6 | Publicação e versionamento final | BLOCKED | 015 |

## Caminho crítico

As TASKs 007, 008 e 009 foram concluídas. O caminho crítico do trabalho restante é:

`TASK 010 → TASK 011 → TASK 012 → TASK 013 → TASK 014 → TASK 015 → TASK 016`

Cada TASK desse caminho deve fornecer seus entregáveis e evidências à seguinte. Decisões preparatórias podem ser discutidas antecipadamente, mas nenhuma TASK bloqueada muda de estado antes do atendimento formal de sua dependência.

## Próxima TASK

**TASK 010 — Testes da aplicação e privacidade.** Ela está READY e inicia o caminho crítico do trabalho restante.

## Checklist para mudança de estado

- [ ] O objetivo e o escopo estão claros e não ampliaram silenciosamente.
- [ ] Todas as dependências exigidas chegaram ao estado necessário.
- [ ] Há exatamente um executor responsável registrado.
- [ ] O revisor independente foi registrado quando possível.
- [ ] Todos os entregáveis previstos existem e estão no local correto.
- [ ] Os critérios de aceite foram verificados, não apenas declarados.
- [ ] Testes e verificações relevantes foram executados e tiveram resultado registrado.
- [ ] Privacidade, integridade e restrições de dados foram conferidas.
- [ ] Nenhum artefato congelado foi recalculado, substituído ou ajustado indevidamente.
- [ ] Evidências objetivas foram vinculadas à TASK.
- [ ] O estado e a tabela-resumo foram atualizados de forma consistente.
- [ ] Para DONE, a mudança foi revisada e versionada.

## Regra de conclusão

Uma TASK só pode receber o estado **DONE** quando houver evidência objetiva, verificável e versionada de que todos os seus critérios de aceite foram cumpridos. Declaração verbal, implementação local sem commit, intenção de revisão ou resultado não reproduzível não são suficientes para DONE.
