"""Relatórios regeneráveis; somente contagens e metadados, sem exemplos pessoais."""
from dados_pede import ROOT


def table(headers, rows):
    def cell(value):
        return str(value).replace("|", "/").replace("\n", " ") if value is not None else "—"
    return "\n".join(["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
                     + ["| " + " | ".join(cell(v) for v in row) + " |" for row in rows])


def write_field_map(rows):
    text = """# Mapa de campos

Regenerável por `python src/auditoria_inicial.py` e `python src/preparacao_longitudinal.py`.
Todos os campos da fonte permanecem em `originais`, por nome interno único, com posição,
cabeçalho original exato, valor, tipo Python, tipo Excel e formato numérico.
Cabeçalhos repetidos são identificados antes da renomeação. Colunas históricas não
substituem os indicadores do ano de referência.

## Colunas de origem e correspondência

"""
    text += table(["Ano", "Posição", "Cabeçalho original", "Nome interno", "Repetido", "Tipos: contagens (todas as linhas)", "Campo derivado"],
                  [[r["ano"], r["posicao"], r["cabecalho_original"], r["nome_interno"], r["repetido"],
                    "; ".join(f"{k}: {v}" for k, v in r["contagens_tipos"].items()), r["campo_derivado"]] for r in rows])
    text += """

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
"""
    (ROOT / "docs/mapa_campos.md").write_text(text, encoding="utf-8")


def report_body(summary, metadata):
    sections = ["Documento **regenerável**. Relatório público agregado; dados individuais em `local_data/`, ignorada pelo Git.",
                f"Execução UTC: {metadata['executed_at']}. Comando: `{metadata['command']}`.",
                "## Procedimentos e correções",
                "Esta etapa contemplou auditoria e preparação dos dados. Os arquivos originais foram preservados. "
                "Cada execução mantém uma cópia local datada somente dos arquivos que serão regenerados. "
                "As bases históricas não foram combinadas à planilha principal.",
                "Foram preservadas as correções de ALFA=0, ano PEDE2022, cabeçalhos repetidos, RA, IAN por D registrado e junções one_to_one. "
                "Foram corrigidos códigos de fase com letra, classificação por tipo Excel, inspeção de todas as linhas, faixas dos oito indicadores, "
                "comparações cadastrais normalizadas e perda da linha física de origem. O registro manual de decisões foi preservado.",
                "## Resultado por ano"]
    sections.append(table(["Ano", "Registros", "Colunas", "D≥0", "Moderada", "Severa", "RA válidos", "RA/ano duplicados"],
        [[year, a["registros"], a["colunas"], a["defasagem"]["D>=0"], a["defasagem"]["moderada"], a["defasagem"]["severa"],
          a["ra_status"].get("valido", 0), a["registros_ra_ano_duplicado"]] for year, a in summary["anos"].items()]))
    sections.append(f"Total: **{summary['total_registros']} registros anuais**. RA presentes nos três anos: **{summary['ra_nos_tres_anos']}**. "
                    "Os totais anuais são observações, não uma contagem de alunos únicos no período.")
    sections.append("## Qualidade por ano e indicador")
    sections.append("Vazias, espaços e erros são estados diferentes. Números válidos abaixo incluem números em texto explicitamente interpretados. "
                    "Os extremos permanecem na base; 0–10 é apenas uma faixa operacional de sinalização.")
    sections.append(table(["Ano", "Indicador", "Numéricos", "Vazias", "Texto vazio/espaços", "Erros Excel", "INCLUIR", "Estrutural", "Outros indisponíveis", "Números em texto", "Zeros", "Fora 0–10"],
        [[q["ano"], q["indicador"], q["disponiveis"], q["estados"].get("celula_vazia", 0),
          q["estados"].get("texto_vazio", 0) + q["estados"].get("espacos", 0), q["estados"].get("erro_excel", 0),
          q["estados"].get("incluir", 0), q["estados"].get("ausencia_estrutural", 0),
          sum(n for k, n in q["estados"].items() if k not in {"numero_valido", "numero_em_texto", "celula_vazia", "texto_vazio", "espacos", "erro_excel", "incluir", "ausencia_estrutural"}),
          q["estados"].get("numero_em_texto", 0), q["zeros"], q["fora_faixa_operacional"]] for q in summary["indicadores"]]))
    sections.append(table(["Ano", "Indicador", "Motivos de indisponibilidade", "Mínimo numérico", "Máximo numérico"],
        [[q["ano"], q["indicador"], "; ".join(f"{k}: {n}" for k, n in q["motivos"].items()) or "nenhum", q["minimo"], q["maximo"]] for q in summary["indicadores"]]))
    sections.append("## Fases, IAN e defasagem: verificações separadas")
    sections.append(table(["Ano", "Fase: status e contagens", "Fase 9", "IAN×D: iguais/divergentes/não comparáveis", "D×(fase−ideal): iguais/divergentes/não comparáveis"],
        [[year, "; ".join(f"{k}: {n}" for k, n in a["fase_status"].items()), a["fases_extraidas"].get("9", 0),
          "/".join(str(a["ian_vs_defasagem"][k]) for k in ("concordantes", "discordantes", "nao_comparaveis")),
          "/".join(str(a["defasagem_vs_fases"][k]) for k in ("concordantes", "discordantes", "nao_comparaveis"))] for year, a in summary["anos"].items()]))
    sections.append("O segundo teste é aritmético sobre códigos extraídos. Concordância não confirma equivalência curricular nem resolve o significado da fase 9. "
                    "A regra do IAN vem da Tabela 41 do DOCX (imagem no parágrafo 23): D≥0→10, −2≤D<0→5, D<−2→2,5.")
    sections.append("## Correspondência e transições descritivas por RA")
    sections.append(table(["Transição", "Recorte na origem", "Elegíveis D≥0", "Encontrados", "Não encontrados", "Destino sem D válido", "D futuro<0"],
        [[pair, label, t["eligible_count"], t["with_dest_count"], t["not_found_in_destination_count"],
          t["found_with_missing_or_invalid_defas_count"], t["dest_defasado_count"]]
         for pair, groups in summary["transicoes"].items() for label, t in groups.items()]))
    sections.append("Todas as junções usam RA válido e `validate=\"one_to_one\"`; duplicidade bloqueia a junção e não é resolvida apagando registros. "
                    "Ausência de destino ou de D futuro gera desfecho desconhecido (null). Os recortes são conferências descritivas; a população do futuro modelo está definida em `docs/contrato_metodologico.md`.")
    sections.append("Nos metadados, `phase_origin_counts` contabiliza todos os elegíveis por fase de origem; "
                    "`phase_origin_found_counts` contabiliza somente os encontrados no destino. As somas correspondem, respectivamente, a elegíveis e encontrados.")
    sections.append("## Comparações cadastrais")
    sections.append(table(["Anos", "Campo", "Pares RA", "Diferenças brutas", "Só representação", "Divergências normalizadas", "Comparáveis normalizados", "Não comparáveis"],
        [[pair, field, group["pares_ra"], c["diferencas_brutas"], c["somente_representacao"], c["divergentes_apos_normalizacao"],
          c["pares_comparaveis_normalizados"], c["nao_comparaveis_normalizados"]]
         for pair, group in summary["cadastro"].items() for field, c in group["campos"].items()]))
    sections.append("Em ano de nascimento, a categoria representação também inclui granularidade: ano isolado versus data completa com o mesmo ano. "
                    "Não se conclui igualdade do dia/mês a partir dessa comparação. Datas ambíguas não são resolvidas pelo outro ano. "
                    "Mudança de instituição/escola pode ser real e não comprova erro de identidade; nomes nunca são chaves de ligação.")
    sections.append(table(["Ano", "Datas de nascimento: status", "Idade: status"],
        [[year, "; ".join(f"{k}: {n}" for k, n in a["data_nascimento_status"].items()),
          "; ".join(f"{k}: {n}" for k, n in a["idade_status"].items())] for year, a in summary["anos"].items()]))
    sections.append("## Conferência com as referências fornecidas")
    sections.append(table(["Verificação", "Calculado", "Referência", "Confere"],
                          [[r["verificacao"], r["calculado"], r["referencia"], "sim" if r["confere"] else "NÃO"] for r in summary["referencias"]]))
    mismatches = [r for r in summary["referencias"] if not r["confere"]]
    sections.append("Todas as referências foram reproduzidas por código." if not mismatches else "Há diferenças a investigar nas linhas marcadas NÃO; nenhuma referência foi aplicada como correção dos dados.")
    sections.append("## Validações e rastreabilidade")
    sections.append(table(["Verificação", "Resultado"], [[k, v] for k, v in metadata["validations"].items()]))
    sections.append(f"Fontes: **{metadata['inventory_count']} arquivos**, integridade antes/depois da execução: **{metadata['source_integrity_preserved']}**; "
                    f"Documentos manuais preservados: **{metadata['manual_documents_preserved']}**. "
                    f"Dados individuais fora do versionamento: **{metadata['privacy']['dados_individuais_fora_versionamento']}**.")
    sections.append(f"Inventário anterior disponível para esta etapa: {metadata['previous_inventory_exists']}. "
                    f"Diferença entre execuções: {metadata['inventory_diff_from_previous_run']}. "
                    "Esta comparação histórica é distinta da releitura dos hashes antes/depois da execução atual.")
    history = metadata["historical_comparison"]
    sections.append(f"Baseline histórico nos metadados disponível: **{history['available']}**; "
                    f"coincidência com as fontes atuais: **{history['matches'] if history['available'] else 'não avaliada'}**. "
                    "A comparação histórica é opcional e não depende de uma pasta de recuperação local. "
                    "A integridade da execução atual é verificada independentemente do baseline.")
    sections.append("Os testes unitários e a validação da base são verificações diferentes. A evidência da execução dos testes está em "
                    "`reports/verificacao_final.md`; metadados registram hashes dos scripts, testes, fontes e saídas. "
                    "Nenhuma execução de teste constitui validação externa das regras de negócio.")
    sections.append("## Pendências metodológicas e impacto")
    sections.append("- **Equivalência curricular:** a Tabela 4 do DOCX usa referências 2020/2021 e difere de rótulos atuais de ALFA/fase 1. A fase extraída não autoriza recalcular a ideal pela idade.\n"
                    "- **Fase 8 e fase 9:** há pesos e aplicabilidade diferentes para a fase 8 nos Quadros 2/3 e no esquema INDE; o significado da fase 9 e de INCLUIR permanece pendente. Os alunos e erros observados foram mantidos.\n"
                    "- **Faixas:** IAN possui regra explícita; IAA tem referência 0–10 no texto e na Tabela 40. Para os demais, a faixa operacional não comprova limites documentais em todos os anos. Extremos precisam de investigação.\n"
                    "- **Pedras e INDE:** limites do dicionário diferem da Figura 3 do DOCX; não houve reclassificação de pedras ou recomposição do INDE.\n"
                    "- **Indisponibilidade:** IPP é estruturalmente ausente em 2022; erros Excel e outros vazios nos demais anos não receberam causa presumida nem imputação.\n"
                    "- **Cadastro:** datas ambíguas, idades armazenadas como datas e divergências normalizadas permanecem sinalizadas; não há correção por suposição.\n"
                    "- **Risco futuro:** perda de seguimento e aplicabilidade dos indicadores podem alterar a população analisável. Alvo, recorte e estratégia temporal estão aprovados em `docs/contrato_metodologico.md`; as coortes são preparadas por `src/preparacao_coortes.py`, com evidências em `reports/relatorio_coortes_modelagem.md`. O treinamento permanece pendente.\n"
                    "- **Escopo:** auditoria e preparação concluídas nos limites das verificações registradas. Análises de negócio completas, notebook preditivo, apresentação, aplicação, publicação e vídeo pertencem às próximas etapas.")
    sections.append("Evidências textuais e visuais e suas localizações: `docs/evidencias_documentais.md`. "
                    "A revisão documental foi realizada em 15/09/2026 e contemplou seis páginas do enunciado, quatro do dicionário, nove de desvendando_passos e dez imagens do DOCX. "
                    "A inspeção das imagens extraídas do DOCX não é uma validação da sua paginação renderizada.")
    return "\n\n".join(sections) + "\n"
