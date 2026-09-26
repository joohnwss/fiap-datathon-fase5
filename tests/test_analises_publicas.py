import hashlib
import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))

import analises_publicas as publicas


class CamadaPublicaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(publicas.JSON_PATH.read_text(encoding="utf-8"))
        cls.manifest = json.loads(publicas.MANIFEST_PATH.read_text(encoding="utf-8"))

    def test_exatamente_onze_perguntas_literais(self):
        perguntas = tuple(q["pergunta"] for q in self.data["perguntas"])
        self.assertEqual(perguntas, publicas.OFFICIAL_QUESTIONS)
        self.assertEqual(self.data["perguntas_oficiais"], list(publicas.OFFICIAL_QUESTIONS))
        self.assertEqual([q["numero"] for q in self.data["perguntas"]], list(range(1, 12)))

    def test_topicos_sao_secundarios(self):
        for numero, pergunta in enumerate(self.data["perguntas"], 1):
            self.assertEqual(pergunta["numero"], numero)
            self.assertEqual(pergunta["topico"], publicas.TOPICS[numero - 1])
            self.assertNotEqual(pergunta["topico"], pergunta["pergunta"])

    def test_schema_autossuficiente(self):
        obrigatorios = {
            "numero", "topico", "pergunta", "status", "resposta",
            "principais_numeros", "nota_numeros", "grafico",
            "como_interpretar", "observamos", "significado", "uso_ong",
            "limites", "populacao_periodo", "fonte_exata",
            "por_que_importa", "como_foi_analisada",
            "analises_complementares_numeros", "analises_complementares_nota",
            "conclusao", "recortes",
        }
        for pergunta in self.data["perguntas"]:
            self.assertTrue(obrigatorios <= pergunta.keys())
            self.assertTrue(pergunta["principais_numeros"])
            self.assertTrue((ROOT / pergunta["grafico"]).is_file())

    def test_storytelling_e_conclusao_presentes_e_especificos(self):
        """Cada pergunta precisa ter texto de storytelling ("por que importa"
        e "como foi analisada") e um bloco de conclusão com os seis
        elementos exigidos — e o texto não pode ser genérico repetido entre
        perguntas (item 5 da correção: "não uma estrutura genérica
        repetida")."""
        campos_conclusao = {
            "constatacao_principal", "diferencas_entre_grupos", "ponto_de_atencao",
            "limite_da_evidencia", "implicacao_pratica", "proximo_acompanhamento",
        }
        vistos_por_que_importa = set()
        vistos_como_foi_analisada = set()
        for pergunta in self.data["perguntas"]:
            numero = pergunta["numero"]
            with self.subTest(numero=numero):
                self.assertTrue(pergunta["por_que_importa"].strip())
                self.assertTrue(pergunta["como_foi_analisada"].strip())
                self.assertEqual(campos_conclusao, set(pergunta["conclusao"]))
                for campo in campos_conclusao:
                    self.assertTrue(pergunta["conclusao"][campo].strip(), f"{campo} vazio na pergunta {numero}")
                # Nenhum texto de storytelling repetido literalmente entre perguntas.
                self.assertNotIn(pergunta["por_que_importa"], vistos_por_que_importa)
                self.assertNotIn(pergunta["como_foi_analisada"], vistos_como_foi_analisada)
                vistos_por_que_importa.add(pergunta["por_que_importa"])
                vistos_como_foi_analisada.add(pergunta["como_foi_analisada"])

    def test_recortes_documentados_para_as_oito_dimensoes_em_todas_as_perguntas(self):
        """Cada pergunta precisa se posicionar explicitamente sobre as oito
        dimensões de recorte pedidas (sexo, idade, fase, ano, Pedra, situação
        de defasagem, cobertura, trajetória longitudinal); quando não
        implementado, o motivo precisa vir de uma lista fechada de razões
        válidas e nunca ficar vazio ("não aceite 'não foi necessário' sem
        demonstração")."""
        dimensoes = {"sexo", "idade", "fase", "ano", "pedra", "situacao_defasagem",
                    "cobertura", "trajetoria_longitudinal"}
        motivos_validos = {
            "não possui relação educacional clara com a pergunta", "variável ausente",
            "cobertura insuficiente", "grupo pequeno", "risco de reconstrução",
            "redundância com outra análise", "falta de pareamento longitudinal confiável",
        }
        for pergunta in self.data["perguntas"]:
            numero = pergunta["numero"]
            recortes = pergunta["recortes"]
            with self.subTest(numero=numero):
                self.assertEqual(dimensoes, set(recortes))
                for dimensao, info in recortes.items():
                    self.assertIn("implementado", info)
                    self.assertTrue(info.get("detalhe", "").strip(),
                                    f"pergunta {numero}, recorte {dimensao}: detalhe vazio")
                    if not info["implementado"]:
                        self.assertIn(info.get("motivo"), motivos_validos,
                                     f"pergunta {numero}, recorte {dimensao}: motivo inválido ou ausente")

    def test_sexo_e_idade_implementados_no_minimo_exigido_com_motivo_consistente(self):
        """Sexo (gênero) e idade (faixa etária calculada a partir do ano de
        nascimento) foram investigados a fundo nas bases brutas (ver docs do
        módulo em src/analises_publicas.py, docs/mapa_campos.md) e, ao
        contrário da rodada anterior, ESTÃO disponíveis com cobertura e
        privacidade suficientes. A correção pós-auditoria comparativa exigiu
        o recorte no mínimo nas perguntas 1, 2, 3, 9, 10 e 11; nas demais, o
        recorte não foi computado por não ter relação educacional clara com
        o que a pergunta pergunta — não por a variável estar indisponível —
        e o motivo precisa ser idêntico e de uma lista fechada válida."""
        minimo_exigido = {1, 2, 3, 9, 10, 11}
        for pergunta in self.data["perguntas"]:
            numero = pergunta["numero"]
            sexo = pergunta["recortes"]["sexo"]
            idade = pergunta["recortes"]["idade"]
            with self.subTest(numero=numero):
                if numero in minimo_exigido:
                    self.assertTrue(sexo["implementado"], f"pergunta {numero}: sexo deveria estar implementado")
                    self.assertTrue(idade["implementado"], f"pergunta {numero}: idade deveria estar implementada")
                else:
                    self.assertFalse(sexo["implementado"])
                    self.assertFalse(idade["implementado"])
                    self.assertEqual(sexo["motivo"], "não possui relação educacional clara com a pergunta")
                    self.assertEqual(idade["motivo"], "não possui relação educacional clara com a pergunta")

    def test_equidade_por_fase_genero_e_idade_presentes_na_pergunta_9(self):
        """A auditoria de equidade prevista no contrato metodológico
        (recall/precisão/calibração por fase) e a auditoria exploratória de
        equidade por gênero e faixa etária recuperada nesta correção (via
        ligação por RA, sem alterar o modelo congelado) precisam estar
        refletidas na pergunta 9, incluindo a reconciliação explícita com o
        "indisponível" do artefato oficial."""
        q9 = next(p for p in self.data["perguntas"] if p["numero"] == 9)
        self.assertTrue(q9["recortes"]["fase"]["implementado"])
        self.assertTrue(q9["recortes"]["sexo"]["implementado"])
        self.assertTrue(q9["recortes"]["idade"]["implementado"])
        texto = json.dumps(q9, ensure_ascii=False)
        self.assertIn("indisponível", texto)
        self.assertIn("Equidade por fase", texto)
        self.assertIn("Equidade por gênero", texto)
        self.assertIn("Equidade por faixa etária", texto)

    def test_q9_documenta_auditoria_da_chave_de_ligacao(self):
        """Correção pós-auditoria comparativa (24/09/2026, rodada 3, item 3):
        a pergunta 9 precisa documentar explicitamente que a ligação entre
        predições e gênero/idade usa uma chave composta (RA + ano), não
        apenas RA — e não pode publicar AP/ROC-AUC "zero" para um grupo sem
        as duas classes."""
        q9 = next(p for p in self.data["perguntas"] if p["numero"] == 9)
        texto = json.dumps(q9, ensure_ascii=False)
        self.assertIn("chave composta", texto)
        self.assertIn("ano dos preditores", texto)
        self.assertIn("não estimável para este grupo", texto)
        # Nenhum grupo publicado (status "estimado") pode ter AP ou ROC-AUC
        # numericamente igual a zero sem contexto — verifica que, quando
        # presentes, são floats plausíveis (nunca int 0 ou 0.0 "inventado").
        linhas = q9["analises_complementares_numeros"]
        for linha in linhas:
            if linha.get("Recorte", "").startswith("Equidade") and linha.get("Recall") not in ("suprimido", "—", None):
                self.assertIn("Positivos" if "Positivos" in linha else "Eventos", linha)
                self.assertIn("Negativos", linha)
                self.assertIn("Alertas", linha)

    def test_q1_sexo_binario_publicado_nos_tres_anos_sem_supressao(self):
        """Correção pós-auditoria comparativa (24/09/2026, rodada 3, item 1):
        a agregação binária (sem defasagem / alguma defasagem) por sexo
        precisa estar publicada para as seis combinações sexo×ano
        (2022/2023/2024 × feminino/masculino), com denominadores explícitos
        e variação em pontos percentuais — sem nenhuma célula suprimida."""
        q1 = next(p for p in self.data["perguntas"] if p["numero"] == 1)
        linhas = [r for r in q1["analises_complementares_numeros"]
                 if r.get("Recorte") == "Defasagem por sexo (sem/alguma defasagem)"]
        self.assertEqual(len(linhas), 6)
        combinacoes = {(r["Ano"], r["Sexo"]) for r in linhas}
        esperado = {(ano, sexo) for ano in ("2022", "2023", "2024") for sexo in ("feminino", "masculino")}
        self.assertEqual(combinacoes, esperado)
        for linha in linhas:
            self.assertIsInstance(linha["n"], int)
            self.assertGreaterEqual(linha["n"], 10)
            self.assertIn("Variação de \"alguma defasagem\" em p.p. vs. ano anterior", linha)
            for categoria in ("sem defasagem", "alguma defasagem"):
                contagem = int(linha[categoria].split("(")[1].rstrip(")"))
                self.assertGreaterEqual(contagem, 10, f"{linha['Ano']}/{linha['Sexo']}/{categoria}")

    def test_faixas_aproximadas_usam_fronteiras_auditadas(self):
        texto = json.dumps(self.data, ensure_ascii=False)
        for faixa in ("7 a 10 anos", "11 a 13 anos", "14 a 16 anos", "17 anos ou mais"):
            self.assertIn(faixa, texto)
        self.assertNotIn("até 10 anos", texto)
        q1 = next(p for p in self.data["perguntas"] if p["numero"] == 1)
        nota = q1["analises_complementares_nota"]
        for fronteira in ("10/11", "13/14", "16/17"):
            self.assertIn(fronteira, nota)
        self.assertIn("faixa vizinha", nota)

    def test_manifesto_confere(self):
        self.assertTrue(self.manifest["independente_de_dados_privados"])
        self.assertTrue(self.manifest["independente_de_artefatos_historicos"])
        for relativo, esperado in self.manifest["output_hashes"].items():
            atual = hashlib.sha256((ROOT / relativo).read_bytes()).hexdigest()
            self.assertEqual(atual, esperado, relativo)

    def test_gerador_nao_importa_codigo_historico(self):
        fonte = Path(publicas.__file__).read_text(encoding="utf-8")
        for proibido in ("import analises_negocio", "import relatorio_analises", "load_prepared("):
            self.assertNotIn(proibido, fonte)

    def test_modelo_e_limiar_permanecem_congelados(self):
        schema = json.loads((ROOT / "artifacts/schema_modelo.json").read_text(encoding="utf-8"))
        self.assertEqual(self.data["modelo_congelado"]["limiar"], schema["limiar"])
        self.assertEqual(self.data["modelo_congelado"]["preditores"], schema["colunas"])
        self.assertFalse(self.data["modelo_congelado"]["retreinado"])


class GeradorPublicoBytesLFTests(unittest.TestCase):
    """`.gitattributes` força `eol=lf` para os arquivos públicos: o Git
    normaliza qualquer CRLF para LF ao versionar. Se o gerador grava CRLF
    em disco (comportamento padrão de `Path.write_text` em texto no
    Windows, sem `newline=` explícito), o SHA-256 do manifesto — calculado
    sobre os bytes crus do disco — nunca bate com o que o Git realmente
    guarda. Estes testes provam a invariante em bytes, não em texto já
    normalizado na leitura, e não dependem do sistema operacional onde
    rodam: o gerador deve produzir LF puro em qualquer plataforma."""

    @classmethod
    def setUpClass(cls):
        cls.manifest_primeira_execucao = publicas.write_public_layer()

    def _arquivos_textuais(self, manifest):
        return [relativo for relativo in manifest["output_hashes"]
                if not relativo.endswith(".png")]

    def test_arquivos_publicos_nao_contem_crlf(self):
        for relativo in self._arquivos_textuais(self.manifest_primeira_execucao):
            conteudo = (ROOT / relativo).read_bytes()
            self.assertNotIn(b"\r\n", conteudo, relativo)
            self.assertNotIn(b"\r", conteudo, relativo)

    def test_hash_do_manifesto_bate_com_os_bytes_reais_do_disco(self):
        for relativo, esperado in self.manifest_primeira_execucao["output_hashes"].items():
            atual = hashlib.sha256((ROOT / relativo).read_bytes()).hexdigest()
            self.assertEqual(atual, esperado, relativo)

    def test_hash_do_manifesto_confere_especificamente_com_perguntas_oficiais(self):
        relativo = "reports/public/perguntas_oficiais_v1.json"
        esperado = self.manifest_primeira_execucao["output_hashes"][relativo]
        atual = hashlib.sha256((ROOT / relativo).read_bytes()).hexdigest()
        self.assertEqual(atual, esperado)

    def test_duas_execucoes_consecutivas_produzem_bytes_identicos(self):
        primeira = {relativo: hashlib.sha256((ROOT / relativo).read_bytes()).hexdigest()
                    for relativo in self._arquivos_textuais(self.manifest_primeira_execucao)}
        segunda_execucao = publicas.write_public_layer()
        segunda = {relativo: hashlib.sha256((ROOT / relativo).read_bytes()).hexdigest()
                   for relativo in self._arquivos_textuais(segunda_execucao)}
        self.assertEqual(primeira, segunda)
        self.assertEqual(self.manifest_primeira_execucao["output_hashes"],
                         segunda_execucao["output_hashes"])

    def test_atributo_git_forca_eol_lf_para_os_arquivos_textuais(self):
        # Confirma a premissa: o Git normaliza estes caminhos para LF ao
        # versionar. Combinado com a ausência de CRLF já provada acima,
        # isso garante que os bytes gravados são exatamente os bytes que
        # o Git vai armazenar — sem precisar invocar o mecanismo de
        # commit para provar.
        for relativo in self._arquivos_textuais(self.manifest_primeira_execucao):
            resultado = subprocess.run(
                ["git", "check-attr", "eol", "--", relativo],
                cwd=ROOT, capture_output=True, text=True, check=True,
            )
            self.assertIn("eol: lf", resultado.stdout, relativo)


if __name__ == "__main__":
    unittest.main()
