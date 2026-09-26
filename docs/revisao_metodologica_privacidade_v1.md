# Revisão metodológica e de privacidade — camada pública v1

## Escopo

Esta revisão cria uma camada pública independente para responder literalmente
às 11 perguntas do PDF do Datathon. Os artefatos históricos permanecem
intactos nesta rodada, mas não são consumidos pela aplicação nem pelo notebook
público.

## Regra de privacidade

O mínimo de dez registros é uma política metodológica criada pelo projeto; não
é uma exigência do enunciado nem foi localizada nos documentos da Passos
Mágicos. A publicação adota:

- supressão primária de células não vazias abaixo de dez;
- supressão integral da partição quando uma célula é pequena;
- supressão complementar de médias, margens, totais e relações determinísticas
  capazes de reconstruir uma célula protegida;
- revisão conjunta de JSON, relatório, figuras, notebook, aplicação e testes.

Na pergunta 1, 2024 é publicado em dois grupos: `sem defasagem` e
`com defasagem (moderada + severa)`. Ambos superam o mínimo adotado. A camada
pública não contém a decomposição do segundo grupo, a média anual do IAN ou
relações determinísticas que permitam reconstruir as duas categorias originais.

## Decisões metodológicas

- Q1 não interpreta comparação entre anos como evolução intranual.
- Q6 não transforma quadrantes por mediana em confirmação diagnóstica.
- Q7 separa associação contemporânea de associação com IPV futuro.
- Q8 explicita a circularidade entre indicadores e INDE.
- Q9 preserva modelo e limiar, distinguindo desenvolvimento com predições OOF
  de teste temporal.
- Q10 mantém a redação oficial, mas distingue Pedra de fase escolar e evolução
  observada de impacto causal.
- Q11 relaciona cada sugestão a evidência, público, ação, prioridade e limite.

## Arquitetura

O pacote público é composto por:

- `reports/public/perguntas_oficiais_v1.json`;
- `reports/public/relatorio_perguntas_oficiais_v1.md`;
- `reports/public/manifesto_integridade_v1.json`;
- onze figuras em `reports/public/figures/`;
- `src/analises_publicas.py`, gerador autocontido;
- notebook e aplicação configurados para consumir somente essa camada.

O gerador público usa somente agregados aprovados incorporados em seu contrato.
Não abre `DATATHON/`, `local_data/`, `local_recovery/` ou arquivos históricos.

## Proveniência dos resultados publicados

| Pergunta | Origem metodológica do agregado aprovado |
|---|---|
| Q1 | Distribuição anual detalhada em 2022–2023; em 2024, dois grupos publicáveis, com moderada e severa agregadas. |
| Q2 | Médias anuais, médias por fase e deltas dos pares longitudinais de IDA. |
| Q3 | Correlações de Spearman IEG×IDA e IEG×IPV, anuais e ajustadas por ano. |
| Q4 | Correlações de Spearman IAA×IDA e IAA×IEG. |
| Q5 | Associação temporal entre IPS na origem e variações futuras de IDA/IEG. |
| Q6 | Cobertura, ausências, IPP×IAN, IPP×defasagem e médias contínuas de IPP por categoria publicável. |
| Q7 | Associações contemporâneas com IPV e associações dos indicadores de origem com IPV futuro. |
| Q8 | Perfis completos publicáveis de IDA, IEG, IPS e IPP e respectiva média de INDE, com ressalva de circularidade. |
| Q9 | Artefato congelado do modelo: desenvolvimento OOF, teste temporal, limiar e matriz de erros. |
| Q10 | Transições agregadas de Pedra e variações observadas de indicadores nos pares longitudinais. |
| Q11 | Síntese das evidências sanitizadas das perguntas anteriores, organizada por público, ação, prioridade e limitação. |

Os números foram transcritos para o contrato autocontido do gerador depois da
revisão conjunta de privacidade. Assim, a regeneração pública é determinística
e não precisa abrir o artefato histórico que lhes deu origem.

## Esquema do JSON público

No nível raiz: `schema_version`, `camada`, `titulo`, `perguntas_oficiais`,
`topicos_secundarios`, `privacidade`, `resumo_executivo`, `perguntas`,
`modelo_congelado` e `dependencias_proibidas_em_execucao`.

Cada item de `perguntas` contém: `numero`, `topico`, `pergunta`, `status`,
`resposta`, `principais_numeros`, `nota_numeros`, `grafico`,
`como_interpretar`, `observamos`, `significado`, `uso_ong`, `limites`,
`populacao_periodo` e `fonte_exata`.

## Limite desta rodada

Os artefatos históricos rastreados ainda existem na árvore do repositório e no
histórico remoto. Portanto, a criação desta camada não encerra a remediação do
repositório público. A retirada ou substituição dos arquivos históricos será
objeto da próxima revisão autorizada.

## Auditoria de divulgação conjunta (24/09/2026)

Uma auditoria comparativa independente recomendou, entre outros pontos,
confirmar formalmente que nenhuma combinação de números publicados nas 11
perguntas permite reconstruir uma célula suprimida. Duas células estão
suprimidas hoje: a divisão exata do grupo "com defasagem" de 2024 entre
moderada e severa (Q1, 534 registros) e a distribuição de IPP por categoria de
defasagem em 2024 (Q6).

Para cada uma, a soma total publicada (ex.: moderada + severa = 534) é uma
única equação com duas incógnitas — não tem solução única sozinha. A
reconstrução exigiria uma SEGUNDA equação independente (por exemplo, uma
média do IAN referente a 2024, ou uma média de IPP por categoria referente a
2024) publicada em qualquer lugar do documento. Uma varredura de todo o texto
publicado (as 11 perguntas, o relatório e o manifesto) confirmou que nenhum
termo desse tipo existe: nem `ian_distribuicao`, `sinal_d`, média/soma/total
do IAN de 2024 em nenhuma pergunta, nem uma média de IPP por categoria
referente a 2024 em nenhuma pergunta além da própria Q6 (onde a linha
permanece com todos os campos numéricos nulos). Ambas as células continuam
seguras. Verificação automatizada e permanente em
`test_auditoria_de_divulgacao_conjunta_entre_perguntas`
(`tests/test_privacidade_publicacao.py`).
