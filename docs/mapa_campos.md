# Mapa de campos

Regenerável por `python src/auditoria_inicial.py` e `python src/preparacao_longitudinal.py`.
Todos os campos da fonte permanecem em `originais`, por nome interno único, com posição,
cabeçalho original exato, valor, tipo Python, tipo Excel e formato numérico.
Cabeçalhos repetidos são identificados antes da renomeação. Colunas históricas não
substituem os indicadores do ano de referência.

## Colunas de origem e correspondência

| Ano | Posição | Cabeçalho original | Nome interno | Repetido | Tipos: contagens (todas as linhas) | Campo derivado |
| --- | --- | --- | --- | --- | --- | --- |
| 2022 | 1 | RA | RA | False | outro_texto: 860 | ra |
| 2022 | 2 | Fase | Fase | False | numero_em_texto: 860 | fase |
| 2022 | 3 | Turma | Turma | False | outro_texto: 860 | turma |
| 2022 | 4 | Nome | Nome | False | outro_texto: 860 | nome |
| 2022 | 5 | Ano nasc | Ano nasc | False | numero_valido: 860 | ano_nascimento |
| 2022 | 6 | Idade 22 | Idade 22 | False | numero_valido: 860 | idade |
| 2022 | 7 | Gênero | Gênero | False | outro_texto: 860 | genero |
| 2022 | 8 | Ano ingresso | Ano ingresso | False | numero_valido: 860 | ano_ingresso |
| 2022 | 9 | Instituição de ensino | Instituição de ensino | False | outro_texto: 860 | instituicao_ensino |
| 2022 | 10 | Pedra 20 | Pedra 20 | False | outro_texto: 323; celula_vazia: 537 | somente originais (sem equivalência presumida) |
| 2022 | 11 | Pedra 21 | Pedra 21 | False | outro_texto: 462; celula_vazia: 398 | somente originais (sem equivalência presumida) |
| 2022 | 12 | Pedra 22 | Pedra 22 | False | outro_texto: 860 | pedra |
| 2022 | 13 | INDE 22 | INDE 22 | False | numero_valido: 860 | inde |
| 2022 | 14 | Cg | Cg | False | numero_valido: 860 | somente originais (sem equivalência presumida) |
| 2022 | 15 | Cf | Cf | False | numero_valido: 860 | somente originais (sem equivalência presumida) |
| 2022 | 16 | Ct | Ct | False | numero_valido: 860 | somente originais (sem equivalência presumida) |
| 2022 | 17 | Nº Av | Nº Av | False | numero_valido: 860 | somente originais (sem equivalência presumida) |
| 2022 | 18 | Avaliador1 | Avaliador1 | False | outro_texto: 860 | somente originais (sem equivalência presumida) |
| 2022 | 19 | Rec Av1 | Rec Av1 | False | outro_texto: 860 | somente originais (sem equivalência presumida) |
| 2022 | 20 | Avaliador2 | Avaliador2 | False | outro_texto: 860 | somente originais (sem equivalência presumida) |
| 2022 | 21 | Rec Av2 | Rec Av2 | False | outro_texto: 860 | somente originais (sem equivalência presumida) |
| 2022 | 22 | Avaliador3 | Avaliador3 | False | outro_texto: 534; celula_vazia: 326 | somente originais (sem equivalência presumida) |
| 2022 | 23 | Rec Av3 | Rec Av3 | False | outro_texto: 860 | somente originais (sem equivalência presumida) |
| 2022 | 24 | Avaliador4 | Avaliador4 | False | outro_texto: 310; celula_vazia: 550 | somente originais (sem equivalência presumida) |
| 2022 | 25 | Rec Av4 | Rec Av4 | False | outro_texto: 296; celula_vazia: 564 | somente originais (sem equivalência presumida) |
| 2022 | 26 | IAA | IAA | False | numero_valido: 860 | iaa |
| 2022 | 27 | IEG | IEG | False | numero_valido: 860 | ieg |
| 2022 | 28 | IPS | IPS | False | numero_valido: 860 | ips |
| 2022 | 29 | Rec Psicologia | Rec Psicologia | False | outro_texto: 860 | somente originais (sem equivalência presumida) |
| 2022 | 30 | IDA | IDA | False | numero_valido: 860 | ida |
| 2022 | 31 | Matem | Matem | False | numero_valido: 858; celula_vazia: 2 | somente originais (sem equivalência presumida) |
| 2022 | 32 | Portug | Portug | False | numero_valido: 858; celula_vazia: 2 | somente originais (sem equivalência presumida) |
| 2022 | 33 | Inglês | Inglês | False | numero_valido: 283; celula_vazia: 577 | somente originais (sem equivalência presumida) |
| 2022 | 34 | Indicado | Indicado | False | outro_texto: 860 | somente originais (sem equivalência presumida) |
| 2022 | 35 | Atingiu PV | Atingiu PV | False | outro_texto: 860 | somente originais (sem equivalência presumida) |
| 2022 | 36 | IPV | IPV | False | numero_valido: 860 | ipv |
| 2022 | 37 | IAN | IAN | False | numero_valido: 860 | ian |
| 2022 | 38 | Fase ideal | Fase ideal | False | outro_texto: 860 | fase_ideal |
| 2022 | 39 | Defas | Defas | False | numero_valido: 860 | defasagem |
| 2022 | 40 | Destaque IEG | Destaque IEG | False | outro_texto: 860 | somente originais (sem equivalência presumida) |
| 2022 | 41 | Destaque IDA | Destaque IDA | False | outro_texto: 860 | somente originais (sem equivalência presumida) |
| 2022 | 42 | Destaque IPV | Destaque IPV | False | outro_texto: 860 | somente originais (sem equivalência presumida) |
| 2023 | 1 | RA | RA | False | outro_texto: 1014 | ra |
| 2023 | 2 | Fase | Fase | False | outro_texto: 1014 | fase |
| 2023 | 3 | INDE 2023 | INDE 2023 | False | numero_valido: 931; erro_excel: 83 | inde |
| 2023 | 4 | Pedra 2023 | Pedra 2023 | False | outro_texto: 931; erro_excel: 83 | pedra |
| 2023 | 5 | Turma | Turma | False | outro_texto: 1014 | turma |
| 2023 | 6 | Nome Anonimizado | Nome Anonimizado | False | outro_texto: 1014 | nome |
| 2023 | 7 | Data de Nasc | Data de Nasc | False | outro_texto: 615; data: 399 | data_nascimento |
| 2023 | 8 | Idade | Idade | False | numero_valido: 615; data: 399 | idade |
| 2023 | 9 | Gênero | Gênero | False | outro_texto: 1014 | genero |
| 2023 | 10 | Ano ingresso | Ano ingresso | False | numero_valido: 1014 | ano_ingresso |
| 2023 | 11 | Instituição de ensino | Instituição de ensino | False | outro_texto: 1014 | instituicao_ensino |
| 2023 | 12 | Pedra 20 | Pedra 20 | False | celula_vazia: 774; outro_texto: 240 | somente originais (sem equivalência presumida) |
| 2023 | 13 | Pedra 21 | Pedra 21 | False | celula_vazia: 679; outro_texto: 335 | somente originais (sem equivalência presumida) |
| 2023 | 14 | Pedra 22 | Pedra 22 | False | celula_vazia: 414; outro_texto: 600 | somente originais (sem equivalência presumida) |
| 2023 | 15 | Pedra 23 | Pedra 23 | False | celula_vazia: 1014 | somente originais (sem equivalência presumida) |
| 2023 | 16 | INDE 22 | INDE 22 | False | celula_vazia: 414; numero_valido: 600 | somente originais (sem equivalência presumida) |
| 2023 | 17 | INDE 23 | INDE 23 | False | celula_vazia: 1014 | somente originais (sem equivalência presumida) |
| 2023 | 18 | Cg | Cg | False | celula_vazia: 1014 | somente originais (sem equivalência presumida) |
| 2023 | 19 | Cf | Cf | False | celula_vazia: 1014 | somente originais (sem equivalência presumida) |
| 2023 | 20 | Ct | Ct | False | celula_vazia: 1014 | somente originais (sem equivalência presumida) |
| 2023 | 21 | Nº Av | Nº Av | False | numero_valido: 938; celula_vazia: 76 | somente originais (sem equivalência presumida) |
| 2023 | 22 | Avaliador1 | Avaliador1 | False | outro_texto: 938; celula_vazia: 76 | somente originais (sem equivalência presumida) |
| 2023 | 23 | Rec Av1 | Rec Av1 | False | celula_vazia: 1014 | somente originais (sem equivalência presumida) |
| 2023 | 24 | Avaliador2 | Avaliador2 | False | outro_texto: 938; celula_vazia: 76 | somente originais (sem equivalência presumida) |
| 2023 | 25 | Rec Av2 | Rec Av2 | False | celula_vazia: 1014 | somente originais (sem equivalência presumida) |
| 2023 | 26 | Avaliador3 | Avaliador3 | False | texto_vazio: 231; outro_texto: 707; celula_vazia: 76 | somente originais (sem equivalência presumida) |
| 2023 | 27 | Rec Av3 | Rec Av3 | False | celula_vazia: 1014 | somente originais (sem equivalência presumida) |
| 2023 | 28 | Avaliador4 | Avaliador4 | False | texto_vazio: 604; outro_texto: 334; celula_vazia: 76 | somente originais (sem equivalência presumida) |
| 2023 | 29 | Rec Av4 | Rec Av4 | False | celula_vazia: 1014 | somente originais (sem equivalência presumida) |
| 2023 | 30 | IAA | IAA | False | numero_valido: 951; celula_vazia: 63 | iaa |
| 2023 | 31 | IEG | IEG | False | numero_valido: 938; celula_vazia: 76 | ieg |
| 2023 | 32 | IPS | IPS | False | numero_valido: 945; erro_excel: 69 | ips |
| 2023 | 33 | IPP | IPP | False | numero_valido: 938; erro_excel: 76 | ipp |
| 2023 | 34 | Rec Psicologia | Rec Psicologia | False | celula_vazia: 1014 | somente originais (sem equivalência presumida) |
| 2023 | 35 | IDA | IDA | False | numero_valido: 937; erro_excel: 1; celula_vazia: 76 | ida |
| 2023 | 36 | Mat | Mat | False | numero_valido: 937; celula_vazia: 77 | somente originais (sem equivalência presumida) |
| 2023 | 37 | Por | Por | False | numero_valido: 937; celula_vazia: 77 | somente originais (sem equivalência presumida) |
| 2023 | 38 | Ing | Ing | False | celula_vazia: 680; numero_valido: 334 | somente originais (sem equivalência presumida) |
| 2023 | 39 | Indicado | Indicado | False | celula_vazia: 1014 | somente originais (sem equivalência presumida) |
| 2023 | 40 | Atingiu PV | Atingiu PV | False | celula_vazia: 1014 | somente originais (sem equivalência presumida) |
| 2023 | 41 | IPV | IPV | False | numero_valido: 938; erro_excel: 76 | ipv |
| 2023 | 42 | IAN | IAN | False | numero_valido: 1014 | ian |
| 2023 | 43 | Fase Ideal | Fase Ideal | False | outro_texto: 1014 | fase_ideal |
| 2023 | 44 | Defasagem | Defasagem | False | numero_valido: 1014 | defasagem |
| 2023 | 45 | Destaque IEG | Destaque IEG | False | celula_vazia: 1014 | somente originais (sem equivalência presumida) |
| 2023 | 46 | Destaque IDA | Destaque IDA | False | celula_vazia: 1014 | somente originais (sem equivalência presumida) |
| 2023 | 47 | Destaque IPV | Destaque IPV | False | celula_vazia: 1014 | somente originais (sem equivalência presumida) |
| 2023 | 48 | Destaque IPV | Destaque IPV_1 | True | celula_vazia: 1014 | somente originais (sem equivalência presumida) |
| 2024 | 1 | RA | RA | False | outro_texto: 1156 | ra |
| 2024 | 2 | Fase | Fase | False | outro_texto: 1118; numero_valido: 38 | fase |
| 2024 | 3 | INDE 2024 | INDE 2024 | False | numero_valido: 1054; erro_excel: 64; incluir: 38 | inde |
| 2024 | 4 | Pedra 2024 | Pedra 2024 | False | outro_texto: 1054; erro_excel: 64; incluir: 38 | pedra |
| 2024 | 5 | Turma | Turma | False | outro_texto: 1118; numero_valido: 38 | turma |
| 2024 | 6 | Nome Anonimizado | Nome Anonimizado | False | outro_texto: 1156 | nome |
| 2024 | 7 | Data de Nasc | Data de Nasc | False | data: 1156 | data_nascimento |
| 2024 | 8 | Idade | Idade | False | numero_valido: 1156 | idade |
| 2024 | 9 | Gênero | Gênero | False | outro_texto: 1156 | genero |
| 2024 | 10 | Ano ingresso | Ano ingresso | False | numero_valido: 1156 | ano_ingresso |
| 2024 | 11 | Instituição de ensino | Instituição de ensino | False | outro_texto: 1155; celula_vazia: 1 | instituicao_ensino |
| 2024 | 12 | Pedra 20 | Pedra 20 | False | texto_vazio: 684; celula_vazia: 281; outro_texto: 191 | somente originais (sem equivalência presumida) |
| 2024 | 13 | Pedra 21 | Pedra 21 | False | texto_vazio: 684; celula_vazia: 208; outro_texto: 264 | somente originais (sem equivalência presumida) |
| 2024 | 14 | Pedra 22 | Pedra 22 | False | texto_vazio: 684; outro_texto: 472 | somente originais (sem equivalência presumida) |
| 2024 | 15 | Pedra 23 | Pedra 23 | False | texto_vazio: 391; outro_texto: 690; erro_excel: 75 | somente originais (sem equivalência presumida) |
| 2024 | 16 | INDE 22 | INDE 22 | False | texto_vazio: 684; numero_valido: 472 | somente originais (sem equivalência presumida) |
| 2024 | 17 | INDE 23 | INDE 23 | False | texto_vazio: 391; numero_valido: 690; erro_excel: 75 | somente originais (sem equivalência presumida) |
| 2024 | 18 | Cg | Cg | False | celula_vazia: 1156 | somente originais (sem equivalência presumida) |
| 2024 | 19 | Cf | Cf | False | celula_vazia: 1156 | somente originais (sem equivalência presumida) |
| 2024 | 20 | Ct | Ct | False | celula_vazia: 1156 | somente originais (sem equivalência presumida) |
| 2024 | 21 | Nº Av | Nº Av | False | numero_valido: 1156 | somente originais (sem equivalência presumida) |
| 2024 | 22 | Avaliador1 | Avaliador1 | False | outro_texto: 1029; celula_vazia: 127 | somente originais (sem equivalência presumida) |
| 2024 | 23 | Rec Av1 | Rec Av1 | False | celula_vazia: 1156 | somente originais (sem equivalência presumida) |
| 2024 | 24 | Avaliador2 | Avaliador2 | False | outro_texto: 1029; celula_vazia: 127 | somente originais (sem equivalência presumida) |
| 2024 | 25 | Rec Av2 | Rec Av2 | False | celula_vazia: 1156 | somente originais (sem equivalência presumida) |
| 2024 | 26 | Avaliador3 | Avaliador3 | False | outro_texto: 793; texto_vazio: 324; celula_vazia: 39 | somente originais (sem equivalência presumida) |
| 2024 | 27 | Avaliador4 | Avaliador4 | False | texto_vazio: 685; outro_texto: 407; celula_vazia: 64 | somente originais (sem equivalência presumida) |
| 2024 | 28 | Avaliador5 | Avaliador5 | False | texto_vazio: 938; outro_texto: 148; celula_vazia: 70 | somente originais (sem equivalência presumida) |
| 2024 | 29 | Avaliador6 | Avaliador6 | False | texto_vazio: 1110; outro_texto: 6; celula_vazia: 40 | somente originais (sem equivalência presumida) |
| 2024 | 30 | IAA | IAA | False | numero_valido: 1054; texto_vazio: 102 | iaa |
| 2024 | 31 | IEG | IEG | False | numero_valido: 1156 | ieg |
| 2024 | 32 | IPS | IPS | False | numero_valido: 1054; erro_excel: 102 | ips |
| 2024 | 33 | IPP | IPP | False | numero_valido: 1054; erro_excel: 102 | ipp |
| 2024 | 34 | Rec Psicologia | Rec Psicologia | False | celula_vazia: 1156 | somente originais (sem equivalência presumida) |
| 2024 | 35 | IDA | IDA | False | numero_valido: 1055; erro_excel: 101 | ida |
| 2024 | 36 | Mat | Mat | False | numero_valido: 1051; texto_vazio: 105 | somente originais (sem equivalência presumida) |
| 2024 | 37 | Por | Por | False | numero_valido: 1050; texto_vazio: 106 | somente originais (sem equivalência presumida) |
| 2024 | 38 | Ing | Ing | False | texto_vazio: 682; numero_valido: 474 | somente originais (sem equivalência presumida) |
| 2024 | 39 | Indicado | Indicado | False | celula_vazia: 1156 | somente originais (sem equivalência presumida) |
| 2024 | 40 | Atingiu PV | Atingiu PV | False | celula_vazia: 1156 | somente originais (sem equivalência presumida) |
| 2024 | 41 | IPV | IPV | False | numero_valido: 1054; erro_excel: 102 | ipv |
| 2024 | 42 | IAN | IAN | False | numero_valido: 1156 | ian |
| 2024 | 43 | Fase Ideal | Fase Ideal | False | outro_texto: 1156 | fase_ideal |
| 2024 | 44 | Defasagem | Defasagem | False | numero_valido: 1156 | defasagem |
| 2024 | 45 | Destaque IEG | Destaque IEG | False | celula_vazia: 1156 | somente originais (sem equivalência presumida) |
| 2024 | 46 | Destaque IDA | Destaque IDA | False | celula_vazia: 1156 | somente originais (sem equivalência presumida) |
| 2024 | 47 | Destaque IPV | Destaque IPV | False | celula_vazia: 1156 | somente originais (sem equivalência presumida) |
| 2024 | 48 | Escola | Escola | False | outro_texto: 1155; celula_vazia: 1 | escola |
| 2024 | 49 | Ativo/ Inativo | Ativo/ Inativo | False | outro_texto: 1156 | somente originais (sem equivalência presumida) |
| 2024 | 50 | Ativo/ Inativo | Ativo/ Inativo_1 | True | outro_texto: 1156 | somente originais (sem equivalência presumida) |

## Esquema derivado e interpretação

| Campos | Conteúdo e regra |
| --- | --- |
| ra, ra_status, ra_ano_duplicado | RA apenas com remoção de espaços nas extremidades; ausente, vazio, erro e duplicidade distintos. Nenhum vínculo pelo nome. |
| ano_referencia, arquivo_origem, aba_origem, linha_origem | Ano da aba PEDE; linha física no XLSX, não índice recalculado. |
| originais, hash_registro_origem | Todos os campos da mesma linha, com tipos e SHA-256 do registro serializado. Datas originais em ISO com tipo Python/Excel conservado. |
| fase_original, fase_extraida, fase_status | ALFA→0; inteiros 0–9; FASE n; Fase ideal n; códigos 1–8 seguidos de uma letra. Anotações finais entre parênteses não fornecem dígitos. Fracionários e formatos não previstos não são truncados. |
| fase_ideal_original, fase_ideal_extraida, fase_ideal_status | Mesma extração explícita; rótulo original integral preservado. |
| fase_equivalencia_curricular_status, fase_ideal_equivalencia_curricular_status | Extração do código não confirma currículo entre anos. Fase 9 sem significado documentado. |
| {ian,ida,ieg,iaa,ips,ipp,ipv,inde}_original | Valor original do indicador corrente; INDE 22 em 2023/2024 fica somente no bloco original. |
| {indicador}_numerico, {indicador}_status, {indicador}_motivo_indisponibilidade | Número finito, número em texto, célula vazia, texto vazio, espaços, erro Excel, INCLUIR, outro texto, data ou outro tipo. Indisponível=null, nunca zero. IPP sem coluna em 2022=ausencia_estrutural. |
| {indicador}_fora_faixa_operacional | Sinalização 0–10 nos oito indicadores, sem alterar extremos; null se não numérico. Não é regra documental universal. |
| defasagem_original, defasagem_numerico, defasagem_registrada, defasagem_status, defasagem_motivo_indisponibilidade | D da fonte; aliases Defas/Defasagem. |
| categoria_defasagem | D≥0 sem_defasagem; −2≤D<0 moderada; D<−2 severa. |
| ian_esperado, ian_divergente_defasagem | IAN 10/5/2,5 segundo D registrado; divergência null quando não comparável. |
| defasagem_calculada, defasagem_calculada_status, defasagem_divergente_calculada | Aritmética fase extraída menos ideal; comparação separada do IAN e sem confirmação curricular. |
| idade_original, idade_numerico, idade_status, idade_motivo_indisponibilidade | Datas no campo idade permanecem datas originais e recebem numérico null. Nenhuma idade inferida. |
| {nome,genero,ano_ingresso,ano_nascimento,data_nascimento,instituicao_ensino,escola,turma,pedra}_padronizado e _status | Texto NFKC, caixa baixa e espaços; Menina/Feminino, Menino/Masculino e Escola Pública/Pública harmonizados explicitamente. Nomes de instituições não são convertidos em categorias presumidas. |
| data_nascimento_padronizado | Datas Excel e ISO preservam semântica; texto dia/mês só convertido se existir uma única data possível. Datas ambíguas=null. |
| ano_nascimento_padronizado | Ano explícito ou extraído de data; ano pode ser inequívoco mesmo se dia/mês forem ambíguos. |
| flags_qualidade | Lista cumulativa de problemas por registro; não serve para excluir alunos automaticamente. Divergências entre anos ficam nos detalhes cadastrais por RA. |

O JSONL contém o registro completo. O CSV é uma visão plana dos campos derivados;
`flags_qualidade` é JSON dentro da célula e `originais` permanece apenas no JSONL.
Não se deve abrir o CSV e deixar um aplicativo reinterpretar RA, datas ou números antes da análise.
Não há fórmulas no XLSX atual. Se surgirem, são preservadas como fórmulas e
marcadas indisponíveis para cálculo automático; nenhum mecanismo recalcula a fonte.
