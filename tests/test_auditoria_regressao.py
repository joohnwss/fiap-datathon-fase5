import sys
import tempfile
import unittest
from pathlib import Path

import pandas as pd
from openpyxl import Workbook

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import auditoria_inicial as auditoria


class AuditoriaRegressionTests(unittest.TestCase):
    def test_phase_labels_and_year(self):
        self.assertEqual(auditoria.parse_phase("ALFA"), 0)
        self.assertEqual(auditoria.parse_phase("Fase 7 (9 anos)"), 7)
        self.assertEqual(auditoria.parse_phase("Fase ideal 3 (7 anos)"), 3)
        self.assertEqual(auditoria.extract_year("PEDE2022"), 2022)

    def test_repeated_headers_keep_original_metadata(self):
        metadata = auditoria.header_metadata(["RA", "Destaque IPV", "Destaque IPV"])
        self.assertEqual(metadata[1]["cabecalho_original"], "Destaque IPV")
        self.assertEqual(metadata[2]["nome_interno"], "Destaque IPV_1")
        self.assertTrue(metadata[2]["repetido"])

    def test_ra_states_and_ian_expectation(self):
        self.assertEqual(auditoria.classify_ra(None), "ausente")
        self.assertEqual(auditoria.classify_ra("  "), "vazio_espacos")
        expected = auditoria.ian_expected(pd.Series([0, -1, -2, -2.1, None]))
        self.assertEqual(expected.iloc[:4].tolist(), [10.0, 5.0, 5.0, 2.5])
        self.assertTrue(pd.isna(expected.iloc[4]))

    def test_transition_rejects_duplicate_destination_ra(self):
        workbook = Workbook()
        first = workbook.active
        first.title = "PEDE2023"
        first.append(["RA", "Fase", "Defas"])
        first.append(["A", "ALFA", 0])
        second = workbook.create_sheet("PEDE2024")
        second.append(["RA", "Fase", "Defas"])
        second.append(["A", 1, 0])
        second.append(["A", 1, 0])
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "fixture.xlsx"
            workbook.save(path)
            with self.assertRaises(ValueError):
                auditoria.year_pair_transition("PEDE2023", "PEDE2024", path)


if __name__ == "__main__":
    unittest.main()
