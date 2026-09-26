"""Regras puras da ficha individual, sem Streamlit e sem persistência.

Este módulo valida a completude da ficha e monta exclusivamente o payload
congelado de sete preditores. Dados cadastrais, notas brutas, IAN, IPP e INDE
nunca atravessam essa fronteira.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Mapping

import calculadoras_indicadores as calculadoras

PREDITORES: tuple[str, ...] = (
    "ida", "ieg", "iaa", "ips", "ipv", "fase_origem", "defasagem_origem",
)


@dataclass(frozen=True)
class ValidacaoFicha:
    erros: dict[str, str]
    payload: dict[str, float | str] | None

    @property
    def valida(self) -> bool:
        return not self.erros and self.payload is not None


def numero_decimal(valor: Any, *, minimo: float | None = None,
                   maximo: float | None = None) -> float:
    """Converte ponto ou vírgula decimal, sem tratar vazio como zero."""
    texto = "" if valor is None else str(valor).strip()
    if not texto:
        raise ValueError("valor obrigatório")
    try:
        numero = float(texto.replace(",", "."))
    except ValueError:
        raise ValueError("informe um número válido") from None
    if not math.isfinite(numero):
        raise ValueError("informe um número finito")
    if minimo is not None and numero < minimo:
        raise ValueError(f"o valor mínimo é {minimo:g}")
    if maximo is not None and numero > maximo:
        raise ValueError(f"o valor máximo é {maximo:g}")
    return numero


def idade_em_anos(valor: Any) -> int:
    texto = "" if valor is None else str(valor).strip()
    if not texto:
        raise ValueError("idade obrigatória")
    try:
        idade = int(texto)
    except ValueError:
        raise ValueError("informe a idade em anos completos") from None
    if str(idade) != texto.lstrip("+") or idade < 0 or idade > 100:
        raise ValueError("informe uma idade inteira entre 0 e 100 anos")
    return idade


def resolver_defasagem(fase_atual: str, fase_ideal: str,
                       registrada: Any = None, escolha: str | None = None) -> tuple[float, str]:
    """Calcula D pelas fases e trata divergência com valor institucional.

    Se um valor registrado divergir, ``escolha`` deve ser ``"calculada"`` ou
    ``"registrada"``. Nenhum valor substitui o outro silenciosamente.
    """
    if fase_atual not in calculadoras.FASES_FICHA or fase_ideal not in calculadoras.FASES_FICHA:
        raise ValueError("fase atual e fase ideal confirmada são obrigatórias")
    calculada = float(calculadoras.calcular_defasagem(int(fase_atual), int(fase_ideal)))
    if registrada in (None, ""):
        return calculada, "calculada"
    valor_registrado = numero_decimal(registrada)
    if math.isclose(valor_registrado, calculada, rel_tol=0.0, abs_tol=1e-12):
        return calculada, "confirmada"
    if escolha == "calculada":
        return calculada, "calculada"
    if escolha == "registrada":
        return valor_registrado, "registrada"
    raise ValueError("confirme qual defasagem deve ser utilizada")


def validar_ficha(dados: Mapping[str, Any]) -> ValidacaoFicha:
    """Valida todos os campos aplicáveis antes de qualquer inferência."""
    erros: dict[str, str] = {}

    if not str(dados.get("identificacao") or "").strip():
        erros["identificacao"] = "Informe o nome ou a identificação interna."
    try:
        idade_em_anos(dados.get("idade"))
    except ValueError as erro:
        erros["idade"] = str(erro).capitalize() + "."
    if dados.get("sexo") not in {"Feminino", "Masculino"}:
        erros["sexo"] = "Selecione o sexo informado no cadastro institucional."

    fase = str(dados.get("fase_origem") or "").strip()
    fase_ideal = str(dados.get("fase_ideal") or "").strip()
    if fase not in calculadoras.FASES_VALIDAS:
        erros["fase_origem"] = (
            "Selecione uma fase atual aceita pelo contrato do modelo (Alfa a Fase 7)."
        )
    if fase_ideal not in calculadoras.FASES_FICHA:
        erros["fase_ideal"] = "Selecione e confirme a fase ideal."

    numericos: dict[str, float] = {}
    for campo in ("ida", "ieg", "iaa", "ips", "ipv"):
        try:
            numericos[campo] = numero_decimal(dados.get(campo), minimo=0, maximo=10)
        except ValueError as erro:
            erros[campo] = f"{campo.upper()}: {erro}."

    try:
        defasagem, _origem = resolver_defasagem(
            fase, fase_ideal, dados.get("defasagem_registrada"),
            dados.get("escolha_defasagem"),
        )
    except ValueError as erro:
        erros["defasagem_origem"] = str(erro).capitalize() + "."
        defasagem = 0.0

    # IPP é obrigatório para concluir a ficha nas fases Alfa–7, embora
    # permaneça estritamente fora do payload do modelo.
    if fase in calculadoras.FASES_VALIDAS:
        try:
            numero_decimal(dados.get("ipp"), minimo=0, maximo=10)
        except ValueError as erro:
            erros["ipp"] = f"IPP: {erro}."

    if erros:
        return ValidacaoFicha(erros=erros, payload=None)

    payload: dict[str, float | str] = {
        "ida": numericos["ida"], "ieg": numericos["ieg"],
        "iaa": numericos["iaa"], "ips": numericos["ips"],
        "ipv": numericos["ipv"], "fase_origem": fase,
        "defasagem_origem": defasagem,
    }
    # Construção deliberadamente posicional para tornar a ordem auditável.
    payload = {campo: payload[campo] for campo in PREDITORES}
    return ValidacaoFicha(erros={}, payload=payload)
