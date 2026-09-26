"""Decisão de gestão de 25/09/2026: adoção do candidato "maior recall
mantendo precisão mínima de 40%" (definido na auditoria experimental de
recall temporal) como PONTO DE ATENÇÃO OPERACIONAL — separado do limiar
metodológico original, que permanece intacto.

Nenhum teste aqui altera `artifacts/`, `reports/metricas_modelagem.json`,
`config/ponto_atencao_operacional.json` ou qualquer arquivo do repositório;
os testes de portabilidade usam diretórios temporários, limpos via
`addCleanup` mesmo em caso de falha.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
import inferencia as inf  # noqa: E402
import modelagem  # noqa: E402
import scripts.gerar_configuracao_operacional as gerador_config_operacional  # noqa: E402

TESTS_DIR = Path(__file__).resolve().parent
if str(TESTS_DIR) not in sys.path:
    sys.path.insert(0, str(TESTS_DIR))
from test_inferencia_aplicacao import official_threshold, operational_threshold  # noqa: E402
from test_streamlit_app import (  # noqa: E402
    PAYLOAD_ALTO_RISCO, PAYLOAD_BAIXO_RISCO, PAYLOAD_ZONA_ENTRE_PONTOS, _estado_sintetico,
)

FONTE_EXPERIMENTAL = ROOT / "reports/experimental/analise_recall_temporal.json"
CONFIG_PATH = ROOT / inf.OPERATIONAL_CONFIG_PATH
NOME_CRITERIO = "maior_recall_precisao_minima_40"
MATRIZ_ESPERADA = {"tp": 49, "fp": 38, "tn": 189, "fn": 35}


class RecuperacaoDoValorExatoTests(unittest.TestCase):
    """Item 2 do enunciado: nada é estimado nem copiado manualmente — tudo
    vem, programaticamente, de reports/experimental/analise_recall_temporal.json."""

    @classmethod
    def setUpClass(cls):
        cls.dados = json.loads(FONTE_EXPERIMENTAL.read_text(encoding="utf-8"))
        cls.candidato = cls.dados["candidatos"][NOME_CRITERIO]

    def test_nome_do_criterio_presente(self):
        self.assertIn(NOME_CRITERIO, self.dados["candidatos"])

    def test_valor_exato_do_limiar(self):
        self.assertEqual(self.candidato["limiar"], 0.15104892174638265)

    def test_metricas_no_desenvolvimento_presentes(self):
        oof = self.candidato["oof"]
        self.assertIn("recall", oof)
        self.assertIn("precisao", oof)
        self.assertGreaterEqual(oof["recall"], 0.0)
        self.assertGreaterEqual(oof["precisao"], 0.40 - 1e-9)  # critério: precisão OOF >= 40%

    def test_metricas_no_teste_temporal_presentes(self):
        t = self.candidato["temporal"]
        self.assertAlmostEqual(t["recall"], 0.5833333333333334, places=12)
        self.assertAlmostEqual(t["precisao"], 0.5632183908045977, places=12)

    def test_matriz_de_confusao_correspondente_49_38_189_35(self):
        t = self.candidato["temporal"]
        obtido = {k: t[k] for k in MATRIZ_ESPERADA}
        self.assertEqual(obtido, MATRIZ_ESPERADA)

    def test_gerador_falha_explicitamente_se_matriz_nao_bater(self):
        """Exercita `scripts/gerar_configuracao_operacional.recuperar_candidato`
        de verdade contra uma cópia adulterada do JSON experimental — uma
        matriz de confusão divergente precisa levantar erro, nunca passar
        silenciosamente."""
        gerador = gerador_config_operacional
        tmp = Path(tempfile.mkdtemp(prefix="fonte_experimental_adulterada_"))
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        adulterado = json.loads(json.dumps(self.dados))
        adulterado["candidatos"][NOME_CRITERIO]["temporal"]["tp"] = 999
        caminho_falso = tmp / "analise_adulterada.json"
        caminho_falso.write_text(json.dumps(adulterado, ensure_ascii=False), encoding="utf-8")

        fonte_original = gerador.FONTE
        gerador.FONTE = caminho_falso
        try:
            with self.assertRaises(AssertionError):
                gerador.recuperar_candidato()
        finally:
            gerador.FONTE = fonte_original

    def test_criterio_definido_somente_com_oof_do_desenvolvimento(self):
        """O texto do critério cita explicitamente 'OOF'; e o candidato só
        carrega métricas de 'oof' e 'temporal' — nunca uma escolha feita
        olhando o teste temporal."""
        self.assertIn("oof", self.candidato["criterio"].lower())
        self.assertIn("oof", self.candidato)
        self.assertIn("temporal", self.candidato)  # só como AVALIAÇÃO POSTERIOR, não escolha


class ConfiguracaoOperacionalIntegridadeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        cls.schema = modelagem.read_json(ROOT / modelagem.SCHEMA)

    def test_arquivo_existe_versionado_fora_de_artifacts(self):
        self.assertTrue(CONFIG_PATH.is_file())
        self.assertNotIn("artifacts", CONFIG_PATH.parts)
        self.assertNotIn("local_data", CONFIG_PATH.parts)

    def test_campos_obrigatorios_presentes(self):
        obrigatorios = {
            "versao", "finalidade", "modelo", "limiar_metodologico_original",
            "ponto_atencao_operacional", "criterio_selecao", "data_da_decisao",
            "metricas_temporais", "avisos", "origem",
        }
        self.assertTrue(obrigatorios.issubset(self.config))

    def test_limiar_metodologico_original_preservado(self):
        """Item 3/6: o limiar metodológico original `0.26696679375725973`
        continua exatamente o mesmo, tanto no schema oficial quanto
        registrado (para conferência cruzada) na configuração operacional."""
        self.assertEqual(self.schema["limiar"], 0.26696679375725973)
        self.assertEqual(self.config["limiar_metodologico_original"], 0.26696679375725973)
        self.assertEqual(self.config["limiar_metodologico_original"], self.schema["limiar"])
        self.assertEqual(official_threshold(), 0.26696679375725973)

    def test_ponto_operacional_e_o_valor_exato_do_candidato(self):
        self.assertEqual(self.config["ponto_atencao_operacional"]["limiar"], 0.15104892174638265)
        self.assertEqual(operational_threshold(), 0.15104892174638265)

    def test_avisos_obrigatorios_presentes(self):
        avisos = self.config["avisos"]
        for chave in ("altera_somente_a_classificacao", "supervisao_humana", "abaixo_do_ponto_nao_elimina_risco"):
            self.assertIn(chave, avisos)
            self.assertTrue(avisos[chave].strip())

    def test_hash_de_proveniencia_bate_com_a_fonte_atual(self):
        """Registro histórico do momento da decisão — não uma dependência
        de execução, mas precisa ser um hash real e verificável."""
        sha_atual = hashlib.sha256(FONTE_EXPERIMENTAL.read_bytes()).hexdigest()
        self.assertEqual(self.config["origem"]["sha256_no_momento_da_decisao"], sha_atual)
        self.assertTrue(self.config["origem"]["criterio_definido_somente_com_oof_do_desenvolvimento"])

    def test_aplicacao_recusa_configuracao_com_limiar_original_divergente(self):
        tmp = Path(tempfile.mkdtemp(prefix="config_operacional_invalida_"))
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        adulterada = dict(self.config)
        adulterada["limiar_metodologico_original"] = 0.5
        (tmp / "config").mkdir(parents=True, exist_ok=True)
        (tmp / inf.OPERATIONAL_CONFIG_PATH).write_text(json.dumps(adulterada, ensure_ascii=False), encoding="utf-8")
        with self.assertRaises(inf.PublicValidationError):
            inf.load_operational_config(tmp, self.schema)

    def test_aplicacao_recusa_configuracao_sem_campo_obrigatorio(self):
        tmp = Path(tempfile.mkdtemp(prefix="config_operacional_incompleta_"))
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        incompleta = dict(self.config)
        del incompleta["avisos"]
        (tmp / "config").mkdir(parents=True, exist_ok=True)
        (tmp / inf.OPERATIONAL_CONFIG_PATH).write_text(json.dumps(incompleta, ensure_ascii=False), encoding="utf-8")
        with self.assertRaises(inf.PublicValidationError):
            inf.load_operational_config(tmp, self.schema)

    def test_aplicacao_recusa_configuracao_ausente(self):
        tmp = Path(tempfile.mkdtemp(prefix="config_operacional_ausente_"))
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        with self.assertRaises(inf.PublicValidationError):
            inf.load_operational_config(tmp, self.schema)

    def test_aplicacao_recusa_limiar_operacional_fora_de_0_1(self):
        tmp = Path(tempfile.mkdtemp(prefix="config_operacional_limiar_invalido_"))
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        adulterada = json.loads(json.dumps(self.config))
        adulterada["ponto_atencao_operacional"]["limiar"] = 1.5
        (tmp / "config").mkdir(parents=True, exist_ok=True)
        (tmp / inf.OPERATIONAL_CONFIG_PATH).write_text(json.dumps(adulterada, ensure_ascii=False), encoding="utf-8")
        with self.assertRaises(inf.PublicValidationError):
            inf.load_operational_config(tmp, self.schema)


class ArtefatosOficiaisInalteradosTests(unittest.TestCase):
    """Item 7 da preservação metodológica: nada em artifacts/ ou nas
    métricas oficiais pode ter sido tocado por esta rodada."""

    ARQUIVOS = (
        "artifacts/configuracao_congelada.json",
        "artifacts/schema_modelo.json",
        "artifacts/modelo_avaliado.joblib",
        "artifacts/avaliacao_temporal.json",
        "reports/metricas_modelagem.json",
        "reports/relatorio_modelagem.md",
    )

    def test_hashes_inalterados_apos_carregar_a_configuracao_operacional(self):
        antes = {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in self.ARQUIVOS}
        inf.prepare_application(ROOT)  # carrega tudo, inclusive a config operacional
        depois = {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in self.ARQUIVOS}
        self.assertEqual(antes, depois)

    def test_sete_preditores_preservados_na_mesma_ordem(self):
        self.assertEqual(
            list(inf.FEATURES),
            ["ida", "ieg", "iaa", "ips", "ipv", "fase_origem", "defasagem_origem"])

    def test_nenhum_vestigio_de_retreino_ou_recalibracao_no_codigo_novo(self):
        codigo = (SRC / "inferencia.py").read_text(encoding="utf-8")
        for termo in (".fit(", "CalibratedClassifierCV", "IsotonicRegression", "LogisticRegression("):
            self.assertNotIn(termo, codigo)


class ProbabilidadeIdenticaClassificacaoDiferenteTests(unittest.TestCase):
    """Itens 5/8/9: mesma probabilidade antes e depois; só a comparação
    muda; e só o caso entre os dois pontos muda de classificação."""

    @classmethod
    def setUpClass(cls):
        cls.contexto = inf.prepare_application(ROOT)

    def _probabilidade_manual(self, payload):
        validado = inf.validate_inputs(payload)
        frame = inf.build_feature_frame(validado)
        proba = self.contexto.pipeline.predict_proba(frame)
        classes = [int(c) for c in self.contexto.pipeline.classes_]
        return float(proba[0, classes.index(1)])

    def test_probabilidade_e_a_mesma_independente_do_ponto_usado(self):
        for payload in (PAYLOAD_BAIXO_RISCO, PAYLOAD_ZONA_ENTRE_PONTOS, PAYLOAD_ALTO_RISCO):
            with self.subTest(payload=payload):
                manual = self._probabilidade_manual(payload)
                resultado = inf.run_inference(self.contexto, payload)
                self.assertAlmostEqual(manual, resultado.probability, places=12)

    def test_somente_o_caso_intermediario_muda_de_classificacao(self):
        limiar_original = self.contexto.validation.threshold
        limiar_operacional = self.contexto.operational["ponto_atencao_operacional"]["limiar"]
        self.assertLess(limiar_operacional, limiar_original)

        casos = {
            "abaixo dos dois pontos": PAYLOAD_BAIXO_RISCO,
            "entre os dois pontos": PAYLOAD_ZONA_ENTRE_PONTOS,
            "acima dos dois pontos": PAYLOAD_ALTO_RISCO,
        }
        mudancas = {}
        for nome, payload in casos.items():
            proba = self._probabilidade_manual(payload)
            risco_original = proba >= limiar_original
            risco_operacional = proba >= limiar_operacional
            mudancas[nome] = risco_original != risco_operacional

        self.assertFalse(mudancas["abaixo dos dois pontos"])
        self.assertTrue(mudancas["entre os dois pontos"])
        self.assertFalse(mudancas["acima dos dois pontos"])

    def test_payload_zona_entre_pontos_esta_de_fato_entre_os_dois_limiares(self):
        proba = self._probabilidade_manual(PAYLOAD_ZONA_ENTRE_PONTOS)
        self.assertGreater(proba, self.contexto.operational["ponto_atencao_operacional"]["limiar"])
        self.assertLess(proba, self.contexto.validation.threshold)


class AplicacaoUsaNovoPontoTests(unittest.TestCase):
    """Itens 10/11: a aplicação (via `run_inference`) e o relatório usam o
    ponto operacional — não mais o metodológico original — para
    classificar."""

    @classmethod
    def setUpClass(cls):
        cls.contexto = inf.prepare_application(ROOT)

    def test_run_inference_classifica_pelo_ponto_operacional(self):
        resultado = inf.run_inference(self.contexto, PAYLOAD_ZONA_ENTRE_PONTOS)
        self.assertEqual(resultado.threshold, self.contexto.operational["ponto_atencao_operacional"]["limiar"])
        self.assertTrue(resultado.is_risk)  # acima do operacional, abaixo do original

    def test_relatorio_html_menciona_o_ponto_operacional(self):
        import importlib
        app_module = importlib.import_module("streamlit_app")
        resultado = inf.run_inference(self.contexto, PAYLOAD_ZONA_ENTRE_PONTOS)
        estado = _estado_sintetico(resultado=resultado, entradas=dict(PAYLOAD_ZONA_ENTRE_PONTOS))
        html_gerado = app_module._gerar_relatorio_html(estado)
        self.assertIn("Ponto de atenção operacional", html_gerado)
        self.assertIn(f"{round(resultado.threshold * 100)}%", html_gerado)


class CopiaPublicaMinimaTests(unittest.TestCase):
    """Item 12: a configuração operacional está entre os caminhos públicos
    obrigatórios e presente em uma cópia pública mínima. Item 13: nenhuma
    dependência de local_data/ ou reports/experimental/ nesse caminho."""

    def test_config_operacional_esta_nos_caminhos_publicos_obrigatorios(self):
        self.assertIn(inf.OPERATIONAL_CONFIG_PATH, inf.PUBLIC_REQUIRED_PATHS)

    def test_copia_publica_minima_inicializa_com_a_configuracao_operacional(self):
        tmp = Path(tempfile.mkdtemp(prefix="copia_publica_ponto_atencao_"))
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        for relativo in inf.PUBLIC_REQUIRED_PATHS:
            destino = tmp / relativo
            destino.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / relativo, destino)
        for pasta in ("DATATHON", "local_data", "local_recovery"):
            self.assertFalse((tmp / pasta).exists())
        self.assertFalse((tmp / "reports" / "experimental").exists())
        contexto = inf.prepare_application(root=tmp)
        self.assertEqual(
            contexto.operational["ponto_atencao_operacional"]["limiar"], 0.15104892174638265)

    def test_inferencia_py_nao_le_reports_experimental_em_tempo_de_execucao(self):
        """A palavra "local_data" aparece legitimamente em docstrings deste
        módulo (explicando por que ele NUNCA lê de lá); o que não pode
        existir é uma leitura de verdade de `reports/experimental/` ou uma
        construção de caminho para `local_data/` fora de comentário."""
        codigo = (SRC / "inferencia.py").read_text(encoding="utf-8")
        # Bane a REFERÊNCIA VIVA (string literal usável como caminho), não a
        # palavra em prosa/comentário explicando por que ela não é lida.
        for literal in ('"reports/experimental', "'reports/experimental",
                        '"local_data', "'local_data"):
            self.assertNotIn(literal, codigo)


class LinguagemPublicaTests(unittest.TestCase):
    def test_frases_obrigatorias_presentes_nos_textos(self):
        import textos_aplicacao as textos
        self.assertIn("40%", textos.EXPLICACAO_AJUSTE_PONTO_ATENCAO)
        self.assertIn("58%", textos.EXPLICACAO_AJUSTE_PONTO_ATENCAO)
        self.assertIn("observação pedagógica", textos.EXPLICACAO_MAIS_ENCAMINHADOS_OBSERVACAO)
        self.assertIn("não representa diagnóstico nem intervenção automática",
                       textos.EXPLICACAO_MAIS_ENCAMINHADOS_OBSERVACAO)

    def test_frases_proibidas_ausentes(self):
        import textos_aplicacao as textos
        codigo = (SRC / "textos_aplicacao.py").read_text(encoding="utf-8").lower()
        proibidas = (
            "o modelo foi retreinado", "modelo ficou mais preciso",
            "a probabilidade individual melhorou", "recall de 58% é suficiente",
            "resultado abaixo do ponto significa ausência de risco",
        )
        for frase in proibidas:
            with self.subTest(frase=frase):
                self.assertNotIn(frase, codigo)

    def test_app_nao_afirma_retreino_nem_suficiencia(self):
        codigo_app = (ROOT / "streamlit_app.py").read_text(encoding="utf-8").lower()
        for frase in ("modelo foi retreinado", "modelo ficou mais preciso",
                      "probabilidade individual melhorou"):
            self.assertNotIn(frase, codigo_app)


if __name__ == "__main__":
    unittest.main()
