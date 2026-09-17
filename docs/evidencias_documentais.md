# Evidências documentais

A revisão documental foi realizada em 15/09/2026. Este registro é separado dos
relatórios regeneráveis e descreve as evidências examinadas, sem validação externa. Os hashes
dos arquivos constam de `docs/inventario_fontes.md` e dos metadados de execução.

## Métodos e limites

- Extração textual completa com pypdf para os três PDFs abaixo e python-docx para os 66 parágrafos do DOCX.
- Renderização dos PDFs com pypdfium2 (escala 1,6) e inspeção visual das páginas indicadas.
- DOCX: inspeção das dez imagens extraídas do pacote OOXML, vinculadas ao número do parágrafo em `word/document.xml`. Nenhuma tabela OOXML: as tabelas relevantes são imagens.
- A paginação renderizada do DOCX não foi verificada. Os localizadores abaixo são parágrafos e partes do pacote, não números de página presumidos.
- Intermediários ficam em `local_data/evidencias/`, ignorada pelo Git. Texto vazio em PDF não foi tratado como ausência de conteúdo.
- Materiais históricos foram inventariados e tiveram hashes conferidos; não foram incorporados à base nem foi necessária nova leitura substantiva de seus relatórios.

## Enunciado: POSTECH - Datathon - Fase 5 (1).pdf

**Leitura textual e visual integral: páginas 1–6.** Páginas 1 e 6 são capa/encerramento; páginas 2–5 contêm o desafio.

| Local | Evidência e consequência |
| --- | --- |
| p. 2 | Caso Passos Mágicos e análise dos anos 2022, 2023 e 2024. A rodada usa exclusivamente a planilha principal. |
| p. 3, perguntas 1–7 | Evolução da adequação/defasagem (IAN); desempenho por fases e anos (IDA); relação IEG com IDA/IPV; coerência IAA com IDA/IEG; antecedentes psicossociais (IPS); IPP versus IAN; comportamentos associados ao IPV. |
| p. 4, perguntas 8–11 | Combinações dos indicadores e INDE; modelo de probabilidade de risco de defasagem; evolução e efetividade; insights adicionais. A análise observacional futura não deve presumir identificação causal. |
| p. 4, entregas | GitHub com código, apresentação gerencial PPT/PDF e notebook Python com engenharia de atributos, treino/teste, modelagem e avaliação. |
| p. 5 | Aplicação Streamlit, deploy no Community Cloud e vídeo de até cinco minutos com ao menos uma pessoa do grupo. |

Esta etapa contemplou auditoria e preparação dos dados. Os demais entregáveis
permanecem no escopo final do projeto, sem execução nesta etapa.

## Dicionário Dados Datathon.pdf

**Leitura textual e visual integral: páginas 1–4.** Refere-se a um esquema histórico;
a introdução cita 2020/2021/2023, enquanto a lista contém campos até 2022. Não é
tratado como mapa exato de todas as colunas 2023/2024 da planilha principal.

| Local | Evidência e uso |
| --- | --- |
| p. 1, FASE_TURMA_2020 | Fase representa nível de aprendizado, turma subdivide uma fase. Dá contexto à extração do prefixo numérico, sem provar equivalência curricular dos códigos atuais. |
| pp. 2–3, TURMA_2021/TURMA_2022 | Exemplos como 1A, 1B e 1C. A regra implementada também é sustentada pelos formatos efetivamente observados em PEDE2024. |
| pp. 1–4, indicadores | INDE descrito como ponderação de IAN, IDA, IEG, IAA, IPS, IPP e IPV; definições gerais dos componentes. Não substitui a regra específica por fase do DOCX. |
| pp. 1–3, PEDRA | Quartzo 2,405–5,506; Ágata 5,506–6,868; Ametista 6,868–8,230; Topázio 8,230–9,294. Diferem da figura do DOCX, portanto nenhuma pedra foi recalculada. |

## PEDE_ Pontos importantes.docx

Texto integral lido (66 parágrafos), dez imagens vistas. As fórmulas e tabelas
listadas abaixo são evidências documentais; não implicam autorização para recalcular indicadores.

| Parágrafo / parte OOXML | Conteúdo visual ou textual | Uso/limitação |
| --- | --- | --- |
| §1, `word/media/image2.png` | Esquema das dimensões do INDE e indicadores, fases 0–7 e fase 8. | Aplicabilidade por fase precisa ser considerada em etapa futura. |
| §3, `word/media/image6.png`, Quadro 2 | IAN 10%; IDA 20% nas fases 0–7 e 40% na fase 8; IEG 20%; IAA 10%. | Não recalcular INDE nesta rodada. |
| §5, `word/media/image8.png`, Quadro 3 | IPS 10% nas fases 0–7 e 20% na fase 8; IPP 10% e IPV 20% nas fases 0–7; IPP/IPV N/A na fase 8. | Não converter automaticamente erros Excel observados em ausência estrutural por fase. |
| §§6–13 | D = fase efetiva − fase ideal; exemplo de linha 280 em 2024. | Sustenta o teste aritmético separado do teste de IAN. |
| §15, `word/media/image4.png`, Tabela 4 | Equivalência ano escolar/fase/idade, com população 2020/2021: Alfa 1º/2º ano e 7–8 anos; fase 1 3º/4º ano e 8–9 anos; fases 2–8 até universidade. | Rótulos atuais como ALFA (2º e 3º ano) e fase 1 (4º ano) não coincidem integralmente. Não reconstruir fase ideal por idade nem confirmar equivalência entre anos. Fase 9 não definida. |
| §23, `word/media/image1.png`, Tabela 41 | D≥0: IAN 10; 0>D≥−2: IAN 5; D<−2: IAN 2,5. | Regra documental aplicada ao D registrado. |
| §§25–30 | IDA apresentado como média de Matemática, Português e Inglês. | Não aplicado para recompor IDA; aplicabilidade de disciplinas e fase 8 exige análise posterior. |
| §§32–37 | IEG como média das pontuações de tarefas. | Sem faixa documental universal inferida apenas dessa fórmula. |
| §§39–43 | IAA e perguntas avaliadas de 0 a 10. | Evidência para sinalizar excessos; não autoriza arredondar registros. |
| §44, `word/media/image7.png`, Tabela 40 | Seis questões de autoavaliação, pesos por alternativas e faixas de fases; total nominal 10. | Valores da tabela têm arredondamentos impressos; a preparação preserva a precisão disponível no XLSX. |
| §45, `word/media/image9.png`, Figura 10 | Pictogramas das alternativas do questionário por fase. | Contexto da autoavaliação, sem transformação de dados. |
| §§47–59 | IPS/IPP como médias de avaliações e descrição longitudinal do IPV. | Não oferece, sozinho, limite universal confirmado para cada ano. |
| §64, `word/media/image10.png` | INDE = 0,1 IAN + 0,2 IDA + 0,2 IEG + 0,1 IAA + 0,1 IPS + 0,1 IPP + 0,2 IPV nas fases 0–7; fase 8 usa 0,1 IAN + 0,4 IDA + 0,2 IEG + 0,1 IAA + 0,2 IPS. | Fórmulas registradas como evidência, sem recomposição. |
| §65, `word/media/image5.png`, Figura 2 | Projeção normal e limites 6,110; 7,154; 8,198. | Não são limites universais de validade de todo INDE. |
| §66, `word/media/image3.png`, Figura 3 | Faixas de pedras com marcas 3,0; 6,1; 7,2; 8,2; 8,4; 9,4. | Diverge do dicionário; não aplicar novas pedras ou escolher uma regra por suposição. |

## desvendando_passos.pdf

Extração textual: **zero caracteres em todas as nove páginas**. Revisão visual
integral realizada: p. 1 capa; p. 2 princípios de admissão; p. 3 inscrição;
p. 4 prova de sondagem; p. 5 entrevistas; p. 6 consenso psicopedagógico sobre
nível de adequação; p. 7 avaliação socioeconômica; p. 8 matrícula; p. 9 encerramento.
O material descreve o processo de entrada e acompanhamento. Não fornece o significado
da fase 9, de INCLUIR ou faixas numéricas dos oito indicadores.

## Convenções técnicas desta implementação

Foram adotadas as seguintes convenções técnicas de processamento:

- ALFA→0 e extração conservadora dos códigos observados; equivalência curricular fica separada.
- Menina/Feminino, Menino/Masculino e Escola Pública/Pública são equivalências textuais explícitas. Instituições nomeadas não são convertidas em categorias de rede presumidas.
- Datas Excel mantêm a data armazenada; texto ambíguo dia/mês recebe status próprio. Nenhuma data é corrigida pelo cadastro de outro ano.
- Faixa operacional 0–10 em IAN, IDA, IEG, IAA, IPS, IPP, IPV e INDE. Qualquer excesso é contado com precisão original, sem corte ou arredondamento.
- IPP sem coluna em 2022 é ausência estrutural. Os erros observados em 2023/2024 conservam seu tipo e motivo, sem inferência de causa.
