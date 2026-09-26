# Identidade visual — Associação Passos Mágicos

Registro da revisão de identidade visual de 25/09/2026. Não altera cálculos,
agregações, o modelo, o limiar ou qualquer artefato congelado — cobre apenas
aparência (logo, paleta, tipografia, layout, modos claro/escuro).

## Logo

Arquivo oficial baixado de
`https://passosmagicos.org.br/wp-content/uploads/2020/10/Passos-magicos-icon-cor.png`
e salvo localmente em `assets/brand/passos-magicos-icon-cor.png` (ver
`assets/brand/ORIGEM.md` para a proveniência completa). Nenhum hotlink em
tempo de execução; nenhuma alteração do conteúdo do arquivo.

## Paleta

| Papel | Claro | Escuro | Fonte |
| --- | --- | --- | --- |
| Fundo | `#faf8f4` | `#12211f` | Escolha de produto (fundo claro aquecido / grafite verde-azulado, nunca preto absoluto) |
| Fundo elevado (cartão/expander) | `#ffffff` | `#16302c` | Escolha de produto |
| Texto principal | `#22282c` | `#eef2f0` | Escolha de produto (alto contraste) |
| Texto secundário | `#5a6268` | `#aab5b2` | Escolha de produto |
| Azul institucional | `#145089` | `#5b9bd8` | **Extraído do logo oficial** (cor dominante do texto "Passos Mágicos"; confirmado também na folha de estilos pública do site oficial) |
| Azul secundário (links) | `#0367b0` | `#7fb8e8` | **Extraído do logo oficial** |
| Verde institucional | `#1e7a4f` | `#4caf7d` | Escolha de produto — não encontrado no ícone isolado nem como cor de marca recorrente na folha de estilos pública consultada; adicionado para compor a paleta pedagógica pedida (azul + verde como cores principais), harmonizado com o azul do logo |
| Amarelo (destaque moderado) | `#e8a400` | `#f0c33c` | Aproximado da família de amarelos/dourados confirmada na folha de estilos pública do site oficial (`#ffe01f`, `#fbba00`, `#fec52b`), ajustado para contraste adequado |
| Vermelho (detalhes/atenção) | `#b23b3b` | `#e07a7a` | Aproximado do vermelho confirmado na folha de estilos pública do site oficial (`#ed3237`), suavizado — uso restrito a pequenos detalhes, nunca como cor de fundo ampla |
| Borda | `#e2ddd4` | `#2a423d` | Escolha de produto |

Contraste (WCAG) verificado por cálculo direto de luminância relativa antes
da implementação: todos os pares texto/fundo acima ficam ≥ 5:1 (a maioria
acima de 7:1, nível AAA para texto normal), exceto o amarelo, que por
desenho nunca é usado como cor de texto — só como destaque discreto (borda,
sublinhado, pequeno realce), nunca como superfície ampla nem como texto
sobre fundo claro.

A paleta categórica dos 11 gráficos Plotly (`src/graficos_publicos.py:CATEGORICAL`,
já validada pela skill `dataviz` numa revisão anterior) **não foi alterada** —
só o fundo/grade/texto dos gráficos passam a acompanhar o modo claro/escuro
selecionado (`graficos_publicos.aplicar_tema`).

## Modos claro e escuro

O tema nativo do Streamlit (`.streamlit/config.toml`) é estático e serve de
base para o modo "Claro". O alternador "Claro/Escuro" da interface (`st.
segmented_control`, componente nativo, sem JavaScript) grava a escolha em
`st.session_state["tema_aparencia"]`; a cada execução do script,
`streamlit_app.py:_aplicar_estilo_visual()` injeta um pequeno bloco `:root {
--pm-*: ...; }` com os valores da tabela acima para o modo atual, seguido do
CSS estático de `assets/styles/app.css` (que só referencia essas variáveis,
nunca cores fixas nas regras de tema). A preferência dura apenas a sessão —
não é persistida em cookie, banco ou armazenamento local.

O logo tem fundo transparente; no modo escuro, é exibido sobre uma pequena
superfície clara discreta (`--pm-logo-fundo`) para preservar a legibilidade
das silhuetas escuras — o arquivo em si nunca é alterado.
