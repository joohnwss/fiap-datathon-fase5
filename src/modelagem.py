"""Seleção exclusiva no desenvolvimento e avaliação temporal única, congelada."""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import platform
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (average_precision_score, brier_score_loss, confusion_matrix,
                             f1_score, precision_recall_curve, precision_score,
                             recall_score, roc_auc_score)
from sklearn.model_selection import StratifiedKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.tree import DecisionTreeClassifier

from dados_pede import ROOT
from preparacao_coortes import FEATURES, PHASES, REFERENCE, META, AUDIT
from rastreabilidade import sha256_file, write_json, now, check_git_privacy, public_text_issues

SEED = 42
NUMERIC = tuple(f for f in FEATURES if f != "fase_origem")
FREEZE = "artifacts/configuracao_congelada.json"
SCHEMA = "artifacts/schema_modelo.json"
MODEL = "artifacts/modelo_avaliado.joblib"
SENS_MODEL = "local_data/modelagem/sensibilidade.joblib"
METRICS = "reports/metricas_modelagem.json"
REPORT = "reports/relatorio_modelagem.md"
ACCESS = "artifacts/avaliacao_temporal.json"
PACKAGES = ("numpy", "pandas", "scikit-learn", "scipy", "joblib", "matplotlib")
SCORES = ("average_precision", "roc_auc", "precisao", "recall", "f1", "brier")
ORDER = ("logistica", "arvore", "floresta", "dummy")
PROTOCOL = {
    "versao": 1, "random_state": SEED,
    "validacao": {"classe": "StratifiedKFold", "n_splits": 5, "shuffle": True, "random_state": SEED},
    "selecao": "Maior AP OOF; empate exato: menor DP de AP nos folds, menor Brier OOF, ordem logistica/arvore/floresta/dummy.",
    "limiar": "p >= limiar; recall >= 0.80; maior precisao; empate: maior recall, depois maior limiar.",
    "preprocessamento": {"numericos": "SimpleImputer median dentro do fold; coluna totalmente ausente no treino bloqueia ajuste",
        "fase": "OneHotEncoder categorias 0..7, sem descarte, handle_unknown=ignore; desconhecida gera vetor zero",
        "padronizacao": "StandardScaler somente nos numericos da logistica",
        "indicadores_ausencia": False, "justificativa": "Nenhuma ausencia observada no desenvolvimento; nao ha padrao aprendivel."},
    "sensibilidade": "Mesmo algoritmo/hiperparametros escolhido, sem defasagem_origem; OOF e limiar proprios antes do teste; nao compete na selecao.",
    "bootstrap": {"n": 2000, "seed": SEED, "confianca": 0.95, "unidade": "transicao/aluno no teste (uma por pessoa)",
        "metodo": "percentil, nao estratificado, pipeline e limiar fixos; nulo por metrica nao estimavel, contar descartes",
        "diferenca": "sem repetidos menos teste completo; reamostragem pareada do teste e mascara de participacao"},
    "robustez": ["casos completos sem reajuste", "com/sem participacao desenvolvimento", "perdas sem alvo",
                 "distribuicao dos sete preditores", "equidade genero se disponivel nas coortes e fase", "falsos positivos/negativos agregados"],
    "privacidade": {"minimo_perfil": 10, "minimo_grupo": 30, "minimo_eventos_e_nao_eventos": 5,
                    "calibracao": "5 faixas uniformes; fundir adjacentes ate pelo menos 20 observacoes; sobra fundida a ultima"},
}


def stable_hash(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                     separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def candidates():
    # Uma configuração por família: sem busca ampla em 60 eventos.
    return {"dummy": DummyClassifier(strategy="prior", random_state=SEED),
            "logistica": LogisticRegression(C=1.0, solver="lbfgs", max_iter=2000, random_state=SEED),
            "arvore": DecisionTreeClassifier(max_depth=3, min_samples_leaf=15, random_state=SEED),
            "floresta": RandomForestClassifier(n_estimators=200, max_depth=3, min_samples_leaf=10,
                                               max_features="sqrt", n_jobs=1, random_state=SEED)}


def make_pipeline(name, *, without_defasagem=False):
    numeric = [f for f in NUMERIC if not (without_defasagem and f == "defasagem_origem")]
    steps = [("imputacao", SimpleImputer(strategy="median"))]
    if name == "logistica":
        steps.append(("escala", StandardScaler()))
    prep = ColumnTransformer([
        ("numericos", Pipeline(steps), numeric),
        ("fase", OneHotEncoder(categories=[list(PHASES)], handle_unknown="ignore", sparse_output=False), ["fase_origem"]),
    ], remainder="drop")
    return Pipeline([("preprocessamento", prep), ("modelo", candidates()[name])])


def validate_X(X):
    if list(X.columns) != list(FEATURES):
        raise ValueError("Schema/ordem: somente os sete preditores aprovados")
    if not isinstance(X.index, pd.RangeIndex) or X.index.start != 0 or X.index.step != 1 or X.index.name is not None:
        raise ValueError("Identificadores nao podem integrar o indice")
    for col in NUMERIC:
        if not pd.api.types.is_numeric_dtype(X[col]) or np.isinf(X[col].to_numpy(dtype=float, na_value=np.nan)).any():
            raise ValueError("Numerico invalido")
    if X.fase_origem.isna().any():
        raise ValueError("Fase ausente")


def fit_checked(pipeline, X, y):
    if X[list(NUMERIC)].isna().all().any():
        raise ValueError("Mediana nao estimavel: coluna totalmente ausente no treino")
    return pipeline.fit(X, y)


def verify_hashes(root, hashes):
    for name, digest in hashes.items():
        if not (root / name).is_file() or sha256_file(root / name) != digest:
            raise ValueError("Hash divergente: " + name)


def load_cohort(root, name, hashes, *, frozen=None):
    if name == "teste_temporal" and frozen is None:
        raise ValueError("Teste temporal exige congelamento documentado")
    if name == "teste_temporal":
        if read_json(root / FREEZE) != frozen or stable_hash(frozen["configuracao"]) != frozen["sha256"]:
            raise ValueError("Congelamento invalido")
        if not (root / ACCESS).exists():
            raise ValueError("Teste temporal exige registro de abertura")
    paths = [f"local_data/{prefix}_{name}.csv" for prefix in ("X", "y", "coorte")]
    verify_hashes(root, {p: hashes[p] for p in paths})
    X = pd.read_csv(root / paths[0], dtype={"fase_origem": str})
    target = pd.read_csv(root / paths[1])
    validate_X(X)
    if list(target) != ["y"] or not target.y.isin([0, 1]).all():
        raise ValueError("Alvo invalido")
    y = target.y.to_numpy(dtype=int)
    if len(X) != len(y) or (len(y), int(y.sum())) != REFERENCE[name]:
        raise ValueError("Contagens divergem do contrato")
    if not X.fase_origem.isin(PHASES).all():
        raise ValueError("Fase fora do dominio na coorte")
    return X, y


def metrics(y, p, threshold):
    y, p = np.asarray(y), np.asarray(p, dtype=float)
    if len(y) != len(p) or not np.isin(y, [0, 1]).all() or not np.isfinite(p).all() or ((p < 0) | (p > 1)).any():
        raise ValueError("Alvos/probabilidades invalidos")
    if not len(y):
        return {"n": 0, "eventos": 0, **{k: None for k in SCORES}, "motivo": "amostra vazia"}
    pred = p >= threshold
    positives = bool(y.sum())
    two_classes = len(np.unique(y)) == 2
    return {"n": len(y), "eventos": int(y.sum()), "prevalencia": float(y.mean()),
            "average_precision": float(average_precision_score(y, p)) if positives else None,
            "roc_auc": float(roc_auc_score(y, p)) if two_classes else None,
            "precisao": float(precision_score(y, pred, zero_division=0)) if pred.any() else None,
            "recall": float(recall_score(y, pred, zero_division=0)) if positives else None,
            "f1": float(f1_score(y, pred, zero_division=0)) if positives or pred.any() else None,
            "brier": float(brier_score_loss(y, p)),
            "matriz_confusao": confusion_matrix(y, pred, labels=[0, 1]).tolist(),
            "previstos_risco": int(pred.sum()), "proporcao_risco": float(pred.mean())}


def choose_threshold(y, p):
    if not np.isfinite(p).all() or not np.isin(y, [0, 1]).all() or not np.sum(y):
        raise ValueError("Probabilidades invalidas ou nenhum evento para escolher limiar")
    precision, recall, thresholds = precision_recall_curve(y, p)
    eligible = [i for i in range(len(thresholds)) if recall[i] >= 0.8]
    best = max(eligible, key=lambda i: (precision[i], recall[i], thresholds[i]))
    t = float(thresholds[best])
    return {"limiar": t, "regra": PROTOCOL["limiar"], "metricas": metrics(y, p, t)}


def metric_difference(a, b):
    return {key: a[key] - b[key] if a[key] is not None and b[key] is not None else None for key in SCORES}


def evaluate_oof(pipeline, X, y, splits):
    p = np.full(len(y), np.nan)
    fold_id = np.full(len(y), -1)
    for fold, (train, valid) in enumerate(splits):
        if set(train) & set(valid) or (fold_id[valid] != -1).any():
            raise ValueError("Folds sobrepostos")
        fitted = fit_checked(clone(pipeline), X.iloc[train], y[train])
        p[valid] = fitted.predict_proba(X.iloc[valid])[:, 1]
        fold_id[valid] = fold
    if not np.isfinite(p).all() or (fold_id < 0).any():
        raise ValueError("OOF incompleto")
    chosen = choose_threshold(y, p)
    by_fold = [metrics(y[v], p[v], chosen["limiar"]) for _, v in splits]
    dispersion = {}
    for key in SCORES:
        values = [m[key] for m in by_fold if m[key] is not None]
        dispersion[key] = {"media": float(np.mean(values)) if values else None,
                           "dp": float(np.std(values, ddof=1)) if len(values) > 1 else None,
                           "folds_validos": len(values)}
    return {**chosen, "folds": by_fold, "dispersao": dispersion}, p, fold_id


def select_development(X, y):
    validate_X(X)
    splits = list(StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED).split(X, y))
    results, probabilities = {}, {}
    for name in candidates():
        results[name], probabilities[name], folds = evaluate_oof(make_pipeline(name), X, y, splits)
    winner = min(results, key=lambda n: (-results[n]["metricas"]["average_precision"],
                 results[n]["dispersao"]["average_precision"]["dp"], results[n]["metricas"]["brier"], ORDER.index(n)))
    sensitivity, sensitivity_p, _ = evaluate_oof(make_pipeline(winner, without_defasagem=True), X, y, splits)
    return {"modelos": results, "vencedor": winner, "sensibilidade_sem_defasagem": sensitivity}, probabilities[winner], sensitivity_p, folds


def freeze_development(root):
    if (root / FREEZE).exists() or (root / ACCESS).exists():
        raise ValueError("Selecao bloqueada: configuracao ja congelada")
    meta = read_json(root / META)
    # Copia somente hashes publicados; nenhum arquivo temporal/JSONL misto e aberto aqui.
    inputs = {p: digest for p, digest in meta["output_hashes"].items() if p.startswith("local_data/")}
    X, y = load_cohort(root, "desenvolvimento", inputs)
    selection, p, sensitivity_p, folds = select_development(X, y)
    winner = selection["vencedor"]
    config = {"protocolo": PROTOCOL, "preditores": list(FEATURES), "categorias_fase": list(PHASES),
              "candidatos": {n: model.get_params() for n, model in candidates().items()},
              "escolha": selection, "algoritmo": type(candidates()[winner]).__name__,
              "hiperparametros": candidates()[winner].get_params(),
              "limiar": selection["modelos"][winner]["limiar"], "input_hashes": inputs,
              "contrato_sha256": sha256_file(root / "docs/contrato_metodologico.md"),
              "codigo_sha256": {p: sha256_file(root / p) for p in ("src/modelagem.py", "src/relatorio_modelagem.py")},
              "packages": {p: importlib.metadata.version(p) for p in PACKAGES}, "python": platform.python_version(),
              "ausencias_desenvolvimento": {c: int(X[c].isna().sum()) for c in FEATURES}}
    frozen = {"congelado_em": now(), "configuracao": config, "sha256": stable_hash(config)}
    write_json(root / FREEZE, frozen)
    # Somente depois da gravação do congelamento: ajuste nos 189 de desenvolvimento.
    pipeline = fit_checked(make_pipeline(winner), X, y)
    sensitivity_model = fit_checked(make_pipeline(winner, without_defasagem=True), X, y)
    (root / SENS_MODEL).parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipeline, root / MODEL, compress=3)
    joblib.dump(sensitivity_model, root / SENS_MODEL, compress=3)
    np.savez(root / "local_data/modelagem/oof.npz", p=p, sensitivity_p=sensitivity_p, folds=folds)
    np.testing.assert_allclose(pipeline.predict_proba(X), joblib.load(root / MODEL).predict_proba(X), rtol=0, atol=0)
    write_json(root / SCHEMA, {"tipo": "modelo avaliado", "treino": "2022->2023", "n": len(y), "eventos": int(y.sum()),
        "colunas": list(FEATURES), "tipos": {f: "string categorica" if f == "fase_origem" else "numero anulavel" for f in FEATURES},
        "categorias_fase": list(PHASES), "classe_positiva": 1, "limiar": config["limiar"],
        "regra_classificacao": "probabilidade >= limiar", "ordem_obrigatoria": True,
        "configuracao_sha256": frozen["sha256"], "modelo_sha256": sha256_file(root / MODEL),
        "sensibilidade_sha256": sha256_file(root / SENS_MODEL), "packages": config["packages"],
        "oof_sha256": sha256_file(root / "local_data/modelagem/oof.npz")})
    # Probabilidades e alinhamento permanecem privados, sem identificadores.
    return frozen


def calibration(y, p):
    y, p = np.asarray(y), np.asarray(p)
    groups, pending = [], []
    bins = np.minimum((p * 5).astype(int), 4)
    for b in range(5):
        pending.extend(np.flatnonzero(bins == b).tolist())
        if len(pending) >= 20:
            groups.append(pending)
            pending = []
    if pending and groups:
        groups[-1].extend(pending)
    elif pending:
        return {"status": "suprimida: menos de 20", "grupos": []}
    return {"status": "estimada", "grupos": [{"n": len(g), "probabilidade_media": float(p[g].mean()),
        "fracao_eventos": float(y[g].mean())} for g in groups]}


def pr_curve(y, p):
    precision, recall, _ = precision_recall_curve(y, p)
    # Sem limiares individuais publicados; grade fixa de recall para visualização.
    return [{"recall": float(r), "precisao_interpolada": float(np.max(precision[recall >= r]))}
            for r in np.linspace(0, 1, 21)]


def bootstrap(y, p, threshold, *, masks=None, n=2000):
    masks = masks or {"completo": np.ones(len(y), dtype=bool)}
    rng = np.random.default_rng(SEED)
    values = {g: {m: [] for m in SCORES} for g in masks}
    if "sem_repetidos" in masks:
        values["diferenca_sem_repetidos_menos_completo"] = {m: [] for m in SCORES}
    for _ in range(n):
        idx = rng.integers(0, len(y), len(y))
        estimates = {}
        for group, mask in masks.items():
            selected = idx[mask[idx]]
            estimates[group] = metrics(y[selected], p[selected], threshold)
            for metric in SCORES:
                v = estimates[group][metric]
                if v is not None:
                    values[group][metric].append(v)
        if "sem_repetidos" in masks:
            for metric in SCORES:
                a, b = estimates["sem_repetidos"][metric], estimates["completo"][metric]
                if a is not None and b is not None:
                    values["diferenca_sem_repetidos_menos_completo"][metric].append(a - b)
    return {group: {m: {"ic95": np.quantile(v, [0.025, 0.975]).tolist() if v else None,
                        "validas": len(v), "invalidas": n - len(v)} for m, v in scores.items()}
            for group, scores in values.items()}


def profile(X):
    if len(X) < 10:
        return {"status": "suprimido: n < 10"}
    out = {"n": len(X), "numericos": {}}
    for c in NUMERIC:
        v = X[c].dropna()
        out["numericos"][c] = {"disponiveis": len(v), "ausentes": int(X[c].isna().sum()),
            "media": float(v.mean()) if len(v) else None, "mediana": float(v.median()) if len(v) else None,
            "dp": float(v.std()) if len(v) > 1 else None}
    counts = X.fase_origem.value_counts()
    out["fase"] = {str(k): int(v) if v >= 10 else "<10" for k, v in counts.items()}
    return out


def subgroup(y, p, threshold):
    if len(y) < 30 or y.sum() < 5 or len(y) - y.sum() < 5:
        return {"status": "suprimido: n < 30 ou menos de 5 eventos/nao eventos"}
    return {"status": "estimado", "metricas": metrics(y, p, threshold), "calibracao": calibration(y, p)}


def robustness(root, frozen, Xd, yd, Xt, yt, p, threshold):
    verify_hashes(root, {AUDIT: frozen["configuracao"]["input_hashes"][AUDIT]})
    rows = [json.loads(line) for line in (root / AUDIT).read_text(encoding="utf-8").splitlines()]
    test = [r for r in rows if r["metadados"]["coorte"] == "teste_temporal"]
    observed = [r for r in test if r["y"] is not None]
    # Confere alinhamento antes de empregar metadados privados como máscaras.
    audit_X = pd.DataFrame([r["X"] for r in observed], columns=FEATURES)
    for c in NUMERIC:
        np.testing.assert_allclose(audit_X[c].to_numpy(float), Xt[c].to_numpy(float), equal_nan=True)
    if audit_X.fase_origem.tolist() != Xt.fase_origem.tolist() or [r["y"] for r in observed] != yt.tolist():
        raise ValueError("Auditoria privada desalinhada")
    repeated = np.array([r["metadados"]["participou_desenvolvimento"] for r in observed], dtype=bool)
    if int(repeated.sum()) != 104:
        raise ValueError("Sobreposicao diverge das coortes")
    missing_rows = [r for r in test if r["metadados"]["status_alvo"] == "destino_ausente"]
    unknown_found = [r for r in test if r["metadados"]["status_alvo"] == "defasagem_destino_indisponivel"]
    if len(missing_rows) != 88 or any(r["y"] is not None for r in missing_rows):
        raise ValueError("Perdas divergem das coortes")
    missing_X = pd.DataFrame([r["X"] for r in missing_rows], columns=FEATURES)
    complete = ~Xt.isna().any(axis=1).to_numpy()
    masks = {"completo": np.ones(len(yt), bool), "casos_completos": complete,
             "sem_repetidos": ~repeated, "repetidos": repeated}
    group_metrics = {g: metrics(yt[mask], p[mask], threshold) for g, mask in masks.items()}
    intervals = bootstrap(yt, p, threshold, masks=masks, n=PROTOCOL["bootstrap"]["n"])
    delta = metric_difference(group_metrics["sem_repetidos"], group_metrics["completo"])
    pred = p >= threshold
    phase_groups = {phase: subgroup(yt[Xt.fase_origem.eq(phase)], p[Xt.fase_origem.eq(phase)], threshold)
                    for phase in PHASES}
    shift = {}
    for c in NUMERIC:
        a, b = Xd[c].dropna(), Xt[c].dropna()
        pooled = np.sqrt((a.var() + b.var()) / 2)
        shift[c] = {"media_desenvolvimento": float(a.mean()), "media_teste": float(b.mean()),
                    "diferenca_padronizada": float((b.mean() - a.mean()) / pooled) if pooled else None,
                    "ausentes_desenvolvimento": int(Xd[c].isna().sum()), "ausentes_teste": int(Xt[c].isna().sum())}
    return {"grupos": group_metrics, "intervalos": intervals, "diferenca_sem_repetidos_menos_completo": delta,
            "casos_completos_desenvolvimento": {"n": int((~Xd.isna().any(axis=1)).sum()), "eventos": int(yd.sum())},
            "perdas": {"sem_destino": profile(missing_X), "encontrados": profile(Xt),
                        "encontrados_sem_alvo": len(unknown_found), "alvo_atribuido": False},
            "distribuicao": {"numericos": shift, "desenvolvimento": profile(Xd), "teste": profile(Xt)},
            "equidade_fase": phase_groups,
            "equidade_genero": {"status": "indisponivel", "motivo": "As coortes aprovadas nao incluem genero, nem nos metadados. Nao se incorpora outra base. Inconsistencias cadastrais ja documentadas limitariam a interpretacao."},
            "erros": {"falsos_positivos": profile(Xt.loc[(yt == 0) & pred]),
                      "falsos_negativos": profile(Xt.loc[(yt == 1) & ~pred])}}


def interpretation(pipeline):
    names = pipeline.named_steps["preprocessamento"].get_feature_names_out().tolist()
    estimator = pipeline.named_steps["modelo"]
    if hasattr(estimator, "coef_"):
        return {"tipo": "coeficientes_log_odds", "intercepto": float(estimator.intercept_[0]),
                "valores": dict(zip(names, estimator.coef_[0].tolist())),
                "nota": "Numericos por um desvio padrao do desenvolvimento; fase one-hot sem referencia descartada, contrastes entre fases sao diferencas entre coeficientes. Associacoes condicionais, nao causais."}
    if hasattr(estimator, "feature_importances_"):
        return {"tipo": "importancia_reducao_impureza", "valores": dict(zip(names, estimator.feature_importances_.tolist())),
                "nota": "Importancias nao tem direcao/sinal e podem favorecer variaveis com mais cortes; fase distribuida entre dummies. Nao expressam causalidade."}
    return {"tipo": "constante", "valores": {}, "nota": "Referencia sem dependencia dos preditores."}


def validate_frozen(root):
    frozen = read_json(root / FREEZE)
    config = frozen["configuracao"]
    if stable_hash(config) != frozen["sha256"] or config["protocolo"] != PROTOCOL:
        raise ValueError("Configuracao congelada alterada")
    verify_hashes(root, config["codigo_sha256"])
    verify_hashes(root, {"docs/contrato_metodologico.md": config["contrato_sha256"]})
    if config["packages"] != {p: importlib.metadata.version(p) for p in PACKAGES}:
        raise ValueError("Versoes divergem do congelamento")
    schema = read_json(root / SCHEMA)
    if schema["configuracao_sha256"] != frozen["sha256"] or schema["colunas"] != list(FEATURES) or schema["limiar"] != config["limiar"]:
        raise ValueError("Schema divergente")
    verify_hashes(root, {MODEL: schema["modelo_sha256"]})
    return frozen


def validate_artifacts(root):
    frozen = validate_frozen(root)
    verify_hashes(root, frozen["configuracao"]["input_hashes"])
    access = read_json(root / ACCESS)
    if access["status"] != "concluida" or access["configuracao_sha256"] != frozen["sha256"] or access["aberta_em"] <= frozen["congelado_em"]:
        raise ValueError("Avaliacao nao concluida ou precede congelamento")
    verify_hashes(root, access["output_hashes"])
    result = read_json(root / METRICS)
    if result["configuracao_sha256"] != frozen["sha256"]:
        raise ValueError("Metricas divergentes do congelamento")
    json.dumps(result, allow_nan=False)
    for population, expected in (("oof", (189, 60)), ("temporal", (311, 84))):
        m = result[population]["metricas"]
        if (m["n"], m["eventos"]) != expected:
            raise ValueError("Contagens de avaliacao divergentes")
    return {"modelagem_congelada_antes_teste": True, "hashes_modelagem_conferidos": True,
            "modelo_avaliado_treinado_apenas_desenvolvimento": True, "metricas_modelagem_validas": True}


def evaluate_temporal(root, frozen):
    if (root / ACCESS).exists():
        raise ValueError("Teste temporal ja aberto; nao repetir avaliacao")
    validate_frozen(root)
    schema = read_json(root / SCHEMA)
    verify_hashes(root, {SENS_MODEL: schema["sensibilidade_sha256"]})
    verify_hashes(root, {"local_data/modelagem/oof.npz": schema["oof_sha256"]})
    access = {"status": "iniciada", "aberta_em": now(), "configuracao_sha256": frozen["sha256"]}
    # Modo exclusivo impede abertura concorrente ou repetição após falha parcial.
    with (root / ACCESS).open("x", encoding="utf-8") as stream:
        json.dump(access, stream, indent=2)
    config = frozen["configuracao"]
    Xt, yt = load_cohort(root, "teste_temporal", config["input_hashes"], frozen=frozen)
    Xd, yd = load_cohort(root, "desenvolvimento", config["input_hashes"])
    model = joblib.load(root / MODEL)
    p = model.predict_proba(Xt)[:, 1]
    sensitivity_p = joblib.load(root / SENS_MODEL).predict_proba(Xt)[:, 1]
    with np.load(root / "local_data/modelagem/oof.npz") as stored:
        oof = {k: stored[k].copy() for k in stored.files}
    threshold = config["limiar"]
    winner = config["escolha"]["vencedor"]
    result = {"configuracao_sha256": frozen["sha256"], "modelo": winner,
        "limiar": threshold, "comparacao_modelos": config["escolha"]["modelos"],
        "oof": {"metricas": metrics(yd, oof["p"], threshold), "calibracao": calibration(yd, oof["p"]), "curva_pr": pr_curve(yd, oof["p"])},
        "temporal": {"metricas": metrics(yt, p, threshold), "calibracao": calibration(yt, p), "curva_pr": pr_curve(yt, p)},
        "sensibilidade_sem_defasagem": {"oof": config["escolha"]["sensibilidade_sem_defasagem"],
            "temporal": metrics(yt, sensitivity_p, config["escolha"]["sensibilidade_sem_defasagem"]["limiar"])},
        "robustez": robustness(root, frozen, Xd, yd, Xt, yt, p, threshold),
        "interpretabilidade": interpretation(model)}
    result["diferenca_temporal_menos_oof"] = metric_difference(result["temporal"]["metricas"], result["oof"]["metricas"])
    np.savez(root / "local_data/modelagem/temporal.npz", p=p, sensitivity_p=sensitivity_p)
    from relatorio_modelagem import render_report, plot_curves
    report = render_report(frozen, result)
    if public_text_issues(report) or public_text_issues(json.dumps(result, ensure_ascii=False)):
        raise ValueError("Conteudo publico invalido")
    write_json(root / METRICS, result)
    (root / REPORT).write_text(report, encoding="utf-8")
    plot_curves(root, result)
    access.update(status="concluida", concluida_em=now(), output_hashes={p: sha256_file(root / p) for p in (METRICS, REPORT, MODEL, SCHEMA, "reports/curvas_modelagem.png")})
    write_json(root / ACCESS, access)
    validate_artifacts(root)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--somente-desenvolvimento", action="store_true")
    args = parser.parse_args()
    check_git_privacy()
    if (ROOT / ACCESS).exists():
        validate_artifacts(ROOT)
        print("Avaliacao ja concluida: hashes conferidos, sem nova selecao ou acesso preditivo ao teste.")
        return
    frozen = validate_frozen(ROOT) if (ROOT / FREEZE).exists() else freeze_development(ROOT)
    print("Configuracao congelada: " + frozen["sha256"])
    if not args.somente_desenvolvimento:
        result = evaluate_temporal(ROOT, frozen)
        print(json.dumps({"modelo": result["modelo"], "limiar": result["limiar"], "temporal": result["temporal"]["metricas"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
