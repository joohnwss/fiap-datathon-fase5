"""Coortes temporais sem treinamento; rastreabilidade individual somente local."""
from __future__ import annotations

import csv
import json
import math
from collections import Counter
from pathlib import Path

import pandas as pd

from auditoria_inicial import pair_records
from dados_pede import ROOT
from rastreabilidade import (start_run, finish_run, sha256_file, find_source_files, git_output,
                            write_jsonl, public_text_issues)
from relatorios_preparacao import table

TRANSITIONS = {"desenvolvimento": (2022, 2023), "teste_temporal": (2023, 2024)}
INDICATORS = ("ida", "ieg", "iaa", "ips", "ipv")
FEATURE_SOURCES = {**{name: name + "_numerico" for name in INDICATORS},
                   "fase_origem": "fase_extraida", "defasagem_origem": "defasagem_registrada"}
FEATURES = tuple(FEATURE_SOURCES)
PHASES = tuple(str(n) for n in range(8))
REFERENCE = {"desenvolvimento": (189, 60), "teste_temporal": (311, 84)}
BASE = "local_data/base_longitudinal.jsonl"
META = "reports/metadados_coortes.json"
REPORT = "reports/relatorio_coortes_modelagem.md"
AUDIT = "local_data/coortes_modelagem.jsonl"
SCHEMA = {
    "version": 1,
    "unit": "transicao_aluno_ano",
    "X": {name: {"source_field": source, "source_year": "ano_origem",
                  "type": "categorical" if name == "fase_origem" else "nullable_number"}
          for name, source in FEATURE_SOURCES.items()},
    "phase_categories": list(PHASES),
    "y": {"type": "nullable_binary", "positive": "D_destino < 0",
          "negative": "D_destino >= 0", "unknown": "destino ausente ou D_destino indisponivel"},
    "private_audit_key": ["ra", "ano_origem", "ano_destino"],
    "csv_columns": [*FEATURES, "y"],
    "jsonl_blocks": ["chave_privada", "X", "y", "metadados"],
    "alignment": "CSV e X/y seguem a ordem dos registros supervisionados do JSONL por coorte; sem indice exportado",
}
CRITERIA = {
    "origin": "RA valido e unico por ano; D_t >= 0; fase extraida entre 0 e 7 (ALFA=0)",
    "destination": "RA correspondente e defasagem registrada valida para rotular",
    "unknown": "preservado no JSONL, excluido dos CSV supervisionados",
    "features": "lista fechada; somente valores do registro de origem; fase categorica",
    "excluded": ["identificadores", "IAN", "INDE", "Pedra", "IPP", "fase ideal", "variaveis futuras",
                 "genero", "idade", "datas", "escola", "instituicao", "unidade", "textos administrativos"],
    "missing": "null no JSONL, campo vazio no CSV; sem imputacao, corte ou arredondamento",
    "split": "temporal fixo, sem embaralhamento; ordem por linha fisica de origem",
}


def load_prepared(root: Path = ROOT) -> list[dict]:
    """Consome a base validada, recusando entradas alteradas desde a preparação."""
    meta = json.loads((root / "reports/metadados_preparacao.json").read_text(encoding="utf-8"))
    for name in (BASE, "local_data/base_longitudinal.csv"):
        if meta["output_hashes"].get(name) != sha256_file(root / name):
            raise ValueError("Base longitudinal divergente dos metadados; execute a preparação")
    current = {f["relative_path"]: f["sha256"] for f in find_source_files(root / "DATATHON")}
    if not current or meta["source_hashes_before"] != current or meta["source_hashes_after"] != current:
        raise ValueError("Fontes divergentes da preparação longitudinal")
    return [json.loads(line) for line in (root / BASE).read_text(encoding="utf-8").splitlines()]


def origin_exclusion(record: dict) -> str | None:
    if record["ra_status"] != "valido" or not record["ra"]:
        return "ra_invalido"
    value = record["defasagem_registrada"]
    if value is None:
        return "defasagem_indisponivel"
    if value < 0:
        return "ja_defasado"
    phase = record["fase_extraida"]
    if phase in (8, 9):
        return f"fase_{phase}"
    if phase not in range(8):
        return "fase_nao_elegivel"
    return None


def origin_features(record: dict) -> dict:
    # Lista positiva: nenhum campo do destino é recebido nesta função.
    result = {name: record[source] for name, source in FEATURE_SOURCES.items()}
    result["fase_origem"] = str(result["fase_origem"])
    for name, value in result.items():
        if name != "fase_origem" and value is not None:
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
                raise ValueError("Campo numérico não validado na base longitudinal")
    return result


def validate_predictors(X: pd.DataFrame) -> None:
    if list(X.columns) != list(FEATURES):
        raise ValueError("X deve conter somente os sete preditores aprovados, na ordem do schema")
    if not isinstance(X.index, pd.RangeIndex) or X.index.start != 0 or X.index.step != 1:
        raise ValueError("X não pode usar identificadores no índice")
    if not isinstance(X["fase_origem"].dtype, pd.CategoricalDtype):
        raise ValueError("Fase de origem deve ser categórica")
    if list(X["fase_origem"].cat.categories) != list(PHASES) or X["fase_origem"].cat.ordered:
        raise ValueError("Domínio categórico de fase inválido")
    if X["fase_origem"].isna().any():
        raise ValueError("Fase indisponível em matriz supervisionada")


def supervised_matrices(rows: list[dict]) -> tuple[pd.DataFrame, pd.Series]:
    observed = [r for r in rows if r["y"] is not None]
    if any(list(r["X"]) != list(FEATURES) for r in rows):
        raise ValueError("Registro contém preditores não aprovados")
    X = pd.DataFrame([r["X"] for r in observed], columns=FEATURES)
    X["fase_origem"] = pd.Categorical(X["fase_origem"], categories=PHASES, ordered=False)
    for name in FEATURES:
        if name != "fase_origem":
            X[name] = pd.array(X[name], dtype="Float64")
    y = pd.Series([r["y"] for r in observed], name="y", dtype="Int64")
    validate_predictors(X)
    if not y.isin([0, 1]).all():
        raise ValueError("Alvo supervisionado inválido")
    return X, y


def coverage(rows: list[dict]) -> dict:
    return {name: {"total": len(rows), "disponiveis": sum(r["X"][name] is not None for r in rows),
                   "ausentes": sum(r["X"][name] is None for r in rows),
                   "motivos": dict(sorted(Counter(r["metadados"]["ausencias"][name]
                                       for r in rows if r["X"][name] is None).items()))}
            for name in FEATURES}


def build_cohorts(records: list[dict]) -> dict:
    cohorts = {}
    for name, (origin, target) in TRANSITIONS.items():
        # A junção consolidada valida unicidade em ambos os anos, inclusive fora do recorte.
        pairs = pair_records(records, origin, target, how="left")
        destinations = {int(p["record_index_origem"]):
                        records[int(p["record_index_destino"])] if p["_merge"] == "both" else None
                        for p in pairs.to_dict("records")}
        origins = sorted(((i, r) for i, r in enumerate(records) if r["ano_referencia"] == origin),
                         key=lambda item: (item[1]["aba_origem"], item[1]["linha_origem"]))
        exclusions = Counter({key: 0 for key in ("ra_invalido", "defasagem_indisponivel", "ja_defasado",
                                                 "fase_8", "fase_9", "fase_nao_elegivel")})
        rows = []
        for index, left in origins:
            reason = origin_exclusion(left)
            if reason:
                exclusions[reason] += 1
                continue
            right = destinations[index]
            future = right["defasagem_registrada"] if right is not None else None
            y = None if future is None else int(future < 0)
            status = "destino_ausente" if right is None else "defasagem_destino_indisponivel" if future is None else "observado"
            X = origin_features(left)
            rows.append({"chave_privada": {"ra": left["ra"], "ano_origem": origin, "ano_destino": target},
                         "X": X, "y": y,
                         "metadados": {"coorte": name, "arquivo_origem": left["arquivo_origem"],
                             "aba_origem": left["aba_origem"], "linha_origem": left["linha_origem"],
                             "aba_destino": right["aba_origem"] if right else None,
                             "linha_destino": right["linha_origem"] if right else None,
                             "status_alvo": status, "defasagem_destino_auditoria": future,
                             "ano_preditores": origin, "supervisionado": y is not None,
                             "ausencias": {feature: left[feature + "_motivo_indisponibilidade"]
                                           if feature in INDICATORS else None for feature in FEATURES},
                             "estados_indicadores": {feature: left[feature + "_status"] for feature in INDICATORS}}})
        observed = [r for r in rows if r["y"] is not None]
        states = Counter(r["metadados"]["status_alvo"] for r in rows)
        events = sum(r["y"] == 1 for r in observed)
        summary = {"ano_origem": origin, "ano_destino": target, "registros_origem": len(origins),
                   "exclusoes_sequenciais": dict(exclusions),
                   "fases_todos_registros_origem": dict(sorted(Counter(str(r["fase_extraida"]) for _, r in origins).items())),
                   "elegiveis_origem": len(rows), "encontrados": len(rows) - states["destino_ausente"],
                   "nao_encontrados": states["destino_ausente"],
                   "destino_sem_defasagem": states["defasagem_destino_indisponivel"],
                   "supervisionados": len(observed), "alvo_1": events, "alvo_0": len(observed) - events,
                   "alvo_desconhecido": len(rows) - len(observed),
                   "taxa_evento": events / len(observed) if observed else None,
                   "cobertura_elegiveis": coverage(rows), "cobertura_supervisionados": coverage(observed)}
        if summary["registros_origem"] != sum(exclusions.values()) + len(rows):
            raise ValueError("Fluxo de inclusão não fecha")
        X, y = supervised_matrices(rows)
        cohorts[name] = {"rows": rows, "X": X, "y": y, "summary": summary}
    development_ra = {r["chave_privada"]["ra"] for r in cohorts["desenvolvimento"]["rows"] if r["y"] is not None}
    for cohort in cohorts.values():
        for row in cohort["rows"]:
            row["metadados"]["participou_desenvolvimento"] = row["chave_privada"]["ra"] in development_ra
    return cohorts


def summarize(cohorts: dict) -> dict:
    test = [r for r in cohorts["teste_temporal"]["rows"] if r["y"] is not None]
    repeated = sum(r["metadados"]["participou_desenvolvimento"] for r in test)
    return {"coortes": {name: c["summary"] for name, c in cohorts.items()},
            "sobreposicao": {"teste_com_participacao_desenvolvimento": repeated,
                             "teste_sem_participacao_desenvolvimento": len(test) - repeated}}


def check_references(cohorts: dict) -> list[dict]:
    references = []
    for name, (size, events) in REFERENCE.items():
        for field, expected in (("supervisionados", size), ("alvo_1", events)):
            actual = cohorts[name]["summary"][field]
            references.append({"coorte": name, "campo": field, "calculado": actual,
                               "referencia": expected, "confere": actual == expected})
    if not all(r["confere"] for r in references):
        raise ValueError("Contagens das coortes divergem do contrato: " + json.dumps(references))
    return references


def csv_rows(cohort: dict, prefix: str) -> tuple[list[str], list[dict]]:
    columns = list(FEATURES) if prefix == "X" else ["y"] if prefix == "y" else [*FEATURES, "y"]
    rows = [{key: ({**r["X"], "y": r["y"]})[key] for key in columns}
            for r in cohort["rows"] if r["y"] is not None]
    return columns, rows


def write_outputs(root: Path, cohorts: dict) -> list[Path]:
    paths = []
    for name, cohort in cohorts.items():
        for prefix in ("coorte", "X", "y"):
            path = root / f"local_data/{prefix}_{name}.csv"
            path.parent.mkdir(parents=True, exist_ok=True)
            columns, rows = csv_rows(cohort, prefix)
            with path.open("w", encoding="utf-8", newline="") as stream:
                writer = csv.DictWriter(stream, fieldnames=columns)
                writer.writeheader()
                writer.writerows(rows)
            paths.append(path)
    write_jsonl(root / AUDIT, [r for c in cohorts.values() for r in c["rows"]])
    return paths + [root / AUDIT]


def validate_outputs(root: Path, cohorts: dict) -> dict:
    expected = [r for c in cohorts.values() for r in c["rows"]]
    actual = [json.loads(line) for line in (root / AUDIT).read_text(encoding="utf-8").splitlines()]
    if actual != expected:
        raise ValueError("JSONL das coortes diverge da base longitudinal")
    for name, cohort in cohorts.items():
        validate_predictors(cohort["X"])
        for prefix in ("coorte", "X", "y"):
            columns, rows = csv_rows(cohort, prefix)
            with (root / f"local_data/{prefix}_{name}.csv").open(encoding="utf-8", newline="") as stream:
                reader = csv.DictReader(stream)
                actual_rows = list(reader)
                if reader.fieldnames != columns:
                    raise ValueError("Colunas de coorte divergentes do schema")
            serialized = [{k: "" if v is None else str(v) for k, v in row.items()} for row in rows]
            if actual_rows != serialized:
                raise ValueError("CSV de coorte diverge dos valores ou da ordem esperada")
    return {"coortes_serializadas_conferidas": True, "X_sem_identificadores": True,
            "X_somente_variaveis_origem": True, "fase_categorica": True,
            "desconhecidos_fora_matrizes_supervisionadas": True, "separacao_temporal_preservada": True}


def report_body(cohorts: dict, started: str, validations: dict) -> str:
    summaries = [c["summary"] for c in cohorts.values()]
    sections = ["# Relatório das coortes de modelagem", "Documento regenerável e agregado; sem amostras individuais.",
                f"Início UTC: {started}. Comando: `python src/preparacao_coortes.py`.",
                "## Fluxo de inclusão e exclusão",
                "Exclusões sequenciais, na ordem abaixo, sem dupla contagem. Fases referem-se ao ano de origem."]
    flow = [("Registros na origem", [s["registros_origem"] for s in summaries])]
    for reason in summaries[0]["exclusoes_sequenciais"]:
        flow.append(("Exclusão: " + reason, [s["exclusoes_sequenciais"][reason] for s in summaries]))
    for field in ("elegiveis_origem", "encontrados", "nao_encontrados", "destino_sem_defasagem", "supervisionados",
                  "alvo_1", "alvo_0", "alvo_desconhecido"):
        flow.append((field, [s[field] for s in summaries]))
    flow.append(("Taxa de evento entre supervisionados", [f"{s['taxa_evento']:.2%}" if s["taxa_evento"] is not None else "não estimável" for s in summaries]))
    sections.append(table(["Etapa", "2022→2023: desenvolvimento", "2023→2024: teste temporal"],
                          [[label, *values] for label, values in flow]))
    sections += ["A distribuição abaixo considera todos os registros de origem, antes das exclusões sequenciais.",
                 table(["Ano de origem", "Fases: contagens"], [[s["ano_origem"], s["fases_todos_registros_origem"]] for s in summaries]),
                 "## Disponibilidade dos preditores",
                 "Valores do ano de origem, sem imputação. Ausências mantêm seu motivo; zeros observados permanecem zeros."]
    availability = []
    for s in summaries:
        for population in ("elegiveis", "supervisionados"):
            for feature, q in s["cobertura_" + population].items():
                availability.append([s["ano_origem"], population, feature, q["total"], q["disponiveis"], q["ausentes"], q["motivos"]])
    sections.append(table(["Ano", "População", "Preditor", "Total", "Disponíveis", "Ausentes", "Motivos"], availability))
    sections += ["## Separação de dados e validações",
                 "X contém somente `" + "`, `".join(FEATURES) + "`. A fase é categórica, com categorias 0 a 7 sem ordem estatística. "
                 "Os CSV não armazenam tipos: usar `supervised_matrices` para reconstruir X e y com os tipos do schema.",
                 "A chave privada (RA e anos), linhas físicas, estados de ausência e informações do destino para auditoria "
                 "ficam em blocos separados no JSONL. Somente o alvo utiliza a defasagem futura. "
                 "RA, nome e demais identificadores não pertencem às colunas nem ao índice de X. "
                 "IAN, INDE, Pedra, IPP, fase ideal, gênero, idade, datas, escola, instituição, unidade e textos administrativos estão fora de X.",
                 "A junção reutiliza a validação one_to_one. O JSONL mantém elegíveis com alvo desconhecido; "
                 "os CSV contêm apenas supervisionados, na mesma ordem por linha física. Não há embaralhamento entre anos. "
                 "As saídas são reabertas e comparadas integralmente aos valores de origem e à lista fechada de preditores.",
                 "As evidências estruturadas das validações e os hashes das saídas constam de `reports/metadados_coortes.json`.",
                 table(["Verificação", "Resultado"], [[key, value] for key, value in validations.items() if key != "referencias"]),
                 "## Comparação e limitações",
                 table(["Sobreposição no teste supervisionado", "Registros"], list(summarize(cohorts)["sobreposicao"].items())),
                 "Diferenças de cobertura, prevalência e perda de acompanhamento entre as transições são descritivas; "
                 "o teste permanece reservado e não orienta seleção de variáveis, algoritmo, hiperparâmetros ou limiar. "
                 "Ausências presentes apenas no teste não fornecem um padrão aprendível no desenvolvimento.",
                 "A equivalência curricular entre anos e o significado da fase 9 permanecem limitados pela documentação. "
                 "Fases 8/9 são excluídas pela fase de origem; uma fase diferente no destino não redefine a elegibilidade de origem. "
                 "INCLUIR não recebe conversão presumida. Não foram identificados conflitos metodológicos impeditivos: "
                 "a exigência de D futuro válido complementa a localização no destino, conforme o contrato.",
                 "Permanecem pendentes as análises das 11 perguntas, a comparação dos perfis de perda de acompanhamento, "
                 "o notebook e o pipeline de imputação/validação interna, a sensibilidade, a avaliação de equidade e o treinamento. "
                 "Nenhum modelo foi treinado e nenhum indicador foi imputado nesta etapa."]
    return "\n\n".join(sections) + "\n"


def validate_artifacts(root: Path, records: list[dict]) -> dict:
    meta = json.loads((root / META).read_text(encoding="utf-8"))
    cohorts = build_cohorts(records)
    references = check_references(cohorts)
    checks = validate_outputs(root, cohorts)
    if meta["summary"] != summarize(cohorts) or meta["cohort_schema"] != SCHEMA or meta["criteria"] != CRITERIA:
        raise ValueError("Metadados de coortes divergentes do cálculo ou schema")
    expected_paths = {AUDIT, REPORT} | {f"local_data/{p}_{n}.csv" for n in TRANSITIONS for p in ("coorte", "X", "y")}
    if set(meta["output_hashes"]) != expected_paths:
        raise ValueError("Inventário de saídas de coortes incompleto")
    for group in ("output_hashes", "input_hashes", "code_hashes", "test_hashes", "manual_document_hashes"):
        if not all(sha256_file(root / p) == digest for p, digest in meta[group].items()):
            raise ValueError("Hashes de coortes divergentes: " + group)
    current_sources = {f["relative_path"]: f["sha256"] for f in find_source_files(root / "DATATHON")}
    if meta["source_hashes_before"] != current_sources or meta["source_hashes_after"] != current_sources:
        raise ValueError("Fontes de coortes divergentes")
    if meta["validations"]["referencias"] != references:
        raise ValueError("Referências de coortes divergentes")
    return {**checks, "hashes_coortes_conferidos": True, "referencias_coortes_conferidas": len(references)}


def main() -> None:
    run = start_run("coortes")
    input_hashes = {p: sha256_file(ROOT / p) for p in (BASE, "local_data/base_longitudinal.csv", "reports/metadados_preparacao.json")}
    records = load_prepared(ROOT)
    cohorts = build_cohorts(records)
    references = check_references(cohorts)
    private_paths = [AUDIT] + [f"local_data/{p}_{n}.csv" for n in TRANSITIONS for p in ("coorte", "X", "y")]
    if set(git_output("check-ignore", "--", *private_paths).splitlines()) != set(private_paths):
        raise ValueError("Todos os artefatos individuais de coortes devem estar ignorados pelo Git")
    outputs = write_outputs(ROOT, cohorts)
    validations = validate_outputs(ROOT, cohorts)
    validations["referencias"] = references
    report = report_body(cohorts, run["started_at"], validations)
    if public_text_issues(report):
        raise ValueError("Relatório de coortes contém linguagem ou caminhos não portáteis")
    (ROOT / REPORT).write_text(report, encoding="utf-8")
    if any(sha256_file(ROOT / p) != digest for p, digest in input_hashes.items()):
        raise ValueError("Entradas longitudinais alteradas durante a geração das coortes")
    finish_run(run, summarize(cohorts), validations, outputs + [ROOT / REPORT],
               extra_metadata={"input_hashes": input_hashes, "cohort_schema": SCHEMA, "criteria": CRITERIA})
    for name, c in cohorts.items():
        s = c["summary"]
        print(f"{name}: {s['supervisionados']} pares; {s['alvo_1']} eventos; {s['alvo_desconhecido']} desconhecidos")


if __name__ == "__main__":
    main()
