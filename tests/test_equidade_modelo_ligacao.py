"""Testes comportamentais da ligação de equidade da Q9.

Executam a ligação real contra os artefatos locais e não se limitam a buscar
palavras no código ou no relatório público.
"""
from __future__ import annotations

import unittest

import numpy as np

from scripts import explorar_equidade_genero_modelo as equidade


class EquidadeModeloLigacaoTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.resultado = equidade.executar_auditoria()

    def test_chave_composta_tem_cardinalidade_um_para_um(self):
        audit = self.resultado["auditoria_da_chave_de_ligacao"]
        self.assertEqual(audit["chave_de_ligacao"], "(ra, ano_preditores) — composta, não apenas RA")
        self.assertEqual(audit["linhas_antes_da_ligacao"], 311)
        self.assertEqual(audit["linhas_com_correspondencia_apos_ligacao"], 311)
        self.assertEqual(audit["linhas_sem_correspondencia_na_base_longitudinal"], 0)
        self.assertEqual(audit["duplicacao_apos_chave_composta"], 0)
        self.assertFalse(audit["correspondencia_multipla_detectada"])
        self.assertEqual(audit["total_linhas_base_longitudinal"], 3030)
        self.assertEqual(audit["chaves_compostas_distintas_na_base"], 3030)
        self.assertEqual(audit["duplicatas_da_chave_composta_na_base"], 0)

    def test_ordem_de_preditores_rotulos_e_probabilidades_e_preservada(self):
        audit = self.resultado["auditoria_da_ordem"]
        self.assertEqual(audit["linhas"], 311)
        self.assertTrue(audit["preditores_na_ordem_oficial"])
        self.assertTrue(audit["rotulos_na_ordem_oficial"])
        self.assertTrue(audit["probabilidades_na_ordem_oficial"])
        self.assertRegex(audit["sha256_rotulos_posicionais"], r"^[0-9a-f]{64}$")
        self.assertRegex(audit["sha256_probabilidades_posicionais"], r"^[0-9a-f]{64}$")

    def test_todas_as_metricas_globais_sao_reproduzidas(self):
        self.assertTrue(self.resultado["reproducao_fiel_do_artefato_oficial"])
        self.assertEqual(
            self.resultado["reproduzido"],
            self.resultado["oficial_para_comparacao"],
        )

    def test_subgrupos_publicaveis_registram_toda_a_matriz(self):
        campos = {
            "n", "positivos", "negativos", "alertas", "verdadeiros_positivos",
            "falsos_positivos", "falsos_negativos", "recall", "precisao",
            "average_precision", "roc_auc",
        }
        grupos = {
            **self.resultado["equidade_por_genero"],
            **self.resultado["equidade_por_faixa_etaria"],
        }
        for nome, grupo in grupos.items():
            with self.subTest(grupo=nome):
                self.assertTrue(campos.issubset(grupo))
                if grupo["status"] == "estimado":
                    self.assertEqual(grupo["positivos"] + grupo["negativos"], grupo["n"])
                    self.assertEqual(grupo["verdadeiros_positivos"] + grupo["falsos_positivos"], grupo["alertas"])

    def test_grupo_sem_duas_classes_nao_publica_auc_nem_celulas_pequenas(self):
        grupo = equidade._metricas(np.ones(30, dtype=int), np.linspace(0.1, 0.9, 30), 0.5)
        self.assertEqual(grupo["status"], "suprimido por privacidade")
        self.assertEqual(grupo["n"], "suprimido")
        self.assertEqual(grupo["positivos"], "suprimido")
        self.assertEqual(grupo["average_precision"], "não estimável para este grupo")
        self.assertEqual(grupo["roc_auc"], "não estimável para este grupo")


if __name__ == "__main__":
    unittest.main()
