# Auditoria experimental do recall temporal — relatório técnico

**Status: análise experimental, não congelada.** Não altera o modelo, o
limiar oficial (`0.26696679375725973`), os artefatos em `artifacts/`, o
notebook ou `reports/metricas_modelagem.json`. Todos os arquivos desta
análise vivem em `reports/experimental/`. Gerado por
`scripts/experimento_recall_temporal.py`.

## 1. Reprodução do resultado atual

Antes de qualquer experimento, as probabilidades OOF do desenvolvimento
foram recalculadas com o protocolo exatamente congelado (`StratifiedKFold`,
5 folds, `shuffle=True`, `random_state=42`, pipeline `logistica`) e as
probabilidades do teste temporal vieram do modelo já congelado
(`artifacts/modelo_avaliado.joblib`, só `.predict_proba`, sem novo ajuste).
As duas reproduções batem **byte a byte** com
`reports/metricas_modelagem.json` — nenhum experimento avançou sem essa
confirmação.

| | Desenvolvimento (OOF) | Teste temporal (2023→2024) |
|---|---|---|
| n | 189 | 311 |
| eventos | 60 | 84 |
| prevalência | 31,75% | 27,01% |
| matriz de confusão | VN=86, FP=43, FN=11, VP=49 | VN=208, FP=19, FN=50, VP=34 |
| sinalizados | 92 (48,68%) | 53 (17,04%) |
| precisão | 53,26% | 64,15% |
| recall | 81,67% | 40,48% |
| especificidade | 66,67% | 91,63% |
| acurácia | 71,43% | 77,81% |
| F1 | 64,47% | 49,64% |
| AP | 66,49% | 62,11% |
| ROC-AUC | 81,42% | 80,44% |
| Brier | 0,1604 | 0,1735 |

## 2. O recall de 40,48% em números absolutos

No teste temporal, **84 estudantes realmente entraram em defasagem** no
período seguinte. O modelo, no limiar oficial, **sinalizou 34 deles e
não sinalizou 50**. Isso é o próprio recall: 34/84 = 40,48%.

Esse resultado se refere aos 84 casos positivos do conjunto de teste
temporal como um todo — não a "seis alunos por sala" nem a qualquer
divisão por turma; a base não permite essa granularidade e a frase erraria
a unidade de análise.

Dos 53 estudantes sinalizados, 34 realmente entraram em defasagem
(precisão de 64,15%) e 19 não entraram (falsos positivos).

## 3. Acurácia e baseline majoritário

| | Modelo (limiar oficial) | Baseline (prevê todos negativos) | Diferença |
|---|---|---|---|
| Acurácia | 77,81% | 72,99% | +4,82 p.p. |
| Acurácia balanceada | (recall+especificidade)/2 = 66,05% | 50,00% | +16,05 p.p. |
| Recall classe positiva | 40,48% | 0,00% | +40,48 p.p. |
| Recall classe negativa | 91,63% | 100,00% | −8,37 p.p. |

A prevalência temporal (27,01%) já garante que prever todos como negativos
produz 72,99% de acurácia — muito próxima da acurácia observada do modelo.
**A acurácia acima de 75% não deveria ser destacada isoladamente como
prova de desempenho**: o ganho real sobre o baseline ingênuo é de menos de
5 pontos percentuais em acurácia simples. A métrica que de fato separa o
modelo do baseline é a acurácia balanceada (+16 p.p.) e o recall da classe
positiva (+40,48 p.p., partindo de zero) — é nelas que a capacidade
preditiva aparece, não na acurácia bruta.

## 4. Candidatos de limiar (definidos exclusivamente no OOF)

Regra de desempate declarada por critério (nunca o teste temporal decide
entre empates): para critérios "recall mínimo", entre os elegíveis
escolhe-se maior precisão, depois maior recall, depois maior limiar; para
"maior F2"/"maior Youden J", maior valor da métrica, depois maior recall,
depois maior limiar; para "precisão mínima", entre os elegíveis
escolhe-se maior recall, depois maior precisão, depois maior limiar.

| Candidato | Limiar | Recall OOF | Precisão OOF | Recall temporal | Precisão temporal | Sinalizados (temporal) | VP | FP | FN |
|---|---|---|---|---|---|---|---|---|---|
| Limiar oficial | 0,2670 | 81,7% | 53,3% | 40,5% | 64,2% | 53 (17,0%) | 34 | 19 | 50 |
| Recall mínimo 85% | 0,2344 | 85,0% | 51,0% | 44,0% | 60,7% | 61 (19,6%) | 37 | 24 | 47 |
| Recall mínimo 90% | 0,1913 | 91,7% | 46,6% | 48,8% | 58,6% | 70 (22,5%) | 41 | 29 | 43 |
| Recall mínimo 95% | 0,1635 | 96,7% | 46,0% | 56,0% | 56,6% | 83 (26,7%) | 47 | 36 | 37 |
| Maior F2 | 0,1635 | 96,7% | 46,0% | 56,0% | 56,6% | 83 (26,7%) | 47 | 36 | 37 |
| Maior Youden J | 0,2670 | 81,7% | 53,3% | 40,5% | 64,2% | 53 (17,0%) | 34 | 19 | 50 |
| Maior recall, precisão ≥ 50% | 0,2254 | 86,7% | 50,0% | 44,0% | 58,7% | 63 (20,3%) | 37 | 26 | 47 |
| Maior recall, precisão ≥ 40% | 0,1510 | 98,3% | 44,0% | 58,3% | 56,3% | 87 (28,0%) | 49 | 38 | 35 |

**Achado notável 1:** "Maior Youden J" coincide, neste OOF, com o próprio
limiar oficial — o limiar já congelado também maximiza recall+especificidade−1
entre os candidatos únicos do desenvolvimento. Isso reforça que o limiar
oficial não é um ponto arbitrário.

**Achado notável 2:** "Recall mínimo 95%" e "Maior F2" coincidem no mesmo
limiar (0,1635) neste conjunto — ambos os critérios apontam para a mesma
região de operação.

## 5. Impacto pedagógico (simulação operacional, teste temporal)

| Candidato | Encaminhados p/ observação | Casos reais encontrados | Casos reais ainda perdidos | Acompanhamentos que são FP |
|---|---|---|---|---|
| Limiar oficial | 53 | 34 | 50 | 19 |
| Recall mínimo 95% / Maior F2 | 83 | 47 | 37 | 36 |
| Maior recall, precisão ≥ 40% | 87 | 49 | 35 | 38 |

Um falso positivo aqui não é necessariamente dano — pode ser apenas uma
revisão pedagógica adicional que confirma que o estudante está bem. Ainda
assim, a carga de acompanhamento adicional é real e precisa ser
dimensionada: o candidato "precisão ≥ 40%" quase dobra o número de
estudantes observados (53→87) para reduzir os casos perdidos de 50 para
35 (−30%).

## 6. Recalibração experimental (Platt e isotônica, ajustadas só no OOF)

| | Brier temporal antes | Brier temporal depois | Correlação de postos com o original |
|---|---|---|---|
| Platt scaling | 0,1735 | 0,1685 (−2,9%) | 1,000 |
| Isotônica | 0,1735 | 0,1789 (+3,1%, pior) | 0,956 |

Platt scaling melhora a calibração (Brier menor) sem alterar a ordenação
dos estudantes (correlação de postos = 1,0, como esperado de uma
transformação monótona). A isotônica, ajustada com apenas 60 eventos no
desenvolvimento, **piora** o Brier no teste temporal — sinal de
sobreajuste local a poucos degraus; não é recomendada aqui.

**Confirmação empírica de que recalibração não cria nova capacidade de
ordenação:** reaplicando o critério "maior F2" às probabilidades
recalibradas (por Platt ou por isotônica) e ao teste temporal, o par
(recall, precisão) resultante é **idêntico** ao do candidato "maior F2"
original: recall = 55,95%, precisão = 56,63% — porque a curva
precisão-recall depende só da ordenação, que a recalibração preserva (ou,
no caso isotônico, quase preserva). O ganho da recalibração está na
interpretação numérica da probabilidade como "chance real", não em um
novo ponto de operação inatingível antes.

## 7. Incerteza (bootstrap, 2000 reamostragens, só no teste temporal)

Para os dois candidatos classificados como "promissores"
(ver seção 9), reamostragem pareada (mesmo resample avaliado no limiar
oficial e no candidato):

| Candidato | Δ recall (IC95) | Δ precisão (IC95) | Δ acurácia balanceada (IC95) |
|---|---|---|---|
| Recall mínimo 95% | [+8,4 p.p.; +23,7 p.p.] | [−15,9 p.p.; +0,6 p.p.] | [+0,2 p.p.; +8,2 p.p.] |
| Maior recall, precisão ≥ 40% | [+10,5 p.p.; +26,7 p.p.] | [−16,3 p.p.; +0,7 p.p.] | [+0,5 p.p.; +9,1 p.p.] |

O ganho de recall é estatisticamente robusto (o IC95 não cruza zero em
nenhum dos dois candidatos). A perda de precisão, embora pontualmente real
(6-8 p.p.), tem IC95 que quase toca zero — não pode ser afirmada com a
mesma confiança que o ganho de recall. O ganho de acurácia balanceada é
real, mas modesto (IC95 aproximando-se de zero no limite inferior).

Com apenas 84 eventos positivos no teste temporal, esses intervalos são
largos; declarar essa incerteza é mais honesto do que apresentar os pontos
centrais como certezas.

## 8. Equidade (limiar oficial e os dois candidatos promissores)

**Gênero** (recall):

| | Feminino | Masculino | Diferença |
|---|---|---|---|
| Limiar oficial | 33,3% | 47,6% | 14,3 p.p. |
| Recall mínimo 95% | 50,0% | 61,9% | 11,9 p.p. |
| Precisão ≥ 40% | 54,8% | 61,9% | 7,1 p.p. |

Os dois candidatos promissores **reduzem**, não ampliam, a diferença de
recall entre gêneros observada no limiar oficial.

**Faixa etária aproximada** (recall; grupos com n<30 ou menos de 5
eventos/não eventos são suprimidos por privacidade):

| Faixa | Limiar oficial | Recall mínimo 95% | Precisão ≥ 40% |
|---|---|---|---|
| 7 a 10 anos | 46,4% | 62,3% | 63,8% |
| 11 a 13 anos | 11,1% | 11,1% | 11,1% |
| 14 a 16 anos | 16,7% | 50,0% | 66,7% |
| 17 anos ou mais | suprimido (n pequeno) | suprimido | suprimido |

**Achado de equidade que precisa de destaque:** a faixa "11 a 13 anos"
permanece com recall de 11,1% (1 de 9 casos reais) em **todos** os
limiares testados, incluindo o mais permissivo (0,1510). Baixar o limiar
não resolve essa lacuna — é um indício de que o modelo atribui
probabilidades sistematicamente baixas aos casos reais dessa faixa etária,
não um problema de ponto de corte. Qualquer decisão operacional deveria
registrar essa limitação explicitamente, e não escolher um limiar só pela
média global quando ela mascara esse grupo.

**Fase**: os subgrupos por fase publicáveis (fase 0 e fase 1) mantêm a
mesma ordem de recall/precisão entre os candidatos observada
agregadamente; fases 2 a 7 seguem suprimidas pela mesma regra de
privacidade já usada no artefato oficial (n≥30 e ≥5 eventos/não eventos).

## 9. Recomendação

Classificação de cada candidato (critérios: redução de falsos negativos,
quantidade adicional sinalizada, precisão resultante, estabilidade
temporal, equidade, incerteza — nessa ordem de prioridade):

| Candidato | Classificação |
|---|---|
| Limiar oficial | **Manter o limiar oficial** |
| Maior Youden J | **Manter o limiar oficial** (limiar numericamente idêntico ao oficial) |
| Recall mínimo 95% | **Candidato operacional promissor** |
| Maior F2 | **Candidato operacional promissor** (mesmo limiar do anterior) |
| Maior recall, precisão ≥ 40% | **Candidato operacional promissor** |
| Recall mínimo 85% | Somente experimental (ganho de recall pequeno: +3,5 p.p.) |
| Recall mínimo 90% | Somente experimental (ganho de recall pequeno: +8,3 p.p.) |
| Maior recall, precisão ≥ 50% | Somente experimental (ganho de recall pequeno: +3,5 p.p.) |

Nenhum candidato foi classificado como "Rejeitado": todos mantêm precisão
acima da prevalência temporal (27,01%) e nenhum amplia a desigualdade de
equidade observada.

**Não se recomenda trocar o limiar oficial apenas por essa análise.** Os
dois candidatos promissores (recall mínimo 95% / maior F2, e maior recall
com precisão ≥ 40%) reduzem os falsos negativos de 50 para 37 e 35
respectivamente (‑26% a ‑30%), com ganho de recall estatisticamente
robusto e sem piora de equidade — mas envolvem quase dobrar o número de
estudantes sinalizados (53→83 ou 53→87) e uma perda de precisão real,
ainda que com incerteza maior do que o ganho de recall. É uma decisão de
política operacional (quanta observação adicional a equipe pedagógica
consegue absorver), não uma correção técnica óbvia — por isso permanece
como recomendação para revisão humana, não como mudança automática.

## 10. Limitações

- Amostra pequena (60 eventos no desenvolvimento, 84 no teste temporal):
  os candidatos de limiar mais extremos (recall mínimo 95%, precisão
  mínima 40%) se apoiam em poucas observações na cauda da distribuição de
  probabilidade — degraus discretos, não uma curva suave.
- A isotônica, em particular, não deveria ser usada em produção com esta
  quantidade de eventos.
- A lacuna de recall na faixa etária "11 a 13 anos" não foi explicada por
  esta análise — apenas documentada. Investigar sua causa (viés nos
  preditores? tamanho de amostra? algo estrutural na faixa?) está fora do
  escopo desta auditoria de limiar.
- Equidade de gênero e de faixa etária dependem de uma ligação (RA, ano de
  referência) com `local_data/base_longitudinal.csv`, auditada e
  confirmada 1:1 sem duplicação (ver
  `scripts/explorar_equidade_genero_modelo.py`), mas essa base não é a
  mesma usada para treinar o modelo — é usada apenas para audição de
  equidade, nunca como preditor.
- Esta análise não avalia se retreinar o modelo (fora do escopo desta
  rodada) produziria um resultado melhor do que qualquer recalibração ou
  escolha de limiar.

## 11. Arquivos gerados

- `reports/experimental/analise_recall_temporal.json` — todos os números
  desta análise, em detalhe.
- `reports/experimental/grafico_candidatos.png` — recall × precisão × %
  sinalizado por candidato, teste temporal.
- `reports/experimental/relatorio_tecnico.md` — este arquivo.
- `reports/experimental/relatorio_professores.md` — versão em linguagem
  acessível para equipe pedagógica.
