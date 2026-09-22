"""Regressão da TASK 010 para `src/inferencia.py` (módulo de inferência da
aplicação pública, sem Streamlit).

Cobre: validador público (seis caminhos, ausência de dependência privada,
artefato ausente, hash/limiar/ordem/`configuracao_sha256` divergentes,
schema incompatível), carregamento e compatibilidade do modelo (classes,
`predict_proba`, classe positiva), validação de entradas (chaves, tipos,
`NaN`/infinito, domínio de fase), formato/valores de `predict_proba` e
reprodução exata da predição comparando `run_inference` com uma chamada
manual de `predict_proba` sobre o modelo oficial.

Nenhum teste aqui altera `artifacts/`, `reports/`, `docs/` ou qualquer
arquivo do repositório: os casos de artefato ausente/adulterado usam cópias
em diretórios temporários, sempre removidos via `addCleanup` (mesmo se o
teste falhar). Nenhum dado privado (`DATATHON/`, `local_data/`,
`local_recovery/`) é lido.
"""
from __future__ import annotations

import ast
import functools
import json
import math
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))
import inferencia as inf  # noqa: E402
import modelagem  # noqa: E402
import rastreabilidade as rastro  # noqa: E402

REAL_ROOT = inf.find_project_root()


@functools.lru_cache(maxsize=1)
def official_threshold() -> float:
    """Lê o limiar oficial diretamente dos três artefatos públicos que o
    registram — nunca de uma constante duplicada no código de teste.

    Confirma que os três valores são numéricos, finitos e idênticos entre
    si antes de retornar o limiar; qualquer divergência levanta
    `AssertionError` (o mesmo tipo de falha clara que um teste chamador
    reportaria)."""
    registros = {
        "artifacts/schema_modelo.json.limiar":
            modelagem.read_json(REAL_ROOT / modelagem.SCHEMA).get("limiar"),
        "artifacts/configuracao_congelada.json.configuracao.limiar":
            modelagem.read_json(REAL_ROOT / modelagem.FREEZE).get("configuracao", {}).get("limiar"),
        "reports/metricas_modelagem.json.limiar":
            modelagem.read_json(REAL_ROOT / modelagem.METRICS).get("limiar"),
    }
    for origem, valor in registros.items():
        if isinstance(valor, bool) or not isinstance(valor, (int, float)):
            raise AssertionError(f"Limiar não numérico em {origem}: {valor!r}")
        if not math.isfinite(valor):
            raise AssertionError(f"Limiar não finito em {origem}: {valor!r}")
    distintos = set(registros.values())
    if len(distintos) != 1:
        raise AssertionError(f"Limiares divergentes entre artefatos públicos: {registros}")
    return float(distintos.pop())


@functools.lru_cache(maxsize=1)
def _real_context() -> inf.ApplicationContext:
    """Carrega o contexto real (validador público + modelo oficial) uma
    única vez por execução da suíte; somente leitura dos artefatos públicos
    reais, nunca alterados."""
    return inf.prepare_application(REAL_ROOT)


def _synthetic_payload(**overrides) -> dict:
    """Payload sintético completo e válido; nenhum valor corresponde a
    registro real do projeto."""
    base = {"ida": "6.5", "ieg": "8.0", "iaa": "7.0", "ips": "5.0", "ipv": "7.5",
            "fase_origem": "2", "defasagem_origem": "0"}
    base.update(overrides)
    return base


class _FakePipeline:
    """Pipeline sintético mínimo para testar `predict()`/`load_model()` sem
    depender do modelo real: expõe apenas `classes_` e `predict_proba`."""

    def __init__(self, classes, retorno):
        self.classes_ = np.array(classes)
        self._retorno = retorno

    def predict_proba(self, frame):
        if isinstance(self._retorno, Exception):
            raise self._retorno
        return self._retorno


class _FakePipelineSemProba:
    """Pipeline sintético sem `predict_proba`, para testar a rejeição."""

    def __init__(self, classes):
        self.classes_ = np.array(classes)


def _frame_sintetico() -> pd.DataFrame:
    return inf.build_feature_frame(inf.validate_inputs(_synthetic_payload()))


# --------------------------------------------------------------------------- #
# Validador público                                                          #
# --------------------------------------------------------------------------- #

class PublicValidatorTests(unittest.TestCase):
    def _make_public_root(self) -> Path:
        """Cópia mínima dos seis caminhos públicos em um diretório
        temporário; limpo mesmo se o teste falhar."""
        tmp = Path(tempfile.mkdtemp(prefix="inferencia_publico_"))
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        for relativo in inf.PUBLIC_REQUIRED_PATHS:
            origem = REAL_ROOT / relativo
            destino = tmp / relativo
            destino.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(origem, destino)
        return tmp

    def test_funciona_com_os_seis_caminhos_publicos_sem_pastas_privadas(self):
        tmp = self._make_public_root()
        for pasta in ("DATATHON", "local_data", "local_recovery"):
            self.assertFalse((tmp / pasta).exists(),
                             f"{pasta}/ não deveria existir na cópia pública")
        resultado = inf.run_public_validator(tmp)
        self.assertIsInstance(resultado, inf.PublicValidationResult)
        self.assertAlmostEqual(resultado.threshold, official_threshold(), places=12)
        self.assertEqual(list(resultado.schema["colunas"]), list(inf.FEATURES))

    def test_falha_sem_contrato_metodologico(self):
        tmp = self._make_public_root()
        (tmp / inf.CONTRACT_PATH).unlink()
        with self.assertRaises(inf.PublicValidationError) as ctx:
            inf.run_public_validator(tmp)
        self.assertIn(inf.CONTRACT_PATH, str(ctx.exception))

    def test_falha_com_modelo_ausente(self):
        tmp = self._make_public_root()
        (tmp / modelagem.MODEL).unlink()
        with self.assertRaises(inf.PublicValidationError):
            inf.run_public_validator(tmp)

    def test_falha_com_schema_ausente(self):
        tmp = self._make_public_root()
        (tmp / modelagem.SCHEMA).unlink()
        with self.assertRaises(inf.PublicValidationError):
            inf.run_public_validator(tmp)

    def test_falha_com_configuracao_congelada_ausente(self):
        tmp = self._make_public_root()
        (tmp / modelagem.FREEZE).unlink()
        with self.assertRaises(inf.PublicValidationError):
            inf.run_public_validator(tmp)

    def test_falha_com_avaliacao_temporal_ausente(self):
        tmp = self._make_public_root()
        (tmp / modelagem.ACCESS).unlink()
        with self.assertRaises(inf.PublicValidationError):
            inf.run_public_validator(tmp)

    def test_falha_com_metricas_ausentes(self):
        tmp = self._make_public_root()
        (tmp / modelagem.METRICS).unlink()
        with self.assertRaises(inf.PublicValidationError):
            inf.run_public_validator(tmp)

    def test_falha_com_hash_do_arquivo_schema_divergente(self):
        """Corrompe apenas os bytes do arquivo schema_modelo.json (conteúdo
        JSON continua válido e com os mesmos campos), o que faz seu hash de
        arquivo divergir do registrado em avaliacao_temporal.json."""
        tmp = self._make_public_root()
        caminho = tmp / modelagem.SCHEMA
        dados = json.loads(caminho.read_text(encoding="utf-8"))
        caminho.write_text(json.dumps(dados, ensure_ascii=False, indent=4) + "\n\n", encoding="utf-8")
        with self.assertRaises(inf.PublicValidationError):
            inf.run_public_validator(tmp)

    def test_falha_com_hash_do_modelo_divergente(self):
        tmp = self._make_public_root()
        caminho = tmp / modelagem.MODEL
        with caminho.open("ab") as arquivo:
            arquivo.write(b"\x00")
        with self.assertRaises(inf.PublicValidationError):
            inf.run_public_validator(tmp)

    def test_falha_com_configuracao_sha256_divergente(self):
        """Adultera somente o registro `configuracao_sha256` de
        reports/metricas_modelagem.json, mantendo o restante intacto."""
        tmp = self._make_public_root()
        caminho = tmp / modelagem.METRICS
        dados = json.loads(caminho.read_text(encoding="utf-8"))
        dados["configuracao_sha256"] = "0" * 64
        caminho.write_text(json.dumps(dados, ensure_ascii=False), encoding="utf-8")
        with self.assertRaises(inf.PublicValidationError) as ctx:
            inf.run_public_validator(tmp)
        self.assertIn("configuracao_sha256", str(ctx.exception))

    def test_falha_com_limiar_divergente(self):
        tmp = self._make_public_root()
        caminho = tmp / modelagem.METRICS
        dados = json.loads(caminho.read_text(encoding="utf-8"))
        dados["limiar"] = 0.5
        caminho.write_text(json.dumps(dados, ensure_ascii=False), encoding="utf-8")
        with self.assertRaises(inf.PublicValidationError) as ctx:
            inf.run_public_validator(tmp)
        self.assertIn("imiar", str(ctx.exception))  # "Limiares divergentes..."

    def test_falha_com_ordem_dos_preditores_divergente(self):
        tmp = self._make_public_root()
        caminho = tmp / modelagem.SCHEMA
        dados = json.loads(caminho.read_text(encoding="utf-8"))
        dados["colunas"] = list(reversed(dados["colunas"]))
        caminho.write_text(json.dumps(dados, ensure_ascii=False), encoding="utf-8")
        with self.assertRaises(inf.PublicValidationError):
            inf.run_public_validator(tmp)

    def test_falha_com_schema_incompativel(self):
        """Remove uma chave obrigatória do schema (limiar); o schema deixa
        de ser compatível com o contrato oficial."""
        tmp = self._make_public_root()
        caminho = tmp / modelagem.SCHEMA
        dados = json.loads(caminho.read_text(encoding="utf-8"))
        del dados["limiar"]
        caminho.write_text(json.dumps(dados, ensure_ascii=False), encoding="utf-8")
        with self.assertRaises(inf.PublicValidationError):
            inf.run_public_validator(tmp)


# --------------------------------------------------------------------------- #
# Modelo e inferência: carregamento, compatibilidade e formato de saída      #
# --------------------------------------------------------------------------- #

class ModelCompatibilityTests(unittest.TestCase):
    def test_carrega_o_modelo_oficial_com_predict_proba_disponivel(self):
        contexto = _real_context()
        self.assertTrue(hasattr(contexto.pipeline, "predict_proba"))
        self.assertEqual(list(int(c) for c in contexto.pipeline.classes_), [0, 1])

    def test_classe_positiva_aceita_apenas_o_inteiro_1(self):
        schema_real = json.loads((REAL_ROOT / modelagem.SCHEMA).read_text(encoding="utf-8"))
        for valor, deve_aceitar in ((1, True), (0, False), (False, False), ("1", False), (1.0, False)):
            with self.subTest(valor=valor):
                schema = dict(schema_real, classe_positiva=valor)
                if deve_aceitar:
                    inf.load_model(REAL_ROOT, schema)  # não deve levantar
                else:
                    with self.assertRaises(inf.PublicValidationError):
                        inf.load_model(REAL_ROOT, schema)

    def test_posicao_da_classe_positiva_usa_classes_e_nao_indice_fixo(self):
        self.assertEqual(inf.positive_class_index(_FakePipeline([0, 1], None)), 1)
        self.assertEqual(inf.positive_class_index(_FakePipeline([1, 0], None)), 0)

    def test_load_model_rejeita_classes_incompativeis(self):
        tmp = Path(tempfile.mkdtemp(prefix="inferencia_modelo_"))
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        caminho_modelo = tmp / modelagem.MODEL
        caminho_modelo.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(_FakePipeline([0, 1, 2], np.array([[0.3, 0.3, 0.4]])), caminho_modelo)
        with self.assertRaises(inf.PublicValidationError):
            inf.load_model(tmp, {"classe_positiva": 1})

    def test_load_model_rejeita_ausencia_de_predict_proba(self):
        tmp = Path(tempfile.mkdtemp(prefix="inferencia_modelo_"))
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        caminho_modelo = tmp / modelagem.MODEL
        caminho_modelo.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(_FakePipelineSemProba([0, 1]), caminho_modelo)
        with self.assertRaises(inf.PublicValidationError):
            inf.load_model(tmp, {"classe_positiva": 1})

    def test_modulo_nunca_chama_predict_do_pipeline(self):
        """Análise textual do próprio código-fonte: só `.predict_proba(` é
        chamado sobre o pipeline, nunca `.predict(` isolado (que aplicaria
        o limiar padrão 0,5 do scikit-learn em vez do limiar congelado)."""
        codigo = (SRC / "inferencia.py").read_text(encoding="utf-8")
        import re
        chamadas_predict_isolado = re.findall(r"\.predict\((?!_proba)", codigo)
        self.assertEqual(chamadas_predict_isolado, [])
        self.assertIn(".predict_proba(", codigo)

    def test_modulo_nunca_chama_fit(self):
        arvore = ast.parse((SRC / "inferencia.py").read_text(encoding="utf-8"))
        nomes_proibidos = {"fit", "fit_transform", "partial_fit"}
        for node in ast.walk(arvore):
            if isinstance(node, ast.Call):
                alvo = node.func.attr if isinstance(node.func, ast.Attribute) else \
                    (node.func.id if isinstance(node.func, ast.Name) else None)
                self.assertNotIn(alvo, nomes_proibidos, f"chamada proibida encontrada: {alvo}")


class PredictShapeAndValueTests(unittest.TestCase):
    def setUp(self):
        self.frame = _frame_sintetico()

    def test_shape_valido_1x2_e_aceito(self):
        pipeline = _FakePipeline([0, 1], np.array([[0.7, 0.3]]))
        resultado = inf.predict(pipeline, self.frame, threshold=0.5)
        self.assertAlmostEqual(resultado.probability, 0.3, places=12)

    def test_shape_1x1_e_rejeitado(self):
        pipeline = _FakePipeline([0, 1], np.array([[1.0]]))
        with self.assertRaises(inf.PublicValidationError):
            inf.predict(pipeline, self.frame, threshold=0.5)

    def test_mais_de_uma_linha_e_rejeitado(self):
        pipeline = _FakePipeline([0, 1], np.array([[0.5, 0.5], [0.5, 0.5]]))
        with self.assertRaises(inf.PublicValidationError):
            inf.predict(pipeline, self.frame, threshold=0.5)

    def test_vetor_unidimensional_e_rejeitado(self):
        pipeline = _FakePipeline([0, 1], np.array([0.5, 0.5]))
        with self.assertRaises(inf.PublicValidationError):
            inf.predict(pipeline, self.frame, threshold=0.5)

    def test_quantidade_de_colunas_incompativel_e_rejeitada(self):
        pipeline = _FakePipeline([0, 1, 2], np.array([[0.5, 0.5]]))
        with self.assertRaises(inf.PublicValidationError):
            inf.predict(pipeline, self.frame, threshold=0.5)

    def test_nan_na_saida_e_rejeitado(self):
        pipeline = _FakePipeline([0, 1], np.array([[np.nan, 0.5]]))
        with self.assertRaises(inf.PublicValidationError):
            inf.predict(pipeline, self.frame, threshold=0.5)

    def test_infinito_na_saida_e_rejeitado(self):
        pipeline = _FakePipeline([0, 1], np.array([[np.inf, -np.inf]]))
        with self.assertRaises(inf.PublicValidationError):
            inf.predict(pipeline, self.frame, threshold=0.5)

    def test_probabilidade_fora_de_0_1_e_rejeitada(self):
        pipeline = _FakePipeline([0, 1], np.array([[1.5, -0.5]]))
        with self.assertRaises(inf.PublicValidationError):
            inf.predict(pipeline, self.frame, threshold=0.5)

    def test_soma_incompativel_com_1_e_rejeitada(self):
        pipeline = _FakePipeline([0, 1], np.array([[0.3, 0.3]]))
        with self.assertRaises(inf.PublicValidationError):
            inf.predict(pipeline, self.frame, threshold=0.5)

    def test_excecao_interna_vira_erro_controlado_sem_vazamento(self):
        pipeline = _FakePipeline([0, 1], ValueError("mensagem interna sensivel do modelo -- C:/segredo"))
        with self.assertRaises(inf.PublicValidationError) as ctx:
            inf.predict(pipeline, self.frame, threshold=0.5)
        mensagem = str(ctx.exception)
        self.assertNotIn("sensivel", mensagem)
        self.assertNotIn("segredo", mensagem)

    def test_classificacao_abaixo_igual_e_acima_do_limiar(self):
        pipeline = _FakePipeline([0, 1], np.array([[0.7, 0.3]]))
        self.assertFalse(inf.predict(pipeline, self.frame, threshold=0.5).is_risk)   # 0.3 < 0.5
        self.assertTrue(inf.predict(pipeline, self.frame, threshold=0.3).is_risk)    # 0.3 == 0.3 (regra >=)
        self.assertTrue(inf.predict(pipeline, self.frame, threshold=0.1).is_risk)    # 0.3 > 0.1


# --------------------------------------------------------------------------- #
# Entradas                                                                    #
# --------------------------------------------------------------------------- #

class InputValidationTests(unittest.TestCase):
    def test_sete_campos_validos_sao_aceitos(self):
        validado = inf.validate_inputs(_synthetic_payload())
        self.assertEqual(set(validado), set(inf.FEATURES))

    def test_seis_numericos_com_valores_sao_convertidos_para_float(self):
        validado = inf.validate_inputs(_synthetic_payload())
        for campo in inf.NUMERIC_FIELDS:
            self.assertIsInstance(validado[campo], float)

    def test_cada_numerico_individualmente_como_none_e_aceito(self):
        for campo in inf.NUMERIC_FIELDS:
            with self.subTest(campo=campo):
                validado = inf.validate_inputs(_synthetic_payload(**{campo: None}))
                self.assertIsNone(validado[campo])

    def test_todos_os_numericos_como_none_e_aceito_pelo_pipeline(self):
        payload = _synthetic_payload(**{c: None for c in inf.NUMERIC_FIELDS})
        validado = inf.validate_inputs(payload)
        self.assertTrue(all(validado[c] is None for c in inf.NUMERIC_FIELDS))
        contexto = _real_context()
        resultado = inf.run_inference(contexto, payload)
        self.assertTrue(0.0 <= resultado.probability <= 1.0)

    def test_fase_origem_de_0_a_7_e_aceita(self):
        for fase in inf.PHASE_CATEGORIES:
            with self.subTest(fase=fase):
                validado = inf.validate_inputs(_synthetic_payload(fase_origem=fase))
                self.assertEqual(validado["fase_origem"], fase)

    def test_fase_ausente_do_payload_e_rejeitada(self):
        payload = _synthetic_payload()
        del payload["fase_origem"]
        with self.assertRaises(inf.InputValidationError):
            inf.validate_inputs(payload)

    def test_fase_vazia_e_rejeitada(self):
        with self.assertRaises(inf.InputValidationError):
            inf.validate_inputs(_synthetic_payload(fase_origem=""))

    def test_fase_fora_do_dominio_e_rejeitada(self):
        for fase in ("8", "9", "10", "-1", "a"):
            with self.subTest(fase=fase):
                with self.assertRaises(inf.InputValidationError):
                    inf.validate_inputs(_synthetic_payload(fase_origem=fase))

    def test_chave_numerica_ausente_e_rejeitada(self):
        for campo in inf.NUMERIC_FIELDS:
            with self.subTest(campo=campo):
                payload = _synthetic_payload()
                del payload[campo]
                with self.assertRaises(inf.InputValidationError):
                    inf.validate_inputs(payload)

    def test_chave_extra_e_rejeitada(self):
        with self.assertRaises(inf.InputValidationError):
            inf.validate_inputs(_synthetic_payload(campo_extra="x"))

    def test_texto_nao_numerico_e_rejeitado(self):
        with self.assertRaises(inf.InputValidationError):
            inf.validate_inputs(_synthetic_payload(ida="abc"))

    def test_nan_e_rejeitado_como_string_e_como_float(self):
        for valor in ("nan", "NaN", float("nan")):
            with self.subTest(valor=valor):
                with self.assertRaises(inf.InputValidationError):
                    inf.validate_inputs(_synthetic_payload(ida=valor))

    def test_infinito_positivo_e_rejeitado(self):
        for valor in ("inf", "Infinity", float("inf")):
            with self.subTest(valor=valor):
                with self.assertRaises(inf.InputValidationError):
                    inf.validate_inputs(_synthetic_payload(ida=valor))

    def test_infinito_negativo_e_rejeitado(self):
        for valor in ("-inf", "-Infinity", float("-inf")):
            with self.subTest(valor=valor):
                with self.assertRaises(inf.InputValidationError):
                    inf.validate_inputs(_synthetic_payload(ida=valor))

    def test_booleano_em_campo_numerico_e_rejeitado(self):
        for valor in (True, False):
            with self.subTest(valor=valor):
                with self.assertRaises(inf.InputValidationError):
                    inf.validate_inputs(_synthetic_payload(ida=valor))

    def test_payload_nao_dicionario_e_rejeitado(self):
        for payload in (None, 42, ["ida", "ieg"], "abc", 3.14):
            with self.subTest(payload=payload):
                with self.assertRaises(inf.InputValidationError):
                    inf.validate_inputs(payload)

    def test_ordem_final_das_colunas_segue_o_contrato_oficial(self):
        payload_fora_de_ordem = {"fase_origem": "2", "defasagem_origem": "0", "ipv": "7.5",
                                 "ips": "5.0", "iaa": "7.0", "ieg": "8.0", "ida": "6.5"}
        frame = inf.build_feature_frame(inf.validate_inputs(payload_fora_de_ordem))
        self.assertEqual(list(frame.columns), list(inf.FEATURES))

    def test_dataframe_tem_exatamente_uma_linha(self):
        frame = _frame_sintetico()
        self.assertEqual(len(frame), 1)


# --------------------------------------------------------------------------- #
# Reprodução da predição                                                      #
# --------------------------------------------------------------------------- #

class PredictionReproductionTests(unittest.TestCase):
    def test_run_inference_reproduz_exatamente_predict_proba_manual(self):
        contexto = _real_context()  # 1) modelo oficial já carregado
        payload = _synthetic_payload()

        # 2) DataFrame oficial construído manualmente
        frame_manual = inf.build_feature_frame(inf.validate_inputs(payload))
        self.assertEqual(list(frame_manual.columns), list(inf.FEATURES))
        self.assertEqual(len(frame_manual), 1)

        # 3) predict_proba direto sobre o pipeline oficial
        proba_manual = contexto.pipeline.predict_proba(frame_manual)

        # 4) localização manual da classe positiva por classes_
        classes = list(int(c) for c in contexto.pipeline.classes_)
        indice_manual = classes.index(1)
        probabilidade_manual = float(proba_manual[0, indice_manual])

        # 5) comparação com run_inference (tolerância numérica: ponto flutuante idêntico esperado)
        resultado = inf.run_inference(contexto, payload)
        self.assertTrue(math.isclose(resultado.probability, probabilidade_manual, rel_tol=1e-9, abs_tol=1e-12))

        # 6) classificação comparada ao limiar oficial
        classificacao_manual = probabilidade_manual >= contexto.validation.threshold
        self.assertEqual(resultado.is_risk, classificacao_manual)
        self.assertEqual(contexto.validation.threshold, official_threshold())


if __name__ == "__main__":
    unittest.main()
