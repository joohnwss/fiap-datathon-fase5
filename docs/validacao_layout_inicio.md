# Validação da página inicial e do layout geral

Data da validação: 23 de setembro de 2026.

## Arquitetura aplicada

- `streamlit_app.py`: composição visual e navegação com componentes nativos do
  Streamlit. A primeira chamada Streamlit é `st.set_page_config`, com título
  público, ícone 🎓 e `layout="wide"`.
- `src/textos_aplicacao.py`: conteúdo editorial da página inicial, incluindo
  abertura, contexto, questão central, objetivo, entregas, percurso de
  navegação, equipe e aviso ético. O módulo não contém lógica de inferência.
- `src/inferencia.py`: permaneceu como camada exclusiva de carregamento,
  validação e inferência do modelo oficial.
- `tests/test_streamlit_app.py`: regressões da configuração, conteúdo público,
  ordem da navegação, equipe, privacidade, ausência de métricas técnicas na
  abertura e preservação dos sete preditores.

Não foram adicionados JavaScript, HTML inseguro, CSS externo nem larguras fixas
em pixels ao código da aplicação.

## Uso da largura por área

| Área | Organização responsiva |
|---|---|
| Início | Hero em proporção 2:1; contexto e objetivo lado a lado; quatro entregas em grade 2×2; cinco passos em linhas de até dois cards; equipe em 3+2 cards. Em telas estreitas, a ordem lógica é preservada no empilhamento. |
| Panorama e resultados | Índice e seletor ocupam a largura útil; no cartão analítico, gráfico e interpretação usam proporção 3:2; significado/ação e limitações/escopo usam pares de colunas. |
| Avaliar um caso | Campos mantidos na ordem oficial em grupos 2, 2 e 3; o Streamlit empilha os controles em telas estreitas. |
| Plano de acompanhamento | Cards em duas colunas, com empilhamento nativo no celular. |
| Entenda os indicadores | Indicadores distribuídos em duas colunas de expansores. |
| Modelo e limitações | Leitura das métricas e explicação metodológica em duas colunas; detalhes técnicos permanecem recolhidos. |

## Validação em Chrome real

O aplicativo local foi aberto em uma nova instância Streamlit e exercitado pelo
Chrome em modo headless por meio do protocolo de depuração do próprio navegador.
A página carregou sem exceções e o endpoint `/_stcore/health` respondeu `ok`.

| Largura | Resultado |
|---:|---|
| 1920 px | Sem overflow horizontal; seis abas visíveis; título principal e hero legíveis; Home completa registrada. |
| 1440 px | Sem overflow horizontal; seis abas visíveis; cards, equipe, Panorama e formulário conferidos. |
| 768 px | Sem overflow horizontal da página; seis abas alcançáveis na barra nativa; conteúdo reorganizado sem corte. |
| 390 px | Sem overflow horizontal da página; cards e formulário empilhados; passos mantidos na ordem 1→5; abas adicionais acessíveis pela navegação horizontal nativa do Streamlit. |

Medições estruturadas: `reports/validacao_layout/validacao_layout.json`.

## Evidências visuais

- `reports/validacao_layout/home_desktop_completa_1920.png`
- `reports/validacao_layout/home_cabecalho_cards_1440.png`
- `reports/validacao_layout/equipe_desktop_1440.png`
- `reports/validacao_layout/home_mobile_390.png`
- `reports/validacao_layout/panorama_desktop_1440.png`
- `reports/validacao_layout/formulario_desktop_1440.png`
- `reports/validacao_layout/formulario_mobile_390.png`

## Verificações automatizadas

Suíte integral atual: **295/295 testes aprovados**, sem falhas, erros ou skips,
em 134,750 s. Os testes específicos cobrem:

1. configuração `wide` exata e como primeira chamada Streamlit;
2. título, subtítulo, introdução, contexto, questão central e objetivo;
3. quatro entregas e cinco passos de navegação na ordem correta;
4. cinco nomes da equipe, sem e-mails, cargos ou ferramentas;
5. aviso ético e proteção de privacidade;
6. seis abas e conteúdo público sem referência a assistentes ou ferramentas;
7. ausência de métricas técnicas na abertura;
8. ausência de HTML inseguro e de larguras fixas;
9. preservação da ordem dos sete preditores e da inferência oficial.

## Navegação entre as 11 perguntas

O índice global continua visível e numerado antes da análise. Logo após o
índice, um container destacado apresenta título, orientação, pergunta atual,
capítulo, seletor direto com exatamente 11 opções e botões anterior/seguinte.
O estado é único (`panorama_pergunta`), portanto seletor, contador, capítulo,
resposta, tabela e gráfico permanecem sincronizados em cada rerun.

- Pergunta 1: botão anterior desabilitado.
- Pergunta 11: botão seguinte desabilitado.
- Não há navegação circular.
- O cartão analítico é numerado pela pergunta selecionada (`Pergunta 1`,
  `Pergunta 2`, …); seus subtítulos não recebem uma segunda numeração.
- Testes da aplicação: **105/105 aprovados**.
- Chrome em 1.440 px: botões laterais visíveis, seletor em largura útil e
  contador destacado; clique real alterou a pergunta 1 para a 2.
- Chrome em 390 px: controles empilhados, botões com 326 px úteis, nenhum texto
  cortado e nenhum overflow horizontal.

Evidências adicionais:

- `reports/validacao_layout/navegacao_perguntas_1440.png`
- `reports/validacao_layout/navegacao_pergunta_2_1440.png`
- `reports/validacao_layout/navegacao_perguntas_390.png`
- `reports/validacao_layout/validacao_navegacao_perguntas.json`

Nenhuma operação Git de preparação, commit, push, merge ou tag foi executada, e
nenhum deploy foi realizado.
