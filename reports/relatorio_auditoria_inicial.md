# Auditoria inicial corrigida

Documento **regenerável**. Relatório público agregado; dados individuais em `local_data/`, ignorada pelo Git.

Execução UTC: 2026-09-17T12:38:26.352406+00:00. Comando: `python src/auditoria_inicial.py`.

## Procedimentos e correções

Esta etapa contemplou auditoria e preparação dos dados. Os arquivos originais foram preservados. Cada execução mantém uma cópia local datada somente dos arquivos que serão regenerados. As bases históricas não foram combinadas à planilha principal.

Foram preservadas as correções de ALFA=0, ano PEDE2022, cabeçalhos repetidos, RA, IAN por D registrado e junções one_to_one. Foram corrigidos códigos de fase com letra, classificação por tipo Excel, inspeção de todas as linhas, faixas dos oito indicadores, comparações cadastrais normalizadas e perda da linha física de origem. O registro manual de decisões foi preservado.

## Resultado por ano

| Ano | Registros | Colunas | D≥0 | Moderada | Severa | RA válidos | RA/ano duplicados |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2022 | 860 | 42 | 259 | 573 | 28 | 860 | 0 |
| 2023 | 1014 | 48 | 462 | 538 | 14 | 1014 | 0 |
| 2024 | 1156 | 50 | 622 | 531 | 3 | 1156 | 0 |

Total: **3030 registros anuais**. RA presentes nos três anos: **468**. Os totais anuais são observações, não uma contagem de alunos únicos no período.

## Qualidade por ano e indicador

Vazias, espaços e erros são estados diferentes. Números válidos abaixo incluem números em texto explicitamente interpretados. Os extremos permanecem na base; 0–10 é apenas uma faixa operacional de sinalização.

| Ano | Indicador | Numéricos | Vazias | Texto vazio/espaços | Erros Excel | INCLUIR | Estrutural | Outros indisponíveis | Números em texto | Zeros | Fora 0–10 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2022 | IAN | 860 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 2022 | IDA | 860 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 6 | 0 |
| 2022 | IEG | 860 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 |
| 2022 | IAA | 860 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 39 | 0 |
| 2022 | IPS | 860 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 2022 | IPP | 0 | 0 | 0 | 0 | 0 | 860 | 0 | 0 | 0 | 0 |
| 2022 | IPV | 860 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 2022 | INDE | 860 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 2023 | IAN | 1014 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 2023 | IDA | 937 | 76 | 0 | 1 | 0 | 0 | 0 | 0 | 1 | 0 |
| 2023 | IEG | 938 | 76 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 2023 | IAA | 951 | 63 | 0 | 0 | 0 | 0 | 0 | 0 | 190 | 0 |
| 2023 | IPS | 945 | 0 | 0 | 69 | 0 | 0 | 0 | 0 | 0 | 0 |
| 2023 | IPP | 938 | 0 | 0 | 76 | 0 | 0 | 0 | 0 | 0 | 0 |
| 2023 | IPV | 938 | 0 | 0 | 76 | 0 | 0 | 0 | 0 | 0 | 26 |
| 2023 | INDE | 931 | 0 | 0 | 83 | 0 | 0 | 0 | 0 | 0 | 0 |
| 2024 | IAN | 1156 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 2024 | IDA | 1055 | 0 | 0 | 101 | 0 | 0 | 0 | 0 | 16 | 0 |
| 2024 | IEG | 1156 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 109 | 0 |
| 2024 | IAA | 1054 | 0 | 102 | 0 | 0 | 0 | 0 | 0 | 20 | 122 |
| 2024 | IPS | 1054 | 0 | 0 | 102 | 0 | 0 | 0 | 0 | 0 | 0 |
| 2024 | IPP | 1054 | 0 | 0 | 102 | 0 | 0 | 0 | 0 | 0 | 0 |
| 2024 | IPV | 1054 | 0 | 0 | 102 | 0 | 0 | 0 | 0 | 0 | 0 |
| 2024 | INDE | 1054 | 0 | 0 | 64 | 38 | 0 | 0 | 0 | 0 | 0 |

| Ano | Indicador | Motivos de indisponibilidade | Mínimo numérico | Máximo numérico |
| --- | --- | --- | --- | --- |
| 2022 | IAN | nenhum | 2.5 | 10.0 |
| 2022 | IDA | nenhum | 0.0 | 9.9 |
| 2022 | IEG | nenhum | 0.0 | 10.0 |
| 2022 | IAA | nenhum | 0.0 | 10.0 |
| 2022 | IPS | nenhum | 2.5 | 10.0 |
| 2022 | IPP | ausencia_estrutural: 860 | — | — |
| 2022 | IPV | nenhum | 2.5 | 10.0 |
| 2022 | INDE | nenhum | 3.032 | 9.442 |
| 2023 | IAN | nenhum | 2.5 | 10.0 |
| 2023 | IDA | erro_excel:#DIV/0!: 1; celula_vazia: 76 | 0.0 | 10.0 |
| 2023 | IEG | celula_vazia: 76 | 3.7 | 10.0 |
| 2023 | IAA | celula_vazia: 63 | 0.0 | 10.0 |
| 2023 | IPS | erro_excel:#N/A: 69 | 2.52 | 10.0 |
| 2023 | IPP | erro_excel:#N/A: 76 | 3.75 | 9.791666667 |
| 2023 | IPV | erro_excel:#N/A: 76 | 3.32 | 10.01 |
| 2023 | INDE | erro_excel:#DIV/0!: 1; erro_excel:#N/A: 82 | 3.745541667 | 9.3712 |
| 2024 | IAN | nenhum | 2.5 | 10.0 |
| 2024 | IDA | erro_excel:#DIV/0!: 101 | 0.0 | 10.0 |
| 2024 | IEG | nenhum | 0.0 | 10.0 |
| 2024 | IAA | texto_vazio: 102 | 0.0 | 10.002 |
| 2024 | IPS | erro_excel:#N/A: 102 | 2.51 | 10.0 |
| 2024 | IPP | erro_excel:#N/A: 102 | 2.5 | 10.0 |
| 2024 | IPV | erro_excel:#N/A: 102 | 2.943333333 | 9.76 |
| 2024 | INDE | erro_excel:#DIV/0!: 63; erro_excel:#N/A: 1; incluir: 38 | 3.7894777778 | 9.531325 |

## Fases, IAN e defasagem: verificações separadas

| Ano | Fase: status e contagens | Fase 9 | IAN×D: iguais/divergentes/não comparáveis | D×(fase−ideal): iguais/divergentes/não comparáveis |
| --- | --- | --- | --- | --- |
| 2022 | interpretado_rotulo: 860 | 0 | 860/0/0 | 860/0/0 |
| 2023 | interpretado_alfa: 231; interpretado_rotulo: 783 | 0 | 1014/0/0 | 1014/0/0 |
| 2024 | interpretado_alfa: 196; interpretado_codigo_turma: 922; interpretado_numerico: 38 | 38 | 1156/0/0 | 1154/2/0 |

O segundo teste é aritmético sobre códigos extraídos. Concordância não confirma equivalência curricular nem resolve o significado da fase 9. A regra do IAN vem da Tabela 41 do DOCX (imagem no parágrafo 23): D≥0→10, −2≤D<0→5, D<−2→2,5.

## Correspondência e transições descritivas por RA

| Transição | Recorte na origem | Elegíveis D≥0 | Encontrados | Não encontrados | Destino sem D válido | D futuro<0 |
| --- | --- | --- | --- | --- | --- | --- |
| 2022->2023 | todas_fases | 259 | 189 | 70 | 0 | 60 |
| 2022->2023 | fases_0_a_7 | 259 | 189 | 70 | 0 | 60 |
| 2023->2024 | todas_fases | 462 | 370 | 92 | 0 | 84 |
| 2023->2024 | fases_0_a_7 | 399 | 311 | 88 | 0 | 84 |

Todas as junções usam RA válido e `validate="one_to_one"`; duplicidade bloqueia a junção e não é resolvida apagando registros. Ausência de destino ou de D futuro gera desfecho desconhecido (null). Os recortes são conferências descritivas, sem decisão sobre população final do modelo.

Nos metadados, `phase_origin_counts` contabiliza todos os elegíveis por fase de origem; `phase_origin_found_counts` contabiliza somente os encontrados no destino. As somas correspondem, respectivamente, a elegíveis e encontrados.

## Comparações cadastrais

| Anos | Campo | Pares RA | Diferenças brutas | Só representação | Divergências normalizadas | Comparáveis normalizados | Não comparáveis |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2022->2023 | nome | 600 | 0 | 0 | 0 | 600 | 0 |
| 2022->2023 | ano_nascimento | 600 | 600 | 595 | 5 | 600 | 0 |
| 2022->2023 | data_nascimento | 600 | 0 | 0 | 0 | 0 | 600 |
| 2022->2023 | genero | 600 | 600 | 588 | 12 | 600 | 0 |
| 2022->2023 | ano_ingresso | 600 | 0 | 0 | 0 | 600 | 0 |
| 2022->2023 | instituicao_ensino | 600 | 600 | 449 | 151 | 600 | 0 |
| 2022->2023 | escola | 600 | 0 | 0 | 0 | 0 | 600 |
| 2023->2024 | nome | 765 | 0 | 0 | 0 | 765 | 0 |
| 2023->2024 | ano_nascimento | 765 | 747 | 744 | 3 | 765 | 0 |
| 2023->2024 | data_nascimento | 765 | 747 | 460 | 287 | 765 | 0 |
| 2023->2024 | genero | 765 | 0 | 0 | 0 | 765 | 0 |
| 2023->2024 | ano_ingresso | 765 | 199 | 0 | 199 | 765 | 0 |
| 2023->2024 | instituicao_ensino | 765 | 98 | 0 | 98 | 765 | 0 |
| 2023->2024 | escola | 765 | 0 | 0 | 0 | 0 | 765 |

Em ano de nascimento, a categoria representação também inclui granularidade: ano isolado versus data completa com o mesmo ano. Não se conclui igualdade do dia/mês a partir dessa comparação. Datas ambíguas não são resolvidas pelo outro ano. Mudança de instituição/escola pode ser real e não comprova erro de identidade; nomes nunca são chaves de ligação.

| Ano | Datas de nascimento: status | Idade: status |
| --- | --- | --- |
| 2022 | coluna_ausente: 860 | numero_valido: 860 |
| 2023 | texto_inequivoco: 615; data_excel: 399 | numero_valido: 615; data: 399 |
| 2024 | data_excel: 1156 | numero_valido: 1156 |

## Conferência com as referências fornecidas

| Verificação | Calculado | Referência | Confere |
| --- | --- | --- | --- |
| 2022: registros | 860 | 860 | sim |
| 2022: colunas | 42 | 42 | sim |
| 2022: D >= 0 | 259 | 259 | sim |
| 2023: registros | 1014 | 1014 | sim |
| 2023: colunas | 48 | 48 | sim |
| 2023: D >= 0 | 462 | 462 | sim |
| 2024: registros | 1156 | 1156 | sim |
| 2024: colunas | 50 | 50 | sim |
| 2024: D >= 0 | 622 | 622 | sim |
| RA comuns 2022->2023 | 600 | 600 | sim |
| RA comuns 2023->2024 | 765 | 765 | sim |
| RA nos três anos | 468 | 468 | sim |
| 2022->2023 todas_fases: with_dest_count | 189 | 189 | sim |
| 2022->2023 todas_fases: dest_defasado_count | 60 | 60 | sim |
| 2023->2024 todas_fases: with_dest_count | 370 | 370 | sim |
| 2023->2024 todas_fases: dest_defasado_count | 84 | 84 | sim |
| 2023->2024 fases_0_a_7: eligible_count | 399 | 399 | sim |
| 2023->2024 fases_0_a_7: with_dest_count | 311 | 311 | sim |
| 2023->2024 fases_0_a_7: not_found_in_destination_count | 88 | 88 | sim |
| 2023->2024 fases_0_a_7: dest_defasado_count | 84 | 84 | sim |
| 2023 IPP: erro_excel:#N/A | 76 | 76 | sim |
| 2024 IPP: erro_excel:#N/A | 102 | 102 | sim |
| 2023 IDA: celula_vazia | 76 | 76 | sim |
| 2023 IDA: erro_excel:#DIV/0! | 1 | 1 | sim |
| 2024 IDA: erro_excel:#DIV/0! | 101 | 101 | sim |
| 2024 INDE: erro_excel:#DIV/0! | 63 | 63 | sim |
| 2024 INDE: erro_excel:#N/A | 1 | 1 | sim |
| 2024 INDE: incluir | 38 | 38 | sim |

Todas as referências foram reproduzidas por código.

## Validações e rastreabilidade

| Verificação | Resultado |
| --- | --- |
| registros_derivados_para_auditoria | 3030 |

Fontes: **13 arquivos**, integridade antes/depois da execução: **True**; Documentos manuais preservados: **True**. Dados individuais fora do versionamento: **True**.

Inventário anterior disponível para esta etapa: True. Diferença entre execuções: {'adicionados': [], 'removidos': [], 'alterados': []}. Esta comparação histórica é distinta da releitura dos hashes antes/depois da execução atual.

Baseline histórico nos metadados disponível: **True**; coincidência com as fontes atuais: **True**. A comparação histórica é opcional e não depende de uma pasta de recuperação local. A integridade da execução atual é verificada independentemente do baseline.

Os testes unitários e a validação da base são verificações diferentes. A evidência da execução dos testes está em `reports/verificacao_final.md`; metadados registram hashes dos scripts, testes, fontes e saídas. Nenhuma execução de teste constitui validação externa das regras de negócio.

## Pendências metodológicas e impacto

- **Equivalência curricular:** a Tabela 4 do DOCX usa referências 2020/2021 e difere de rótulos atuais de ALFA/fase 1. A fase extraída não autoriza recalcular a ideal pela idade.
- **Fase 8 e fase 9:** há pesos e aplicabilidade diferentes para a fase 8 nos Quadros 2/3 e no esquema INDE; o significado da fase 9 e de INCLUIR permanece pendente. Os alunos e erros observados foram mantidos.
- **Faixas:** IAN possui regra explícita; IAA tem referência 0–10 no texto e na Tabela 40. Para os demais, a faixa operacional não comprova limites documentais em todos os anos. Extremos precisam de investigação.
- **Pedras e INDE:** limites do dicionário diferem da Figura 3 do DOCX; não houve reclassificação de pedras ou recomposição do INDE.
- **Indisponibilidade:** IPP é estruturalmente ausente em 2022; erros Excel e outros vazios nos demais anos não receberam causa presumida nem imputação.
- **Cadastro:** datas ambíguas, idades armazenadas como datas e divergências normalizadas permanecem sinalizadas; não há correção por suposição.
- **Risco futuro:** perda de seguimento e aplicabilidade dos indicadores podem alterar a população analisável. Definição de alvo, recorte e estratégia temporal do modelo ficam para decisão posterior.
- **Escopo:** auditoria e preparação concluídas nos limites das verificações registradas. Análises de negócio completas, notebook preditivo, apresentação, aplicação, publicação e vídeo pertencem às próximas etapas.

Evidências textuais e visuais e suas localizações: `docs/evidencias_documentais.md`. A revisão documental foi realizada em 15/09/2026 e contemplou seis páginas do enunciado, quatro do dicionário, nove de desvendando_passos e dez imagens do DOCX. A inspeção das imagens extraídas do DOCX não é uma validação da sua paginação renderizada.
