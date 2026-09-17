"""Auditoria agregada da base principal; valores individuais ficam em local_data."""
from __future__ import annotations
from collections import Counter
from pathlib import Path
import re
import pandas as pd

# Contratos dos testes existentes preservados, com implementação compartilhada.
from dados_pede import (
    ROOT, SOURCE, INDICATORS, classify_cell, classify_ra, column_mapping,
    defas_category_counts, extract_year, header_metadata, ian_expected,
    normalize_ra, parse_phase, parse_phase_detail, prepare_records, read_frames,
    read_sheet_dataframe, record_type_summary, safe_parse_int, json_value,
)
from rastreabilidade import (
    sha256_file, find_source_files, compare_inventories, start_run, finish_run,
    write_json, write_jsonl,
)


def operational_column_range(column: str):
    return (0.0, 10.0) if re.fullmatch(r"(?:IAN|IDA|IEG|IAA|IPS|IPP|IPV|INDE)(?:\s+\d{2,4})?", column.strip(), re.I) else None


def full_column_audit(frames: dict) -> tuple[dict, list[dict]]:
    result, details = {}, []
    for sheet, frame in frames.items():
        types, columns = record_type_summary(frame), {}
        matrix = frame.to_numpy(dtype=object, copy=False)
        for position, column in enumerate(frame.columns):
            states, errors, numbers = Counter(), Counter(), []
            limits, outliers = operational_column_range(column), 0
            for offset, value in enumerate(matrix[:, position]):
                cell_type = frame.attrs["cell_metadata"][column][offset]["tipo_excel"]
                info = classify_cell(value, cell_type)
                states[info["status"]] += 1
                number = info["numero"]
                outside = number is not None and limits is not None and not limits[0] <= number <= limits[1]
                outliers += int(outside)
                if number is not None:
                    numbers.append(number)
                if cell_type == "e":
                    errors[str(value)] += 1
                if number is None or outside or info["status"] == "numero_em_texto":
                    details.append({"aba": sheet, "linha_origem": frame.attrs["source_rows"][offset],
                                    "coluna_interna": column, "valor_original": json_value(value),
                                    "tipo_excel": cell_type, **info, "fora_faixa_operacional": bool(outside)})
            columns[column] = {"linhas_examinadas": len(frame), "tipos": types[column],
                               "estados": dict(states), "erros_excel": dict(errors),
                               "numericos_disponiveis": len(numbers), "zeros_numericos": sum(n == 0 for n in numbers),
                               "minimo": min(numbers, default=None), "maximo": max(numbers, default=None),
                               "faixa_operacional": limits, "fora_faixa_operacional": outliers,
                               "regra_documental": "docs/evidencias_documentais.md; 0–10 é sinalização operacional"}
        result[sheet] = columns
    return result, details


def indicator_quality(records: list[dict]) -> list[dict]:
    result = []
    for year in (2022, 2023, 2024):
        subset = [r for r in records if r["ano_referencia"] == year]
        for indicator in INDICATORS:
            field = indicator.lower()
            states = Counter(r[field + "_status"] for r in subset)
            reasons = Counter(r[field + "_motivo_indisponibilidade"] for r in subset
                              if r[field + "_motivo_indisponibilidade"] is not None)
            numbers = [r[field + "_numerico"] for r in subset if r[field + "_numerico"] is not None]
            result.append({"ano": year, "indicador": indicator, "total": len(subset), "estados": dict(states),
                           "motivos": dict(reasons), "disponiveis": len(numbers), "indisponiveis": len(subset) - len(numbers),
                           "zeros": sum(v == 0 for v in numbers),
                           "fora_faixa_operacional": sum(r[field + "_fora_faixa_operacional"] is True for r in subset),
                           "minimo": min(numbers, default=None), "maximo": max(numbers, default=None)})
    return result


def record_summary(frames: dict, records: list[dict]) -> dict:
    result = {}
    for sheet, frame in frames.items():
        subset = [r for r in records if r["aba_origem"] == sheet]
        annual = {"registros": len(subset), "colunas": len(frame.columns),
                  "linha_cabecalho": frame.attrs["header_row"],
                  "primeira_linha_dados": min(frame.attrs["source_rows"], default=None),
                  "ultima_linha_dados": max(frame.attrs["source_rows"], default=None),
                  "linhas_fisicas_sem_registro": frame.attrs["physical_max_row"] - len(frame) - 1,
                  "cabecalhos_repetidos": [m for m in frame.attrs["header_metadata"] if m["repetido"]],
                  "ra_status": dict(Counter(r["ra_status"] for r in subset)),
                  "registros_ra_ano_duplicado": sum(r["ra_ano_duplicado"] for r in subset),
                  "defasagem": defas_category_counts(pd.Series([r["defasagem_registrada"] for r in subset])),
                  "fases_extraidas": dict(sorted(Counter(str(r["fase_extraida"]) for r in subset).items())),
                  "flags_qualidade": dict(Counter(flag for r in subset for flag in r["flags_qualidade"]))}
        for field in ("fase_status", "fase_ideal_status", "data_nascimento_status", "idade_status"):
            annual[field] = dict(Counter(r[field] for r in subset))
        for field, label in (("ian_divergente_defasagem", "ian_vs_defasagem"),
                             ("defasagem_divergente_calculada", "defasagem_vs_fases")):
            annual[label] = {"concordantes": sum(r[field] is False for r in subset),
                             "discordantes": sum(r[field] is True for r in subset),
                             "nao_comparaveis": sum(r[field] is None for r in subset)}
        result[str(extract_year(sheet))] = annual
    return result


def pair_records(records: list[dict], origin: int, target: int, how: str = "inner") -> pd.DataFrame:
    # O índice apenas localiza o registro já associado ao RA; não vincula alunos.
    sides = []
    for year in (origin, target):
        rows = [{"RA": r["ra"], "record_index": i} for i, r in enumerate(records)
                if r["ano_referencia"] == year and r["ra_status"] == "valido"]
        side = pd.DataFrame(rows, columns=["RA", "record_index"])
        if side["RA"].duplicated().any():
            raise ValueError(f"RA duplicado no ano {year}; junção bloqueada, registros preservados")
        sides.append(side)
    return sides[0].merge(sides[1], on="RA", how=how, suffixes=("_origem", "_destino"),
                          validate="one_to_one", indicator=True)


def transition_summary(records: list[dict], origin: int, target: int) -> tuple[dict, list[dict]]:
    pairs = pair_records(records, origin, target, how="left")
    result, details = {}, []
    for label in ("todas_fases", "fases_0_a_7"):
        counts, phase_counts, found_phase_counts = Counter(), Counter(), Counter()
        for row in pairs.to_dict("records"):
            left = records[int(row["record_index_origem"])]
            d, phase = left["defasagem_registrada"], left["fase_extraida"]
            if d is None or d < 0 or (label == "fases_0_a_7" and (phase is None or not 0 <= phase <= 7)):
                continue
            counts["eligible_count"] += 1
            phase_counts[str(phase)] += 1
            found = row["_merge"] == "both"
            right = records[int(row["record_index_destino"])] if found else None
            future = right["defasagem_registrada"] if found else None
            if not found:
                counts["not_found_in_destination_count"] += 1
            else:
                counts["with_dest_count"] += 1
                found_phase_counts[str(phase)] += 1
                if future is None:
                    counts["found_with_missing_or_invalid_defas_count"] += 1
                else:
                    counts["dest_defasado_count" if future < 0 else "dest_em_fase_count" if future == 0 else "dest_adiantado_count"] += 1
            details.append({"ano_origem": origin, "ano_destino": target, "recorte_descritivo": label,
                            "ra": left["ra"], "linha_origem": left["linha_origem"],
                            "linha_destino": right["linha_origem"] if right else None,
                            "destino_observado": found, "defasagem_futura": future,
                            "defasagem_futura_binaria": None if future is None else int(future < 0)})
        keys = ("eligible_count", "with_dest_count", "not_found_in_destination_count",
                "found_with_missing_or_invalid_defas_count", "dest_defasado_count", "dest_em_fase_count", "dest_adiantado_count")
        result[label] = {k: counts[k] for k in keys}
        result[label].update(phase_origin_counts=dict(phase_counts),
                             phase_origin_found_counts=dict(found_phase_counts), cardinalidade="one_to_one",
                             ra_origem_invalido_fora_juncao=sum(r["ano_referencia"] == origin and r["ra_status"] != "valido" for r in records))
    return result, details


def year_pair_transition(origin_sheet: str, target_sheet: str, file_path: Path) -> dict:
    frames = read_frames(file_path)
    return transition_summary(prepare_records(frames, file_path), extract_year(origin_sheet), extract_year(target_sheet))[0]


def cadastral_divergence_summary(frames: dict, records: list[dict]) -> tuple[dict, list[dict]]:
    fields = ("nome", "ano_nascimento", "data_nascimento", "genero", "ano_ingresso", "instituicao_ensino", "escola")
    mappings = {extract_year(sheet): column_mapping(frame, extract_year(sheet)) for sheet, frame in frames.items()}
    result, details = {}, []
    for origin, target in ((2022, 2023), (2023, 2024)):
        pairs = pair_records(records, origin, target)
        aggregate = {}
        for field in fields:
            counts = Counter()
            for row in pairs.to_dict("records"):
                left, right = records[int(row["record_index_origem"])], records[int(row["record_index_destino"])]
                l_col, r_col = mappings[origin][field], mappings[target][field]
                l_cell, r_cell = left["originais"].get(l_col, {}), right["originais"].get(r_col, {})
                if field == "ano_nascimento":
                    l_cell = l_cell or left["originais"].get(mappings[origin]["data_nascimento"], {})
                    r_cell = r_cell or right["originais"].get(mappings[target]["data_nascimento"], {})
                l_norm, r_norm = left[field + "_padronizado"], right[field + "_padronizado"]
                l_raw, r_raw = l_cell.get("valor"), r_cell.get("valor")
                raw_comparable = l_raw is not None and r_raw is not None and str(l_raw).strip() != "" and str(r_raw).strip() != ""
                raw_diff = raw_comparable and (l_raw != r_raw or l_cell.get("tipo_python") != r_cell.get("tipo_python"))
                comparable = l_norm is not None and r_norm is not None
                normalized_diff = comparable and l_norm != r_norm
                representation_only = comparable and raw_diff and not normalized_diff
                for key, condition in (("pares_comparaveis_brutos", raw_comparable), ("diferencas_brutas", raw_diff),
                    ("pares_comparaveis_normalizados", comparable), ("divergentes_apos_normalizacao", normalized_diff),
                    ("somente_representacao", representation_only), ("nao_comparaveis_normalizados", not comparable)):
                    counts[key] += int(condition)
                if raw_diff or normalized_diff or not comparable:
                    details.append({"ano_origem": origin, "ano_destino": target, "ra": left["ra"],
                                    "campo": field, "linha_origem": left["linha_origem"], "linha_destino": right["linha_origem"],
                                    "valor_origem": l_raw, "valor_destino": r_raw,
                                    "normalizado_origem": l_norm, "normalizado_destino": r_norm,
                                    "status_origem": left[field + "_status"], "status_destino": right[field + "_status"],
                                    "somente_representacao": bool(representation_only),
                                    "divergente_apos_normalizacao": bool(normalized_diff) if comparable else None})
            aggregate[field] = dict(counts)
        result[f"{origin}->{target}"] = {"pares_ra": len(pairs), "cardinalidade": "one_to_one", "campos": aggregate}
    return result, details


def build_field_map(frames: dict) -> list[dict]:
    rows = []
    for sheet, frame in frames.items():
        year = extract_year(sheet)
        mapping, types = column_mapping(frame, year), record_type_summary(frame)
        for m in frame.attrs["header_metadata"]:
            col = m["nome_interno"]
            canonical = [k for k, v in mapping.items() if v == col]
            rows.append({"ano": year, "aba": sheet, **m, "tipos_observados": types[col]["observed_types"],
                         "contagens_tipos": types[col]["type_counts"],
                         "campo_derivado": ", ".join(canonical) if canonical else "somente originais (sem equivalência presumida)"})
    return rows


def check_references(summary: dict) -> list[dict]:
    """Referências são expectativas de conferência, nunca valores de saída."""
    rows = []
    def check(label, actual, expected):
        rows.append({"verificacao": label, "calculado": actual, "referencia": expected, "confere": actual == expected})
    for year, n, cols, no_gap in ((2022, 860, 42, 259), (2023, 1014, 48, 462), (2024, 1156, 50, 622)):
        annual = summary["anos"][str(year)]
        check(f"{year}: registros", annual["registros"], n)
        check(f"{year}: colunas", annual["colunas"], cols)
        check(f"{year}: D >= 0", annual["defasagem"]["D>=0"], no_gap)
    for pair, expected in (("2022->2023", 600), ("2023->2024", 765)):
        check(f"RA comuns {pair}", summary["cadastro"][pair]["pares_ra"], expected)
    check("RA nos três anos", summary["ra_nos_tres_anos"], 468)
    for pair, label, key, expected in (
        ("2022->2023", "todas_fases", "with_dest_count", 189), ("2022->2023", "todas_fases", "dest_defasado_count", 60),
        ("2023->2024", "todas_fases", "with_dest_count", 370), ("2023->2024", "todas_fases", "dest_defasado_count", 84),
        ("2023->2024", "fases_0_a_7", "eligible_count", 399), ("2023->2024", "fases_0_a_7", "with_dest_count", 311),
        ("2023->2024", "fases_0_a_7", "not_found_in_destination_count", 88), ("2023->2024", "fases_0_a_7", "dest_defasado_count", 84)):
        check(f"{pair} {label}: {key}", summary["transicoes"][pair][label][key], expected)
    for year, indicator, reason, expected in (
        (2023, "IPP", "erro_excel:#N/A", 76), (2024, "IPP", "erro_excel:#N/A", 102),
        (2023, "IDA", "celula_vazia", 76), (2023, "IDA", "erro_excel:#DIV/0!", 1),
        (2024, "IDA", "erro_excel:#DIV/0!", 101), (2024, "INDE", "erro_excel:#DIV/0!", 63),
        (2024, "INDE", "erro_excel:#N/A", 1), (2024, "INDE", "incluir", 38)):
        item = next(q for q in summary["indicadores"] if q["ano"] == year and q["indicador"] == indicator)
        check(f"{year} {indicator}: {reason}", item["motivos"].get(reason, 0), expected)
    return rows


def audit_frames(frames: dict, records: list[dict]) -> tuple[dict, dict]:
    columns, cell_details = full_column_audit(frames)
    cadastral, cadastral_details = cadastral_divergence_summary(frames, records)
    transitions, transition_details = {}, []
    for origin, target in ((2022, 2023), (2023, 2024)):
        aggregate, details = transition_summary(records, origin, target)
        transitions[f"{origin}->{target}"] = aggregate
        transition_details.extend(details)
    ra_sets = [{r["ra"] for r in records if r["ano_referencia"] == y and r["ra_status"] == "valido"} for y in (2022, 2023, 2024)]
    result = {"total_registros": len(records), "anos": record_summary(frames, records),
              "indicadores": indicator_quality(records), "colunas": columns, "cadastro": cadastral,
              "transicoes": transitions, "ra_nos_tres_anos": len(set.intersection(*ra_sets)), "mapa_campos": build_field_map(frames)}
    result["referencias"] = check_references(result)
    return result, {"celulas": cell_details, "cadastro": cadastral_details, "transicoes": transition_details}


def main() -> None:
    from relatorios_preparacao import write_field_map, report_body
    run = start_run("auditoria")
    frames = read_frames()
    records = prepare_records(frames)
    summary, details = audit_frames(frames, records)
    for kind, rows in details.items():
        write_jsonl(ROOT / "local_data" / "auditoria" / f"detalhes_{kind}.jsonl", rows)
    write_json(ROOT / "local_data/auditoria/resumo.json", summary)
    write_field_map(summary["mapa_campos"])
    metadata = finish_run(run, summary, {"registros_derivados_para_auditoria": len(records)},
                          [ROOT / "local_data/auditoria/resumo.json", ROOT / "docs/mapa_campos.md"])
    (ROOT / "reports/relatorio_auditoria_inicial.md").write_text(
        "# Auditoria inicial corrigida\n\n" + report_body(summary, metadata), encoding="utf-8")
    print(f"Auditoria: {len(records)} registros; referências: {sum(r['confere'] for r in summary['referencias'])}/{len(summary['referencias'])}; integridade: {metadata['source_integrity_preserved']}")


if __name__ == "__main__":
    main()
