"""Verificação final independente das saídas e execução registrada dos testes."""
from __future__ import annotations
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from dados_pede import ROOT
from rastreabilidade import (sha256_file, find_source_files, check_git_privacy, write_json,
                            historical_comparison, public_text_issues)
from preparacao_longitudinal import validate_source_correspondence, validate_outputs


def main():
    started = datetime.now(timezone.utc).isoformat()
    command = [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py", "-v"]
    # A saída do processo filho deve usar a mesma codificação da leitura,
    # inclusive no Windows, onde a codificação padrão pode ser diferente.
    tests = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, encoding="utf-8",
                           env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    log = ROOT / "local_data/verificacao/testes.txt"
    log.parent.mkdir(parents=True, exist_ok=True)
    log.write_text(tests.stdout + tests.stderr, encoding="utf-8")
    if tests.returncode:
        raise RuntimeError(f"Testes falharam; consulte {log}")
    meta_paths = [ROOT / "artifacts_meta.json", ROOT / "reports/metadados_preparacao.json"]
    metas = [json.loads(p.read_text(encoding="utf-8")) for p in meta_paths]
    current_sources = {f["relative_path"]: f["sha256"] for f in find_source_files(ROOT / "DATATHON")}
    checks = {"testes_exit_code": tests.returncode, "fontes_conferidas": len(current_sources),
              "hashes_fontes_auditoria_e_preparacao": all(m["source_hashes_before"] == m["source_hashes_after"] == current_sources for m in metas),
              "hashes_scripts_e_testes": all(sha256_file(ROOT / p) == digest for m in metas for group in ("code_hashes", "test_hashes") for p, digest in m[group].items()),
              "hashes_saidas": all(sha256_file(ROOT / p) == digest for m in metas for p, digest in m["output_hashes"].items()),
              "documentos_manuais_preservados": all(sha256_file(ROOT / p) == digest for m in metas for p, digest in m["manual_document_hashes"].items()),
              "referencias_reproduzidas": all(r["confere"] for m in metas for r in m["summary"]["referencias"]),
              "auditoria_e_preparacao_mesmos_agregados": metas[0]["summary"] == metas[1]["summary"],
              **check_git_privacy()}
    base = ROOT / "local_data/base_longitudinal.jsonl"
    records = [json.loads(line) for line in base.read_text(encoding="utf-8").splitlines()]
    checks.update(validate_source_correspondence(records, ROOT / "DATATHON/BASE DE DADOS PEDE 2024 - DATATHON.xlsx"))
    checks.update(validate_outputs(base, ROOT / "local_data/base_longitudinal.csv", records))
    # Projetos anteriores sem esta etapa continuam verificáveis; no projeto
    # com o módulo de coortes, a ausência de qualquer saída é uma falha.
    if (ROOT / "src/preparacao_coortes.py").exists():
        from preparacao_coortes import validate_artifacts
        checks.update(validate_artifacts(ROOT, records))
    history = {m["kind"]: historical_comparison(m.get("historical_baseline"), current_sources) for m in metas}
    public_paths = [ROOT / p for p in subprocess.run(["git", "ls-files", "--cached", "--others", "--exclude-standard"], cwd=ROOT,
                                                    capture_output=True, text=True, encoding="utf-8", check=True).stdout.splitlines()]
    # Procura valores individuais exatos de RA/nome em JSON; evita publicar amostras.
    private_values = {r["ra"] for r in records if r["ra"]} | {r["nome_padronizado"] for r in records if r["nome_padronizado"]}
    leaks = []
    for p in public_paths:
        if p.suffix.lower() not in {".md", ".json"}:
            continue
        content = p.read_text(encoding="utf-8").casefold()
        if any('"' + value.casefold() + '"' in content for value in private_values):
            leaks.append(p.relative_to(ROOT).as_posix())
    checks["amostras_individuais_em_documentos_publicos"] = len(leaks)
    checks["sem_amostras_individuais_detectadas"] = not leaks
    if any(value is False for value in checks.values()):
        write_json(ROOT / "local_data/verificacao/falha.json", checks)
        raise RuntimeError("Verificação final falhou; consulte local_data/verificacao/falha.json")
    completed = datetime.now(timezone.utc).isoformat()
    result = {"started_at": started, "completed_at": completed,
              "command": "python src/verificar_entrega.py",
              "test_command": 'python -m unittest discover -s tests -p "test_*.py" -v', "test_log_sha256": sha256_file(log),
              "historical_comparison": history,
              "checks": checks,
              "source_hashes_after_final_check": {f["relative_path"]: f["sha256"] for f in find_source_files(ROOT / "DATATHON")}}
    if result["source_hashes_after_final_check"] != current_sources:
        raise RuntimeError("Fontes alteradas durante a verificação final")
    from relatorios_preparacao import table
    report = "# Verificação final da entrega\n\nRegenerável por `python src/verificar_entrega.py`.\n\n"
    report += f"Início UTC: {started}. Fim UTC: {completed}.\n\nComando: `{result['command']}`.\n\n"
    report += table(["Verificação", "Resultado"], list(checks.items())) + "\n\n"
    report += "## Comparação histórica opcional\n\n"
    report += table(["Etapa", "Baseline disponível", "Coincide com fontes atuais"],
                    [[kind, h["available"], h["matches"]] for kind, h in history.items()]) + "\n\n"
    report += "A comparação histórica usa os hashes transportados nos metadados. Sem baseline, consta como não disponível; não é requisito para verificar a integridade atual. Nenhuma pasta histórica local é necessária.\n\n"
    report += f"Testes executados: `{result['test_command']}`. Saída completa local: `local_data/verificacao/testes.txt`. SHA-256: `{result['test_log_sha256']}`.\n\n"
    report += "```text\n" + tests.stderr.strip() + "\n```\n\n"
    report += "Os dados foram relidos e comparados célula a célula com a fonte após serialização. Os testes cobrem regressões técnicas; não confirmam regras curriculares ou decisões de negócio. A busca por amostras é uma checagem suplementar, não uma prova geral de anonimização.\n"
    # O relatório anterior será substituído: verifica-se a versão nova em memória.
    report_path = ROOT / "reports/verificacao_final.md"
    public_issues = {p.relative_to(ROOT).as_posix(): public_text_issues(p.read_text(encoding="utf-8"))
                     for p in public_paths if p != report_path and p.suffix.lower() in {".md", ".json", ".py", ".txt"}}
    public_issues[report_path.relative_to(ROOT).as_posix()] = public_text_issues(report)
    public_issues = {p: issues for p, issues in public_issues.items() if issues}
    if public_issues:
        write_json(ROOT / "local_data/verificacao/falha_publicacao.json", public_issues)
        raise RuntimeError("Conteúdo público não portátil; consulte local_data/verificacao/falha_publicacao.json")
    checks["artefatos_publicos_portateis"] = True
    report += "\nVerificação de conteúdo público: caminhos relativos e linguagem acadêmica, sem identificadores locais de usuário.\n"
    write_json(ROOT / "local_data/verificacao/resultado.json", result)
    report_path.write_text(report, encoding="utf-8")
    print(f"Verificação final aprovada: {len(records)} registros, {checks['celulas_originais_conferidas']} células, {len(current_sources)} fontes intactas.")


if __name__ == "__main__":
    main()
