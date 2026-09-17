# Contrato metodológico

Decisão do grupo aprovada em 17/09/2026. Integrantes: Victor, Jonatas,
Izadora, Laura e Lucas. Este documento estabelece o protocolo das análises e da
modelagem do Tech Challenge Fase 5, com base na auditoria dos dados PEDE de
2022, 2023 e 2024. A modelagem ainda não foi iniciada.

As definições se apoiam nas [evidências documentais](evidencias_documentais.md)
e no [relatório de preparação](../reports/relatorio_preparacao_inicial.md).
O protocolo orienta a próxima etapa; não constitui resultado de treinamento.

## Objetivo preditivo e unidade de análise

Estimar a probabilidade de um aluno sem defasagem no ano t apresentar defasagem
no ano t+1. O modelo principal estudará a entrada em defasagem, isto é, sua
incidência. Alunos já defasados permanecerão nas análises descritivas, mas não
integrarão esse modelo.

A unidade de análise será uma transição aluno-ano, identificada localmente por
RA, ano de origem e ano de destino. O RA será utilizado exclusivamente para
correspondência longitudinal e auditoria, sem integrar as variáveis preditoras
ou os arquivos públicos. As junções dependerão de RA válido e único por ano;
duplicidades deverão ser investigadas, sem exclusão silenciosa ou junção por nome.

## População elegível e alvo

A população do modelo será composta por transições com RA válido, defasagem
registrada na origem maior ou igual a zero, fase de origem entre 0 e 7 e
observação válida da defasagem no ano seguinte. ALFA será interpretado como
fase 0. A defasagem registrada será preservada, sem reconstrução pela idade.

| Condição no ano de destino | Alvo |
| --- | --- |
| Defasagem registrada menor que zero | y = 1 |
| Defasagem registrada maior ou igual a zero | y = 0 |
| Ausência de observação no destino ou defasagem futura indisponível | y = desconhecido |

Alunos sem observação futura não serão classificados automaticamente como
y = 0. Os elegíveis pelos critérios de origem cujo alvo seja desconhecido
permanecerão no acompanhamento da cobertura e das perdas, fora do treinamento
e da avaliação supervisionada.

Ficarão fora do modelo principal os registros com fase de origem 8, por suas
regras próprias de aplicabilidade e composição dos indicadores, e fase de
origem 9, cujo significado não está documentado. Registros INCLUIR não serão
convertidos numericamente por suposição. Esses casos permanecerão nas análises
descritivas e nas limitações. A indisponibilidade em um indicador candidato
seguirá a política de dados ausentes, sem presumir uma fase a partir desse texto.

## Divisão temporal

| Finalidade | Transição | Registros observados | Eventos de defasagem futura |
| --- | --- | ---: | ---: |
| Desenvolvimento | 2022→2023 | 189 | 60 |
| Teste temporal final | 2023→2024 | 311 | 84 |

As contagens correspondem ao recorte das fases 0 a 7 na origem, com desfecho
observado. O conjunto 2023→2024 ficará reservado para a avaliação final e não
poderá ser utilizado para escolher algoritmo, hiperparâmetros, variáveis ou
limiar. A auditoria já realizada sobre qualidade e contagens não autoriza ajuste
das escolhas metodológicas com base no desempenho nesse teste.

## Variáveis candidatas e exclusões

As variáveis candidatas serão IDA, IEG, IAA, IPS, IPV, fase de origem tratada
como categórica e defasagem registrada no ano de origem. Todos os atributos
deverão estar disponíveis no ano t. Será realizada uma análise de sensibilidade
sem a defasagem de origem, definida e ajustada exclusivamente no desenvolvimento.

| Variável excluída do modelo | Justificativa |
| --- | --- |
| RA e nome | Identificadores; RA restrito à correspondência e auditoria local. |
| IAN | Derivado diretamente da defasagem. |
| INDE | Composição dos indicadores, incluindo IAN. |
| Pedra | Classificação derivada do desempenho/INDE. |
| IPP | Ausência estrutural em 2022. |
| Fase ideal | Redundância com fase e defasagem. |
| Informações do ano futuro | Vazamento de informação. |
| Gênero | Uso apenas na auditoria de equidade, sem participação como preditor. |
| Datas e idade | Inconsistências confirmadas entre anos. |
| Escola e instituição | Mudanças cadastrais e risco de baixa generalização. |

A exclusão de uma variável do modelo não implica sua exclusão das análises das
11 perguntas de negócio. Indicadores compostos e informações futuras podem ser
estudados descritivamente, com sua função e temporalidade explicitadas.

## Dados ausentes

A imputação dos indicadores numéricos utilizará a mediana calculada
exclusivamente no desenvolvimento, como transformação dentro do pipeline.
Na validação cruzada, a mediana será ajustada somente na parcela de treino de
cada dobra. Para avaliar o teste temporal, será utilizada a transformação
ajustada no desenvolvimento completo, sem qualquer informação do teste.

Nenhuma ausência será convertida em zero. Os estados originais de
indisponibilidade, como erro Excel, célula vazia, texto e ausência estrutural,
serão preservados na base auditável. O alvo desconhecido não será imputado.
Os resultados com imputação serão comparados aos resultados em casos completos,
com explicitação das diferenças de amostra e cobertura por indicador e ano.

Um sinalizador de ausência somente poderá ser utilizado como preditor quando
houver variação observável no desenvolvimento. Ausências presentes apenas no
teste não fornecem um padrão de ausência aprendível pelo modelo; sua ocorrência
e seus efeitos sobre a cobertura deverão ser relatados.

## Modelos planejados e validação interna

Serão considerados DummyClassifier como referência de prevalência, regressão
logística regularizada como modelo principal interpretável, árvore de decisão
rasa e floresta aleatória com complexidade controlada como comparação
exploratória. A complexidade será limitada pelo tamanho do desenvolvimento:
189 transições, das quais 60 correspondem a eventos.

A validação interna será estratificada, com cinco divisões, embaralhamento e
semente fixa, registrada na implementação. Ocorrerá exclusivamente dentro de
2022→2023. Todas as transformações, inclusive imputação, codificação da fase e
eventual padronização, integrarão o pipeline e serão ajustadas em cada parcela
de treino. A seleção de hiperparâmetros ocorrerá somente no desenvolvimento.

Probabilidades fora das dobras, produzidas para cada observação sem utilizá-la
no ajuste daquela dobra, orientarão a escolha do limiar. As decisões e análises
de sensibilidade serão fixadas antes da avaliação temporal final.

## Métricas e limiar operacional

Average Precision será a métrica principal. Serão relatados também ROC-AUC,
precisão, recall, F1, matriz de confusão, Brier Score e curva de calibração.
A acurácia não será a métrica principal. As medidas dependentes de classificação
serão calculadas com o limiar previamente definido no desenvolvimento.

O limiar priorizará a identificação dos alunos que realmente entrarão em
defasagem. Nas probabilidades fora das dobras do desenvolvimento, será buscado
recall de aproximadamente 80%, adotando 0,80 como patamar mínimo operacional.
Entre os limiares que atenderem a esse patamar, será escolhido o de maior
precisão, registrando o recall efetivamente alcançado e a quantidade sinalizada.
O limiar será aplicado sem alteração no teste temporal.

Em uso futuro, poderão ser estudados ajustes por capacidade de atendimento e a
seleção dos N alunos com maior probabilidade. Essas políticas deverão ser
identificadas separadamente e não modificarão retrospectivamente as métricas
oficiais obtidas com o limiar congelado.

## Incerteza e alunos repetidos

Serão calculados intervalos de confiança no teste temporal por bootstrap,
documentando unidade de reamostragem, semente, número de reamostragens e nível
de confiança. Métricas pontuais não serão apresentadas como valores exatos sem
informar incerteza. O tamanho da amostra e a quantidade de eventos acompanharão
os resultados; métricas não estimáveis em subgrupos ou reamostragens serão
identificadas, sem atribuição artificial de valores.

Um aluno poderá aparecer nas duas transições. Isso não representa vazamento
direto, pois os anos são distintos e RA e nome não serão preditores. Contudo,
a repetição pode afetar a interpretação da generalização. A avaliação mostrará
o resultado no teste temporal completo, o resultado no subconjunto de alunos
que não participaram do desenvolvimento e a diferença entre os resultados,
com suas respectivas amostras e incertezas. Esses recortes não serão utilizados
para reajustar o modelo após a abertura do teste.

## Perda de acompanhamento e equidade

Entre os elegíveis pelos critérios de origem, serão comparados encontrados e
não encontrados no ano seguinte quanto a fase, defasagem inicial, IDA, IEG,
IAA, IPS e IPV, para avaliar possível viés de seleção. Os encontrados sem
defasagem futura válida serão contabilizados separadamente. Ausência de
acompanhamento não será interpretada como sucesso ou fracasso educacional.

Mesmo sem gênero como preditor, serão avaliadas taxa de sinalização, recall,
precisão e calibração por gênero e fase, quando houver tamanho suficiente.
Serão informados denominadores, eventos e indisponibilidades; grupos muito
pequenos não terão métricas individualizadas divulgadas. As inconsistências
cadastrais de gênero identificadas na auditoria deverão acompanhar a interpretação.

## Modelo de avaliação e modelo final

O modelo de avaliação será treinado em 2022→2023 e testado uma única vez em
2023→2024. Esse teste será a origem das métricas oficiais divulgadas. As análises
predefinidas de sensibilidade, cobertura e subgrupos integrarão essa avaliação,
sem nova rodada de seleção a partir dos resultados do teste.

O modelo final do Streamlit será retreinado futuramente com as duas transições
rotuladas, utilizando o mesmo algoritmo e os mesmos hiperparâmetros definidos
anteriormente. Nesse estágio, as duas transições constituirão a base de ajuste
final, inclusive para as transformações do pipeline. Essa etapa será posterior
ao encerramento da avaliação temporal.

Não serão atribuídas ao modelo final métricas calculadas sobre seu treino
completo como evidência de generalização. A aplicação e a apresentação deverão
esclarecer que as métricas oficiais vêm do teste temporal do modelo de avaliação,
e não de um novo teste independente do modelo retreinado.

## Interpretação e limites de uso

O modelo será preditivo e observacional. Não afirmará causalidade, não
substituirá a avaliação pedagógica, não decidirá exclusão ou atendimento
automaticamente e não será apresentado como diagnóstico individual definitivo.
As probabilidades servirão de apoio à priorização e à avaliação pela equipe
responsável, considerando cobertura, incerteza e contexto educacional.

## Metodologia das 11 perguntas de negócio

As análises apresentarão população, período, denominadores e cobertura. A base
possui observações anuais; comparações entre anos não serão apresentadas como
medidas de evolução dentro de um mesmo ano sem observações que as sustentem.

| Pergunta | Abordagem aprovada |
| --- | --- |
| 1. IAN | Distribuição da defasagem por ano, fase e severidade. D≥0 indica ausência de defasagem, −2≤D<0 indica defasagem moderada e D<−2 indica severa, conforme a regra documental do IAN. |
| 2. IDA | Média, mediana, dispersão e cobertura por ano e fase, distinguindo mudanças de composição das mudanças dos alunos acompanhados. |
| 3. IEG × IDA/IPV | Correlação de Spearman, gráficos e análise de associação, sem inferência causal. |
| 4. IAA × IDA/IEG | Coerência, diferenças e perfis de autoavaliação em relação ao desempenho e ao engajamento. |
| 5. IPS antecedendo quedas | IPS no ano t comparado à variação futura de IDA e IEG entre t e t+1, apenas quando houver medidas válidas e correspondência longitudinal. |
| 6. IPP × IAN | Análise apenas dos anos com IPP disponível, informando a indisponibilidade estrutural em 2022 e a cobertura nos demais anos. |
| 7. IPV | Associações longitudinais e importância preditiva; o termo influência não será empregado como afirmação de causalidade. |
| 8. Indicadores × INDE | Reconhecimento de que o INDE é uma composição ponderada dos indicadores, com regras de aplicabilidade por fase; uma relação mecânica não será apresentada como descoberta causal. |
| 9. Machine Learning | Aplicação integral do contrato temporal, da população e do alvo definidos neste documento. |
| 10. Efetividade | Evolução, permanência e transições, sem afirmação de impacto causal na ausência de grupo de controle. |
| 11. Insights | Exploração de perda de acompanhamento, perfis de risco, transições e qualidade dos dados. |

Quartzo, Ágata, Ametista e Topázio são pedras/faixas de desempenho, e não fases
educacionais, apesar da redação da pergunta 10 do enunciado. As pedras observadas
serão preservadas; divergências documentais de faixas não serão resolvidas por
reclassificação presumida.

## Continuidade e rastreabilidade

A preparação das coortes, as análises, o notebook e o treinamento serão
realizados em etapa posterior. Nenhum modelo foi treinado até este marco.
Alterações futuras deste protocolo deverão ser registradas com data e
justificativa no [registro de decisões](registro_decisoes.md), preservando o
histórico e distinguindo decisões anteriores e posteriores ao teste temporal.
O [status do projeto](status_projeto.md) reúne as instruções de continuidade.
