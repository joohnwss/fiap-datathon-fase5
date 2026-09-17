# Registro de decisões

- Arquivos originais em DATATHON mantidos intocados.
- Inventário e hashes registrados para rastreabilidade e auditoria reproduzível.
- Junções por RA somente após validação de unicidade e documentações de correspondência.
- Populações candidatas tratadas como comparação preliminar e não como recorte definitivo.
- Dados locais sensíveis permanecem em diretório ignorado pelo Git.
- Relatórios versionados devem ser agregados e sem nomes, RAs ou datas completas de nascimento.

## 17/09/2026 — Contrato metodológico aprovado

O grupo aprovou o [contrato metodológico](contrato_metodologico.md), que passa a
definir o recorte do modelo e a abordagem das 11 perguntas. As decisões
preliminares acima permanecem como registro histórico da etapa de auditoria.

- Estimar a entrada em defasagem em t+1 entre alunos com defasagem registrada
  não negativa em t e fase de origem de 0 a 7, com ALFA equivalente a 0.
  O alvo exige observação futura válida; ausência de destino não equivale a y = 0.
- Usar a transição aluno-ano como unidade, com RA apenas para correspondência
  e auditoria local. Fases 8 e 9 e códigos INCLUIR não serão reinterpretados
  por suposição; seus limites permanecem nas análises descritivas.
- Desenvolver em 2022→2023 (189 registros; 60 eventos) e reservar 2023→2024
  para teste temporal final (311 registros; 84 eventos), sem seleção pelo teste.
- Considerar IDA, IEG, IAA, IPS, IPV, fase categórica e defasagem de origem;
  prever sensibilidade sem defasagem inicial e observar as exclusões do contrato.
- Preservar estados de ausência e imputar por mediana dentro do pipeline,
  ajustada exclusivamente no desenvolvimento e nas parcelas de treino das dobras.
- Planejar referência de prevalência, regressão logística regularizada,
  árvore rasa e floresta aleatória de complexidade controlada, com validação
  estratificada de cinco divisões, embaralhamento e semente fixa.
- Adotar Average Precision como métrica principal, limiar definido por
  probabilidades fora das dobras com recall próximo de 80% e maior precisão
  entre os limiares elegíveis; congelar esse limiar no teste.
- Relatar métricas complementares, calibração e intervalos por bootstrap,
  comparar alunos novos e repetidos e examinar perda de acompanhamento e
  equidade por gênero e fase, respeitando amostras pequenas.
- Separar o modelo de avaliação temporal do futuro modelo retreinado para
  Streamlit; as métricas oficiais serão as do teste temporal.
- Adotar interpretação preditiva e observacional, sem causalidade, diagnóstico
  definitivo ou decisões automáticas de atendimento. Pedras representam faixas
  de desempenho, não fases educacionais.

Não houve treinamento neste marco. As próximas entregas e os procedimentos de
reprodução constam do [status do projeto](status_projeto.md).
