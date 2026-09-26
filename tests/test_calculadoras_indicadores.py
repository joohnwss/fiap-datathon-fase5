"""Testes das calculadoras de indicadores com fórmula oficial confirmada
(defasagem e IAN) — ver docs/auditoria_calculadoras_indicadores.md."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import calculadoras_indicadores as calc  # noqa: E402


class TestCalcularDefasagem(unittest.TestCase):
    def test_exemplo_oficial_linha_280_2024(self):
        # PEDE_ Pontos importantes.docx, §§6-13: D = fase efetiva - fase ideal.
        self.assertEqual(calc.calcular_defasagem(3, 3), 0)
        self.assertEqual(calc.calcular_defasagem(2, 4), -2)
        self.assertEqual(calc.calcular_defasagem(5, 2), 3)

    def test_limites_exatos_da_faixa_de_fases(self):
        self.assertEqual(calc.calcular_defasagem(0, 0), 0)
        self.assertEqual(calc.calcular_defasagem(7, 0), 7)
        self.assertEqual(calc.calcular_defasagem(0, 7), -7)

    def test_fase_efetiva_fora_da_faixa_levanta_erro(self):
        with self.assertRaises(calc.EntradaInvalidaError):
            calc.calcular_defasagem(9, 0)
        with self.assertRaises(calc.EntradaInvalidaError):
            calc.calcular_defasagem(-1, 0)

    def test_fase_ideal_fora_da_faixa_levanta_erro(self):
        with self.assertRaises(calc.EntradaInvalidaError):
            calc.calcular_defasagem(0, 9)
        with self.assertRaises(calc.EntradaInvalidaError):
            calc.calcular_defasagem(0, -1)

    def test_tipo_invalido_levanta_erro(self):
        with self.assertRaises(calc.EntradaInvalidaError):
            calc.calcular_defasagem("3", 2)  # type: ignore[arg-type]
        with self.assertRaises(calc.EntradaInvalidaError):
            calc.calcular_defasagem(3.5, 2)  # type: ignore[arg-type]

    def test_booleano_nao_e_aceito_como_fase(self):
        # bool é subtipo de int em Python; nunca é uma fase válida.
        with self.assertRaises(calc.EntradaInvalidaError):
            calc.calcular_defasagem(True, 0)  # type: ignore[arg-type]


class TestIanPelaDefasagem(unittest.TestCase):
    def test_sem_defasagem_gera_ian_dez(self):
        self.assertEqual(calc.ian_pela_defasagem(0), 10.0)
        self.assertEqual(calc.ian_pela_defasagem(5), 10.0)

    def test_defasagem_moderada_gera_ian_cinco(self):
        self.assertEqual(calc.ian_pela_defasagem(-0.5), 5.0)
        self.assertEqual(calc.ian_pela_defasagem(-2), 5.0)

    def test_defasagem_severa_gera_ian_dois_e_meio(self):
        self.assertEqual(calc.ian_pela_defasagem(-2.1), 2.5)
        self.assertEqual(calc.ian_pela_defasagem(-10), 2.5)

    def test_limite_exato_entre_categorias(self):
        # D>=0 -> 10; -2<=D<0 -> 5; D<-2 -> 2.5 (limiares fechados/abertos documentados).
        self.assertEqual(calc.ian_pela_defasagem(-1.9999), 5.0)
        self.assertEqual(calc.ian_pela_defasagem(-2.0001), 2.5)

    def test_none_levanta_erro(self):
        with self.assertRaises(calc.EntradaInvalidaError):
            calc.ian_pela_defasagem(None)  # type: ignore[arg-type]

    def test_nao_numero_levanta_erro(self):
        with self.assertRaises(calc.EntradaInvalidaError):
            calc.ian_pela_defasagem("abc")  # type: ignore[arg-type]

    def test_infinito_e_nan_levantam_erro(self):
        with self.assertRaises(calc.EntradaInvalidaError):
            calc.ian_pela_defasagem(float("inf"))
        with self.assertRaises(calc.EntradaInvalidaError):
            calc.ian_pela_defasagem(float("nan"))

    def test_booleano_nao_e_aceito_como_defasagem(self):
        with self.assertRaises(calc.EntradaInvalidaError):
            calc.ian_pela_defasagem(True)  # type: ignore[arg-type]

    def test_consistente_com_dados_pede_expected_ian_value(self):
        # Nenhuma fórmula reinventada: a mesma regra de src/dados_pede.py.
        dados_pede_path = Path(__file__).resolve().parents[1] / "src"
        if str(dados_pede_path) not in sys.path:
            sys.path.insert(0, str(dados_pede_path))
        import dados_pede  # noqa: E402

        for d in (-10, -3, -2.5, -2, -1, -0.5, 0, 0.5, 3, 10):
            self.assertEqual(calc.ian_pela_defasagem(d), dados_pede.expected_ian_value(d))


class TestCategoriaDefasagem(unittest.TestCase):
    def test_categorias_corretas(self):
        self.assertEqual(calc.categoria_defasagem(0), "Em fase")
        self.assertEqual(calc.categoria_defasagem(5), "Em fase")
        self.assertEqual(calc.categoria_defasagem(-0.5), "Defasagem moderada")
        self.assertEqual(calc.categoria_defasagem(-2), "Defasagem moderada")
        self.assertEqual(calc.categoria_defasagem(-2.1), "Defasagem severa")

    def test_none_e_invalido(self):
        with self.assertRaises(calc.EntradaInvalidaError):
            calc.categoria_defasagem(None)  # type: ignore[arg-type]


class TestSugerirFaseIdealPorIdade(unittest.TestCase):
    def test_idade_8_e_ambigua_alfa_ou_fase1(self):
        resultado = calc.sugerir_fase_ideal_por_idade(8)
        self.assertTrue(resultado["ambigua"])
        codigos = {codigo for _, codigo in resultado["candidatas"]}
        self.assertEqual(codigos, {"0", "1"})

    def test_idade_12_sugere_apenas_fase_3(self):
        resultado = calc.sugerir_fase_ideal_por_idade(12)
        self.assertFalse(resultado["ambigua"])
        self.assertEqual([codigo for _, codigo in resultado["candidatas"]], ["3"])

    def test_idades_de_fase_unica_nao_sao_ambiguas(self):
        for idade, fase_esperada in ((14, "4"), (15, "5"), (16, "6"), (17, "7")):
            with self.subTest(idade=idade):
                resultado = calc.sugerir_fase_ideal_por_idade(idade)
                self.assertFalse(resultado["ambigua"])
                self.assertEqual([codigo for _, codigo in resultado["candidatas"]], [fase_esperada])

    def test_idade_18_ou_mais_sugere_fase_8(self):
        resultado = calc.sugerir_fase_ideal_por_idade(20)
        self.assertEqual([codigo for _, codigo in resultado["candidatas"]], ["8"])

    def test_idade_fora_de_qualquer_faixa_nao_sugere_nada(self):
        resultado = calc.sugerir_fase_ideal_por_idade(3)
        self.assertEqual(resultado["candidatas"], [])
        self.assertFalse(resultado["ambigua"])

    def test_idade_invalida(self):
        with self.assertRaises(calc.EntradaInvalidaError):
            calc.sugerir_fase_ideal_por_idade(-1)
        with self.assertRaises(calc.EntradaInvalidaError):
            calc.sugerir_fase_ideal_por_idade(12.5)  # type: ignore[arg-type]
        with self.assertRaises(calc.EntradaInvalidaError):
            calc.sugerir_fase_ideal_por_idade(True)  # type: ignore[arg-type]


class TestCalcularIda(unittest.TestCase):
    def test_media_exata_das_tres_notas(self):
        self.assertAlmostEqual(calc.calcular_ida(6, 7, 8), 7.0)
        self.assertAlmostEqual(calc.calcular_ida(10, 10, 10), 10.0)
        self.assertAlmostEqual(calc.calcular_ida(0, 0, 0), 0.0)

    def test_aceita_ponto_como_separador_decimal_via_float(self):
        self.assertAlmostEqual(calc.calcular_ida(6.5, 7.25, 8.0), (6.5 + 7.25 + 8.0) / 3)

    def test_limites_0_e_10(self):
        self.assertAlmostEqual(calc.calcular_ida(0, 10, 5), 5.0)

    def test_rejeita_nota_abaixo_de_0_ou_acima_de_10(self):
        with self.assertRaises(calc.EntradaInvalidaError):
            calc.calcular_ida(-0.1, 5, 5)
        with self.assertRaises(calc.EntradaInvalidaError):
            calc.calcular_ida(5, 10.1, 5)

    def test_nao_calcula_com_nota_ausente(self):
        with self.assertRaises(calc.EntradaInvalidaError):
            calc.calcular_ida(None, 7, 8)  # type: ignore[arg-type]
        with self.assertRaises(calc.EntradaInvalidaError):
            calc.calcular_ida(6, None, None)  # type: ignore[arg-type]

    def test_nenhuma_imputacao_de_nota_ausente(self):
        """Duas ou uma nota não geram um IDA "parcial" com peso redistribuído
        — a ausência de qualquer uma das três levanta erro, nunca calcula."""
        with self.assertRaises(calc.EntradaInvalidaError):
            calc.calcular_ida(6, 7, None)  # type: ignore[arg-type]


class TestCalcularIaa(unittest.TestCase):
    def test_grupo_de_fase(self):
        self.assertEqual(calc.grupo_fase_iaa("0"), "0-2")
        self.assertEqual(calc.grupo_fase_iaa("2"), "0-2")
        self.assertEqual(calc.grupo_fase_iaa("3"), "3-8")
        self.assertEqual(calc.grupo_fase_iaa("7"), "3-8")

    def test_todas_respostas_a_soma_exatamente_10_nos_dois_grupos(self):
        respostas_a = {i: "A" for i in range(1, 7)}
        self.assertEqual(calc.calcular_iaa("1", respostas_a), 10)
        self.assertEqual(calc.calcular_iaa("5", respostas_a), 10)

    def test_valores_da_tabela_40_fases_0_a_2(self):
        respostas = {1: "A", 2: "B", 3: "C", 4: "A", 5: "B", 6: "C"}
        esperado = 10 / 6 + 7 / 6 + 3.5 / 6 + 10 / 6 + 7 / 6 + 3.5 / 6
        self.assertAlmostEqual(calc.calcular_iaa("0", respostas), esperado)

    def test_valores_da_tabela_40_fases_3_a_8_incluem_d(self):
        respostas = {1: "A", 2: "B", 3: "C", 4: "D", 5: "D", 6: "D"}
        esperado = 10 / 6 + 7.5 / 6 + 5 / 6 + (2.5 / 6) * 3
        self.assertAlmostEqual(calc.calcular_iaa("4", respostas), esperado)

    def test_resposta_d_invalida_para_fases_0_a_2(self):
        respostas = {1: "A", 2: "B", 3: "C", 4: "D", 5: "A", 6: "A"}
        with self.assertRaises(calc.EntradaInvalidaError):
            calc.calcular_iaa("1", respostas)

    def test_exige_as_seis_respostas(self):
        with self.assertRaises(calc.EntradaInvalidaError):
            calc.calcular_iaa("1", {1: "A", 2: "A", 3: "A", 4: "A", 5: "A"})

    def test_fase_fora_do_dominio(self):
        with self.assertRaises(calc.EntradaInvalidaError):
            calc.grupo_fase_iaa("9")


class TestCalcularInde(unittest.TestCase):
    def test_pesos_fases_0_a_7(self):
        pesos = calc.pesos_inde("3")
        self.assertEqual(sum(pesos.values()), 1.0)
        self.assertEqual(pesos["ida"], 0.2)
        self.assertEqual(pesos["ipv"], 0.2)

    def test_pesos_fase_8(self):
        pesos = calc.pesos_inde("8")
        self.assertEqual(sum(pesos.values()), 1.0)
        self.assertEqual(pesos["ida"], 0.4)
        self.assertNotIn("ipp", pesos)
        self.assertNotIn("ipv", pesos)

    def test_calculo_completo_fases_0_a_7(self):
        componentes = {"ian": 10, "ida": 7, "ieg": 8, "iaa": 9, "ips": 6, "ipp": 7, "ipv": 8}
        valor, faltantes = calc.calcular_inde("3", componentes)
        self.assertEqual(faltantes, [])
        esperado = 10 * .1 + 7 * .2 + 8 * .2 + 9 * .1 + 6 * .1 + 7 * .1 + 8 * .2
        self.assertAlmostEqual(valor, esperado)

    def test_componente_ausente_nao_calcula_parcial(self):
        valor, faltantes = calc.calcular_inde("3", {"ian": 10, "ida": 7})
        self.assertIsNone(valor)
        self.assertEqual(set(faltantes), {"ieg", "iaa", "ips", "ipp", "ipv"})

    def test_nenhuma_substituicao_por_zero(self):
        valor, faltantes = calc.calcular_inde("3", {
            "ian": 10, "ida": 7, "ieg": 8, "iaa": 9, "ips": 6, "ipp": None, "ipv": 8,
        })
        self.assertIsNone(valor)
        self.assertEqual(faltantes, ["ipp"])


if __name__ == "__main__":
    unittest.main()
