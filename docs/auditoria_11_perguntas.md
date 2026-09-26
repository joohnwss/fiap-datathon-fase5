# Auditoria das 11 perguntas de negócio

Data da auditoria: 23/09/2026. Esta matriz registra o estado encontrado antes
da reconstrução da navegação e dos cartões. A existência de uma figura não foi
considerada suficiente para classificar uma resposta como completa.

## Matriz de auditoria do estado anterior

| Nº | Pergunta oficial | Capítulo | Dados usados | Chaves JSON | Gráfico | Resposta atual | Situação |
|---|---|---|---|---|---|---|---|
| 1 | Qual é o perfil de defasagem e como evolui? | Trajetória e defasagem | Categorias de defasagem, sinal de D, IAN e regra de privacidade por ano | `analises.anuais.<ano>.categorias`, `.sinal_d`, `.ian_distribuicao`; `privacidade` | `reports/figures/01_defasagem.png` | Percentuais de 2022/2023; 2024 descrito apenas como “omitido por privacidade”, sem contagens, denominadores ou regra objetiva no cartão. | PARCIALMENTE RESPONDIDA |
| 2 | O IDA melhora, permanece estável ou cai entre fases e anos? | Aprendizagem e engajamento | Estatísticas anuais, por fase e mudanças nos pares longitudinais | `analises.anuais.<ano>.indicadores.ida`, `analises.ida_fase`, `analises.longitudinal.<transição>.mudancas.ida` | `reports/figures/02_ida.png` | Médias anuais e direção geral, sem tabela de cobertura/denominadores nem separação explícita entre corte anual e pares. | PARCIALMENTE RESPONDIDA |
| 3 | Qual a associação de IEG com IDA e IPV? | Aprendizagem e engajamento | Correlações anuais e ajustadas por ano | `analises.associacoes.<ano>.ieg x ida`, `.ieg x ipv`, `analises.associacoes.ajustado_ano` | `reports/figures/03_associacoes.png` | Direção e intensidade, sem tabela com n nem instrução de leitura do gráfico. | PARCIALMENTE RESPONDIDA |
| 4 | A autoavaliação IAA é coerente com IDA e IEG? | Dimensões psicossociais e psicopedagógicas | Correlações e diferenças assinadas de IAA | `analises.associacoes.<ano>.iaa x ida`, `.iaa x ieg`, `analises.autoavaliacao` | `reports/figures/03_associacoes.png` | Conclusão de associação fraca, mas sem números principais em tabela e com gráfico compartilhado pouco explicado. | PARCIALMENTE RESPONDIDA |
| 5 | Existem padrões de IPS que antecedem quedas futuras de IDA ou IEG? | Dimensões psicossociais e psicopedagógicas | IPS na origem, deltas futuros, sensibilidades e perfis | `analises.longitudinal.<transição>.ips.<ida\|ieg>` | `reports/figures/04_ips.png` | Conclusão para IDA em destaque; faltavam os quatro resultados, n e pares ausentes em uma tabela legível. | PARCIALMENTE RESPONDIDA |
| 6 | IPP confirma ou contradiz a defasagem identificada por IAN? | Dimensões psicossociais e psicopedagógicas | Correlações IPP×IAN/IPP×D e perfis por mediana | `analises.ipp.<ano>` | `reports/figures/05_ipp.png` | Correlações principais sem denominadores, cobertura ou orientação explícita de leitura. | PARCIALMENTE RESPONDIDA |
| 7 | Quais indicadores estão mais associados ao IPV? | Indicadores globais, risco e prioridades | Correlações contemporâneas e futuras com IPV | `analises.ipv.<ano>.associacoes`, `.por_fase`; `analises.longitudinal.<transição>.ipv_futuro` | `reports/figures/06_ipv.png` | Indicador líder por ano, sem tabela de n; seleção no código não usava explicitamente valor absoluto. | PARCIALMENTE RESPONDIDA |
| 8 | Quais combinações de IDA, IEG, IPS e IPP se associam a maior INDE? | Indicadores globais, risco e prioridades | Perfis completos, medianas e INDE médio | `analises.inde.<ano>` | `reports/figures/07_inde.png` | A resposta da interface saltava 2023, embora o artefato oficial contenha o ano. | PARCIALMENTE RESPONDIDA |
| 9 | Como o modelo avaliado apoia a previsão de risco? | Indicadores globais, risco e prioridades | Métricas OOF, temporais, diferenças e matriz de confusão | `modelo.oof`, `modelo.temporal`, `modelo.diferencas`, `modelo.limiar` | `reports/figures/09_modelo.png` | Queda de recall informada, sem tabela conjunta de n, eventos, precisão, recall, F1 e Brier. | PARCIALMENTE RESPONDIDA |
| 10 | O que os indicadores mostram sobre evolução nas Pedras? | Trajetória e defasagem | Distribuição anual, transições e evolução de Pedra | `analises.pedras.<ano>`, `analises.longitudinal.<transição>.pedras_evolucao`, `.pedras_transicoes` | `reports/figures/08_pedras.png` | Percentuais de melhora/piora sem contagens, denominadores e estabilidade no cartão. | PARCIALMENTE RESPONDIDA |
| 11 | Quais insights adicionais orientam coleta e monitoramento? | Trajetória e defasagem | Perdas, perfis, cobertura, deslocamento entre coortes e heterogeneidade por fase | `analises.perdas`, `modelo.distribuicao.numericos`, `analises.ida_fase` | `reports/figures/10_insights.png` | Exibia apenas perdas de correspondência; não sintetizava os demais insights oficiais da pergunta. | PARCIALMENTE RESPONDIDA |

## Prova do conjunto oficial

As perguntas aparecem integralmente nas seções `## 1` a `## 11` de
`reports/relatorio_analises_negocio.md` (linhas 11, 82, 151, 178, 212, 296,
341, 416, 489, 534 e 692 na versão auditada). O JSON confirma exatamente as
chaves `"1"` a `"11"` em `reports/metricas_analises_negocio.json.perguntas`.

1. Qual é o perfil de defasagem e como evolui?
2. O IDA melhora, permanece estável ou cai entre fases e anos?
3. Qual a associação de IEG com IDA e IPV?
4. A autoavaliação IAA é coerente com IDA e IEG?
5. Existem padrões de IPS que antecedem quedas futuras de IDA ou IEG?
6. IPP confirma ou contradiz a defasagem identificada por IAN?
7. Quais indicadores estão mais associados ao IPV?
8. Quais combinações de IDA, IEG, IPS e IPP se associam a maior INDE?
9. Como o modelo avaliado apoia a previsão de risco?
10. O que os indicadores mostram sobre evolução nas Pedras?
11. Quais insights adicionais orientam coleta e monitoramento?

Cada item corresponde, na mesma ordem, a `_q1`…`_q11` em
`src/textos_aplicacao.py`. Os gráficos são os dez arquivos listados na matriz;
Q3 e Q4 compartilham `03_associacoes.png`. Na interface reconstruída, todos
usam o mesmo componente de cartão em `_tab_panorama_e_resultados`, escolhido
diretamente pelo seletor global `panorama_pergunta`.

## Capítulos e diagnóstico de navegação

- Trajetória e defasagem — 3 perguntas: 1, 10 e 11.
- Aprendizagem e engajamento — 2 perguntas: 2 e 3.
- Dimensões psicossociais e psicopedagógicas — 3 perguntas: 4, 5 e 6.
- Indicadores globais, risco e prioridades — 3 perguntas: 7, 8 e 9.

O código anterior não impunha um limite técnico de sete perguntas. O defeito
era de descoberta: o usuário precisava escolher um capítulo primeiro, cada
capítulo oferecia somente duas ou três opções e apenas um cartão era renderizado
por vez. Não havia lista global nem indicação visível do conjunto completo;
portanto, enxergar sete era um resultado plausível do percurso feito pelo
usuário, não evidência de que as outras quatro estivessem ausentes do código.

## Auditoria específica de 2024 na pergunta 1

O artefato registra 1.156 observações anuais, cobertura completa do IAN e a
regra `privacidade.minimo_perfil = 10` com supressão integral da partição quando
qualquer célula não vazia fica abaixo desse mínimo. Em 2024, tanto
`categorias.status` quanto `ian_distribuicao.status` registram a ativação dessa
regra. A reconstrução mantém a supressão e explica o critério sem publicar a
contagem protegida. A comparação categórica 2022–2024, portanto, não é válida;
o total e as estatísticas globais de 2024 não substituem a distribuição por
categoria.

Há risco de divulgação por diferença quando estatísticas derivadas da mesma
partição são combinadas. Por isso, uma futura regeneração dos artefatos deve
revisar em conjunto as margens publicadas, e não apenas o texto da interface.
