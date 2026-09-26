# Auditoria de fórmulas institucionais — calculadoras de indicadores

Revisão de 25/09/2026 (rodada de correção). **Substitui integralmente** a
versão anterior deste documento: a auditoria de 25/09/2026 (primeira rodada)
classificou IDA, IEG, IAA, IPS, IPP e IPV como não reproduzíveis a partir de
`DATATHON/PEDE_ Pontos importantes.docx`, mas essa leitura foi incompleta —
o texto plano do documento não foi cruzado com as **imagens/tabelas
incorporadas** (`word/media/imageN.png`), que contêm as fórmulas e escalas
completas para vários indicadores. Esta rodada releu o arquivo por completo
— texto (via `python-docx`) e as 10 imagens incorporadas, uma a uma — e
corrige o veredito onde a evidência visual estava disponível e era
inequívoca.

Distinção importante mantida em toda a auditoria: **indicador educacional**
(o valor calculado por uma fórmula documentada, útil para o profissional
entender e registrar o caso) é diferente de **entrada do modelo** (um dos
sete campos em `inferencia.FEATURES`). Uma calculadora só é implementada
quando o valor calculado é exatamente o que o modelo já espera naquele
campo — nunca um oitavo campo novo.

## Fontes consultadas nesta rodada

- `DATATHON/PEDE_ Pontos importantes.docx` — texto integral (`python-docx`,
  todos os parágrafos não vazios) **e as 10 imagens incorporadas**
  (`word/media/image1.png` a `image10.png`), extraídas do pacote OOXML e
  inspecionadas visualmente uma a uma nesta rodada.
- `DATATHON/Dicionário Dados Datathon.pdf` (já lido em rodada anterior).
- `docs/evidencias_documentais.md`, `docs/mapa_campos.md`,
  `docs/contrato_metodologico.md` (contexto e domínio oficial dos sete
  preditores).

## Matriz corrigida

### Defasagem (D)

- **Fórmula:** `D = Fase Efetiva − Fase Ideal` (texto do documento,
  confirmado com o exemplo da linha 280/2024: fase efetiva 2, fase ideal 3,
  D = −1).
- **Reproduzível:** sim — já implementada (`calcular_defasagem`), sem
  alteração de lógica nesta rodada.
- **Observação corrigida:** a fase ideal usada no cálculo deve vir do
  registro institucional ou de confirmação humana — nunca ser derivada
  silenciosamente da idade (ver seção "Idade e fase ideal" abaixo).

### IAN — Indicador de Adequação de Nível

- **Fórmula:** Tabela 41 do documento (`image1.png`): D≥0 → 10 (Em fase);
  −2≤D<0 → 5 (Moderada); D<−2 → 2,5 (Severa).
- **Reproduzível:** sim — já implementada (`ian_pela_defasagem`), idêntica à
  regra em `src/dados_pede.py:expected_ian_value`. Sem alteração de lógica
  nesta rodada; passa a ser exibida sistematicamente junto da defasagem no
  formulário (situação + valor do IAN), sempre como informação educacional,
  nunca como oitavo preditor.

### Idade e fase ideal (equivalência ano escolar/fase/idade)

- **Fonte:** Tabela 4 do documento (`image4.png`), população de referência
  2020/2021.
- **Reproduzível como SUGESTÃO, não como cálculo automático silencioso:** a
  própria tabela apresenta faixas etárias que **se sobrepõem na fronteira**
  (ex.: Alfa = 7–8 anos, Fase 1 = 8–9 anos — um estudante de 8 anos cabe nas
  duas). O documento não resolve essa ambiguidade, e o domínio de fases
  vigente no modelo (`inferencia.PHASE_CATEGORIES`, "0"–"7") não foi
  conferido contra a base 2020/2021 da tabela. Por isso, a idade **sugere**
  uma fase ideal (com aviso explícito quando a idade cai numa fronteira
  ambígua), mas o profissional sempre confirma ou escolhe manualmente a
  fase ideal antes de qualquer cálculo de defasagem. Implementado como
  `calculadoras_indicadores.sugerir_fase_ideal_por_idade`.

### IDA — Indicador de Desempenho Acadêmico

- **Fórmula (fases 0–7):** `IDA = (Nota Matemática + Nota Português + Nota
  Inglês) / 3` — texto explícito do documento.
- **Fase 8:** o Quadro 2 (`image6.png`) esclarece que, na Fase 8, o IDA
  registra "a nota média obtida pelos alunos em todas as disciplinas
  curriculares cursadas, nas respectivas instituições de ensino superior" —
  uma fórmula **diferente e não documentada em detalhe** (número de
  disciplinas variável, sem lista fechada). A calculadora de três notas,
  portanto, **não se aplica à Fase 8** — o que na prática nunca ocorre nesta
  ficha, já que `fase_origem` só aceita "0"–"7".
- **Reproduzível:** sim, para fases 0–7, com as três notas informadas
  diretamente pelo usuário (nunca reconstruída a partir da base histórica,
  onde a cobertura de Inglês é majoritariamente ausente — ver rodada
  anterior). A calculadora não afirma reproduzir o IDA histórico de nenhum
  estudante da base; é uma ferramenta de apoio ao preenchimento de um caso
  novo, a partir de três notas que o próprio usuário fornece.
- **Implementado:** `calculadoras_indicadores.calcular_ida` — exige as três
  notas (0–10 cada), nunca imputa a ausente, retorna a média com precisão
  plena internamente.

### IEG — Indicador de Engajamento

- **Fonte:** "Soma das pontuações das tarefas realizadas e registradas /
  Número de tarefas" (texto) + Quadro/figura de composição do INDE
  (`image2.png`): fonte = "Registros de entrega de lição de casa e de
  voluntariado".
- **Reproduzível:** **não**. Não há, em nenhuma imagem ou texto do
  documento, uma lista fechada de tarefas, uma escala de pontuação por
  tarefa, nem uma regra para tarefa não registrada. "Número de tarefas" é
  variável por estudante e por período, sem domínio fechado. Manter entrada
  institucional direta.

### IAA — Indicador de Autoavaliação

- **Fonte:** Tabela 40 (`image7.png`) + Figura 10 (`image9.png`) —
  **corrige o veredito da rodada anterior**. A tabela documenta, de forma
  completa e fechada: exatamente 6 perguntas fixas; 4 alternativas
  possíveis por pergunta (A/B/C/D, com pictogramas); valor em pontos de
  cada alternativa, **diferente conforme o grupo de fases** (Fases 0 a 2:
  A=1,667, B=1,167, C=0,583, sem D; Fases 3 a 8: A=1,667, B=1,25, C=0,833,
  D=0,417); soma máxima 10,000. Nenhum peso é inventado — todos os valores
  vêm literalmente da tabela.
- **Reproduzível:** sim, para as 6 perguntas fixas, com base no grupo de
  fases derivado de `fase_origem` (0–2 ou 3–7, já que 8 não está no domínio
  do formulário).
- **Implementado:** `calculadoras_indicadores.calcular_iaa` — exige uma
  resposta (A/B/C/D) para cada uma das 6 perguntas, soma os pontos da
  tabela oficial.

### IPS — Indicador Psicossocial

- **Fonte:** "Soma das pontuações dos avaliadores / Número de avaliadores"
  (texto) + Quadro 3 (`image8.png`): "Avaliação da equipe de psicólogas...
  por meio de questionário".
- **Reproduzível:** **não**. Nenhuma imagem documenta o questionário (número
  de perguntas, escala, pontuação por resposta). "Número de avaliadores" é
  variável e não documentado. Manter entrada institucional direta.

### IPP — Indicador Psicopedagógico

- **Fonte:** "Soma das avaliações sobre aspectos pedagógicos / Número de
  avaliações" (texto) + Quadro 3 (`image8.png`): "Avaliação da equipe de
  educadores e psicopedagogos... por meio de questionário".
- **Reproduzível:** **não**, pelo mesmo motivo do IPS — questionário não
  documentado em detalhe. Mantido fora do formulário de "Avaliar um caso"
  (IPP nunca foi um dos sete preditores nem está no domínio do modelo).

### IPV — Indicador do Ponto de Virada

- **Fonte:** "Análises longitudinais de progresso acadêmico, engajamento e
  desenvolvimento emocional" (texto).
- **Reproduzível:** **não** — o próprio documento o descreve como uma
  análise longitudinal multidimensional, não uma média ponderável. Manter
  entrada institucional direta; nenhuma calculadora de média simples.

### INDE — Índice de Desenvolvimento Educacional

- **Fórmula (Fases 0–7):** `INDE = IAN×0,1 + IDA×0,2 + IEG×0,2 + IAA×0,1 +
  IPS×0,1 + IPP×0,1 + IPV×0,2` (Quadro "Composição do INDE", `image10.png`).
- **Fórmula (Fase 8):** `INDE = IAN×0,1 + IDA×0,4 + IEG×0,2 + IAA×0,1 +
  IPS×0,2` (mesma fonte).
- **Reproduzível como informação complementar:** sim, a fórmula em si é
  inequívoca. Calculado **somente** quando todos os componentes exigidos
  pela fase estiverem disponíveis (informados ou calculados) — nunca com
  substituição por zero, nunca parcial. Fase 8 não ocorre neste formulário
  (fora do domínio de `fase_origem`); a implementação cobre apenas Fases
  0–7, e a função aceita explicitamente informar quais componentes faltam.
- **Faixas "Pedra" (Quartzo/Ágata/Ametista/Topázio): NÃO implementadas.** A
  Figura 3 (`image3.png`) apresenta as faixas como um gráfico de barras
  (3,0–6,1–7,2–8,2–9,4), sem notação explícita de inclusão/exclusão nas
  fronteiras (não há "≥"/"<" no gráfico, ao contrário da Tabela 41 do IAN).
  A auditoria de rodada anterior também já havia registrado divergência
  entre esta figura e a faixa de Pedra do Dicionário de Dados. Sem
  confirmação inequívoca dos limites, a aplicação **não classifica** o INDE
  calculado em nenhuma Pedra — mostra apenas o valor numérico, com nota
  explicando que a classificação institucional em Pedra não está
  reproduzida aqui.
- **Implementado:** `calculadoras_indicadores.calcular_inde` — nunca
  enviado ao modelo; exibido só no resumo/relatório como informação
  complementar; nunca confundido com a probabilidade da estimativa.

## Resumo das classificações (corrigido)

| Indicador | Classificação | Calculadora implementada nesta rodada |
| --- | --- | --- |
| Defasagem | FÓRMULA OFICIAL CONFIRMADA | Já existia (mantida) |
| IAN | FÓRMULA OFICIAL CONFIRMADA | Já existia (mantida) |
| Fase ideal por idade | SUGESTÃO CONFIRMADA, COM AMBIGUIDADE DE FRONTEIRA DOCUMENTADA | Sim — sugestão, nunca automática |
| IDA (fases 0–7) | FÓRMULA OFICIAL CONFIRMADA | **Sim (nova)** |
| IDA (fase 8) | NÃO DOCUMENTADA EM DETALHE | Não (fora do domínio do formulário) |
| IAA | FÓRMULA OFICIAL CONFIRMADA (Tabela 40) | **Sim (nova)** |
| INDE (Fases 0–7) | FÓRMULA OFICIAL CONFIRMADA | **Sim (nova, complementar)** |
| Pedra (classificação do INDE) | LIMITES SEM NOTAÇÃO DE FRONTEIRA INEQUÍVOCA | Não |
| IEG | NÃO REPRODUZÍVEL (sem escala/lista de tarefas) | Não |
| IPS | NÃO REPRODUZÍVEL (questionário não documentado) | Não |
| IPP | NÃO REPRODUZÍVEL (questionário não documentado); fora do modelo | Não |
| IPV | NÃO REPRODUZÍVEL (análise longitudinal, não é média) | Não |

## Por que nenhuma fórmula foi inventada

Toda fórmula implementada nesta rodada (defasagem, IAN, IDA, IAA, INDE) tem
uma citação direta a um texto ou tabela/imagem específica do documento
fonte, com os valores exatos reproduzidos sem arredondamento adicional,
sem peso presumido e sem substituição de dado ausente. Onde a fonte não
fechava a fórmula (IEG, IPS, IPP, IPV) ou não fechava a notação de fronteira
(faixas de Pedra), a aplicação mantém a entrada institucional direta e
explica ao usuário, em linguagem simples, por que a calculadora não está
disponível para aquele campo específico.
