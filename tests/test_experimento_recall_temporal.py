"""Testes da auditoria experimental de recall temporal.

Não testam frases no relatório: executam a análise real (uma única vez,
compartilhada via `setUpClass`, como já é o padrão em
`test_equidade_modelo_ligacao.py`) e verificam o comportamento.
"""
from __future__ import annotations

import hashlib
import inspect
import unittest

import numpy as np

from scripts import experimento_recall_temporal as exp

ARTEFATOS_PROTEGIDOS = (
    "artifacts/configuracao_congelada.json",
    "artifacts/schema_modelo.json",
    "artifacts/modelo_avaliado.joblib",
    "artifacts/avaliacao_temporal.json",
    "reports/metricas_modelagem.json",
    "reports/relatorio_modelagem.md",
    "reports/curvas_modelagem.png",
    "docs/TASKS.md",
)


def _sha256(path):
    return hashlib.sha256((exp.ROOT / path).read_bytes()).hexdigest()


class ExperimentoRecallTemporalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.hashes_antes = {p: _sha256(p) for p in ARTEFATOS_PROTEGIDOS}
        cls.resultado = exp.executar()

    def test_reproducao_bate_exatamente_com_artefato_oficial(self):
        self.assertTrue(self.resultado["reproducao"]["reproducao_confere"])
        oficial = exp.modelagem.read_json(exp.ROOT / exp.modelagem.METRICS)
        self.assertEqual(self.resultado["reproducao"]["oof"], oficial["oof"]["metricas"])
        self.assertEqual(self.resultado["reproducao"]["temporal"], oficial["temporal"]["metricas"])
        self.assertEqual(self.resultado["reproducao"]["limiar_oficial"], 0.26696679375725973)

    def test_selecao_de_candidatos_nao_aceita_dados_temporais(self):
        """Garantia estrutural: a assinatura de `selecionar_candidatos` não
        tem parâmetro para nada do teste temporal — não há como, mesmo por
        engano, escolher um limiar espiando o teste."""
        parametros = list(inspect.signature(exp.selecionar_candidatos).parameters)
        for proibido in ("y_temporal", "p_temporal", "yt", "Xt"):
            self.assertNotIn(proibido, parametros)
        self.assertEqual(parametros[:2], ["y_dev", "p_dev"])

    def test_candidatos_sao_definidos_so_pelo_desenvolvimento(self):
        """Mesmos dados de desenvolvimento => mesmos limiares, não importa
        o que exista (ou não) do lado do teste temporal."""
        frozen, schema, limiar_oficial, Xd, yd, Xt, yt, pipeline = exp.carregar_dados_oficiais()
        p_oof, _ = exp.reproduzir_oof(Xd, yd)
        candidatos_a = exp.selecionar_candidatos(yd, p_oof)
        candidatos_b = exp.selecionar_candidatos(yd, p_oof)  # nenhum argumento temporal em nenhuma chamada
        self.assertEqual({n: c["limiar"] for n, c in candidatos_a.items()},
                          {n: c["limiar"] for n, c in candidatos_b.items()})

    def test_determinismo_da_reproducao_oof(self):
        frozen, schema, limiar_oficial, Xd, yd, Xt, yt, pipeline = exp.carregar_dados_oficiais()
        p1, limiar1 = exp.reproduzir_oof(Xd, yd)
        p2, limiar2 = exp.reproduzir_oof(Xd, yd)
        np.testing.assert_array_equal(p1, p2)
        self.assertEqual(limiar1, limiar2)

    def test_nenhum_artefato_oficial_e_sobrescrito(self):
        for caminho in ARTEFATOS_PROTEGIDOS:
            with self.subTest(caminho=caminho):
                self.assertEqual(_sha256(caminho), self.hashes_antes[caminho],
                                  f"{caminho} foi modificado pela análise experimental")

    def test_matrizes_de_confusao_sao_consistentes(self):
        n_dev = self.resultado["reproducao"]["oof"]["n"]
        n_temp = self.resultado["reproducao"]["temporal"]["n"]
        for nome, dados in self.resultado["candidatos"].items():
            with self.subTest(candidato=nome):
                o = dados["oof"]
                self.assertEqual(o["tp"] + o["fp"] + o["tn"] + o["fn"], n_dev)
                self.assertEqual(o["tp"] + o["fp"], o["sinalizados"])
                t = dados["temporal"]
                self.assertEqual(t["tp"] + t["fp"] + t["tn"] + t["fn"], n_temp)
                self.assertEqual(t["tp"] + t["fp"], t["sinalizados"])

    def test_baseline_majoritario_e_um_menos_prevalencia(self):
        y = np.array([1, 1, 1, 0, 0, 0, 0, 0, 0, 0])
        baseline = exp.baseline_majoritario(y)
        self.assertAlmostEqual(baseline["acuracia"], 0.7)
        self.assertAlmostEqual(baseline["acuracia_balanceada"], 0.5)
        self.assertEqual(baseline["recall_classe_positiva"], 0.0)
        self.assertEqual(baseline["recall_classe_negativa"], 1.0)
        # E também bate com o baseline real relatado para o teste temporal:
        temp = self.resultado["baseline_majoritario"]["temporal"]
        self.assertAlmostEqual(temp["acuracia"], 1.0 - temp["prevalencia"])

    def test_privacidade_nos_subgrupos_de_equidade(self):
        """Nenhum grupo pequeno vaza contagem, mesmo indiretamente."""
        for nome_candidato, blocos in self.resultado["equidade"].items():
            for categoria in ("genero", "faixa_etaria_aproximada"):
                for grupo, valores in blocos[categoria].items():
                    with self.subTest(candidato=nome_candidato, categoria=categoria, grupo=grupo):
                        if valores["status"] == "suprimido por privacidade":
                            for campo in ("n", "positivos", "negativos", "alertas",
                                          "verdadeiros_positivos", "falsos_positivos", "falsos_negativos"):
                                self.assertEqual(valores[campo], "suprimido")
                        else:
                            self.assertEqual(valores["status"], "estimado")
                            self.assertGreaterEqual(valores["n"], 30)
                            self.assertGreaterEqual(valores["positivos"], 5)
                            self.assertGreaterEqual(valores["negativos"], 5)
            for fase, valores in blocos["fase"].items():
                with self.subTest(candidato=nome_candidato, fase=fase):
                    if valores["status"] == "estimado":
                        self.assertGreaterEqual(valores["metricas"]["n"], 30)

    def test_candidato_recalibrado_reproduz_o_par_recall_precisao_do_criterio_original(self):
        """Prova empírica de que a recalibração monótona não cria nova
        capacidade de ordenação: o par (recall, precisão) do critério
        'maior F2' aplicado às probabilidades recalibradas por Platt deve
        bater com o candidato 'maior_f2' original (mesma curva PR/ROC)."""
        original = self.resultado["candidatos"]["maior_f2"]["temporal"]
        platt = self.resultado["recalibracao"]["platt"]["candidato_maior_f2_recalibrado_temporal"]
        self.assertAlmostEqual(original["recall"], platt["recall"], places=6)
        self.assertAlmostEqual(original["precisao"], platt["precisao"], places=6)

    def test_bootstrap_nao_mistura_desenvolvimento_e_teste(self):
        """`bootstrap_temporal` só recebe o teste temporal — sem parâmetro
        de desenvolvimento na assinatura."""
        parametros = list(inspect.signature(exp.bootstrap_temporal).parameters)
        self.assertNotIn("y_dev", parametros)
        self.assertNotIn("p_dev", parametros)
        for candidato, intervalos in self.resultado["bootstrap_temporal"].items():
            with self.subTest(candidato=candidato):
                for grupo in ("a", "b", "diferenca_b_menos_a"):
                    for metrica in ("recall", "precisao", "acuracia_balanceada"):
                        self.assertEqual(intervalos[grupo][metrica]["validas"] +
                                          intervalos[grupo][metrica]["invalidas"], 2000)

    def test_classificacao_do_limiar_oficial_e_manter(self):
        self.assertEqual(self.resultado["classificacoes"]["limiar_oficial"], "Manter o limiar oficial")

    def test_candidato_numericamente_identico_ao_oficial_nao_e_rejeitado(self):
        """`maior_youden_j` coincide, neste conjunto, com o limiar oficial —
        deve ser rotulado como equivalente, nunca como "Rejeitado"."""
        if abs(self.resultado["candidatos"]["maior_youden_j"]["limiar"] -
               self.resultado["candidatos"]["limiar_oficial"]["limiar"]) < 1e-9:
            self.assertEqual(self.resultado["classificacoes"]["maior_youden_j"], "Manter o limiar oficial")

    def test_grafico_e_json_experimentais_sao_gerados_fora_dos_artefatos_oficiais(self):
        self.assertTrue((exp.OUT_DIR / "analise_recall_temporal.json").exists())
        self.assertTrue((exp.OUT_DIR / "grafico_candidatos.png").exists())
        self.assertEqual(exp.OUT_DIR, exp.ROOT / "reports/experimental")


if __name__ == "__main__":
    unittest.main()
