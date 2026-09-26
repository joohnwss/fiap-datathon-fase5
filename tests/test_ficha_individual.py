"""Contrato funcional da ficha individual completa."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import calculadoras_indicadores as calc  # noqa: E402
import ficha_individual as ficha  # noqa: E402
import inferencia  # noqa: E402


def dados_validos(**mudancas):
    dados = {
        "identificacao": "J.S.", "idade": "14", "sexo": "Feminino",
        "fase_origem": "2", "fase_ideal": "4",
        "ida": "7", "ieg": "8", "iaa": "9", "ips": "6", "ipv": "8",
        "ipp": "7", "defasagem_registrada": "", "escolha_defasagem": None,
    }
    dados.update(mudancas)
    return dados


class ConversaoNumericaTests(unittest.TestCase):
    def test_virgula_decimal(self):
        self.assertEqual(ficha.numero_decimal("7,5"), 7.5)

    def test_ponto_decimal(self):
        self.assertEqual(ficha.numero_decimal("7.5"), 7.5)

    def test_zero_explicito(self):
        self.assertEqual(ficha.numero_decimal("0", minimo=0), 0)

    def test_vazio_nao_vira_zero(self):
        with self.assertRaises(ValueError):
            ficha.numero_decimal("")

    def test_nan_invalido(self):
        with self.assertRaises(ValueError):
            ficha.numero_decimal("nan")

    def test_infinito_invalido(self):
        with self.assertRaises(ValueError):
            ficha.numero_decimal("inf")

    def test_abaixo_de_zero_invalido(self):
        with self.assertRaises(ValueError):
            ficha.numero_decimal("-0,1", minimo=0)

    def test_acima_de_dez_invalido(self):
        with self.assertRaises(ValueError):
            ficha.numero_decimal("10.1", maximo=10)

    def test_idade_inteira(self):
        self.assertEqual(ficha.idade_em_anos("14"), 14)

    def test_idade_decimal_invalida(self):
        with self.assertRaises(ValueError):
            ficha.idade_em_anos("14,5")


class FaseDefasagemIanTests(unittest.TestCase):
    def test_idade_8_tem_duas_candidatas(self):
        resultado = calc.sugerir_fase_ideal_por_idade(8)
        self.assertEqual([c for _, c in resultado["candidatas"]], ["0", "1"])
        self.assertTrue(resultado["ambigua"])

    def test_idade_9_sugere_fase_1(self):
        self.assertEqual(calc.sugerir_fase_ideal_por_idade(9)["candidatas"][0][1], "1")

    def test_idade_14_sugere_fase_4(self):
        self.assertEqual(calc.sugerir_fase_ideal_por_idade(14)["candidatas"][0][1], "4")

    def test_idade_fora_da_tabela_nao_inventa_fase(self):
        self.assertEqual(calc.sugerir_fase_ideal_por_idade(6)["candidatas"], [])

    def test_defasagem_menos_dois(self):
        self.assertEqual(calc.calcular_defasagem(2, 4), -2)

    def test_defasagem_positiva(self):
        self.assertEqual(calc.calcular_defasagem(4, 1), 3)

    def test_defasagem_zero(self):
        self.assertEqual(calc.calcular_defasagem(3, 3), 0)

    def test_ian_em_fase(self):
        self.assertEqual(calc.ian_pela_defasagem(3), 10)

    def test_ian_moderado(self):
        self.assertEqual(calc.ian_pela_defasagem(-2), 5)

    def test_ian_severo(self):
        self.assertEqual(calc.ian_pela_defasagem(-3), 2.5)

    def test_divergencia_exige_confirmacao(self):
        with self.assertRaises(ValueError):
            ficha.resolver_defasagem("2", "4", "-1")

    def test_divergencia_pode_usar_calculada(self):
        self.assertEqual(ficha.resolver_defasagem("2", "4", "-1", "calculada")[0], -2)

    def test_divergencia_pode_usar_registrada(self):
        self.assertEqual(ficha.resolver_defasagem("2", "4", "-1", "registrada")[0], -1)


class FormulasTests(unittest.TestCase):
    def test_ida_media(self):
        self.assertEqual(calc.calcular_ida(6, 7, 8), 7)

    def test_ida_exige_tres_notas(self):
        with self.assertRaises(calc.EntradaInvalidaError):
            calc.calcular_ida(6, 7, None)

    def test_iaa_perguntas_exatas(self):
        self.assertEqual(calc.PERGUNTAS_IAA[2], "Como se sente sobre sua vida familiar?")
        self.assertEqual(len(calc.PERGUNTAS_IAA), 6)

    def test_iaa_inicial_nao_aceita_d(self):
        with self.assertRaises(calc.EntradaInvalidaError):
            calc.calcular_iaa("2", {i: ("D" if i == 6 else "A") for i in range(1, 7)})

    def test_iaa_posterior_aceita_d(self):
        self.assertGreater(calc.calcular_iaa("3", {i: "D" for i in range(1, 7)}), 0)

    def test_iaa_seis_a_exatamente_dez(self):
        self.assertEqual(calc.calcular_iaa("7", {i: "A" for i in range(1, 7)}), 10)

    def test_iaa_resposta_ausente_bloqueia(self):
        with self.assertRaises(calc.EntradaInvalidaError):
            calc.calcular_iaa("3", {i: "A" for i in range(1, 6)})

    def test_inde_alfa_a_7(self):
        componentes = {"ian": 10, "ida": 7, "ieg": 8, "iaa": 9, "ips": 6, "ipp": 7, "ipv": 8}
        self.assertAlmostEqual(calc.calcular_inde("3", componentes)[0], 7.8)

    def test_inde_fase_8(self):
        componentes = {"ian": 10, "ida": 7, "ieg": 8, "iaa": 9, "ips": 6}
        self.assertAlmostEqual(calc.calcular_inde("8", componentes)[0], 7.5)

    def test_inde_incompleto_nao_e_calculado(self):
        valor, faltantes = calc.calcular_inde("3", {"ian": 10})
        self.assertIsNone(valor)
        self.assertIn("ipp", faltantes)


class LimitesDosIndicadoresTests(unittest.TestCase):
    """Nenhum indicador aceita valores fora de 0–10 (nem negativos, nem
    acima de 10, ex.: 100) — inclusive IPP e IPV, revisados nesta rodada."""

    def assertErro(self, campo, valor):
        resultado = ficha.validar_ficha(dados_validos(**{campo: valor}))
        self.assertIn(campo, resultado.erros)
        self.assertIsNone(resultado.payload)

    def assertAceito(self, campo, valor, esperado):
        resultado = ficha.validar_ficha(dados_validos(**{campo: valor}))
        self.assertTrue(resultado.valida, resultado.erros)
        valor_no_payload = resultado.payload.get(campo) if campo in ficha.PREDITORES else None
        if valor_no_payload is not None:
            self.assertAlmostEqual(valor_no_payload, esperado)

    def test_ipp_negativo_rejeitado(self): self.assertErro("ipp", "-1")
    def test_ipp_cem_rejeitado(self): self.assertErro("ipp", "100")
    def test_ipp_zero_aceito(self):
        resultado = ficha.validar_ficha(dados_validos(ipp="0"))
        self.assertTrue(resultado.valida, resultado.erros)
    def test_ipp_dez_aceito(self):
        resultado = ficha.validar_ficha(dados_validos(ipp="10"))
        self.assertTrue(resultado.valida, resultado.erros)
    def test_ipp_acima_de_dez_rejeitado(self): self.assertErro("ipp", "10.5")

    def test_ipv_negativo_rejeitado(self): self.assertErro("ipv", "-1")
    def test_ipv_cem_rejeitado(self): self.assertErro("ipv", "100")
    def test_ipv_zero_aceito(self): self.assertAceito("ipv", "0", 0.0)
    def test_ipv_dez_aceito(self): self.assertAceito("ipv", "10", 10.0)

    def test_ida_cem_rejeitado(self): self.assertErro("ida", "100")
    def test_ieg_cem_rejeitado(self): self.assertErro("ieg", "100")
    def test_iaa_cem_rejeitado(self): self.assertErro("iaa", "100")
    def test_ips_cem_rejeitado(self): self.assertErro("ips", "100")

    def test_ipp_negativo_nao_calcula_inde(self):
        """Um IPP fora do range nunca deve, silenciosamente, entrar no
        cálculo do INDE — a ficha inteira fica inválida antes disso."""
        resultado = ficha.validar_ficha(dados_validos(ipp="-5"))
        self.assertFalse(resultado.valida)


class ValidacaoFichaTests(unittest.TestCase):
    def assertErro(self, campo, **mudancas):
        resultado = ficha.validar_ficha(dados_validos(**mudancas))
        self.assertIn(campo, resultado.erros)
        self.assertIsNone(resultado.payload)

    def test_identificacao_obrigatoria(self): self.assertErro("identificacao", identificacao="")
    def test_idade_obrigatoria(self): self.assertErro("idade", idade="")
    def test_sexo_obrigatorio(self): self.assertErro("sexo", sexo="Selecione")
    def test_fase_atual_obrigatoria(self): self.assertErro("fase_origem", fase_origem="")
    def test_fase_ideal_obrigatoria(self): self.assertErro("fase_ideal", fase_ideal="")
    def test_ida_obrigatorio(self): self.assertErro("ida", ida="")
    def test_ieg_obrigatorio(self): self.assertErro("ieg", ieg="")
    def test_iaa_obrigatorio(self): self.assertErro("iaa", iaa="")
    def test_ips_obrigatorio(self): self.assertErro("ips", ips="")
    def test_ipv_obrigatorio(self): self.assertErro("ipv", ipv="")
    def test_ipp_obrigatorio(self): self.assertErro("ipp", ipp="")

    def test_ficha_completa_e_valida(self):
        self.assertTrue(ficha.validar_ficha(dados_validos()).valida)

    def test_payload_tem_sete_preditores(self):
        payload = ficha.validar_ficha(dados_validos()).payload
        self.assertEqual(len(payload), 7)

    def test_payload_preserva_ordem_oficial(self):
        payload = ficha.validar_ficha(dados_validos()).payload
        self.assertEqual(tuple(payload), inferencia.FEATURES)
        self.assertEqual(tuple(payload), ficha.PREDITORES)

    def test_identificacao_fora_do_payload(self):
        self.assertNotIn("identificacao", ficha.validar_ficha(dados_validos()).payload)

    def test_idade_fora_do_payload(self):
        self.assertNotIn("idade", ficha.validar_ficha(dados_validos()).payload)

    def test_sexo_fora_do_payload(self):
        self.assertNotIn("sexo", ficha.validar_ficha(dados_validos()).payload)

    def test_ian_fora_do_payload(self):
        self.assertNotIn("ian", ficha.validar_ficha(dados_validos()).payload)

    def test_ipp_fora_do_payload(self):
        self.assertNotIn("ipp", ficha.validar_ficha(dados_validos()).payload)

    def test_inde_fora_do_payload(self):
        self.assertNotIn("inde", ficha.validar_ficha(dados_validos()).payload)

    def test_notas_brutas_fora_do_payload(self):
        resultado = ficha.validar_ficha(dados_validos(nota_matematica="7"))
        self.assertNotIn("nota_matematica", resultado.payload)

    def test_payload_aceito_pela_inferencia(self):
        payload = ficha.validar_ficha(dados_validos()).payload
        validado = inferencia.validate_inputs(payload)
        self.assertEqual(tuple(inferencia.build_feature_frame(validado).columns), inferencia.FEATURES)


if __name__ == "__main__":
    unittest.main()
