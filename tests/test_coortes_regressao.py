import copy
import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd
from openpyxl import Workbook

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import dados_pede as d
import preparacao_coortes as c
import rastreabilidade as r


def prepared_fixture():
    """Casos de teste isolados, passando pelo mesmo leitor da base real."""
    wb = Workbook()
    headers = ["RA", "Fase", "Defasagem", "IDA", "IEG", "IAA", "IPS", "IPV", "IAN",
               "INDE 2022", "IPP", "Nome", "Gênero"]
    by_year = {
        2022: [["A", "ALFA (2º e 3º ano)", 0, None, 0, 7, "#N/A", 8, 10, 9, 4, "Pessoa A", "Menina"],
               ["B", "2L", 1, 6, 7, 8, 9, 10], ["C", "3", 0, 5, 5, 5, 5, 5],
               ["D", 8, 0], ["E", 9, 0], ["F", 2, -1], ["G", 2, None],
               [None, 2, 0], ["H", "INCLUIR", 0], ["I", 1, 0]],
        2023: [["I", 2, None], ["A", 1, -1, 99, 98, 97, 96, 95],
               ["B", 3, 0, 3, 4, 5, 6, 7], ["D", 8, -1], ["E", 9, -1]],
        2024: [["B", 9, 2, 88, 87, 86, 85, 84]],
    }
    frames = {}
    for i, (year, rows) in enumerate(by_year.items()):
        ws = wb.active if i == 0 else wb.create_sheet()
        ws.title = f"PEDE{year}"
        ws.append(headers)
        for row in rows:
            ws.append(row)
        frames[ws.title] = d.read_sheet_dataframe(ws)
    return d.prepare_records(frames)


class CoortesRegressionTests(unittest.TestCase):
    def setUp(self):
        self.records = prepared_fixture()
        self.cohorts = c.build_cohorts(self.records)

    def test_positive_negative_and_unknown_outcomes(self):
        rows = {row["chave_privada"]["ra"]: row for row in self.cohorts["desenvolvimento"]["rows"]}
        self.assertEqual(rows["A"]["y"], 1)
        self.assertEqual(rows["B"]["y"], 0)
        self.assertIsNone(rows["C"]["y"])
        self.assertEqual(rows["C"]["metadados"]["status_alvo"], "destino_ausente")
        self.assertIsNone(rows["I"]["y"])
        self.assertEqual(rows["I"]["metadados"]["status_alvo"], "defasagem_destino_indisponivel")
        self.assertEqual(self.cohorts["desenvolvimento"]["y"].tolist(), [1, 0])
        self.assertEqual(self.cohorts["teste_temporal"]["y"].tolist(), [0])

    def test_origin_eligibility_and_phase_exclusions(self):
        s = self.cohorts["desenvolvimento"]["summary"]
        self.assertEqual(s["registros_origem"], 10)
        self.assertEqual(s["elegiveis_origem"], 4)
        self.assertEqual(s["encontrados"], 3)
        self.assertEqual(s["nao_encontrados"], 1)
        self.assertEqual(s["destino_sem_defasagem"], 1)
        self.assertEqual(s["exclusoes_sequenciais"], {
            "ra_invalido": 1, "defasagem_indisponivel": 1, "ja_defasado": 1,
            "fase_8": 1, "fase_9": 1, "fase_nao_elegivel": 1})
        self.assertEqual(s["alvo_desconhecido"], 2)
        # A fase 9 no destino não altera a elegibilidade pela fase de origem.
        self.assertEqual(self.cohorts["teste_temporal"]["summary"]["supervisionados"], 1)

    def test_alpha_is_categorical_zero(self):
        X = self.cohorts["desenvolvimento"]["X"]
        self.assertEqual(X.loc[0, "fase_origem"], "0")
        self.assertIsInstance(X["fase_origem"].dtype, pd.CategoricalDtype)
        self.assertFalse(X["fase_origem"].cat.ordered)

    def test_missing_values_reasons_and_observed_zero_survive_serialization(self):
        cohort = self.cohorts["desenvolvimento"]
        row = cohort["rows"][0]
        self.assertIsNone(row["X"]["ida"])
        self.assertEqual(row["metadados"]["ausencias"]["ips"], "erro_excel:#N/A")
        self.assertEqual(row["X"]["ieg"], 0)
        self.assertTrue(pd.isna(cohort["X"].loc[0, "ida"]))
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            c.write_outputs(root, self.cohorts)
            self.assertTrue(all(c.validate_outputs(root, self.cohorts).values()))
            with (root / "local_data/X_desenvolvimento.csv").open(encoding="utf-8", newline="") as stream:
                first = next(csv.DictReader(stream))
            self.assertEqual(first["ida"], "")
            self.assertEqual(float(first["ieg"]), 0)

    def test_identifiers_and_all_unapproved_columns_are_rejected(self):
        X = self.cohorts["desenvolvimento"]["X"]
        self.assertEqual(list(X), ["ida", "ieg", "iaa", "ips", "ipv", "fase_origem", "defasagem_origem"])
        for forbidden in ("ra", "nome", "ian", "inde", "pedra", "ipp", "fase_ideal", "genero", "idade",
                          "data", "escola", "instituicao", "unidade", "ida_destino", "linha_origem", "y"):
            with self.subTest(field=forbidden):
                invalid = X.assign(**{forbidden: 1})
                with self.assertRaises(ValueError):
                    c.validate_predictors(invalid)
        indexed = X.copy()
        indexed.index = ["A", "B"]
        with self.assertRaises(ValueError):
            c.validate_predictors(indexed)

    def test_destination_features_cannot_change_origin_predictors(self):
        changed = copy.deepcopy(self.records)
        for row in changed:
            if row["ano_referencia"] == 2023:
                for feature in c.INDICATORS:
                    row[feature + "_numerico"] = -999
        rebuilt = c.build_cohorts(changed)
        pd.testing.assert_frame_equal(self.cohorts["desenvolvimento"]["X"], rebuilt["desenvolvimento"]["X"])
        self.assertEqual(self.cohorts["desenvolvimento"]["X"].loc[1, "ida"], 6)

    def test_fixed_temporal_split_and_stable_source_order(self):
        reordered = c.build_cohorts(list(reversed(self.records)))
        for name, years in c.TRANSITIONS.items():
            pd.testing.assert_frame_equal(self.cohorts[name]["X"], reordered[name]["X"])
            for row in reordered[name]["rows"]:
                self.assertEqual((row["chave_privada"]["ano_origem"], row["chave_privada"]["ano_destino"]), years)
                self.assertEqual(row["metadados"]["ano_preditores"], years[0])
        self.assertTrue(self.cohorts["teste_temporal"]["rows"][0]["metadados"]["participou_desenvolvimento"])

    def test_duplicate_ra_blocks_both_sides(self):
        for year in (2022, 2023, 2024):
            changed = copy.deepcopy(self.records)
            changed.append(copy.deepcopy(next(r for r in changed if r["ano_referencia"] == year and r["ra"] == "B")))
            with self.subTest(year=year), self.assertRaisesRegex(ValueError, "duplicado"):
                c.build_cohorts(changed)

    def test_tampered_csv_or_jsonl_is_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            c.write_outputs(root, self.cohorts)
            path = root / "local_data/X_desenvolvimento.csv"
            path.write_text(path.read_text(encoding="utf-8").replace("ida,", "ra,", 1), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Colunas"):
                c.validate_outputs(root, self.cohorts)
            c.write_outputs(root, self.cohorts)
            path = root / c.AUDIT
            rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
            rows[0]["y"] = 0
            r.write_jsonl(path, rows)
            with self.assertRaisesRegex(ValueError, "JSONL"):
                c.validate_outputs(root, self.cohorts)

    def test_references_fail_without_changing_counts(self):
        before = copy.deepcopy(c.summarize(self.cohorts))
        with self.assertRaisesRegex(ValueError, "divergem"):
            c.check_references(self.cohorts)
        self.assertEqual(before, c.summarize(self.cohorts))

    def test_recovery_only_copies_cohort_outputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "DATATHON").mkdir()
            (root / "reports").mkdir()
            outputs = c.write_outputs(root, self.cohorts)
            with patch.object(r, "ROOT", root), patch.object(r, "check_git_privacy", return_value={}), \
                 patch.object(r, "git_output", return_value=""):
                run = r.start_run("coortes")
                self.assertEqual(run["command"], "python src/preparacao_coortes.py")
                recovery = root / run["recovery_directory"]
                for path in outputs:
                    self.assertEqual(path.read_bytes(), (recovery / path.relative_to(root)).read_bytes())
                r.finish_run(run, c.summarize(self.cohorts), {}, outputs)
                self.assertFalse((root / "docs/inventario_fontes.md").exists())
                self.assertTrue((root / c.META).exists())

    def test_generation_metadata_and_independent_validation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "DATATHON").mkdir()
            (root / "reports").mkdir()
            r.write_jsonl(root / c.BASE, self.records)
            (root / "local_data/base_longitudinal.csv").write_text("base de teste\n", encoding="utf-8")
            r.write_json(root / "reports/metadados_preparacao.json", {})
            before = r.sha256_file(root / c.BASE)
            private = [c.AUDIT] + [f"local_data/{p}_{n}.csv" for n in c.TRANSITIONS for p in ("coorte", "X", "y")]
            with patch.object(c, "ROOT", root), patch.object(r, "ROOT", root), \
                 patch.object(c, "load_prepared", return_value=self.records), \
                 patch.object(c, "REFERENCE", {"desenvolvimento": (2, 1), "teste_temporal": (1, 0)}), \
                 patch.object(r, "check_git_privacy", return_value={}), patch.object(r, "git_output", return_value=""), \
                 patch.object(c, "git_output", return_value="\n".join(private)):
                c.main()
                self.assertTrue(c.validate_artifacts(root, self.records)["hashes_coortes_conferidos"])
                self.assertEqual(r.sha256_file(root / c.BASE), before)
                self.assertEqual(r.public_text_issues((root / c.REPORT).read_text(encoding="utf-8")), [])
                meta = json.loads((root / c.META).read_text(encoding="utf-8"))
                meta["summary"]["coortes"]["desenvolvimento"]["alvo_1"] += 1
                r.write_json(root / c.META, meta)
                with self.assertRaisesRegex(ValueError, "Metadados"):
                    c.validate_artifacts(root, self.records)

    @unittest.skipUnless(d.SOURCE.exists(), "Fonte privada indisponível")
    def test_real_source_counts_and_prepared_base_agree(self):
        records = d.prepare_records(d.read_frames())
        cohorts = c.build_cohorts(records)
        references = c.check_references(cohorts)
        self.assertEqual(len(references), 4)
        self.assertTrue(all(ref["confere"] for ref in references))
        prepared = d.ROOT / c.BASE
        if prepared.exists():
            local = [json.loads(line) for line in prepared.read_text(encoding="utf-8").splitlines()]
            local_cohorts = c.build_cohorts(local)
            for name in c.TRANSITIONS:
                self.assertEqual(cohorts[name]["rows"], local_cohorts[name]["rows"])


if __name__ == "__main__":
    unittest.main()
