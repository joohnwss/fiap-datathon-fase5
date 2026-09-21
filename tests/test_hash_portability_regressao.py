import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import analises_negocio as analyses
import modelagem as modeling
import rastreabilidade as trace


class HashPortabilityRegressionTests(unittest.TestCase):
    def test_lf_text_matches_hash_recorded_with_crlf(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sample.json"
            path.write_bytes(b'{"value": 1}\n{"value": 2}\n')
            expected = hashlib.sha256(path.read_bytes().replace(b"\n", b"\r\n")).hexdigest()
            self.assertTrue(trace.file_matches_sha256(path, expected))
            modeling.verify_hashes(Path(tmp), {path.name: expected})

    def test_crlf_text_matches_hash_recorded_with_lf(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sample.csv"
            path.write_bytes(b"column\r\nvalue\r\n")
            expected = hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()
            self.assertTrue(trace.file_matches_sha256(path, expected))
            modeling.verify_hashes(Path(tmp), {path.name: expected})

    def test_real_text_change_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sample.md"
            expected = hashlib.sha256(b"original\r\n").hexdigest()
            path.write_bytes(b"changed\n")
            self.assertFalse(trace.file_matches_sha256(path, expected))

    def test_binary_change_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sample.bin"
            expected = hashlib.sha256(b"payload\r\n").hexdigest()
            path.write_bytes(b"payload\n")
            self.assertFalse(trace.file_matches_sha256(path, expected))

    def test_real_change_in_input_model_or_output_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name in ("input.csv", "modelo.joblib", "output.json"):
                path = root / name
                path.write_bytes(b"original\r\n")
                expected = trace.sha256_file(path)
                path.write_bytes(b"changed\n")
                with self.subTest(path=name), self.assertRaisesRegex(ValueError, "Hash divergente"):
                    modeling.verify_hashes(root, {name: expected})

    def test_historical_code_hashes_are_preserved_and_do_not_bind_current_code(self):
        historical = {"src/modelagem.py": "1" * 64,
                      "src/relatorio_modelagem.py": "2" * 64}
        snapshot = historical.copy()
        trace.validate_historical_code_hashes(
            historical, ("src/modelagem.py", "src/relatorio_modelagem.py"))
        self.assertEqual(historical, snapshot)
        with tempfile.TemporaryDirectory() as tmp:
            current = Path(tmp) / "modelagem.py"
            current.write_text("código mantido posteriormente\n", encoding="utf-8")
            self.assertNotEqual(trace.sha256_file(current), historical["src/modelagem.py"])
            trace.validate_historical_code_hashes(
                historical, ("src/modelagem.py", "src/relatorio_modelagem.py"))

    def test_invalid_historical_code_hash_inventory_is_rejected(self):
        expected = ("src/modelagem.py", "src/relatorio_modelagem.py")
        for hashes in ({"src/modelagem.py": "1" * 64},
                       {**{path: "1" * 64 for path in expected}, "src/extra.py": "2" * 64},
                       {path: "not-a-sha256" for path in expected}):
            with self.subTest(paths=set(hashes)), self.assertRaises(ValueError):
                trace.validate_historical_code_hashes(hashes, expected)

    def test_missing_or_extra_input_path_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "reports").mkdir()
            (root / analyses.REPORT).write_text("report\n", encoding="utf-8")
            payload = {"schema_version": 1,
                       "perguntas": {str(i): "question" for i in range(1, 12)},
                       "input_hashes": {"expected.json": "0" * 64},
                       "source_hashes": {}, "output_hashes": {}, "code_hashes": {},
                       "modelo": {}, "figuras": []}
            (root / analyses.METRICS).write_text(json.dumps(payload), encoding="utf-8")
            common = (patch.object(analyses, "find_source_files", return_value=[]),
                      patch.object(analyses, "official_model", return_value={}),
                      patch.object(analyses, "public_text_issues", return_value=[]))
            for current in ({}, {"expected.json": "0" * 64, "extra.json": "1" * 64}):
                with self.subTest(paths=set(current)), common[0], common[1], common[2], \
                     patch.object(analyses, "input_hashes", return_value=current):
                    with self.assertRaisesRegex(ValueError, "Entradas das análises alteradas"):
                        analyses.validate_artifacts(root)


if __name__ == "__main__":
    unittest.main()
