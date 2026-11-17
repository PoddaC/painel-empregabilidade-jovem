"""
test_analisador_llm.py - o CAMINHO do modelo de linguagem, sem baixar nada.

Usa um modelo minusculo e aleatorio (tests/miniatura.py). Confere que o
codigo carrega do disco, monta o prompt, pontua as letras e devolve uma
categoria DA LISTA com probabilidades que somam 1. O acerto e da bancada.
"""

import pytest

pytest.importorskip("torch")

from src.analisador_llm import AnalisadorLLM, montar_pergunta
from src.tarefas import TAREFAS
from tests.miniatura import criar_modelo_miniatura


@pytest.fixture(scope="module")
def analisador(tmp_path_factory):
    pasta = criar_modelo_miniatura(tmp_path_factory.mktemp("mini"))
    return AnalisadorLLM(modelo=pasta, dispositivo="cpu")


@pytest.mark.parametrize("tipo", list(TAREFAS))
def test_categoria_sempre_da_lista(analisador, tipo):
    r = analisador.analisar("Brasil gerou 235 mil vagas em agosto. " * 100, tipo)
    assert r["categoria"] in TAREFAS[tipo]["categorias"]
    assert abs(sum(p for _, p in r["alternativas"]) - 1) < 1e-3
    assert len(r["trecho"]) < 1600  # leu o recorte, nao o texto inteiro


def test_prompt_traz_as_definicoes():
    p = montar_pergunta("texto", "setor")
    assert "G) Mercado em geral" in p and "construção civil" in p


def test_modelo_ausente_e_oserror(tmp_path):
    with pytest.raises(OSError):
        AnalisadorLLM(modelo=str(tmp_path / "nada"), dispositivo="cpu")
