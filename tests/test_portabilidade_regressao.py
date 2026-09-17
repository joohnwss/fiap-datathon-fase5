import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from openpyxl import Workbook

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import auditoria_inicial as a
import dados_pede as d
import rastreabilidade as r
import relatorios_preparacao as reports
import verificar_entrega as verification
from preparacao_longitudinal import validate_source_correspondence, write_flat_csv


MANUAL = ("registro_decisoes.md", "revisao_auditoria.md", "requisitos.md", "evidencias_documentais.md",
          "contrato_metodologico.md", "status_projeto.md")


def fixture(root):
    source = root / "DATATHON/BASE DE DADOS PEDE 2024 - DATATHON.xlsx"
    source.parent.mkdir()
    (root / "docs").mkdir()
    (root / "reports").mkdir()
    for name in MANUAL:
        (root / "docs" / name).write_text("Registro manual preservado.\n", encoding="utf-8")
    (root / "README.md").write_text("Estado do projeto preservado.\n", encoding="utf-8")
    wb = Workbook()
    for i, year in enumerate((2022, 2023, 2024)):
        ws = wb.active if i == 0 else wb.create_sheet()
        ws.title = f"PEDE{year}"
        ws.append(["Fase", "IAN", " RA ", "Fase ideal", "Defasagem"])
        ws.append(["2L", 10, "A", "FASE 2", 0])
    wb.save(source)
    frames = d.read_frames(source)
    return source, frames, d.prepare_records(frames, source)


class PortabilidadeRegressionTests(unittest.TestCase):
    def test_ra_outside_first_column_and_tampered_association(self):
        with tempfile.TemporaryDirectory() as tmp:
            source, _, records = fixture(Path(tmp))
            checks = validate_source_correspondence(records, source)
            self.assertEqual(checks["registros_conferidos_na_origem"], 3)
            self.assertEqual(checks["celulas_originais_conferidas"], 15)
            wrong = copy.deepcopy(records)
            wrong[0]["ra"] = "OTHER"
            with self.assertRaisesRegex(ValueError, "RA perdeu associação"):
                validate_source_correspondence(wrong, source)

    def test_phase_counts_include_eligible_missing_destination(self):
        records = [
            {"ano_referencia": 2023, "ra": "A", "ra_status": "valido", "fase_extraida": 2, "defasagem_registrada": 0, "linha_origem": 2},
            {"ano_referencia": 2023, "ra": "B", "ra_status": "valido", "fase_extraida": 3, "defasagem_registrada": 1, "linha_origem": 3},
            {"ano_referencia": 2023, "ra": "C", "ra_status": "valido", "fase_extraida": 8, "defasagem_registrada": 0, "linha_origem": 4},
            {"ano_referencia": 2024, "ra": "A", "ra_status": "valido", "fase_extraida": 3, "defasagem_registrada": -1, "linha_origem": 2}]
        result, _ = a.transition_summary(records, 2023, 2024)
        self.assertEqual(result["todas_fases"]["phase_origin_counts"], {"2": 1, "3": 1, "8": 1})
        self.assertEqual(result["fases_0_a_7"]["phase_origin_counts"], {"2": 1, "3": 1})
        for group in result.values():
            self.assertEqual(group["phase_origin_found_counts"], {"2": 1})
            self.assertEqual(sum(group["phase_origin_counts"].values()), group["eligible_count"])
            self.assertEqual(sum(group["phase_origin_found_counts"].values()), group["with_dest_count"])

    def test_history_is_optional_and_metadata_only(self):
        self.assertIsNone(r.historical_baseline({}))
        self.assertEqual(r.historical_comparison(None, {"file": "hash"})["status"], "nao_disponivel")
        previous = {"source_hashes_before": {"file": "old"}, "executed_at": "2026-09-15"}
        baseline = r.historical_baseline(previous)
        self.assertFalse(r.historical_comparison(baseline, {"file": "new"})["matches"])
        self.assertEqual(r.historical_baseline({"historical_baseline": baseline}), baseline)

    def test_new_run_portable_reports_and_manual_documents_preserved(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _, frames, records = fixture(root)
            before = {name: r.sha256_file(root / "docs" / name) for name in MANUAL}
            readme_before = r.sha256_file(root / "README.md")
            with patch.object(r, "ROOT", root), patch.object(reports, "ROOT", root), \
                 patch.object(r, "check_git_privacy", return_value={"dados_individuais_fora_versionamento": True}), \
                 patch.object(r, "git_output", return_value=""):
                run = r.start_run("auditoria")
                self.assertIsNone(run["historical_baseline"])
                summary, _ = a.audit_frames(frames, records)
                reports.write_field_map(summary["mapa_campos"])
                meta = r.finish_run(run, summary, {}, [root / "docs/mapa_campos.md"])
                rendered = reports.report_body(summary, meta)
                self.assertEqual(meta["command"], "python src/auditoria_inicial.py")
                self.assertEqual(meta["working_directory"], ".")
                self.assertIsNone(meta["historical_comparison"]["matches"])
                self.assertTrue(meta["source_integrity_preserved"])
                self.assertTrue(meta["manual_documents_preserved"])
                self.assertEqual(r.public_text_issues(rendered), [])
                self.assertEqual(r.public_text_issues(json.dumps(meta)), [])
                self.assertEqual(set(meta["manual_document_hashes"]),
                                 {"docs/" + name for name in MANUAL} | {"README.md"})
                self.assertEqual(meta["manual_document_hashes"]["README.md"], readme_before)
            self.assertEqual(before, {name: r.sha256_file(root / "docs" / name) for name in MANUAL})
            self.assertEqual(readme_before, r.sha256_file(root / "README.md"))
            self.assertEqual({p.name for p in (root / "docs").glob("*.md")}, set(MANUAL) | {"mapa_campos.md", "inventario_fontes.md"})

    def test_manual_mutation_during_run_is_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            fixture(root)
            with patch.object(r, "ROOT", root), patch.object(r, "check_git_privacy", return_value={}), \
                 patch.object(r, "git_output", return_value=""):
                run = r.start_run("auditoria")
                (root / "docs/registro_decisoes.md").write_text("Alterado", encoding="utf-8")
                with self.assertRaisesRegex(RuntimeError, "integridade"):
                    r.finish_run(run, {}, {}, [])

    def test_absolute_path_detector_and_portable_command(self):
        windows = "C:" + "/" + "Users/exemplo/python.exe"
        unix = "/" + "home/exemplo/projeto"
        self.assertIn("caminho_absoluto", r.public_text_issues(windows))
        self.assertIn("caminho_absoluto", r.public_text_issues(json.dumps({"command": windows.replace("/", "\\")})))
        self.assertIn("caminho_absoluto", r.public_text_issues(unix))
        self.assertEqual(r.public_text_issues("python src/auditoria_inicial.py\nworking_directory: ."), [])
        self.assertEqual(r.public_text_issues(Path(r.__file__).read_text(encoding="utf-8")), [])

    def test_public_language_accepts_academic_acronym_and_rejects_editorial_context(self):
        for text in ("modelo de IA", "IA aplicada à educação", "conversa pedagógica",
                     "O usuário informa os indicadores."):
            with self.subTest(text=text):
                self.assertEqual(r.public_text_issues(text), [])
        # A composição em tempo de execução evita exemplos proibidos no texto público.
        forbidden = ("Co" "dex", "Co" "pilot", "prom" "pt", "nesta conver" "sa",
                     "o usuário solici" "tou", "assistência automa" "tizada",
                     "o usuario solici" "tou", "assistencia automa" "tizada")
        for text in forbidden:
            for variant in (text, text.upper(), text.replace(" ", "\n")):
                with self.subTest(text=variant):
                    self.assertIn("contexto_editorial", r.public_text_issues(variant))

    def test_final_verification_runs_without_local_recovery(self):
        # Execução do verificador em projeto temporário sem histórico. Somente
        # as chamadas externas de Git/testes são simuladas; hashes, reabertura
        # e correspondência célula a célula são executados de fato.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source, _, records = fixture(root)
            jsonl = root / "local_data/base_longitudinal.jsonl"
            csv_path = root / "local_data/base_longitudinal.csv"
            r.write_jsonl(jsonl, records)
            write_flat_csv(csv_path, records)
            sources = {f["relative_path"]: f["sha256"] for f in r.find_source_files(root / "DATATHON")}
            for kind, path in (("auditoria", "artifacts_meta.json"), ("preparacao", "reports/metadados_preparacao.json")):
                r.write_json(root / path, {"kind": kind, "source_hashes_before": sources, "source_hashes_after": sources,
                    "code_hashes": {}, "test_hashes": {}, "output_hashes": {jsonl.relative_to(root).as_posix(): r.sha256_file(jsonl)},
                    "manual_document_hashes": {"docs/" + name: r.sha256_file(root / "docs" / name) for name in MANUAL},
                    "summary": {"referencias": [{"confere": True}]}})
            public = "artifacts_meta.json\nreports/metadados_preparacao.json\n"
            def external(args, **kwargs):
                return subprocess.CompletedProcess(args, 0, public if args[0] == "git" else "", "OK\n" if args[0] != "git" else "")
            with patch.object(verification, "ROOT", root), patch.object(verification.subprocess, "run", side_effect=external), \
                 patch.object(verification, "check_git_privacy", return_value={"dados_individuais_fora_versionamento": True}):
                verification.main()
            self.assertFalse((root / "local_recovery").exists())
            result = json.loads((root / "local_data/verificacao/resultado.json").read_text(encoding="utf-8"))
            self.assertTrue(result["checks"]["hashes_fontes_auditoria_e_preparacao"])
            self.assertTrue(all(h["status"] == "nao_disponivel" for h in result["historical_comparison"].values()))
            self.assertEqual(result["checks"]["celulas_originais_conferidas"], 15)
            self.assertEqual(r.public_text_issues((root / "reports/verificacao_final.md").read_text(encoding="utf-8")), [])


if __name__ == "__main__":
    unittest.main()
