# Relatório das coortes de modelagem

Documento regenerável e agregado; sem amostras individuais.

Início UTC: 2026-09-17T14:21:01.779003+00:00. Comando: `python src/preparacao_coortes.py`.

## Fluxo de inclusão e exclusão

Exclusões sequenciais, na ordem abaixo, sem dupla contagem. Fases referem-se ao ano de origem.

| Etapa | 2022→2023: desenvolvimento | 2023→2024: teste temporal |
| --- | --- | --- |
| Registros na origem | 860 | 1014 |
| Exclusão: ra_invalido | 0 | 0 |
| Exclusão: defasagem_indisponivel | 0 | 0 |
| Exclusão: ja_defasado | 601 | 552 |
| Exclusão: fase_8 | 0 | 63 |
| Exclusão: fase_9 | 0 | 0 |
| Exclusão: fase_nao_elegivel | 0 | 0 |
| elegiveis_origem | 259 | 399 |
| encontrados | 189 | 311 |
| nao_encontrados | 70 | 88 |
| destino_sem_defasagem | 0 | 0 |
| supervisionados | 189 | 311 |
| alvo_1 | 60 | 84 |
| alvo_0 | 129 | 227 |
| alvo_desconhecido | 70 | 88 |
| Taxa de evento entre supervisionados | 31.75% | 27.01% |

A distribuição abaixo considera todos os registros de origem, antes das exclusões sequenciais.

| Ano de origem | Fases: contagens |
| --- | --- |
| 2022 | {'0': 190, '1': 192, '2': 155, '3': 148, '4': 76, '5': 60, '6': 18, '7': 21} |
| 2023 | {'0': 231, '1': 173, '2': 200, '3': 132, '4': 94, '5': 65, '6': 33, '7': 23, '8': 63} |

## Disponibilidade dos preditores

Valores do ano de origem, sem imputação. Ausências mantêm seu motivo; zeros observados permanecem zeros.

| Ano | População | Preditor | Total | Disponíveis | Ausentes | Motivos |
| --- | --- | --- | --- | --- | --- | --- |
| 2022 | elegiveis | ida | 259 | 259 | 0 | {} |
| 2022 | elegiveis | ieg | 259 | 259 | 0 | {} |
| 2022 | elegiveis | iaa | 259 | 259 | 0 | {} |
| 2022 | elegiveis | ips | 259 | 259 | 0 | {} |
| 2022 | elegiveis | ipv | 259 | 259 | 0 | {} |
| 2022 | elegiveis | fase_origem | 259 | 259 | 0 | {} |
| 2022 | elegiveis | defasagem_origem | 259 | 259 | 0 | {} |
| 2022 | supervisionados | ida | 189 | 189 | 0 | {} |
| 2022 | supervisionados | ieg | 189 | 189 | 0 | {} |
| 2022 | supervisionados | iaa | 189 | 189 | 0 | {} |
| 2022 | supervisionados | ips | 189 | 189 | 0 | {} |
| 2022 | supervisionados | ipv | 189 | 189 | 0 | {} |
| 2022 | supervisionados | fase_origem | 189 | 189 | 0 | {} |
| 2022 | supervisionados | defasagem_origem | 189 | 189 | 0 | {} |
| 2023 | elegiveis | ida | 399 | 388 | 11 | {'celula_vazia': 11} |
| 2023 | elegiveis | ieg | 399 | 388 | 11 | {'celula_vazia': 11} |
| 2023 | elegiveis | iaa | 399 | 399 | 0 | {} |
| 2023 | elegiveis | ips | 399 | 398 | 1 | {'erro_excel:#N/A': 1} |
| 2023 | elegiveis | ipv | 399 | 388 | 11 | {'erro_excel:#N/A': 11} |
| 2023 | elegiveis | fase_origem | 399 | 399 | 0 | {} |
| 2023 | elegiveis | defasagem_origem | 399 | 399 | 0 | {} |
| 2023 | supervisionados | ida | 311 | 300 | 11 | {'celula_vazia': 11} |
| 2023 | supervisionados | ieg | 311 | 300 | 11 | {'celula_vazia': 11} |
| 2023 | supervisionados | iaa | 311 | 311 | 0 | {} |
| 2023 | supervisionados | ips | 311 | 311 | 0 | {} |
| 2023 | supervisionados | ipv | 311 | 300 | 11 | {'erro_excel:#N/A': 11} |
| 2023 | supervisionados | fase_origem | 311 | 311 | 0 | {} |
| 2023 | supervisionados | defasagem_origem | 311 | 311 | 0 | {} |

## Separação de dados e validações

X contém somente `ida`, `ieg`, `iaa`, `ips`, `ipv`, `fase_origem`, `defasagem_origem`. A fase é categórica, com categorias 0 a 7 sem ordem estatística. Os CSV não armazenam tipos: usar `supervised_matrices` para reconstruir X e y com os tipos do schema.

A chave privada (RA e anos), linhas físicas, estados de ausência e informações do destino para auditoria ficam em blocos separados no JSONL. Somente o alvo utiliza a defasagem futura. RA, nome e demais identificadores não pertencem às colunas nem ao índice de X. IAN, INDE, Pedra, IPP, fase ideal, gênero, idade, datas, escola, instituição, unidade e textos administrativos estão fora de X.

A junção reutiliza a validação one_to_one. O JSONL mantém elegíveis com alvo desconhecido; os CSV contêm apenas supervisionados, na mesma ordem por linha física. Não há embaralhamento entre anos. As saídas são reabertas e comparadas integralmente aos valores de origem e à lista fechada de preditores.

As evidências estruturadas das validações e os hashes das saídas constam de `reports/metadados_coortes.json`.

| Verificação | Resultado |
| --- | --- |
| coortes_serializadas_conferidas | True |
| X_sem_identificadores | True |
| X_somente_variaveis_origem | True |
| fase_categorica | True |
| desconhecidos_fora_matrizes_supervisionadas | True |
| separacao_temporal_preservada | True |

## Comparação e limitações

| Sobreposição no teste supervisionado | Registros |
| --- | --- |
| teste_com_participacao_desenvolvimento | 104 |
| teste_sem_participacao_desenvolvimento | 207 |

Diferenças de cobertura, prevalência e perda de acompanhamento entre as transições são descritivas; o teste permanece reservado e não orienta seleção de variáveis, algoritmo, hiperparâmetros ou limiar. Ausências presentes apenas no teste não fornecem um padrão aprendível no desenvolvimento.

A equivalência curricular entre anos e o significado da fase 9 permanecem limitados pela documentação. Fases 8/9 são excluídas pela fase de origem; uma fase diferente no destino não redefine a elegibilidade de origem. INCLUIR não recebe conversão presumida. Não foram identificados conflitos metodológicos impeditivos: a exigência de D futuro válido complementa a localização no destino, conforme o contrato.

Permanecem pendentes as análises das 11 perguntas, a comparação dos perfis de perda de acompanhamento, o notebook e o pipeline de imputação/validação interna, a sensibilidade, a avaliação de equidade e o treinamento. Nenhum modelo foi treinado e nenhum indicador foi imputado nesta etapa.
