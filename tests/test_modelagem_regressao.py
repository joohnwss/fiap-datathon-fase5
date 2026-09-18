"""Regressões da separação temporal e do protocolo de modelagem."""
import copy
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import joblib
import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.model_selection import StratifiedKFold

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import modelagem as m


def fixture(n=60):
    rng = np.random.default_rng(123)
    X = pd.DataFrame({c: rng.normal(6, 2, n) for c in m.FEATURES})
    X["fase_origem"] = [str(i % 8) for i in range(n)]
    y = np.array([int(i % 3 == 0) for i in range(n)])
    return X, y


class ModelagemRegressionTests(unittest.TestCase):
    def test_closed_predictors_identifiers_and_future_rejected(self):
        X, _ = fixture()
        self.assertEqual(list(m.FEATURES), ["ida", "ieg", "iaa", "ips", "ipv", "fase_origem", "defasagem_origem"])
        for col in ("ra", "nome", "y", "ida_destino", "defasagem_destino", "ian", "inde", "ipp", "genero", "idade", "data", "unidade"):
            with self.subTest(col=col), self.assertRaisesRegex(ValueError, "Schema"):
                m.validate_X(X.assign(**{col: 1}))
        X.index = [f"p{i}" for i in range(len(X))]
        with self.assertRaisesRegex(ValueError, "indice"):
            m.validate_X(X)

    def test_schema_column_order(self):
        X, _ = fixture()
        with self.assertRaisesRegex(ValueError, "ordem"):
            m.validate_X(X[list(reversed(m.FEATURES))])
        m.validate_X(X)

    def test_median_learned_only_on_training(self):
        X, y = fixture()
        X.loc[:19, "ida"] = 2.
        X.loc[20:, "ida"] = 999.
        model = m.fit_checked(m.make_pipeline("logistica"), X.iloc[:20], y[:20])
        imputer = model["preprocessamento"].named_transformers_["numericos"]["imputacao"]
        self.assertEqual(imputer.statistics_[0], 2.)
        test = X.iloc[20:].copy()
        test["ida"] = np.nan
        transformed = imputer.transform(test[list(m.NUMERIC)])
        np.testing.assert_array_equal(transformed[:, 0], 2.)
        model.predict_proba(test)
        self.assertEqual(imputer.statistics_[0], 2.)

    def test_empty_training_feature_fails_without_zero(self):
        X, y = fixture()
        X["ida"] = np.nan
        with self.assertRaisesRegex(ValueError, "Mediana"):
            m.fit_checked(m.make_pipeline("logistica"), X, y)

    def test_unknown_phase_safe_and_no_new_category(self):
        X, y = fixture()
        model = m.fit_checked(m.make_pipeline("logistica"), X, y)
        X["fase_origem"] = "desconhecida"
        prob = model.predict_proba(X)
        self.assertTrue(np.isfinite(prob).all())
        encoder = model["preprocessamento"].named_transformers_["fase"]
        self.assertEqual(encoder.categories_[0].tolist(), list(m.PHASES))
        self.assertTrue((encoder.transform(X[["fase_origem"]]) == 0).all())

    def test_random_state_reproducibility(self):
        X, y = fixture()
        for name in m.candidates():
            a = m.fit_checked(m.make_pipeline(name), X, y).predict_proba(X)
            b = m.fit_checked(m.make_pipeline(name), X, y).predict_proba(X)
            np.testing.assert_array_equal(a, b)

    def test_oof_alignment_and_fold_local_fit(self):
        X, y = fixture()
        splits = list(StratifiedKFold(5, shuffle=True, random_state=m.SEED).split(X, y))
        pipe = m.make_pipeline("logistica")
        _, p, folds = m.evaluate_oof(pipe, X, y, splits)
        for fold, (train, valid) in enumerate(splits):
            direct = m.fit_checked(clone(pipe), X.iloc[train], y[train]).predict_proba(X.iloc[valid])[:, 1]
            np.testing.assert_array_equal(p[valid], direct)
            np.testing.assert_array_equal(folds[valid], fold)
        with self.assertRaisesRegex(ValueError, "sobrepostos"):
            m.evaluate_oof(pipe, X, y, [splits[0], splits[0]])

    def test_threshold_recall_and_max_precision(self):
        y = np.array([1, 1, 1, 1, 1, 0, 0, 0])
        p = np.array([.9, .8, .7, .6, .2, .65, .3, .1])
        chosen = m.choose_threshold(y, p)
        self.assertGreaterEqual(chosen["metricas"]["recall"], .8)
        for t in np.unique(p):
            other = m.metrics(y, p, t)
            if other["recall"] >= .8:
                self.assertGreaterEqual(chosen["metricas"]["precisao"], other["precisao"])

    def test_threshold_deterministic_precision_tie(self):
        y = np.array([1] * 5 + [0] * 5)
        p = np.array([.9, .8, .7, .6, .2, .95, .85, .75, .65, .1])
        # Em .6: 4/8; em .1: 5/10; em .2: 5/9, logo .2 vence.
        self.assertEqual(m.choose_threshold(y, p)["limiar"], .2)
        p[-1] = .2  # Agora .6 e .2 empatam em precisão: recall maior vence.
        self.assertEqual(m.choose_threshold(y, p)["limiar"], .2)
        perm = np.arange(len(y))[::-1]
        self.assertEqual(m.choose_threshold(y[perm], p[perm])["limiar"], m.choose_threshold(y, p)["limiar"])

    def test_selection_has_no_file_access(self):
        X, y = fixture()
        with patch.object(m, "load_cohort", side_effect=AssertionError("acesso indevido")), \
             patch.object(Path, "open", side_effect=AssertionError("acesso indevido")):
            selection, _, _, _ = m.select_development(X, y)
        self.assertIn(selection["vencedor"], m.candidates())

    def test_temporal_access_requires_freeze(self):
        with tempfile.TemporaryDirectory() as tmp, self.assertRaisesRegex(ValueError, "congelamento"):
            m.load_cohort(Path(tmp), "teste_temporal", {})

    def test_pipeline_persistence_reproduces_probabilities(self):
        X, y = fixture()
        model = m.fit_checked(m.make_pipeline("logistica"), X, y)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "model.joblib"
            joblib.dump(model, path)
            restored = joblib.load(path)
            np.testing.assert_array_equal(model.predict_proba(X), restored.predict_proba(X))
            self.assertEqual(restored.feature_names_in_.tolist(), list(m.FEATURES))

    def test_metric_invalid_values_and_undefined_denominators(self):
        for p in ([np.nan, .5], [np.inf, .5], [-1, .5]):
            with self.assertRaisesRegex(ValueError, "invalidos"):
                m.metrics([0, 1], p, .4)
        score = m.metrics([0, 0], [.1, .1], .5)
        self.assertIsNone(score["roc_auc"])
        self.assertIsNone(score["precisao"])
        self.assertIsNone(score["recall"])
        json.dumps(score, allow_nan=False)

    def test_bootstrap_invalid_replicates_explicit_and_reproducible(self):
        y, p = np.array([0, 0, 1]), np.array([.1, .2, .8])
        a = m.bootstrap(y, p, .4, n=25)
        self.assertEqual(a, m.bootstrap(y, p, .4, n=25))
        self.assertGreater(a["completo"]["roc_auc"]["invalidas"], 0)
        self.assertEqual(a["completo"]["roc_auc"]["validas"] + a["completo"]["roc_auc"]["invalidas"], 25)

    def test_tampered_cohort_hash_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "coorte.csv"
            path.write_text("original", encoding="utf-8")
            hashes = {"coorte.csv": m.sha256_file(path)}
            path.write_text("alterado", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Hash divergente"):
                m.verify_hashes(root, hashes)

    def test_stable_hash_and_configuration_mutation(self):
        a = {"a": 1, "b": {"c": 2}}
        self.assertEqual(m.stable_hash(a), m.stable_hash({"b": {"c": 2}, "a": 1}))
        b = copy.deepcopy(a)
        b["b"]["c"] = 3
        self.assertNotEqual(m.stable_hash(a), m.stable_hash(b))

    def test_small_groups_and_profiles_are_suppressed(self):
        X, y = fixture(9)
        self.assertNotIn("numericos", m.profile(X))
        self.assertNotIn("metricas", m.subgroup(y, np.ones(9) * .4, .3))
        self.assertEqual(m.calibration(y, np.ones(9) * .4)["grupos"], [])

    @unittest.skipUnless((m.ROOT / "local_data/X_desenvolvimento.csv").exists(), "Coorte privada indisponivel")
    def test_real_development_counts_without_test_access(self):
        hashes = m.read_json(m.ROOT / m.META)["output_hashes"]
        X, y = m.load_cohort(m.ROOT, "desenvolvimento", hashes)
        self.assertEqual((len(X), int(y.sum())), (189, 60))

    def test_completed_artifacts_counts_privacy_and_integrity_when_present(self):
        if not (m.ROOT / m.ACCESS).exists():
            return  # Antes do primeiro teste temporal: nenhuma leitura da coorte reservada.
        checks = m.validate_artifacts(m.ROOT)
        self.assertTrue(all(checks.values()))
        result = m.read_json(m.ROOT / m.METRICS)
        self.assertEqual((result["temporal"]["metricas"]["n"], result["temporal"]["metricas"]["eventos"]), (311, 84))
        forbidden = {"ra", "nome", "linha_origem", "chave_privada", "predicoes_individuais", "y_true"}
        def visit(value):
            if isinstance(value, dict):
                self.assertFalse(forbidden & value.keys())
                for child in value.values():
                    visit(child)
            elif isinstance(value, list):
                for child in value:
                    visit(child)
        for filename in (m.FREEZE, m.SCHEMA, m.METRICS, m.ACCESS):
            value = m.read_json(m.ROOT / filename)
            visit(value)
            self.assertEqual(m.public_text_issues(json.dumps(value, ensure_ascii=False)), [])

    def test_repeated_temporal_evaluation_is_blocked(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / m.ACCESS).parent.mkdir()
            (root / m.ACCESS).write_text("{}", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "ja aberto"):
                m.evaluate_temporal(root, {})

    def test_full_synthetic_workflow_freezes_before_first_temporal_read(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name in ("src/modelagem.py", "src/relatorio_modelagem.py", "docs/contrato_metodologico.md"):
                (root / name).parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(m.ROOT / name, root / name)
            (root / "local_data").mkdir()
            hashes, rows = {}, []
            for cohort, (n, events) in m.REFERENCE.items():
                X, _ = fixture(n)
                y = np.array([1] * events + [0] * (n - events))
                for prefix, frame in (("X", X), ("y", pd.DataFrame({"y": y})), ("coorte", X.assign(y=y))):
                    name = f"local_data/{prefix}_{cohort}.csv"
                    frame.to_csv(root / name, index=False)
                    hashes[name] = m.sha256_file(root / name)
                for i, values in enumerate(X.to_dict("records")):
                    rows.append({"X": values, "y": int(y[i]), "metadados": {"coorte": cohort,
                        "participou_desenvolvimento": i < 104, "status_alvo": "observado"}})
                if cohort == "teste_temporal":
                    for values in X.iloc[:88].to_dict("records"):
                        rows.append({"X": values, "y": None, "metadados": {"coorte": cohort,
                            "participou_desenvolvimento": False, "status_alvo": "destino_ausente"}})
            (root / m.AUDIT).write_text("\n".join(json.dumps(r) for r in rows), encoding="utf-8")
            hashes[m.AUDIT] = m.sha256_file(root / m.AUDIT)
            m.write_json(root / m.META, {"output_hashes": hashes})
            opened = []
            original_open = Path.open
            def guarded_open(path, *args, **kwargs):
                if "teste_temporal" in path.name or path.name == "coortes_modelagem.jsonl":
                    self.assertTrue((root / m.FREEZE).exists())
                    self.assertTrue((root / m.ACCESS).exists())
                    opened.append(path.name)
                return original_open(path, *args, **kwargs)
            with patch.object(Path, "open", guarded_open):
                frozen = m.freeze_development(root)
                self.assertFalse(opened)
                original_bootstrap = m.bootstrap
                def short_bootstrap(*args, **kwargs):
                    kwargs["n"] = 10
                    return original_bootstrap(*args, **kwargs)
                with patch.object(m, "bootstrap", side_effect=short_bootstrap):
                    result = m.evaluate_temporal(root, frozen)
            self.assertTrue(opened)
            self.assertEqual(result["temporal"]["metricas"]["n"], 311)
            self.assertEqual(result["robustez"]["grupos"]["sem_repetidos"]["n"], 207)
            self.assertEqual(result["robustez"]["perdas"]["sem_destino"]["n"], 88)
            self.assertTrue(all(m.validate_artifacts(root).values()))
            with self.assertRaisesRegex(ValueError, "bloqueada"):
                m.freeze_development(root)
            with self.assertRaisesRegex(ValueError, "ja aberto"):
                m.evaluate_temporal(root, frozen)


if __name__ == "__main__":
    unittest.main()
