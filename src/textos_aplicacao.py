"""Conteúdo textual e editorial da aplicação pública.

Módulo exclusivamente de apresentação: nenhuma lógica de inferência, nenhum
dado privado, nenhuma dependência de `streamlit`. `streamlit_app.py` é a
única camada que conhece a interface; `src/inferencia.py` é a única camada
que conhece o modelo; este módulo só conhece texto.

Fontes documentais usadas para cada definição (nenhum significado, faixa,
unidade ou interpretação foi inventado):

- `DATATHON/Dicionário Dados Datathon.pdf` (p. 1–2, seção "Métricas e
  Conceitos") — nome por extenso e definição geral de IDA, IEG, IAA, IPS,
  IPV e IAN; explicação de Fase/Turma. Hash conferido em
  `docs/inventario_fontes.md`.
- `docs/evidencias_documentais.md` — leitura integral do dicionário oficial
  e do documento "PEDE_ Pontos importantes.docx"; regra do IAN por
  defasagem (D≥0→10; −2≤D<0→5; D<−2→2,5); faixa operacional 0–10 dos
  indicadores; fórmula D = fase efetiva − fase ideal.
- `docs/mapa_campos.md` — convenção ALFA→0 e categorização de defasagem
  (D≥0 sem defasagem; −2≤D<0 moderada; D<−2 severa).
- `docs/contrato_metodologico.md` — lista fechada dos sete preditores
  aprovados e o compromisso de não afirmar causalidade.
- `docs/decisao_modelo_operacional.md` (seção do contrato de sete
  preditores) — tipo, obrigatoriedade, domínio e tratamento de ausência de
  cada campo; confirmação de que a faixa 0–10 é descritiva, não um limite
  imposto pelo pipeline.
- `reports/metricas_analises_negocio.json` — respostas numéricas às 11
  perguntas de negócio (painel "Panorama e resultados"), lidas em tempo de
  execução; nenhum número duplicado como literal neste módulo.
- `DATATHON/Relatorio PEDE2022.pdf` — usado apenas como fonte conceitual
  (nunca lido em tempo de execução pela aplicação): tabela de equivalência
  idade/fase (p. física 39, numeração impressa 23), metodologia do IAN por
  defasagem (p. física 145, impressa 129), comparação do IAN (p. física 148,
  impressa 132), IPS (p. física 175, impressa 159), Ponto de Virada (p.
  física 189, impressa 173). A ausência de menção a "Ponto de Virada" e a
  "vulnerabilidades" nas páginas revisadas em auditoria anterior foi
  limitação de extração textual (a maior parte do PDF é imagem), não
  ausência de conteúdo no documento — os conceitos existem no relatório e
  são usados aqui apenas de forma conceitual, sem números 2020–2022.
- Métricas de desempenho (precisão, recall, AP, ROC-AUC, Brier, matriz de
  confusão, calibração, limiar): lidas em tempo de execução dos artefatos
  oficiais (`artifacts/schema_modelo.json`, `artifacts/avaliacao_temporal.json`,
  `reports/metricas_modelagem.json`, `artifacts/configuracao_congelada.json`)
  por `streamlit_app.py`, nunca duplicadas manualmente neste módulo.
"""
from __future__ import annotations

FONTES_DOCUMENTAIS: tuple[str, ...] = (
    "Dicionário de Dados do Datathon (Associação Passos Mágicos), fornecido com o desafio",
    "docs/evidencias_documentais.md",
    "docs/mapa_campos.md",
    "docs/contrato_metodologico.md",
    "docs/decisao_modelo_operacional.md",
)

# ---------------------------------------------------------------------------
# Dicionário dos sete indicadores oficiais (usado no formulário e na página
# "Entenda os indicadores"). Cada entrada é fiel às fontes documentais acima;
# nenhuma faixa, unidade ou interpretação foi adicionada além do que consta
# nelas.
# ---------------------------------------------------------------------------

INDICADORES: dict[str, dict[str, str]] = {
    "ida": {
        "sigla": "IDA",
        "nome_extenso": "Indicador de Aprendizagem",
        "definicao": (
            "Reflete o desempenho acadêmico do(a) estudante, pela média das notas "
            "do indicador de aprendizagem registradas na avaliação PEDE da Associação "
            "Passos Mágicos."
        ),
        "o_que_informar": "O valor do indicador tal como registrado na base oficial mais recente.",
        "ausencia": "Campo obrigatório para concluir a ficha.",
        "exemplo": "6.5",
        "ressalva": "Um valor mais baixo não indica, isoladamente, causa de nenhum resultado.",
    },
    "ieg": {
        "sigla": "IEG",
        "nome_extenso": "Indicador de Engajamento",
        "definicao": "Reflete o engajamento do(a) estudante, pela média das notas de engajamento registradas na avaliação PEDE.",
        "o_que_informar": "O valor do indicador tal como registrado na base oficial mais recente.",
        "ausencia": "Campo obrigatório para concluir a ficha.",
        "exemplo": "8.0",
        "ressalva": "Um valor mais baixo não indica, isoladamente, causa de nenhum resultado.",
    },
    "iaa": {
        "sigla": "IAA",
        "nome_extenso": "Indicador de Autoavaliação",
        "definicao": "Reflete a autoavaliação do(a) estudante, pela média das notas de autoavaliação registradas na avaliação PEDE.",
        "o_que_informar": "O valor do indicador tal como registrado na base oficial mais recente.",
        "ausencia": "Campo obrigatório para concluir a ficha.",
        "exemplo": "7.0",
        "ressalva": "Um valor mais baixo não indica, isoladamente, causa de nenhum resultado.",
    },
    "ips": {
        "sigla": "IPS",
        "nome_extenso": "Indicador Psicossocial",
        "definicao": "Reflete o contexto psicossocial do(a) estudante, pela média das notas psicossociais registradas na avaliação PEDE.",
        "o_que_informar": "O valor do indicador tal como registrado na base oficial mais recente.",
        "ausencia": "Campo obrigatório para concluir a ficha.",
        "exemplo": "5.0",
        "ressalva": "Um valor mais baixo não indica, isoladamente, causa de nenhum resultado.",
    },
    "ipv": {
        "sigla": "IPV",
        "nome_extenso": "Ponto de Virada institucional",
        "definicao": (
            "Descreve uma análise longitudinal da evolução do(a) estudante ao longo "
            "do tempo — não é uma média de notas nem é calculado por esta ficha."
        ),
        "o_que_informar": "Consulte o IPV no cadastro ou na planilha institucional do estudante.",
        "ausencia": "Campo obrigatório para concluir a ficha.",
        "exemplo": "7.5",
        "ressalva": "Um valor mais baixo não indica, isoladamente, causa de nenhum resultado.",
    },
    "fase_origem": {
        "sigla": "Fase de origem",
        "nome_extenso": "Fase educacional de origem",
        "definicao": (
            "A fase está relacionada ao nível de aprendizado do(a) estudante na "
            "Associação Passos Mágicos (a turma, por sua vez, é a divisão de alunos "
            "dentro de uma mesma fase — este campo não pede a turma)."
        ),
        "o_que_informar": "A fase registrada no ano de origem da observação, de 0 a 7 (a codificação oficial usa \"0\" para a fase inicial, correspondente à alfabetização).",
        "ausencia": "Campo obrigatório — não pode ficar em branco.",
        "exemplo": "2",
        "ressalva": "É um dado de contexto escolar, não uma medida de desempenho isolada.",
    },
    "defasagem_origem": {
        "sigla": "Defasagem de origem",
        "nome_extenso": "Defasagem escolar registrada na origem",
        "definicao": (
            "A diferença entre a fase efetiva e a fase considerada ideal para "
            "o(a) estudante no ano de origem (fase efetiva menos fase ideal). "
            "Valores negativos indicam que a fase efetiva ficou abaixo da fase ideal."
        ),
        "o_que_informar": "O valor de defasagem registrado no ano de origem (pode ser negativo, zero ou positivo).",
        "ausencia": "Campo obrigatório para concluir a ficha.",
        "exemplo": "0",
        "ressalva": "Descreve a situação registrada, não uma previsão nem uma falha do(a) estudante.",
    },
}

CAMPOS_NUMERICOS: tuple[str, ...] = ("ida", "ieg", "iaa", "ips", "ipv")
CAMPO_FASE = "fase_origem"
CAMPO_DEFASAGEM = "defasagem_origem"

EXPLICACAO_DEFASAGEM = (
    "**O que é \"defasagem\" neste projeto?** É a diferença entre a fase em que "
    "o(a) estudante efetivamente está e a fase considerada ideal para a idade/série "
    "(fase efetiva menos fase ideal). Um valor igual a zero ou positivo indica que "
    "não há defasagem; valores negativos indicam que a fase efetiva está abaixo da "
    "ideal. Esta aplicação estima a **probabilidade de entrada em defasagem no ano "
    "seguinte**, ou seja, de um(a) estudante sem defasagem na origem passar a "
    "apresentar defasagem."
)

# ---------------------------------------------------------------------------
# "Avaliar um caso" — identificação e contexto do caso (revisão editorial,
# 25/09/2026, Parte 4). Identificação, idade e sexo nunca são enviados ao
# modelo; servem apenas para organizar o relatório.
# ---------------------------------------------------------------------------

ROTULO_IDENTIFICACAO_CASO = "Nome ou identificação interna *"
AVISO_IDENTIFICACAO_OPCIONAL = (
    "Use nome, iniciais ou código interno apenas para organizar esta ficha e o "
    "relatório durante a sessão. A identificação não é enviada ao modelo nem "
    "persistida pela aplicação. Não informe CPF, RA, e-mail, telefone ou endereço."
)
AVISO_CONTEXTO_NAO_ALTERA_ESTIMATIVA = (
    "A identificação e o sexo organizam a ficha e o relatório e não entram no "
    "modelo. A idade orienta a sugestão de fase ideal; depois da confirmação humana, "
    "as fases determinam a defasagem usada pelo modelo."
)
AVISO_IDADE_NAO_AUTOMATIZA_CALCULO = (
    "A idade sugere a fase ideal pela tabela documental, mas nunca substitui uma "
    "escolha humana. Confirme a fase ideal antes de calcular a defasagem."
)
# Texto único e discreto — aparece como legenda no formulário de "Avaliar
# um caso" e, de forma resumida, no rodapé da aplicação
# (`RODAPE_APLICACAO`), no lugar de dois avisos maiores e mais verbosos.
AVISO_PRIVACIDADE_AVALIAR = (
    "A identificação pode ser um nome, iniciais ou código interno e é usada somente "
    "para organizar a ficha e o relatório durante a sessão. Ela não é enviada ao "
    "modelo nem persistida pela aplicação. Caso o relatório seja "
    "baixado, o arquivo permanecerá no dispositivo do usuário."
)
AVISO_USO_RESPONSAVEL_CURTO = (
    "O resultado apoia o acompanhamento educacional e não representa diagnóstico "
    "nem decisão automática."
)

ROTULO_IDADE_CONTEXTO = "Idade em anos completos *"
AJUDA_IDADE_CONTEXTO = (
    "Usada para sugerir a fase ideal pela tabela documental. Não é enviada "
    "diretamente ao modelo e nunca substitui a confirmação do usuário."
)

SEXO_OPCOES: tuple[str, ...] = ("Selecione", "Feminino", "Masculino")

# ---------------------------------------------------------------------------
# "Avaliar um caso" — calculadoras de indicadores (revisão editorial,
# 25/09/2026, Partes 2–3). Ver docs/auditoria_calculadoras_indicadores.md:
# apenas defasagem e IAN têm fórmula oficial confirmada para cálculo nesta
# aplicação.
# ---------------------------------------------------------------------------

NOTA_IEG_SEM_CALCULO = (
    "O IEG deve ser informado conforme o registro institucional, com base nos "
    "registros de atividades e tarefas realizadas pelo(a) estudante."
)
NOTA_IPS_SEM_CALCULO = (
    "O IPS deve ser informado conforme o registro institucional, com base na "
    "avaliação da equipe responsável pelos aspectos psicossociais."
)
NOTA_IPV_SEM_CALCULO = (
    "O IPV deve ser informado conforme o registro institucional. Ele descreve "
    "a evolução do(a) estudante ao longo do tempo."
)

# ---------------------------------------------------------------------------
# IPP — indicador de contexto, obrigatório para calcular o INDE completo nas
# fases Alfa a 7. Nunca é um dos sete preditores enviados ao modelo.
# ---------------------------------------------------------------------------

ROTULO_IPP_INSTITUCIONAL = "IPP — Indicador Psicopedagógico institucional *"
AJUDA_IPP_INSTITUCIONAL = (
    "Informe o IPP disponível no registro institucional das avaliações "
    "pedagógicas do estudante. É usado apenas para calcular o INDE "
    "complementar — não é um dos sete indicadores usados na estimativa."
)
NOTA_IPP_NAO_SE_APLICA = (
    "IPP: não se aplica à fase informada — selecione a fase atual acima para "
    "informar o IPP."
)

ROTULO_MODO_DEFASAGEM_DIRETO = "Já possuo a defasagem registrada"
ROTULO_MODO_DEFASAGEM_CALCULADO = "Quero calcular pela fase atual e pela fase ideal"
ROTULO_MODO_IDA_DIRETO = "Já possuo o IDA institucional"
ROTULO_MODO_IDA_CALCULADO = "Quero calcular pelas três notas"
ROTULO_MODO_IAA_DIRETO = "Já possuo o IAA institucional"
ROTULO_MODO_IAA_CALCULADO = "Quero calcular pelas 6 perguntas"

AJUDA_FASE_IDEAL = (
    "A fase considerada ideal para o(a) estudante — pelo registro "
    "institucional, ou pela sugestão por idade abaixo, sempre confirmada por "
    "você antes do cálculo."
)
EXPLICACAO_CALCULO_DEFASAGEM = (
    "Mostra a diferença entre a fase em que o(a) estudante está e a fase ideal "
    "confirmada para ele(a). O cálculo é fase atual menos fase ideal. Exemplo: "
    "fase atual 2 e fase ideal 3 resultam em −1, indicando uma fase de atraso. "
    "Zero ou valor positivo indica que não há defasagem; −1 ou −2 indica "
    "defasagem moderada; abaixo de −2 indica defasagem severa."
)
EXPLICACAO_CALCULO_IAN = (
    "O IAN (Indicador de Adequação de Nível) é calculado a partir da defasagem: "
    "10 quando não há defasagem, 5 para defasagem moderada e 2,5 para defasagem "
    "severa. Ele aparece no resumo e no relatório apenas como contexto — não é "
    "enviado como um oitavo indicador para a estimativa."
)

# ---------------------------------------------------------------------------
# Idade → sugestão de fase ideal (revisão de 25/09/2026, Parte 2). A
# sugestão nunca decide sozinha: a tabela institucional tem faixas etárias
# que se sobrepõem em alguns pontos (ex.: 8 anos cabe em duas fases), então
# o profissional sempre confirma ou escolhe a fase ideal manualmente.
# ---------------------------------------------------------------------------

AVISO_SUGESTAO_FASE_IDEAL = (
    "A idade pode sugerir uma fase ideal, mas não decide sozinha — confirme ou "
    "escolha a fase ideal abaixo antes de calcular a defasagem."
)


def texto_sugestao_fase_ideal(candidatas: tuple, ambigua: bool) -> str:
    """`candidatas` é a lista `[(rótulo, código), ...]` de
    `calculadoras_indicadores.sugerir_fase_ideal_por_idade`."""
    if not candidatas:
        return "Não há sugestão de fase ideal para essa idade nesta tabela institucional."
    rotulos = " ou ".join(rotulo for rotulo, _ in candidatas)
    if ambigua:
        return (
            f"Essa idade está na fronteira entre fases na tabela institucional: {rotulos}. "
            "Confirme a fase ideal correta abaixo."
        )
    return f"Sugestão com base na idade: {rotulos}. Confirme a fase ideal abaixo."


# ---------------------------------------------------------------------------
# IDA — calculadora pelas três notas (revisão de 25/09/2026, Parte 4).
# ---------------------------------------------------------------------------

ROTULO_NOTA_MATEMATICA = "Nota de Matemática"
ROTULO_NOTA_PORTUGUES = "Nota de Português"
ROTULO_NOTA_INGLES = "Nota de Inglês"
AJUDA_NOTAS_IDA = (
    "Informe as notas de Matemática, Português e Inglês, cada uma de 0 a 10. "
    "O IDA é a média das três: (Matemática + Português + Inglês) / 3, pela "
    "fórmula documentada pela Associação Passos Mágicos. As três notas são "
    "obrigatórias — sem alguma delas, use o IDA institucional ao lado."
)
AVISO_IDA_ESCOPO_FASES = (
    "Essa calculadora vale para as fases escolares 0 a 7. No ensino superior "
    "(Fase 8), a instituição usa a média das disciplinas cursadas na "
    "faculdade, não estas três notas — informe o IDA institucional nesse caso."
)

# ---------------------------------------------------------------------------
# IAA — calculadora pelas 6 perguntas do questionário de autoavaliação
# (revisão de 25/09/2026, Parte 5, Tabela 40).
# ---------------------------------------------------------------------------

AJUDA_IAA_CALCULO = (
    "Responda as seis perguntas do questionário de autoavaliação institucional. "
    "O IAA é a soma dos pontos de cada resposta, pela tabela oficial da "
    "Associação Passos Mágicos (os pontos variam um pouco conforme a fase)."
)
OPCOES_RESPOSTA_IAA_TEXTO: dict[str, str] = {
    "": "Selecione",
    "A": "A",
    "B": "B",
    "C": "C",
    "D": "D",
}

# ---------------------------------------------------------------------------
# INDE — informação complementar (revisão de 25/09/2026, Parte 6). Nunca
# enviado ao modelo; nunca confundido com a estimativa.
# ---------------------------------------------------------------------------

EXPLICACAO_INDE = (
    "O INDE combina os sete indicadores institucionais numa nota única, pela "
    "fórmula oficial da Associação Passos Mágicos. Aparece aqui só como "
    "informação complementar, quando todos os indicadores necessários estão "
    "disponíveis — nunca é enviado à estimativa, e não é a mesma coisa que ela."
)


def texto_inde_incompleto(faltantes: list) -> str:
    nomes = ", ".join(str(f).upper() for f in faltantes)
    return f"INDE não calculado — faltam: {nomes}."

# ---------------------------------------------------------------------------
# "Avaliar um caso" — relatório individual do caso (revisão editorial,
# 25/09/2026, Parte 8). Gerado somente em memória, nunca escrito em disco.
# ---------------------------------------------------------------------------

RELATORIO_ARQUIVO_NOME = "relatorio_acompanhamento.html"
RELATORIO_ROTULO_CONTEXTO = "Informação de contexto"
RELATORIO_ROTULO_CALCULADO = "Valor calculado pela fórmula institucional"
RELATORIO_ROTULO_INDICADOR = "Indicador utilizado na estimativa"
RELATORIO_ROTULO_RESULTADO = "Resultado da ferramenta"
RELATORIO_AVISO_DIAGNOSTICO = (
    "Este relatório não constitui diagnóstico. É apoio à priorização e deve ser "
    "interpretado por profissionais responsáveis pelo(a) estudante."
)
RELATORIO_AVISO_IMPRESSAO = (
    "Para gerar um PDF, abra este arquivo no navegador e use Imprimir → Salvar "
    "como PDF."
)
RELATORIO_AVISO_ARMAZENAMENTO = (
    "Este relatório não fica salvo nesta aplicação: o conteúdo é preparado "
    "somente em memória e existe apenas no download que você acabou de fazer. "
    "Uma vez baixado, o arquivo passa a existir no seu dispositivo — cabe a você "
    "e à instituição guardá-lo de forma adequada."
)

# ---------------------------------------------------------------------------
# Tradução obrigatória (seção 5 da solicitação) — termo técnico -> forma
# principal em linguagem simples. Os termos técnicos aparecem entre
# parênteses apenas na camada de aprofundamento.
# ---------------------------------------------------------------------------

TRADUCOES: tuple[tuple[str, str], ...] = (
    ("Probabilidade predita", "Estimativa do modelo"),
    ("Threshold / limiar", "Ponto de atenção do modelo"),
    ("Classe positiva", "Caso sinalizado para acompanhamento"),
    ("Preditor", "Indicador utilizado"),
    ("Inferência", "Cálculo da estimativa"),
    ("Falso positivo", "Caso sinalizado que não apresentou posteriormente o evento"),
    ("Falso negativo", "Caso não sinalizado que apresentou posteriormente o evento"),
    ("Calibração", "Proximidade entre as estimativas e o que ocorreu na prática"),
)

# ---------------------------------------------------------------------------
# Mensagens de resultado (seção 4.3) — texto fixo, institucional, nunca gerado
# a partir de causa individual.
# ---------------------------------------------------------------------------

TITULO_ACIMA_DO_PONTO = "Este caso ficou acima do ponto de atenção."
TEXTO_ACIMA_DO_PONTO = (
    "A combinação dos indicadores sugere que o caso merece uma análise mais "
    "cuidadosa pela equipe. Isso não significa que o(a) estudante necessariamente "
    "entrará em defasagem."
)

TITULO_ABAIXO_DO_PONTO = "Este caso não ultrapassou o ponto de atenção."
TEXTO_ABAIXO_DO_PONTO = (
    "Isso não garante ausência de dificuldades. Esta estimativa pode deixar de "
    "identificar alguns casos, portanto observações pedagógicas e mudanças "
    "recentes também precisam ser consideradas."
)

AVISO_NAO_CAUSAL = (
    "A estimativa é calculada a partir da **combinação dos sete indicadores** "
    "informados. Ela não é uma relação de causa e efeito: descreve associações "
    "observadas nos dados históricos, não mecanismos causais, e não aponta qual "
    "indicador, isoladamente, foi mais determinante neste caso."
)

AVISO_SUPERVISAO_HUMANA = (
    "Este resultado é apoio à priorização e deve ser sempre revisado por uma "
    "equipe pedagógica ou profissional responsável. Ele não substitui avaliação "
    "pedagógica ou profissional, nem constitui diagnóstico."
)

AVISO_ABAIXO_NAO_ELIMINA_RISCO = (
    "Um resultado abaixo do ponto de atenção **não elimina o risco**: é apenas o "
    "ponto de corte usado por esta ferramenta para sinalizar prioridade, calibrado "
    "para um nível de sensibilidade que não se manteve completo no teste mais "
    "recente."
)

# ---------------------------------------------------------------------------
# Próximos passos — protocolo geral, institucional, não personalizado por
# indicador. Integrado ao resultado de "Avaliar um caso" (revisão editorial,
# 25/09/2026, Parte 7) — não existe mais como aba independente.
# ---------------------------------------------------------------------------

PROTOCOLO_PROXIMOS_PASSOS: tuple[str, ...] = (
    "Conferir as informações preenchidas.",
    "Observar a trajetória recente do(a) estudante.",
    "Conversar com o(a) estudante.",
    "Conversar com a família, quando apropriado.",
    "Discutir o caso com a equipe pedagógica.",
    "Definir e acompanhar ações de apoio.",
)

ORIENTACAO_PRIORIDADE_ABAIXO = (
    "O resultado abaixo do ponto de atenção não elimina a necessidade de "
    "acompanhamento. Outros sinais percebidos pela equipe devem continuar sendo "
    "considerados."
)

AVISO_DECISAO_PROFISSIONAIS = (
    "Estas são orientações gerais. A decisão sobre qualquer acompanhamento cabe "
    "aos profissionais responsáveis pelo estudante."
)

# ---------------------------------------------------------------------------
# Página inicial — reconstruída como abertura editorial (revisão de
# identidade visual, 25/09/2026, item 12). O logo, o subtítulo do projeto e
# o seletor de aparência ficam no cabeçalho (`streamlit_app.py:_cabecalho`),
# fora desta aba.
# ---------------------------------------------------------------------------

SUBTITULO_PROJETO = "Dados para acompanhar trajetórias educacionais"

TITULO_EDITORIAL_INICIO = "Educação se transforma quando enxergamos cada trajetória."
TEXTO_APOIO_INICIO = (
    "Uma aplicação para compreender os indicadores do PEDE, explorar os "
    "principais resultados e apoiar o acompanhamento de estudantes pela equipe "
    "da Associação Passos Mágicos."
)

CONTEXTO_DESAFIO = (
    "A Associação Passos Mágicos atua na transformação da vida de crianças e jovens "
    "em situação de vulnerabilidade social por meio da educação. Para acompanhar essa "
    "trajetória, a instituição realiza anualmente o PEDE (Pesquisa Extensiva do "
    "Desenvolvimento Educacional), uma avaliação multidimensional que reúne indicadores "
    "de aprendizagem, engajamento, autoavaliação, aspectos psicossociais e trajetória "
    "escolar dos anos de 2022 a 2024.\n\n"
    "Esta aplicação foi construída para professores(as) e profissionais da ONG: "
    "organiza esses registros em informações compreensíveis e em uma ferramenta de "
    "apoio ao acompanhamento, preservando a privacidade dos estudantes e evitando "
    "interpretações causais ou decisões automáticas."
)

QUESTAO_CENTRAL = (
    "Como os dados do PEDE podem ajudar a compreender a trajetória dos estudantes, "
    "identificar sinais de atenção e apoiar ações de acompanhamento pela Associação "
    "Passos Mágicos?"
)

OBJETIVO_TRABALHO = (
    "Organizar e interpretar os dados educacionais para responder às perguntas de "
    "negócio propostas, apresentar os principais padrões encontrados e disponibilizar "
    "uma ferramenta de apoio à avaliação de risco de defasagem. A aplicação não "
    "substitui a análise dos profissionais: ela oferece evidências adicionais para "
    "orientar o acompanhamento humano."
)

# Três caminhos, em linhas editoriais numeradas — não três cartões genéricos
# (revisão de identidade visual, 25/09/2026, item 12).
CAMINHOS_APLICACAO: tuple[tuple[str, str], ...] = (
    ("Conhecer o panorama",
     "As 11 perguntas de negócio respondidas com evidências, gráficos e conclusões "
     "em linguagem acessível."),
    ("Avaliar um caso",
     "Uma ficha para estimar, a partir de sete indicadores já usados pela "
     "instituição, o risco de um(a) estudante entrar em defasagem."),
    ("Entender os indicadores",
     "O significado de cada sigla (IDA, IEG, IAA, IPS, IPV, fase e defasagem) e "
     "como a Passos Mágicos os utiliza."),
)

EQUIPE: tuple[str, ...] = (
    "Lucas de Oliveira Schroeder",
    "Izadora Rayana Bento Araujo",
    "Laura Rossati de Oliveira",
    "Victor Thiago Farias Santos",
    "Jônatas Williams Santos Silva",
)

# Rodapé único, discreto, reunindo os créditos do projeto e um resumo dos
# dois avisos de privacidade/uso responsável, sem repetir os avisos
# maiores exibidos em outros pontos da aplicação.
RODAPE_APLICACAO = (
    "Projeto acadêmico do Datathon — Fase 5 (FIAP), em colaboração de dados com a "
    "Associação Passos Mágicos. " + AVISO_USO_RESPONSAVEL_CURTO +
    " Nenhum dado individual é armazenado ou enviado a terceiros nesta aplicação."
)
# ---------------------------------------------------------------------------
# "Modelo e limitações" — visão simples (exemplos com número vindo do
# artefato, nunca duplicado manualmente; só o padrão de frase é fixo aqui).
# ---------------------------------------------------------------------------

def frase_precisao(precisao: float) -> str:
    casos_de_dez = round(precisao * 10)
    return (
        f"**Precisão de aproximadamente {precisao * 100:.0f}%:** de cada 10 casos "
        f"sinalizados pelo modelo, cerca de {casos_de_dez} realmente apresentaram o evento "
        "no teste temporal."
    )


def frase_recall(recall: float) -> str:
    casos_de_dez = round(recall * 10)
    return (
        f"**Recall de aproximadamente {recall * 100:.0f}%:** de cada 10 casos que "
        f"apresentaram o evento no teste temporal, aproximadamente {casos_de_dez} "
        "foram identificados pelo modelo."
    )


AVISO_APROXIMACAO = (
    "Estes números são aproximações baseadas no teste temporal (2023→2024) e não "
    "são garantias para cada estudante individualmente."
)

EXPLICACAO_FALSO_POSITIVO = "Caso sinalizado pelo modelo que não apresentou posteriormente o evento."
EXPLICACAO_FALSO_NEGATIVO = "Caso não sinalizado pelo modelo que apresentou posteriormente o evento."
EXPLICACAO_PONTO_DE_ATENCAO = (
    "O valor de estimativa a partir do qual um caso passa a ser sinalizado para "
    "acompanhamento. O ponto mostrado nos números acima é o ponto metodológico "
    "original, escolhido durante o desenvolvimento do modelo (sensibilidade mínima "
    "de 80% nos dados de desenvolvimento) e preservado sem recálculo. A aplicação "
    "usa hoje, para sinalizar cada caso, um ponto operacional ajustado, comparado "
    "logo abaixo. Em nenhum dos dois casos o modelo ou a probabilidade calculada "
    "mudam; só muda o valor de comparação."
)

# ---------------------------------------------------------------------------
# Ponto de atenção operacional (decisão de gestão, 25/09/2026) — auditoria
# experimental de recall temporal (reports/experimental/). Ajusta somente a
# REGRA DE SINALIZAÇÃO (o valor com que a probabilidade já calculada pelo
# modelo é comparada); a probabilidade individual nunca muda.
# ---------------------------------------------------------------------------

EXPLICACAO_AJUSTE_PONTO_ATENCAO = (
    "O ponto de atenção foi ajustado para reduzir a quantidade de estudantes em "
    "risco que deixam de ser sinalizados. No teste temporal, a identificação dos "
    "casos reais aumentou de aproximadamente 40% para 58%."
)
EXPLICACAO_MAIS_ENCAMINHADOS_OBSERVACAO = (
    "Com o novo ponto, mais estudantes são encaminhados para observação "
    "pedagógica. Isso não representa diagnóstico nem intervenção automática."
)

TITULO_PONTO_METODOLOGICO_ORIGINAL = "Ponto metodológico original"
TITULO_PONTO_OPERACIONAL_ADOTADO = "Ponto operacional adotado"


def texto_ponto_metodologico_original(metricas_temporal: dict) -> str:
    """Recebe `contexto.validation.metrics["temporal"]["metricas"]` (artefato
    oficial, nunca recalculado aqui) e monta o texto de rastreabilidade —
    nenhum número fica hardcoded neste módulo."""
    verdadeiros_positivos = metricas_temporal["matriz_confusao"][1][1]
    eventos = metricas_temporal["eventos"]
    return (
        "Preservado para rastreabilidade — é o ponto escolhido durante o "
        "desenvolvimento do modelo, exigindo sensibilidade mínima de 80% nos dados "
        "de desenvolvimento. No teste temporal: recall de "
        f"{metricas_temporal['recall'] * 100:.2f}%, precisão de "
        f"{metricas_temporal['precisao'] * 100:.2f}%, identificando "
        f"{verdadeiros_positivos} de {eventos} casos reais."
    )


def texto_ponto_operacional_adotado(metricas_operacional: dict) -> str:
    """Recebe o bloco `ponto_operacional_adotado` de
    `config/ponto_atencao_operacional.json` (já validado pela aplicação) —
    nenhum número fica hardcoded neste módulo."""
    return (
        "Usado atualmente por esta aplicação para decidir se um caso fica acima ou "
        "abaixo do ponto de atenção. Escolhido em auditoria experimental, "
        "exclusivamente com dados de desenvolvimento — nunca olhando o teste "
        "temporal na escolha do valor. No teste temporal: recall de "
        f"{metricas_operacional['recall'] * 100:.2f}%, precisão aproximada de "
        f"{metricas_operacional['precisao'] * 100:.2f}%, identificando "
        f"{metricas_operacional['verdadeiros_positivos']} de "
        f"{metricas_operacional['positivos_reais']} casos reais — "
        f"{metricas_operacional['falsos_negativos']} ainda não identificados, de "
        f"{metricas_operacional['sinalizados']} estudantes sinalizados. "
        f"Desses, {metricas_operacional['verdadeiros_positivos']} apresentaram o "
        f"evento e {metricas_operacional['falsos_positivos']} não. "
        "Acompanhamento humano permanece obrigatório."
    )
EXPLICACAO_CALIBRACAO = (
    "O quanto as estimativas do modelo se aproximam do que de fato aconteceu depois. "
    "No teste temporal, o modelo tendeu a prever probabilidades um pouco menores do "
    "que a proporção real de casos observados — ou seja, tendeu a **subestimar** o risco."
)
EXPLICACAO_TESTE_TEMPORAL = (
    "O modelo foi treinado com dados da transição 2022→2023 e avaliado, sem nenhum "
    "reajuste, com dados reais da transição seguinte (2023→2024). É a verificação mais "
    "rigorosa disponível: dados que o modelo nunca viu durante o treinamento."
)

AVISO_FINALIDADE_EDUCACIONAL = (
    "Esta é uma aplicação **educacional e demonstrativa** do Datathon Fase 5 "
    "(Associação Passos Mágicos). Não é um sistema de produção institucional."
)
AVISO_CARATER_OBSERVACIONAL = (
    "O modelo é preditivo e observacional, não causal, e não constitui diagnóstico "
    "individual."
)
LIMITACOES_MODELO: tuple[str, ...] = (
    "A sensibilidade (recall) caiu de cerca de 82% na validação interna do "
    "desenvolvimento para cerca de 40% no teste temporal mais recente — no ano "
    "seguinte, o modelo identificou uma fração bem menor dos casos reais de "
    "entrada em defasagem.",
    "No teste temporal, o modelo tendeu a prever probabilidades menores do que a "
    "proporção real de casos observados (subestimação).",
    "A amostra de desenvolvimento é pequena (60 eventos) e há um único corte "
    "temporal — os resultados têm incerteza relevante e podem não se repetir em "
    "anos futuros.",
    "Supervisão humana é obrigatória: toda saída exige revisão por equipe "
    "pedagógica ou profissional antes de qualquer decisão.",
)
EXPLICACAO_TESTE_MAIS_REALISTA = (
    "O desempenho no teste temporal (2023→2024) é mais realista do que o "
    "desempenho no desenvolvimento: o desenvolvimento mede o quanto o modelo "
    "aprendeu os próprios dados de treino, enquanto o teste temporal mede o "
    "quanto isso se sustenta em dados de um ano que o modelo nunca viu."
)

# ---------------------------------------------------------------------------
# Contexto institucional (aba Início, seção 5.1)
# ---------------------------------------------------------------------------

CONTEXTO_INSTITUCIONAL = (
    "A Associação Passos Mágicos atua na educação de crianças e jovens em "
    "situação de vulnerabilidade social, acompanhando sua trajetória escolar "
    "ao longo dos anos. Para isso, a instituição realiza anualmente a PEDE "
    "(Pesquisa Extensiva do Desenvolvimento Educacional), uma avaliação "
    "multidimensional: ela não olha só para notas, mas combina indicadores "
    "acadêmicos (como aprendizagem e engajamento), psicossociais e "
    "psicopedagógicos em um retrato mais completo do desenvolvimento de cada "
    "estudante."
)
CONTEXTO_PROJETO = (
    "Este projeto organiza os dados já coletados pela instituição em um "
    "panorama compreensível e em uma estimativa de risco por caso, como "
    "apoio ao acompanhamento educacional que a equipe já realiza."
)
CONTEXTO_NAO_SUBSTITUI = (
    "O objetivo não é substituir professores(as) ou profissionais da ONG: é "
    "organizar informação que já existe, para apoiar decisões que continuam "
    "sendo humanas."
)
CHAMADA_DUAS_OPCOES = (
    "Para continuar, abra uma das abas acima: **\"Panorama e resultados\"** "
    "para conhecer o retrato geral dos dados, ou **\"Avaliar um caso\"** para "
    "estimar o risco de um(a) estudante específico(a)."
)
ENTREGA_DA_FERRAMENTA: tuple[str, ...] = (
    "Panorama agregado dos dados da instituição.",
    "Respostas às perguntas de negócio da análise exploratória.",
    "Estimativa individual de risco para um caso específico.",
    "Orientações gerais de acompanhamento.",
    "Metodologia e limitações do modelo.",
)

# ---------------------------------------------------------------------------
# Painel "Panorama e resultados" — leitura estrita de
# reports/metricas_analises_negocio.json em tempo de execução. As funções
# abaixo só formatam valores já carregados; nenhum número oficial é
# duplicado como literal neste módulo (a única exceção são os exemplos de
# precisão/recall em `frase_precisao`/`frase_recall`, que já recebem o valor
# como parâmetro, não como constante).
# ---------------------------------------------------------------------------

CONTEXTO_DADOS_PANORAMA: tuple[str, ...] = (
    "Período analisado: 2022 a 2024.",
    "Os registros são observações anuais — o mesmo(a) estudante pode aparecer "
    "em mais de um ano; os totais anuais não representam estudantes únicos.",
    "As análises longitudinais (que comparam um ano com o seguinte) usam "
    "apenas os pares de registros efetivamente encontrados nos dois anos.",
    "Grupos com menos de 10 observações foram omitidos, para preservar a "
    "privacidade.",
    "Todos os resultados são observacionais: descrevem associações "
    "encontradas nos dados, não demonstram causalidade.",
)

AVISO_TRES_PERIODOS = (
    "Este projeto trabalha com três períodos que nunca devem ser confundidos: "
    "o panorama exploratório cobre **2022–2024**; o modelo foi **desenvolvido** "
    "na transição **2022→2023**; e foi **testado**, sem nenhum reajuste, na "
    "transição seguinte, **2023→2024**. A estimativa individual que você gera "
    "em \"Avaliar um caso\" é sempre sobre um caso hipotético, feita com o "
    "modelo já congelado — não é uma nova análise exploratória nem um novo "
    "teste do modelo."
)

CAPITULOS: tuple[tuple[str, tuple[int, ...]], ...] = (
    ("Trajetória e defasagem", (1, 10, 11)),
    ("Aprendizagem e engajamento", (2, 3)),
    ("Dimensões psicossociais e psicopedagógicas", (4, 5, 6)),
    ("Indicadores globais, risco e prioridades", (7, 8, 9)),
)


def _get(d: dict, *caminho: str, default=None):
    """Acesso seguro a um caminho aninhado de dicionários; nunca levanta
    `KeyError` — devolve `default` se qualquer nível do caminho faltar."""
    atual = d
    for chave in caminho:
        if not isinstance(atual, dict) or chave not in atual:
            return default
        atual = atual[chave]
    return atual


def _pct(valor: float | None) -> str:
    return f"{valor:.0%}" if isinstance(valor, (int, float)) else "não disponível"


def _pct1(valor: float | None) -> str:
    return f"{valor:.1%}" if isinstance(valor, (int, float)) else "não disponível"


def _rho(valor: float | None) -> str:
    return f"ρ≈{valor:.2f}" if isinstance(valor, (int, float)) else "não estimado"


def _numero(valor: float | int | None, casas: int = 2) -> str:
    """Formata somente para apresentação; o valor sempre vem do artefato."""
    if not isinstance(valor, (int, float)):
        return "não disponível"
    return f"{valor:.{casas}f}"


def _fracao(contagem, denominador) -> str:
    if not isinstance(contagem, (int, float)) or not isinstance(denominador, (int, float)):
        return "não disponível"
    return f"{int(contagem)}/{int(denominador)} ({contagem / denominador:.1%})"


def construir_resumo_executivo(analises: dict, modelo: dict) -> tuple[str, ...]:
    """Cinco pontos, cada um com linguagem de associação (nunca causal),
    construídos a partir dos valores carregados de
    `reports/metricas_analises_negocio.json` no momento da chamada."""
    mod22 = _get(analises, "anuais", "2022", "categorias", "proporcoes", "moderada")
    mod23 = _get(analises, "anuais", "2023", "categorias", "proporcoes", "moderada")
    ida22 = _get(analises, "anuais", "2022", "indicadores", "ida", "media")
    ida23 = _get(analises, "anuais", "2023", "indicadores", "ida", "media")
    ida24 = _get(analises, "anuais", "2024", "indicadores", "ida", "media")
    rho_ieg_ida = _get(analises, "associacoes", "ajustado_ano", "ieg x ida", "rho")
    rho_ieg_ipv = _get(analises, "associacoes", "ajustado_ano", "ieg x ipv", "rho")
    recall_dev = _get(modelo, "oof", "recall")
    recall_teste = _get(modelo, "temporal", "recall")

    def _f(valor):
        return f"{valor:.1f}" if isinstance(valor, (int, float)) else "não disponível"

    return (
        f"A defasagem escolar continua relevante: {_pct(mod22)} dos registros de "
        f"2022 e {_pct(mod23)} dos registros de 2023 apresentavam defasagem "
        "moderada.",
        f"O desempenho acadêmico médio (IDA) melhorou de {_f(ida22)} em 2022 "
        f"para {_f(ida23)} em 2023, e depois recuou para {_f(ida24)} em 2024.",
        f"O engajamento apresenta associação moderada com o desempenho "
        f"acadêmico ({_rho(rho_ieg_ida)}) e com o ponto de virada "
        f"({_rho(rho_ieg_ipv)}) — associação, não causa.",
        "Os indicadores psicossociais e psicopedagógicos acrescentam "
        "dimensões diferentes da acadêmica, com concordância apenas fraca a "
        "moderada entre si.",
        f"O desempenho do modelo cai de forma relevante do desenvolvimento "
        f"({_pct(recall_dev)} de recall) para o teste temporal "
        f"({_pct(recall_teste)}), reforçando a necessidade de supervisão "
        "humana.",
    )


def _q1(analises, modelo, privacidade=None):
    linhas = []
    partes = []
    for ano in ("2022", "2023"):
        dist = _get(analises, "anuais", ano, "categorias", default={})
        denom = dist.get("denominador")
        cont = dist.get("contagens", {})
        prop = dist.get("proporcoes", {})
        partes.append(
            f"{ano}: {cont.get('moderada')}/{denom} ({_pct1(prop.get('moderada'))}) moderada "
            f"e {cont.get('severa')}/{denom} ({_pct1(prop.get('severa'))}) severa"
        )
        for categoria in ("sem_defasagem", "moderada", "severa"):
            linhas.append({
                "Ano": ano,
                "Categoria": categoria.replace("_", " "),
                "Contagem": cont.get(categoria),
                "Denominador": denom,
                "Percentual": _pct1(prop.get(categoria)),
            })
    total24 = _get(analises, "anuais", "2024", "total")
    status24 = _get(analises, "anuais", "2024", "categorias", "status")
    minimo = _get(privacidade or {}, "minimo_perfil")
    resposta = (
        "Entre os registros anuais, " + "; ".join(partes) + ". Em 2024, a divisão por "
        f"categoria não é publicável: no conjunto de {total24} registros, ao menos uma "
        f"célula não vazia ficou abaixo do mínimo de {minimo}, acionando a supressão integral."
    )
    linhas.append({"Ano": "2024", "Categoria": "partição protegida", "Contagem": None,
                   "Denominador": total24, "Percentual": None})
    return {"resposta": resposta, "observamos": "A participação moderada caiu entre 2022 e 2023; a comparação categórica com 2024 não é autorizada pelo artefato.",
            "principais_numeros": linhas,
            "nota_numeros": f"Regra aplicada em 2024: {status24}; mínimo publicável por célula: {minimo}."}


def _q2(analises, modelo, privacidade=None):
    ida22 = _get(analises, "anuais", "2022", "indicadores", "ida", "media")
    ida23 = _get(analises, "anuais", "2023", "indicadores", "ida", "media")
    ida24 = _get(analises, "anuais", "2024", "indicadores", "ida", "media")
    resposta = (
        f"A média do IDA foi {ida22:.2f} em 2022, subiu para {ida23:.2f} em 2023 "
        f"e recuou para {ida24:.2f} em 2024 — melhora seguida de recuo, não uma "
        "tendência única em uma direção."
    )
    linhas = []
    for ano in ("2022", "2023", "2024"):
        s = _get(analises, "anuais", ano, "indicadores", "ida", default={})
        linhas.append({"Período": ano, "n válido": s.get("n"), "Total": s.get("total"),
                       "Cobertura": _pct(s.get("cobertura")), "Média IDA": _numero(s.get("media")),
                       "Mediana": _numero(s.get("mediana"))})
    for transicao in ("2022→2023", "2023→2024"):
        s = _get(analises, "longitudinal", transicao, "mudancas", "ida", default={})
        linhas.append({"Período": transicao, "n válido": s.get("n"), "Total": s.get("total"),
                       "Cobertura": _pct(s.get("cobertura")), "Média IDA": f"Δ {_numero(s.get('media'))}",
                       "Mediana": f"Δ {_numero(s.get('mediana'))}"})
    return {"resposta": resposta, "observamos": "A leitura anual mostra alta e depois recuo; nos pares acompanhados, a mudança média foi positiva em 2022→2023 e negativa em 2023→2024.",
            "principais_numeros": linhas}


def _q3(analises, modelo, privacidade=None):
    rho_ida = _get(analises, "associacoes", "ajustado_ano", "ieg x ida", "rho")
    rho_ipv = _get(analises, "associacoes", "ajustado_ano", "ieg x ipv", "rho")
    resposta = (
        f"O engajamento (IEG) apresenta associação positiva e moderada tanto "
        f"com o desempenho acadêmico ({_rho(rho_ida)}) quanto com o ponto de "
        f"virada ({_rho(rho_ipv)}), de forma consistente entre os anos "
        "analisados."
    )
    linhas = []
    for par in ("ieg x ida", "ieg x ipv"):
        s = _get(analises, "associacoes", "ajustado_ano", par, default={})
        linhas.append({"Associação ajustada por ano": par.upper(), "ρ de Spearman": _numero(s.get("rho")),
                       "n (pares completos)": s.get("n"), "Intensidade": s.get("intensidade")})
    ns = sorted({linha["n (pares completos)"] for linha in linhas})
    texto_n = ", ".join(str(n) for n in ns)
    return {"resposta": resposta, "observamos": f"As duas correlações ajustadas por ano são positivas e moderadas, com {texto_n} pares completos nos cálculos.",
            "principais_numeros": linhas}


def _q4(analises, modelo, privacidade=None):
    rho_ida = _get(analises, "associacoes", "ajustado_ano", "iaa x ida", "rho")
    rho_ieg = _get(analises, "associacoes", "ajustado_ano", "iaa x ieg", "rho")
    resposta = (
        f"A autoavaliação (IAA) apresenta associação positiva, mas fraca, com "
        f"o desempenho acadêmico ({_rho(rho_ida)}) e com o engajamento "
        f"({_rho(rho_ieg)}) — os instrumentos medem construtos diferentes, "
        "não é esperado que concordem plenamente."
    )
    linhas = []
    for par in ("iaa x ida", "iaa x ieg"):
        s = _get(analises, "associacoes", "ajustado_ano", par, default={})
        linhas.append({"Associação ajustada por ano": par.upper(), "ρ de Spearman": _numero(s.get("rho")),
                       "n (pares completos)": s.get("n"), "Intensidade": s.get("intensidade")})
    return {"resposta": resposta, "observamos": "IAA varia na mesma direção de IDA e IEG, mas as correlações são fracas; isso não permite classificar estudantes como coerentes ou incoerentes.",
            "principais_numeros": linhas}


def _q5(analises, modelo, privacidade=None):
    rho_ida_1 = _get(analises, "longitudinal", "2022→2023", "ips", "ida", "associacao", "rho")
    rho_ida_2 = _get(analises, "longitudinal", "2023→2024", "ips", "ida", "associacao", "rho")
    rho_ieg_1 = _get(analises, "longitudinal", "2022→2023", "ips", "ieg", "associacao", "rho")
    rho_ieg_2 = _get(analises, "longitudinal", "2023→2024", "ips", "ieg", "associacao", "rho")
    resposta = (
        "IPS na origem quase não se associa às mudanças futuras: para IDA, "
        f"{_rho(rho_ida_1)} em 2022→2023 e {_rho(rho_ida_2)} em 2023→2024; "
        f"para IEG, {_rho(rho_ieg_1)} e {_rho(rho_ieg_2)}, respectivamente. "
        "Os dados não sustentam um padrão monotônico útil de antecedência nesta base."
    )
    linhas = []
    for transicao in ("2022→2023", "2023→2024"):
        for indicador in ("ida", "ieg"):
            s = _get(analises, "longitudinal", transicao, "ips", indicador, "associacao", default={})
            linhas.append({"Transição": transicao, "Relação": f"IPS origem × Δ{indicador.upper()}",
                           "ρ de Spearman": _numero(s.get("rho")), "n": s.get("n"),
                           "Pares ausentes": s.get("ausentes_par")})
    valores = [rho_ida_1, rho_ida_2, rho_ieg_1, rho_ieg_2]
    return {"resposta": resposta, "observamos": f"As quatro correlações ficam entre {_numero(min(valores))} e {_numero(max(valores))}, próximas de zero.",
            "principais_numeros": linhas}


def _q6(analises, modelo, privacidade=None):
    rho_2023 = _get(analises, "ipp", "2023", "ipp x ian", "rho")
    rho_2024 = _get(analises, "ipp", "2024", "ipp x ian", "rho")
    resposta = (
        f"A associação entre IPP e IAN é fraca em 2023 ({_rho(rho_2023)}) e em "
        f"2024 ({_rho(rho_2024)}) — a avaliação psicopedagógica e a adequação "
        "de nível concordam pouco, e não é esperado que concordem plenamente."
    )
    linhas = []
    for ano in ("2023", "2024"):
        s = _get(analises, "ipp", ano, "ipp x ian", default={})
        linhas.append({"Ano": ano, "Relação": "IPP × IAN", "ρ de Spearman": _numero(s.get("rho")),
                       "n": s.get("n"), "Total anual": s.get("total"), "Ausentes no par": s.get("ausentes_par")})
    return {"resposta": resposta, "observamos": "A concordância ordinal é positiva, porém fraca, nos dois anos em que IPP existe.",
            "principais_numeros": linhas}


def _q7(analises, modelo, privacidade=None):
    partes = []
    linhas = []
    for ano in ("2022", "2023", "2024"):
        associacoes = _get(analises, "ipv", ano, "associacoes", default={})
        validos = {k: v.get("rho") for k, v in associacoes.items() if isinstance(v, dict) and v.get("rho") is not None}
        if not validos:
            continue
        melhor = max(validos, key=lambda chave: abs(validos[chave]))
        partes.append(f"{ano}: {melhor.upper()} ({_rho(validos[melhor])})")
        s = associacoes[melhor]
        linhas.append({"Ano": ano, "Maior |ρ| com IPV": melhor.upper(), "ρ de Spearman": _numero(s.get("rho")),
                       "n": s.get("n"), "Intensidade": s.get("intensidade")})
    resposta = (
        "O indicador mais associado ao ponto de virada (IPV) muda de ano para "
        "ano: " + "; ".join(partes) + ". O ranking é descritivo, não uma regra fixa."
    )
    return {"resposta": resposta, "observamos": "IDA lidera em 2022 e 2023; em 2024, IPP apresenta a maior associação contemporânea com IPV.",
            "principais_numeros": linhas}


def _q8(analises, modelo, privacidade=None):
    partes = []
    linhas = []
    for ano in ("2022", "2023", "2024"):
        perfis = _get(analises, "inde", ano, "perfis_publicados", default={})
        validos = {k: v.get("media") for k, v in perfis.items() if isinstance(v, dict) and v.get("media") is not None}
        if not validos:
            continue
        melhor = max(validos, key=validos.get)
        partes.append(f"{ano}: \"{melhor}\" (média {validos[melhor]:.2f})")
        detalhe = perfis[melhor]
        linhas.append({"Ano": ano, "Perfil de maior média publicável": melhor,
                       "n": detalhe.get("n"), "INDE médio": _numero(detalhe.get("media")),
                       "Casos completos": _get(analises, "inde", ano, "n_completos")})
    resposta = (
        "O perfil com todos os indicadores altos ao mesmo tempo tende a ter o "
        "maior INDE médio: " + "; ".join(partes) + ". Isso é esperado, já que o "
        "INDE combina esses próprios indicadores — não é uma descoberta "
        "independente."
    )
    return {"resposta": resposta, "observamos": "Em cada ano, o maior INDE médio publicável aparece em um perfil com IDA, IEG e IPS altos; a posição do IPP varia em 2023 e 2024.",
            "principais_numeros": linhas}


def _q9(analises, modelo, privacidade=None):
    recall_dev = _get(modelo, "oof", "recall")
    recall_teste = _get(modelo, "temporal", "recall")
    resposta = (
        f"O recall (sensibilidade) do modelo caiu de {_pct(recall_dev)} na "
        f"validação interna de desenvolvimento para {_pct(recall_teste)} no "
        "teste temporal — uma queda relevante que exige supervisão humana em "
        "qualquer uso do modelo."
    )
    linhas = []
    for rotulo, chave in (("Desenvolvimento OOF", "oof"), ("Teste temporal", "temporal")):
        s = _get(modelo, chave, default={})
        linhas.append({"Avaliação": rotulo, "n": s.get("n"), "Eventos": s.get("eventos"),
                       "Precisão": _pct(s.get("precisao")), "Recall": _pct(s.get("recall")),
                       "F1": _pct(s.get("f1")), "Brier": _numero(s.get("brier"), 3)})
    matriz = _get(modelo, "temporal", "matriz_confusao", default=[[None, None], [None, None]])
    falsos_negativos, verdadeiros_positivos = matriz[1]
    eventos = _get(modelo, "temporal", "eventos")
    return {"resposta": resposta, "observamos": f"No teste temporal, o modelo identificou {verdadeiros_positivos} de {eventos} eventos e deixou {falsos_negativos} falsos negativos.",
            "principais_numeros": linhas}


def _q10(analises, modelo, privacidade=None):
    p1 = _get(analises, "longitudinal", "2022→2023", "pedras_evolucao", "proporcoes", default={})
    p2 = _get(analises, "longitudinal", "2023→2024", "pedras_evolucao", "proporcoes", default={})
    resposta = (
        f"Entre 2022 e 2023, {_pct(p1.get('melhoria'))} dos casos melhoraram de "
        f"Pedra e {_pct(p1.get('piora'))} pioraram; entre 2023 e 2024, "
        f"{_pct(p2.get('melhoria'))} melhoraram e {_pct(p2.get('piora'))} "
        "pioraram — proporções parecidas, sem tendência geral clara de melhora."
    )
    linhas = []
    for transicao, dist in (("2022→2023", p1), ("2023→2024", p2)):
        cont = _get(analises, "longitudinal", transicao, "pedras_evolucao", "contagens", default={})
        denom = _get(analises, "longitudinal", transicao, "pedras_evolucao", "denominador")
        for categoria in ("melhoria", "estabilidade", "piora"):
            linhas.append({"Transição": transicao, "Movimento": categoria,
                           "Contagem": cont.get(categoria), "Denominador": denom,
                           "Percentual": _pct(dist.get(categoria))})
    return {"resposta": resposta, "observamos": "A estabilidade reúne metade ou pouco mais dos pares; melhora e piora têm magnitudes próximas nas duas transições.",
            "principais_numeros": linhas}


def _q11(analises, modelo, privacidade=None):
    d1 = _get(analises, "perdas", "2022→2023", "desfecho", default={})
    d2 = _get(analises, "perdas", "2023→2024", "desfecho", default={})
    ausentes1 = _get(d1, "contagens", "destino_ausente")
    denom1 = _get(d1, "denominador")
    ausentes2 = _get(d2, "contagens", "destino_ausente")
    denom2 = _get(d2, "denominador")
    deslocamentos = _get(modelo, "distribuicao", "numericos", default={})
    indicador_deslocado = max(
        deslocamentos,
        key=lambda chave: abs(deslocamentos[chave].get("diferenca_padronizada") or 0),
    )
    deslocamento = deslocamentos[indicador_deslocado].get("diferenca_padronizada")
    fases_2024 = _get(analises, "ida_fase", "2024", default={})
    medias_fase = {fase: valores.get("media") for fase, valores in fases_2024.items()
                   if isinstance(valores, dict) and valores.get("media") is not None}
    fase_min = min(medias_fase, key=medias_fase.get)
    fase_max = max(medias_fase, key=medias_fase.get)
    resposta = (
        f"Uma fração relevante de estudantes elegíveis não tem correspondência "
        f"no ano seguinte: {ausentes1}/{denom1} entre 2022→2023 e "
        f"{ausentes2}/{denom2} entre 2023→2024. O maior deslocamento entre as "
        f"coortes ocorreu em {indicador_deslocado.upper()} ({_numero(deslocamento)}), "
        f"e o IDA médio de 2024 variou de {_numero(medias_fase[fase_min])} na fase "
        f"{fase_min} a {_numero(medias_fase[fase_max])} na fase {fase_max}."
    )
    linhas = []
    for transicao, desfecho in (("2022→2023", d1), ("2023→2024", d2)):
        denom = desfecho.get("denominador")
        ausentes = _get(desfecho, "contagens", "destino_ausente")
        observados = _get(desfecho, "contagens", "desfecho_observado")
        linhas.append({"Evidência": "Correspondência futura", "Período/recorte": transicao,
                       "Resultado": f"{_fracao(ausentes, denom)} sem correspondência",
                       "Base": f"{denom} elegíveis; {observados} com desfecho observado"})
    linhas.append({"Evidência": "Maior deslocamento entre coortes", "Período/recorte": "desenvolvimento × teste",
                   "Resultado": f"{indicador_deslocado.upper()}: {_numero(deslocamento)} DP",
                   "Base": "diferença padronizada"})
    linhas.append({"Evidência": "Amplitude do IDA por fase", "Período/recorte": "2024",
                   "Resultado": f"{_numero(medias_fase[fase_min])} (fase {fase_min}) a {_numero(medias_fase[fase_max])} (fase {fase_max})",
                   "Base": "médias publicáveis por fase"})
    perda1 = _get(d1, "proporcoes", "destino_ausente")
    perda2 = _get(d2, "proporcoes", "destino_ausente")
    return {"resposta": resposta, "observamos": f"A perda de correspondência passou de {_pct1(perda1)} para {_pct1(perda2)}; ao mesmo tempo, composição das coortes e médias por fase variaram.",
            "principais_numeros": linhas}


_EXTRATORES = {1: _q1, 2: _q2, 3: _q3, 4: _q4, 5: _q5, 6: _q6, 7: _q7, 8: _q8, 9: _q9, 10: _q10, 11: _q11}

# Texto estático (significado/uso pela ONG/limites/fonte), fiel às seções
# "Interpretação"/"Limitação"/"Recomendação" de
# `reports/relatorio_analises_negocio.md`, reorganizado no formato de cartão
# desta seção — nenhuma conclusão nova em relação ao relatório oficial.
PERGUNTAS_NEGOCIO: tuple[dict, ...] = (
    {
        "numero": 1, "pergunta": "Qual é o perfil geral de defasagem dos alunos (IAN) e como ele evolui ao longo do ano?",
        "grafico": "reports/public/figures/01_ian.png",
        "significado": "A defasagem moderada é o padrão mais comum; a severa é rara. Como o IAN incorpora a defasagem por regra documental, a associação entre os dois é matemática, não uma descoberta.",
        "uso_ong": "Priorizar acompanhamento pedagógico da defasagem e revisar divergências de registro na origem, mantendo o valor já registrado.",
        "limites": "Anos com detalhamento suprimido (privacidade) não autorizam concluir ausência de defasagem severa. Mudanças de composição entre anos impedem inferir evolução individual só pelas proporções.",
        "fonte_periodo": "reports/relatorio_analises_negocio.md — registros anuais de 2022 e 2023 (2024 parcialmente suprimido).",
    },
    {
        "numero": 2, "pergunta": "O desempenho acadêmico médio (IDA) está melhorando, estagnado ou caindo ao longo das fases e anos?",
        "grafico": "reports/public/figures/02_ida.png",
        "significado": "O desempenho acadêmico médio não segue uma tendência única: subiu de 2022 para 2023 e recuou em 2024.",
        "uso_ong": "Monitorar o IDA e sua cobertura por fase, distinguindo mudança de composição da turma de progresso dos(as) estudantes acompanhados(as).",
        "limites": "Fases agregadas misturam anos e estudantes repetidos entre coortes. Dispersão (desvio padrão) não é um intervalo de confiança.",
        "fonte_periodo": "reports/relatorio_analises_negocio.md — registros anuais de 2022, 2023 e 2024.",
    },
    {
        "numero": 3, "pergunta": "O grau de engajamento dos alunos (IEG) tem relação direta com seus indicadores de desempenho (IDA) e do ponto de virada (IPV)?",
        "grafico": "reports/public/figures/03_ieg.png",
        "significado": "Engajamento, desempenho acadêmico e ponto de virada tendem a andar juntos de forma moderada e consistente entre anos.",
        "uso_ong": "Acompanhar o engajamento junto ao desempenho, sem tratar a correlação como efeito de nenhuma intervenção específica.",
        "limites": "É uma associação contemporânea (mesmo ano); pode refletir contexto comum ou o próprio mecanismo de avaliação, não uma relação de causa e efeito.",
        "fonte_periodo": "reports/relatorio_analises_negocio.md — registros anuais de 2022 a 2024, agregado ajustado por ano.",
    },
    {
        "numero": 4, "pergunta": "As percepções dos alunos sobre si mesmos (IAA) são coerentes com seu desempenho real (IDA) e engajamento (IEG)?",
        "grafico": "reports/public/figures/04_iaa.png",
        "significado": "A coerência é fraca — o(a) próprio(a) estudante e as avaliações externas de desempenho/engajamento medem coisas parcialmente diferentes.",
        "uso_ong": "Usar divergências grandes como tema de escuta pedagógica, não como sinal isolado de erro de percepção do(a) estudante.",
        "limites": "IAA, IDA e IEG não medem o mesmo construto; uma diferença de pontuação não é diagnóstico. Este cartão compartilha o gráfico da pergunta anterior (associações de IEG), porque ambas tratam do mesmo conjunto de correlações.",
        "fonte_periodo": "reports/relatorio_analises_negocio.md — registros anuais de 2022 a 2024, agregado ajustado por ano.",
    },
    {
        "numero": 5, "pergunta": "Há padrões psicossociais (IPS) que antecedem quedas de desempenho acadêmico ou de engajamento?",
        "grafico": "reports/public/figures/05_ips.png",
        "significado": "Nesta base, o IPS na origem não mostra um padrão útil de antecedência às quedas futuras de IDA ou IEG.",
        "uso_ong": "Acompanhar o IPS e as mudanças futuras em conjunto, sem criar triagem automática baseada só no IPS.",
        "limites": "Antecedência temporal não estabelece causa; regressão à média, cobertura e mudanças de instrumento podem explicar parte do resultado.",
        "fonte_periodo": "reports/relatorio_analises_negocio.md — pares longitudinais 2022→2023 e 2023→2024.",
    },
    {
        "numero": 6, "pergunta": "As avaliações psicopedagógicas (IPP) confirmam ou contradizem a defasagem identificada pelo IAN?",
        "grafico": "reports/public/figures/06_ipp.png",
        "significado": "A concordância entre avaliação psicopedagógica (IPP) e adequação de nível (IAN) é fraca — não se exige que concordem plenamente.",
        "uso_ong": "Investigar perfis contrastantes (IPP e IAN discordantes) com a equipe pedagógica, preservando o contexto de cada avaliação.",
        "limites": "O IPP não existia como coluna em 2022 (ausência estrutural, não zero). IAN e defasagem têm relação matemática entre si.",
        "fonte_periodo": "reports/relatorio_analises_negocio.md — registros de 2023 e 2024 (IPP ausente em 2022).",
    },
    {
        "numero": 7, "pergunta": "Quais comportamentos — acadêmicos, emocionais ou de engajamento — mais influenciam o IPV ao longo do tempo?",
        "grafico": "reports/public/figures/07_ipv.png",
        "significado": "O indicador mais associado ao ponto de virada muda de ano para ano — não há um único “indicador-chave” estável.",
        "uso_ong": "Monitorar os indicadores associados em conjunto, evitando concluir que um deles isoladamente “leva” ao ponto de virada.",
        "limites": "As correlações não isolam o efeito próprio de cada indicador nem ajustam diferenças por fase. O IPV também compõe o INDE.",
        "fonte_periodo": "reports/relatorio_analises_negocio.md — registros anuais de 2022, 2023 e 2024.",
    },
    {
        "numero": 8, "pergunta": "Quais combinações de indicadores (IDA + IEG + IPS + IPP) elevam mais a nota global do aluno (INDE)?",
        "grafico": "reports/public/figures/08_inde.png",
        "significado": "Perfis com vários indicadores altos ao mesmo tempo têm INDE médio mais alto — resultado esperado, pois o INDE é uma combinação desses próprios indicadores.",
        "uso_ong": "Usar os perfis para descrever a multidimensionalidade dos casos, evitando priorizar um único componente só por sua associação matemática ao INDE.",
        "limites": "Há circularidade: o INDE combina estes indicadores com IAN, IAA e IPV, com pesos que mudam por fase. Perfis de anos diferentes não são diretamente equivalentes.",
        "fonte_periodo": "reports/relatorio_analises_negocio.md — casos completos de 2022 e 2024.",
    },
    {
        "numero": 9, "pergunta": "Quais padrões nos indicadores permitem identificar alunos em risco antes de queda no desempenho ou aumento da defasagem? Construa um modelo preditivo que mostre uma probabilidade do aluno ou aluna entrar em risco de defasagem.",
        "grafico": "reports/public/figures/09_modelo.png",
        "significado": "O modelo perde sensibilidade relevante ao ser testado em um ano que nunca viu — a meta de recall do desenvolvimento não se mantém no teste temporal.",
        "uso_ong": "Usar a estimativa como apoio à revisão humana, monitorando também os casos que o modelo deixa de sinalizar (falsos negativos).",
        "limites": "Base de desenvolvimento pequena, um único teste temporal, perdas e sobreposição de estudantes entre coortes. O alvo é entrada em defasagem entre elegíveis, não qualquer queda de desempenho.",
        "fonte_periodo": "reports/metricas_modelagem.json — desenvolvimento 2022→2023, teste temporal 2023→2024.",
    },
    {
        "numero": 10, "pergunta": "Os indicadores mostram melhora consistente ao longo do ciclo nas diferentes fases (Quartzo, Ágata, Ametista e Topázio), confirmando o impacto real do programa?",
        "grafico": "reports/public/figures/10_efetividade.png",
        "significado": "As proporções de melhora e piora de Pedra são parecidas entre si — não há uma tendência geral clara de melhora ou piora institucional nesses dados.",
        "uso_ong": "Acompanhar permanência, avanços e recuos de Pedra junto à cobertura de dados, sem confundir Pedra (baseada no INDE) com fase escolar.",
        "limites": "Sem grupo de controle ou contrafactual, essa evolução não confirma impacto de nenhuma ação institucional. A matriz detalhada pode ser suprimida por células pequenas.",
        "fonte_periodo": "reports/relatorio_analises_negocio.md — pares longitudinais 2022→2023 e 2023→2024.",
    },
    {
        "numero": 11, "pergunta": "Você pode adicionar mais insights e pontos de vista não abordados nas perguntas, utilize a criatividade e a análise dos dados para trazer sugestões para a Passos Mágicos.",
        "grafico": "reports/public/figures/11_insights.png",
        "significado": "Uma parte relevante dos(as) estudantes elegíveis não tem correspondência no ano seguinte — isso é, em si, um sinal para melhorar a coleta e o acompanhamento.",
        "uso_ong": "Registrar o motivo de saída, padronizar instrumentos e definições por fase, e monitorar disponibilidade e perdas a cada ciclo.",
        "limites": "Ausência de correspondência entre anos não prova evasão, sucesso ou fracasso; não explica sozinha a queda de recall do modelo.",
        "fonte_periodo": "reports/relatorio_analises_negocio.md — coortes elegíveis 2022→2023 e 2023→2024.",
    },
)


# Conjunto único dos caminhos de gráfico usados pelas 11 perguntas (10
# arquivos distintos — Q3 e Q4 compartilham reports/figures/03_associacoes.png).
PERGUNTAS_NEGOCIO_GRAFICOS: tuple[str, ...] = tuple(
    dict.fromkeys(item["grafico"] for item in PERGUNTAS_NEGOCIO)
)


# Metadados editoriais que tornam a leitura de cada resultado autossuficiente.
# As chaves JSON apontam para a origem exata; nenhum resultado numérico é
# repetido aqui.
METADADOS_ANALISE: dict[int, dict[str, str]] = {
    1: {
        "como_interpretar": "Compare as alturas das categorias dentro de cada ano. A ausência de barras categóricas em 2024 significa proteção de privacidade, não ausência de defasagem.",
        "populacao_periodo": "Todos os registros anuais disponíveis de 2022, 2023 e 2024; os denominadores estão na tabela e representam registros, não estudantes únicos.",
        "fonte_exata": "reports/metricas_analises_negocio.json — analises.anuais.<ano>.categorias; analises.anuais.<ano>.total; privacidade.minimo_perfil; privacidade.particoes_pequenas.",
    },
    2: {
        "como_interpretar": "Os pontos anuais resumem todos os registros válidos; os recortes por fase mostram heterogeneidade. As mudanças longitudinais comparam somente estudantes encontrados nos dois anos.",
        "populacao_periodo": "Registros anuais de 2022–2024 e pares correspondidos nas transições 2022→2023 e 2023→2024.",
        "fonte_exata": "reports/metricas_analises_negocio.json — analises.anuais.<ano>.indicadores.ida; analises.ida_fase; analises.longitudinal.<transição>.mudancas.ida.",
    },
    3: {
        "como_interpretar": "ρ positivo indica que valores maiores tendem a ocorrer juntos; use a intensidade registrada no artefato para distinguir associação fraca, moderada ou forte.",
        "populacao_periodo": "Pares completos dos registros anuais de 2022–2024; agregado ajustado por ano.",
        "fonte_exata": "reports/metricas_analises_negocio.json — analises.associacoes.<ano>.ieg x ida; analises.associacoes.<ano>.ieg x ipv; analises.associacoes.ajustado_ano.",
    },
    4: {
        "como_interpretar": "Observe as correlações de IAA com IDA e IEG. Valores próximos de zero indicam pouca concordância de ordenação, não erro em uma das avaliações.",
        "populacao_periodo": "Pares completos dos registros anuais de 2022–2024; agregado ajustado por ano.",
        "fonte_exata": "reports/metricas_analises_negocio.json — analises.associacoes.<ano>.iaa x ida; analises.associacoes.<ano>.iaa x ieg; analises.autoavaliacao.",
    },
    5: {
        "como_interpretar": "Cada ponto relaciona IPS no ano de origem à mudança posterior de IDA ou IEG. Correlações próximas de zero não sustentam um padrão monotônico útil.",
        "populacao_periodo": "Estudantes correspondidos e com o par de medidas disponível em 2022→2023 e 2023→2024.",
        "fonte_exata": "reports/metricas_analises_negocio.json — analises.longitudinal.<transição>.ips.<ida|ieg>.associacao; .sensibilidade; .perfis.",
    },
    6: {
        "como_interpretar": "ρ resume se IPP e IAN ordenam os registros de forma parecida. As tabelas de perfis mostram combinações alinhadas e contrastantes sem criar diagnóstico.",
        "populacao_periodo": "Registros de 2023 e 2024 com IPP e IAN disponíveis; IPP é estruturalmente ausente em 2022.",
        "fonte_exata": "reports/metricas_analises_negocio.json — analises.ipp.<ano>.ipp x ian; analises.ipp.<ano>.perfis; analises.ipp.<ano>.mediana_ipp.",
    },
    7: {
        "como_interpretar": "Compare o valor absoluto de ρ dentro de cada ano. O maior valor aponta a associação contemporânea mais forte, não um fator causal isolado.",
        "populacao_periodo": "Pares completos por indicador nos registros anuais de 2022, 2023 e 2024.",
        "fonte_exata": "reports/metricas_analises_negocio.json — analises.ipv.<ano>.associacoes; analises.ipv.<ano>.por_fase; analises.longitudinal.<transição>.ipv_futuro.",
    },
    8: {
        "como_interpretar": "Cada perfil combina indicadores abaixo/acima da mediana anual. Compare médias somente entre perfis publicáveis do mesmo ano; o INDE já incorpora esses componentes.",
        "populacao_periodo": "Casos completos e perfis com pelo menos o mínimo publicável em 2022, 2023 e 2024.",
        "fonte_exata": "reports/metricas_analises_negocio.json — analises.inde.<ano>.criterio; .n_completos; .medianas; .perfis_publicados.",
    },
    9: {
        "como_interpretar": "Compare desenvolvimento e teste temporal, principalmente o recall: ele mede a parcela dos eventos reais que foi sinalizada. Brier menor indica probabilidades mais próximas dos desfechos.",
        "populacao_periodo": "Desenvolvimento OOF na transição 2022→2023 e teste temporal congelado em 2023→2024; os tamanhos das amostras e eventos estão na tabela.",
        "fonte_exata": "reports/metricas_analises_negocio.json — modelo.oof; modelo.temporal; modelo.diferencas; modelo.limiar. Origem espelhada: reports/metricas_modelagem.json.",
    },
    10: {
        "como_interpretar": "As barras separam avanço, estabilidade e recuo na ordem das Pedras entre dois registros do mesmo estudante.",
        "populacao_periodo": "Pares com Pedra reconhecida nos dois anos nas transições 2022→2023 e 2023→2024; os denominadores estão na tabela.",
        "fonte_exata": "reports/metricas_analises_negocio.json — analises.pedras.<ano>.distribuicao; analises.longitudinal.<transição>.pedras_evolucao; .pedras_transicoes.",
    },
    11: {
        "como_interpretar": "A primeira parte mostra cobertura e perdas de correspondência; a segunda mostra mudança de distribuição entre coortes. Perda de correspondência não equivale automaticamente a evasão.",
        "populacao_periodo": "Coortes elegíveis de origem nas transições 2022→2023 e 2023→2024, além dos registros anuais de 2022–2024; os denominadores estão na tabela.",
        "fonte_exata": "reports/metricas_analises_negocio.json — analises.perdas.<transição>.distribuicao; .desfecho; .perfis; modelo.distribuicao.numericos; analises.ida_fase.",
    },
}


def construir_perguntas_com_respostas(
    analises: dict, modelo: dict, privacidade: dict | None = None
) -> dict[int, dict]:
    """Combina o texto estático de `PERGUNTAS_NEGOCIO` com a resposta
    numérica extraída em tempo de execução de `analises`/`modelo` (ambos já
    carregados de `reports/metricas_analises_negocio.json`)."""
    resultado = {}
    for item in PERGUNTAS_NEGOCIO:
        numero = item["numero"]
        extrator = _EXTRATORES[numero]
        numeros = extrator(analises, modelo, privacidade)
        resultado[numero] = {**item, **METADADOS_ANALISE[numero], **numeros}
    return resultado


# ---------------------------------------------------------------------------
# Idade, notas e IDA — explicação acessível (aba "Entenda os indicadores")
# ---------------------------------------------------------------------------

EXPLICACAO_IDADE_FASE_DEFASAGEM = (
    "**Como idade, fase e defasagem se relacionam.** Institucionalmente, cada "
    "fase da Passos Mágicos corresponde a uma faixa etária esperada (ex.: "
    "Alfa para 7–8 anos, Fase 1 para 8–9 anos, e assim por diante) — isso "
    "ajuda a instituição a definir a **fase ideal** de cada estudante. A "
    "**defasagem** é a diferença entre a fase em que o(a) estudante "
    "efetivamente está e essa fase ideal. A ficha recebe a idade para mostrar "
    "uma sugestão documental, sempre exige confirmação humana da fase ideal "
    "e calcula fase atual menos fase ideal. A idade não é enviada ao modelo."
)
EXPLICACAO_NOTAS_IDA = (
    "**Como as notas participam do IDA.** Segundo a metodologia da própria "
    "Passos Mágicos, o IDA (Indicador de Aprendizagem) é composto a partir "
    "das notas de Matemática, Português e Inglês. Na ficha, o usuário pode "
    "informar o IDA institucional ou calcular (Matemática + Português + "
    "Inglês) / 3. As notas brutas ficam fora da entrada do modelo."
)
EXPLICACAO_AGREGADO_VS_DETALHE = (
    "**O que se perde ao usar só o IDA.** Um valor agregado (como o IDA) "
    "sempre esconde parte do detalhe: um(a) estudante forte em Português e "
    "fraco em Matemática pode ter o mesmo IDA que o perfil inverso. Por "
    "por isso a ficha registra também as notas usadas no cálculo e a idade "
    "usada na sugestão. O modelo continua recebendo somente o IDA calculado "
    "e a fase/defasagem confirmadas, nunca esses dados brutos."
)
EXPLICACAO_OBSERVACAO_ANUAL_PAR_LONGITUDINAL = (
    "**Observação anual** é o registro de um(a) estudante em um único ano "
    "(ex.: os dados de 2022). **Par longitudinal** é quando o mesmo RA é "
    "encontrado em dois anos consecutivos (ex.: 2022 e 2023) — só esses "
    "pares entram nas análises que comparam mudança ao longo do tempo; "
    "quem aparece em só um dos dois anos não entra nessas comparações."
)
EXPLICACAO_PEDRAS = (
    "**O que são as Pedras.** A Passos Mágicos classifica cada estudante em "
    "uma \"Pedra\" (Quartzo, Ágata, Ametista ou Topázio) a partir da faixa em "
    "que o INDE se encontra — é uma forma de resumir o índice geral em "
    "categorias, não uma fase escolar."
)
EXPLICACAO_PONTO_DE_VIRADA = (
    "**Ponto de Virada, com prudência.** A Passos Mágicos usa o conceito de "
    "\"Ponto de Virada\" para descrever um momento de transformação na "
    "trajetória do(a) estudante, avaliado institucionalmente pelo indicador "
    "IPV. O IPV cumpre dois papéis nesta aplicação, e nenhum dos dois deve "
    "ser interpretado isoladamente: ele é um dos indicadores analisados no "
    "panorama exploratório (ver \"Panorama e resultados\"), onde sua "
    "associação com outros indicadores muda de ano para ano — o que não "
    "demonstra causalidade — e é, ao mesmo tempo, **um dos sete preditores "
    "diretos** usados pelo modelo em \"Avaliar um caso\", onde a estimativa "
    "gerada sempre depende da combinação dos sete preditores em conjunto, "
    "nunca do IPV sozinho."
)
