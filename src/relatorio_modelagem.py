"""Relatório agregado da avaliação congelada, sem linhas de alunos."""
from relatorios_preparacao import table


def number(value):
    return "não estimável" if value is None else f"{value:.4f}"


def metric_table(rows):
    return table(["População", "n", "Eventos", "AP", "ROC-AUC", "Precisão", "Recall", "F1", "Brier", "Sinalizados"],
        [[name, m["n"], m["eventos"], *[number(m[k]) for k in ("average_precision", "roc_auc", "precisao", "recall", "f1", "brier")],
          m["previstos_risco"]] for name, m in rows])


def profile_table(profiles):
    rows = []
    for name, profile in profiles.items():
        if "numericos" not in profile:
            rows.append([name, "suprimido", "—", "—", "—", "—"])
            continue
        for col, v in profile["numericos"].items():
            rows.append([name, col, v["disponiveis"], v["ausentes"], number(v["media"]), number(v["mediana"])])
    return table(["Grupo", "Preditor", "Disponíveis", "Ausentes", "Média", "Mediana"], rows)


def render_report(frozen, r):
    config = frozen["configuracao"]
    comparison = r["comparacao_modelos"]
    winner = r["modelo"]
    winner_result = comparison[winner]
    rob = r["robustez"]
    sections = ["# Relatório de modelagem preditiva",
        "Documento agregado gerado por `python src/modelagem.py`. O registro de abertura bloqueia novas seleções e avaliações. "
        "Uma execução posterior apenas verifica a integridade dos artefatos existentes.",
        "## Desenho temporal",
        "Desenvolvimento: 2022→2023, 189 transições e 60 eventos. Teste temporal reservado: 2023→2024, 311 transições e 84 eventos. "
        "São elegíveis estudantes sem defasagem na origem e fase de 0 a 7. Alvo 1 indica entrada em defasagem no destino; "
        "alvo 0 indica permanência sem defasagem. Desfechos desconhecidos não integram as matrizes supervisionadas. "
        "A auditoria de contagens anterior não foi usada para decidir algoritmo, transformações ou limiar.",
        "## Pipeline e configurações",
        "Preditores, na ordem exigida: `" + "`, `".join(config["preditores"]) + "`. "
        "A lista fechada exclui identificadores, alvo, campos futuros e administrativos. Os números são imputados por mediana "
        "dentro de cada fold; uma coluna totalmente ausente no treino bloqueia o ajuste. Somente a logística padroniza os números. "
        "Fase usa one-hot de domínio 0–7, sem categoria descartada; categoria desconhecida gera vetor zero. "
        "Nenhuma ausência é convertida em zero. Não há indicadores de ausência: os 189 registros de desenvolvimento estão completos.",
        "Uma configuração por família, fixada antes do teste: Dummy de prevalência; logística regularizada com C=1; "
        "árvore com profundidade 3 e mínimo de 15 por folha; floresta com 200 árvores, profundidade 3, mínimo de 10 por folha "
        "e max_features=sqrt. A regularização e as folhas mínimas limitam a complexidade em apenas 60 eventos. "
        "Não houve busca ampla, balanceamento artificial, ajuste de calibração ou seleção adicional de preditores. Semente: 42.",
        "## Validação interna e seleção",
        "Cinco folds estratificados, com embaralhamento e semente 42, compartilhados pelos quatro modelos. "
        "Cada observação recebe uma probabilidade de um ajuste que não a utilizou; todas as transformações pertencem ao pipeline. "
        "A tabela usa o limiar próprio de cada candidato, selecionado nas respectivas probabilidades OOF pelo mesmo critério.",
        metric_table([(n, m["metricas"]) for n, m in comparison.items()]),
        table(["Modelo", "Limiar OOF", "AP por fold: média ± DP", "Brier por fold: média ± DP"],
            [[n, number(m["limiar"]), f"{m['dispersao']['average_precision']['media']:.4f} ± {m['dispersao']['average_precision']['dp']:.4f}",
              f"{m['dispersao']['brier']['media']:.4f} ± {m['dispersao']['brier']['dp']:.4f}"] for n, m in comparison.items()]),
        "Regra anterior ao teste: " + config["protocolo"]["selecao"],
        f"Modelo selecionado: **{winner}**. AP OOF {winner_result['metricas']['average_precision']:.4f}, "
        f"contra {comparison['dummy']['metricas']['average_precision']:.4f} do Dummy; "
        f"DP da AP entre folds {winner_result['dispersao']['average_precision']['dp']:.4f} e "
        f"Brier OOF {winner_result['metricas']['brier']:.4f}. A logística é a candidata interpretável de referência, "
        "mas a escolha segue o resultado calculado. A estabilidade e a calibração são descritas e entram nos desempates; "
        "não se declara superioridade estatística com cinco folds. As configurações completas estão no congelamento.",
        "As médias e desvios de todas as seis métricas, além das matrizes por fold, estão em `metricas_modelagem.json`. "
        "AP OOF agregada não é a média das AP dos folds. O Dummy pode apresentar AP OOF diferente da prevalência, "
        "pois as prevalências de treino variam ligeiramente entre folds. Métricas de classificação por fold usam "
        "o limiar escolhido no OOF completo: sua dispersão é descritiva. A seleção de modelo e limiar reutiliza o OOF; "
        "portanto essas métricas internas têm otimismo de seleção e não substituem o teste temporal.",
        "## Limiar e congelamento",
        config["protocolo"]["limiar"],
        f"Limiar: **{r['limiar']:.12f}**. OOF: precisão {r['oof']['metricas']['precisao']:.4f}, "
        f"recall {r['oof']['metricas']['recall']:.4f}, F1 {r['oof']['metricas']['f1']:.4f}; "
        f"{r['oof']['metricas']['previstos_risco']} classificados como risco. "
        f"Matriz [[VN, FP], [FN, VP]]: `{r['oof']['metricas']['matriz_confusao']}`.",
        f"Configuração gravada antes do ajuste completo e da leitura do teste em `{frozen['congelado_em']}`. "
        f"SHA-256 canônico: `{frozen['sha256']}`. `artifacts/configuracao_congelada.json` contém preditores, "
        "pré-processamento, algoritmos e hiperparâmetros, validação, escolha, sensibilidade, métricas OOF, limiares, "
        "sementes, versões e hashes das coortes e do código. `artifacts/avaliacao_temporal.json` registra a abertura "
        "posterior e os hashes das saídas. Configuração e fontes divergentes causam falha explícita.",
        "## Avaliação temporal única",
        metric_table([("Desenvolvimento OOF", r["oof"]["metricas"]), ("Teste temporal", r["temporal"]["metricas"])]),
        f"Prevalência no teste: {r['temporal']['metricas']['prevalencia']:.2%}; proporção classificada como risco: "
        f"{r['temporal']['metricas']['proporcao_risco']:.2%}. Matriz [[VN, FP], [FN, VP]]: "
        f"`{r['temporal']['metricas']['matriz_confusao']}`. A meta de recall é uma regra de escolha no desenvolvimento, "
        "não uma garantia no próximo ano. O resultado temporal não altera o pipeline ou o limiar.",
        table(["Métrica", "Teste menos OOF", "IC 95% no teste", "Reamostragens válidas / inválidas"],
            [[k, number(r["diferenca_temporal_menos_oof"][k]),
              " a ".join(number(v) for v in rob["intervalos"]["completo"][k]["ic95"]),
              f"{rob['intervalos']['completo'][k]['validas']} / {rob['intervalos']['completo'][k]['invalidas']}"]
             for k in r["diferenca_temporal_menos_oof"]]),
        "Bootstrap percentil de 2.000 reamostragens, semente 42, 95%, por transição/aluno do teste, sem estratificação. "
        "Pipeline e limiar ficam fixos. Amostras sem duas classes não estimam ROC-AUC; sem eventos não estimam AP/recall; "
        "sem sinalizados não estimam precisão. O descarte é por métrica, contado explicitamente. "
        "Os intervalos condicionam ao modelo treinado e não incluem incerteza do treino/seleção ou correlação institucional.",
        "## Precisão-recall e calibração",
        "![Curvas agregadas de precisão-recall e calibração](curvas_modelagem.png)",
        "A curva PR publicada usa envelope de precisão em 21 pontos fixos de recall, sem limiares ou probabilidades individuais. "
        "A AP oficial é calculada diretamente nas probabilidades, sem integrar esse envelope. Calibração utiliza até cinco "
        "faixas uniformes, fundindo adjacentes até ao menos 20 observações; sobra é fundida à última. "
        "São diagnósticos descritivos; não se recalibra usando o teste.",
        table(["População", "n na faixa", "Probabilidade média", "Fração de eventos"],
            [[pop, b["n"], number(b["probabilidade_media"]), number(b["fracao_eventos"])]
             for pop in ("oof", "temporal") for b in r[pop]["calibracao"]["grupos"]]),
        "## Robustez e cobertura",
        "Os recortes a seguir reutilizam o mesmo modelo avaliado e limiar; não há reajuste nos subgrupos.",
        metric_table(list(rob["grupos"].items())),
        "O desenvolvimento tem 189 casos completos; sua análise coincide com o OOF principal. "
        "A comparação de casos completos no teste muda a amostra, não demonstra isoladamente o efeito da imputação.",
        table(["Grupo", "Métrica", "IC 95%", "Válidas / inválidas"],
            [[g, k, " a ".join(number(v) for v in value["ic95"]) if value["ic95"] else "não estimável",
              f"{value['validas']} / {value['invalidas']}"]
             for g, scores in rob["intervalos"].items() if g != "completo" for k, value in scores.items()]),
        "104 pessoas do teste participaram do desenvolvimento e 207 não participaram. A diferença sem repetidos menos "
        "teste completo usa reamostragem pareada do teste e reaplicação da máscara em cada amostra. "
        "Não é um teste independente de diferença entre populações; há composição e sobreposição entre recortes.",
        table(["Métrica", "Sem repetidos menos completo"], [[k, number(v)] for k, v in rob["diferenca_sem_repetidos_menos_completo"].items()]),
        "### Sensibilidade sem defasagem de origem",
        "Definida pelo contrato e ajustada antes da abertura do teste. Usa o mesmo algoritmo/hiperparâmetros vencedor, "
        "remove defasagem apenas no ColumnTransformer e escolhe seu próprio limiar com OOF de desenvolvimento. "
        "Não participa da escolha do vencedor e não substitui o modelo principal.",
        metric_table([("Sem defasagem OOF", r["sensibilidade_sem_defasagem"]["oof"]["metricas"]),
                      ("Sem defasagem temporal", r["sensibilidade_sem_defasagem"]["temporal"])]),
        f"Limiar da sensibilidade: {r['sensibilidade_sem_defasagem']['oof']['limiar']:.12f}.",
        "### Perda de acompanhamento",
        "88 elegíveis de 2023 não foram encontrados em 2024; nenhum alvo foi atribuído. "
        f"Encontrados sem defasagem futura válida: {rob['perdas']['encontrados_sem_alvo']}. "
        "Comparam-se perfis de origem, sem estimar desempenho nos ausentes.",
        profile_table({"Sem destino": rob["perdas"]["sem_destino"], "Encontrados": rob["perdas"]["encontrados"]}),
        table(["Grupo", "Fase de origem (células <10 suprimidas)"],
            [[g, str(rob["perdas"][g].get("fase", {}))] for g in ("sem_destino", "encontrados")]),
        "### Mudança de distribuição",
        "Diferença padronizada = (média teste − média desenvolvimento) / raiz da média das duas variâncias. "
        "Usa somente valores observados. Não é teste causal nem critério de nova seleção.",
        table(["Preditor", "Média desenvolvimento", "Média teste", "Diferença padronizada", "Ausentes desenvolvimento / teste"],
            [[c, number(v["media_desenvolvimento"]), number(v["media_teste"]), number(v["diferenca_padronizada"]),
              f"{v['ausentes_desenvolvimento']} / {v['ausentes_teste']}"] for c, v in rob["distribuicao"]["numericos"].items()]),
        table(["População", "Fases (células <10 suprimidas)"],
            [[g, str(rob["distribuicao"][g]["fase"])] for g in ("desenvolvimento", "teste")]),
        "### Equidade descritiva",
        rob["equidade_genero"]["motivo"],
        "Fase é avaliada na origem, com limiar fixo. Exigem-se pelo menos 30 observações e 5 eventos e 5 não eventos por grupo. "
        "Outros grupos têm métricas e denominadores detalhados suprimidos. Comparações não demonstram equidade causal.",
        metric_table([(f"Fase {g}", v["metricas"]) for g, v in rob["equidade_fase"].items() if v["status"] == "estimado"]),
        table(["Fase", "Estado"], [[g, v["status"]] for g, v in rob["equidade_fase"].items()]),
        table(["Fase", "n na faixa", "Probabilidade média", "Fração de eventos"],
            [[g, b["n"], number(b["probabilidade_media"]), number(b["fracao_eventos"])]
             for g, v in rob["equidade_fase"].items() if v["status"] == "estimado" for b in v["calibracao"]["grupos"]]),
        "### Falsos positivos e falsos negativos",
        "Perfis agregados dos erros no teste. Células de fase com menos de 10 são suprimidas. "
        "Falsos positivos não significam necessidade pedagógica inexistente; o alvo cobre apenas a entrada em defasagem observada.",
        profile_table(rob["erros"]),
        "## Interpretabilidade",
        r["interpretabilidade"]["nota"],
        table(["Atributo transformado", r["interpretabilidade"]["tipo"]],
            [[k, number(v)] for k, v in sorted(r["interpretabilidade"]["valores"].items(), key=lambda item: -abs(item[1]))]),
        "As primeiras linhas têm maior magnitude absoluta no ajuste completo de desenvolvimento. "
        "Coeficientes positivos elevam o escore condicional e negativos o reduzem; para árvores, importâncias não fornecem direção. "
        "Correlação entre indicadores e a amostra pequena tornam magnitudes e rankings instáveis. "
        "Valores de fases pouco observadas não sustentam conclusões específicas.",
        "## Limitações e modelo operacional futuro",
        "Amostra de desenvolvimento pequena (60 eventos), um único corte temporal, perdas de acompanhamento, "
        "ausências que surgem apenas no teste, alunos repetidos e possíveis mudanças curriculares limitam generalização. "
        "A ausência de gênero nas coortes impede essa auditoria de equidade. Fases 8/9 e registros fora da elegibilidade "
        "não são cobertos. AP depende de prevalência e composição; probabilidades não representam diagnóstico. "
        "OOF pós-seleção é otimista e os intervalos bootstrap não capturam toda a incerteza. "
        "Nenhum resultado estabelece causalidade ou substitui avaliação pedagógica.",
        "`artifacts/modelo_avaliado.joblib` foi ajustado exclusivamente em 2022→2023. "
        "O modelo operacional com as duas transições não foi criado. Se for retreinado futuramente, deverá ter identificação "
        "própria e manter separadas as métricas oficiais deste modelo avaliado. Aplicação, notebook final e publicação são etapas posteriores.",
        "Referências técnicas: [imputação em pipelines](https://scikit-learn.org/stable/modules/impute.html) e "
        "[métricas de classificação](https://scikit-learn.org/stable/modules/model_evaluation.html)."]
    return "\n\n".join(sections) + "\n"


def plot_curves(root, result):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.2), layout="constrained")
    for population, label, color in (("oof", "Desenvolvimento OOF", "#2563a8"), ("temporal", "Teste temporal", "#ad542b")):
        curve = result[population]["curva_pr"]
        axes[0].step([x["recall"] for x in curve], [x["precisao_interpolada"] for x in curve], where="post", label=label, color=color)
        bins = result[population]["calibracao"]["grupos"]
        axes[1].plot([x["probabilidade_media"] for x in bins], [x["fracao_eventos"] for x in bins], "o-", label=label, color=color)
    axes[0].axhline(result["temporal"]["metricas"]["prevalencia"], color="gray", linestyle=":", label="Prevalência temporal")
    axes[1].plot([0, 1], [0, 1], "--", color="gray", label="Referência ideal")
    for ax, xlabel, ylabel in zip(axes, ("Recall", "Probabilidade média"), ("Precisão (envelope)", "Fração de eventos")):
        ax.set(xlabel=xlabel, ylabel=ylabel, xlim=(0, 1), ylim=(0, 1.02))
        ax.grid(alpha=.15)
        ax.legend(fontsize=8, loc="best")
    fig.savefig(root / "reports/curvas_modelagem.png", dpi=160)
    plt.close(fig)
