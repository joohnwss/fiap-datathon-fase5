"""Inventários, recuperação local e metadados reproduzíveis, sem dados pessoais."""
from __future__ import annotations
import hashlib
import importlib.metadata
import json
import platform
import shutil
import subprocess
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def find_source_files(base_dir: Path) -> list[dict]:
    return [{"relative_path": p.relative_to(base_dir).as_posix(), "size_bytes": p.stat().st_size,
             "sha256": sha256_file(p)} for p in sorted(base_dir.rglob("*")) if p.is_file()]


def compare_inventories(previous: dict, current: dict) -> dict:
    return {"adicionados": sorted(current.keys() - previous.keys()),
            "removidos": sorted(previous.keys() - current.keys()),
            "alterados": sorted(k for k in previous.keys() & current.keys() if previous[k] != current[k])}


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as stream:
        for row in rows:
            stream.write(json.dumps(row, ensure_ascii=False, allow_nan=False) + "\n")


def git_output(*args) -> str:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True,
                          encoding="utf-8", check=True).stdout.strip()


def check_git_privacy() -> dict:
    probes = ["local_data/base_longitudinal.jsonl", "local_recovery/probe.txt", "DATATHON/probe.txt"]
    ignored = git_output("check-ignore", "--", *probes).splitlines()
    tracked = git_output("ls-files", "--", "local_data", "local_recovery", "DATATHON").splitlines()
    result = {"diretorios_ignorados": sorted(ignored), "arquivos_individuais_rastreados": len(tracked),
              "dados_individuais_fora_versionamento": set(ignored) == set(probes) and not tracked}
    if not result["dados_individuais_fora_versionamento"]:
        raise RuntimeError("local_data, local_recovery e DATATHON precisam estar ignorados e sem arquivos rastreados")
    return result


def manual_hashes() -> dict:
    # Estes arquivos nunca são sobrescritos pelos scripts automáticos.
    return {str(p.relative_to(ROOT).as_posix()): sha256_file(p)
            for p in [ROOT / "docs/registro_decisoes.md", ROOT / "docs/revisao_auditoria.md", ROOT / "docs/requisitos.md",
                      ROOT / "docs/evidencias_documentais.md", ROOT / "docs/contrato_metodologico.md",
                      ROOT / "docs/status_projeto.md", ROOT / "README.md"]
            if p.exists()}


def historical_baseline(previous: dict) -> dict | None:
    """Transporta somente hashes e data; nenhuma dependência de cópias locais."""
    baseline = previous.get("historical_baseline")
    if baseline and baseline.get("source_hashes"):
        return {"source_hashes": baseline["source_hashes"], "recorded_at": baseline.get("recorded_at")}
    hashes = previous.get("source_hashes_before", previous.get("hashes"))
    return {"source_hashes": hashes, "recorded_at": previous.get("started_at", previous.get("executed_at"))} if hashes else None


def historical_comparison(baseline: dict | None, current: dict) -> dict:
    if not baseline or not baseline.get("source_hashes"):
        return {"available": False, "status": "nao_disponivel", "matches": None, "diff": None}
    hashes = baseline["source_hashes"]
    return {"available": True, "status": "comparado", "matches": hashes == current,
            "diff": compare_inventories(hashes, current)}


def public_text_issues(text: str) -> list[str]:
    """Detecta caminhos locais absolutos e vocabulário alheio ao relatório acadêmico."""
    patterns = {
        "caminho_absoluto": r"(?i)(?:(?<![\w\\])[a-z]:[\\/]|\\\\[a-z0-9_.-]+\\|(?<![\w:/])/(?:home|Users|tmp|var|usr|opt|mnt|private|workspace|root)(?:/|\\))",
        # Literais segmentados permitem verificar também o próprio código-fonte.
        "contexto_editorial": (r"(?i)\b(?:co" r"dex|co" r"pilot|prom" r"pt|"
                               r"nesta\s+conver" r"sa|o\s+usu[áa]rio\s+solici" r"tou|"
                               r"assist[êe]ncia\s+automa" r"tizada)\b"),
    }
    return [name for name, pattern in patterns.items() if re.search(pattern, text)]


def outputs_for_run(kind: str) -> list[str]:
    common = ["docs/inventario_fontes.md", "docs/mapa_campos.md", "local_data/auditoria/resumo.json"]
    common += [f"local_data/auditoria/detalhes_{name}.jsonl" for name in ("celulas", "cadastro", "transicoes")]
    return common + (["artifacts_meta.json", "reports/relatorio_auditoria_inicial.md"] if kind == "auditoria" else
                     ["reports/metadados_preparacao.json", "reports/relatorio_preparacao_inicial.md",
                      "local_data/base_longitudinal.jsonl", "local_data/base_longitudinal.csv"])


def start_run(kind: str) -> dict:
    privacy = check_git_privacy()
    started = now()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    recovery = ROOT / "local_recovery" / f"{stamp}_{kind}"
    recovery.mkdir(parents=True)
    for name in outputs_for_run(kind):
        source = ROOT / name
        if source.is_file():
            (recovery / name).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, recovery / name)
    inventory = find_source_files(ROOT / "DATATHON")
    hashes = {f["relative_path"]: f["sha256"] for f in inventory}
    meta_path = ROOT / ("artifacts_meta.json" if kind == "auditoria" else "reports/metadados_preparacao.json")
    previous = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.exists() else {}
    script = "auditoria_inicial" if kind == "auditoria" else "preparacao_longitudinal"
    run = {"kind": kind, "started_at": started, "command": f"python src/{script}.py",
           "working_directory": ".", "recovery_directory": recovery.relative_to(ROOT).as_posix(),
           "historical_baseline": historical_baseline(previous),
           "source_hashes_before": hashes, "inventory": inventory,
           "previous_inventory_exists": bool(previous.get("source_hashes_before", previous.get("hashes"))),
           "inventory_diff_from_previous_run": compare_inventories(previous.get("source_hashes_before", previous.get("hashes", {})), hashes),
           "manual_hashes_before": manual_hashes(), "git_before": git_output("status", "--short"),
           "privacy": privacy, "metadata_path": meta_path.relative_to(ROOT).as_posix()}
    write_json(recovery / "run_before.json", run)
    return run


def finish_run(run: dict, summary: dict, validations: dict, outputs: list[Path]) -> dict:
    after = {f["relative_path"]: f["sha256"] for f in find_source_files(ROOT / "DATATHON")}
    baseline = run.get("historical_baseline")
    metadata = {"regeneravel": True, "schema_version": 2, "kind": run["kind"], "started_at": run["started_at"],
                "executed_at": now(), "command": run["command"], "working_directory": run["working_directory"],
                "recovery_directory": run["recovery_directory"], "source_file": "DATATHON/BASE DE DADOS PEDE 2024 - DATATHON.xlsx",
                "inventory_count": len(after), "source_hashes_before": run["source_hashes_before"], "source_hashes_after": after,
                "source_integrity_preserved": run["source_hashes_before"] == after,
                "source_diff_during_run": compare_inventories(run["source_hashes_before"], after),
                "previous_inventory_exists": run["previous_inventory_exists"],
                "inventory_diff_from_previous_run": run["inventory_diff_from_previous_run"],
                "historical_baseline": baseline,
                "historical_comparison": historical_comparison(baseline, after),
                "manual_documents_preserved": run["manual_hashes_before"] == manual_hashes(),
                "manual_document_hashes": manual_hashes(), "privacy": check_git_privacy(),
                "python": platform.python_version(),
                "packages": {p: importlib.metadata.version(p) for p in ("pandas", "openpyxl", "pypdf", "python-docx")},
                "code_hashes": {p.relative_to(ROOT).as_posix(): sha256_file(p) for p in sorted((ROOT / "src").glob("*.py"))},
                "test_hashes": {p.relative_to(ROOT).as_posix(): sha256_file(p) for p in sorted((ROOT / "tests").glob("*.py"))},
                "output_hashes": {p.relative_to(ROOT).as_posix(): sha256_file(p) for p in outputs},
                "validations": validations, "summary": summary}
    write_json(ROOT / run["metadata_path"], metadata)
    # Metadados de preparação são agregados e devem poder ser versionados.
    inventory_lines = ["# Inventário das fontes", "", "Regenerável por qualquer um dos scripts de auditoria/preparação.",
                       "", f"Execução UTC: {metadata['executed_at']}", "", "| Arquivo relativo | Tamanho (bytes) | SHA-256 |", "| --- | ---: | --- |"]
    inventory_lines.extend(f"| {f['relative_path']} | {f['size_bytes']} | {f['sha256']} |" for f in run["inventory"])
    (ROOT / "docs/inventario_fontes.md").write_text("\n".join(inventory_lines) + "\n", encoding="utf-8")
    if not metadata["source_integrity_preserved"] or not metadata["manual_documents_preserved"]:
        raise RuntimeError("Falha de integridade; consulte os metadados e a recuperação local")
    return metadata
