"""
test_api.py - cada promessa da API, conferida.

    pip install -r requirements-dev.txt
    pytest

Nao precisa do modelo baixado: os testes da ANALISE usam o motor de regras
(rapido e deterministico) ou um motor falso. O que o modelo de verdade
ACERTA e trabalho da bancada (python -m src.bancada), nao destes testes.
"""

import time

import pytest
from fastapi.testclient import TestClient

from api import motor
from api.main import app
from api.rotas import noticias as rotas_noticias
from src.tarefas import TAREFAS

TEXTO = ("Brasil gerou mais de 235 mil novos postos de trabalho em agosto, "
         "e o desemprego caiu ao menor nivel da serie.")


@pytest.fixture
def cliente(monkeypatch, tmp_path):
    """API com o motor de regras e o CSV do POST numa pasta temporaria."""
    monkeypatch.setenv("PAINEL_MOTOR", "regras")
    monkeypatch.setattr(rotas_noticias, "CSV_API", tmp_path / "noticias_via_api.csv")
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


# --- contrato: toda rota declara o que devolve -----------------------
def test_toda_rota_tem_modelo_de_resposta(cliente):
    esquema = cliente.get("/openapi.json").json()
    for caminho, metodos in esquema["paths"].items():
        for metodo, op in metodos.items():
            ok = next(v for k, v in op["responses"].items() if k.startswith("2"))
            corpo = ok["content"]["application/json"]["schema"]
            assert corpo, f"{metodo.upper()} {caminho} devolve 'string' no /docs"


# --- noticias --------------------------------------------------------
def test_listar_e_filtro_vazio_e_200(cliente):
    r = cliente.get("/noticias", params={"limite": 3})
    assert r.status_code == 200 and len(r.json()["noticias"]) == 3
    r = cliente.get("/noticias", params={"busca": "zzzz-nada"})
    assert r.status_code == 200 and r.json()["total"] == 0  # recorte vazio NAO e erro


def test_noticia_por_id_e_404(cliente):
    primeira = cliente.get("/noticias").json()["noticias"][0]
    r = cliente.get(f"/noticias/{primeira['id']}")
    assert r.status_code == 200 and "texto" in r.json()
    r = cliente.get("/noticias/nao-existe")
    assert r.status_code == 404 and "GET /noticias" in r.json()["detail"]


def test_estatisticas_nao_e_engolida_pelo_id(cliente):
    r = cliente.get("/noticias/estatisticas")
    assert r.status_code == 200 and r.json()["total"] >= 42


def test_sem_coleta_e_503(cliente, monkeypatch, tmp_path):
    monkeypatch.setattr(rotas_noticias, "CSV_NOTICIAS", tmp_path / "nao_existe.csv")
    r = cliente.get("/noticias")
    assert r.status_code == 503 and "coleta" in r.json()["detail"]


def test_post_201_depois_409(cliente):
    corpo = {"titulo": "Programa abre vagas para jovens aprendizes",
             "editoria": "economia", "ano_mes": "2026-11", "url": "https://x.gov.br/n/1"}
    r = cliente.post("/noticias", json=corpo)
    assert r.status_code == 201 and r.json()["noticia"]["origem"] == "via_api"
    r = cliente.post("/noticias", json=corpo)
    assert r.status_code == 409


def test_post_recusa_em_voz_alta(cliente):
    r = cliente.post("/noticias", json={"titulo": "curto", "ano_mes": "nov/2026", "telefone": "99"})
    tipos = {e["loc"][-1]: e["type"] for e in r.json()["detail"]}
    assert r.status_code == 422
    assert tipos == {"titulo": "string_too_short", "ano_mes": "string_pattern_mismatch",
                     "telefone": "extra_forbidden"}


# --- analise ---------------------------------------------------------
def test_processar_texto_cumpre_o_contrato(cliente):
    for tipo in ("tendencia", "setor"):
        r = cliente.post("/processar_texto", json={"texto": TEXTO, "tipo_analise": tipo})
        assert r.status_code == 200
        d = r.json()
        assert d["tipo_analise"] == tipo and 0 <= d["confianca"] <= 1
        assert d["motor"].startswith("regras")
        assert {a["categoria"] for a in d["alternativas"]} == set(TAREFAS[tipo]["categorias"])


def test_processar_texto_422(cliente):
    r = cliente.post("/processar_texto", json={"texto": "curto", "tipo_analise": "humor"})
    assert r.status_code == 422 and len(r.json()["detail"]) == 2


def test_modelo_ausente_503_e_resto_no_ar(monkeypatch, tmp_path):
    """Falhe em pedaços: sem o modelo, a analise da 503 - e as noticias seguem 200."""
    monkeypatch.setenv("PAINEL_MOTOR", "llm")
    monkeypatch.setenv("PAINEL_MODELO", str(tmp_path / "modelo-que-nao-existe"))
    with TestClient(app) as c:
        assert c.get("/saude").json()["modelo_carregado"] is False
        r = c.post("/processar_texto", json={"texto": TEXTO})
        assert r.status_code == 503 and "baixar_modelo" in r.json()["detail"]
        assert c.get("/noticias").status_code == 200


def test_tempo_esgotado_504(cliente, monkeypatch):
    class Lento:
        descricao = "lento"
        def analisar(self, texto, tipo):
            time.sleep(1.5)
            return {}
    monkeypatch.setitem(motor.MOTORES, "analise", Lento())
    monkeypatch.setenv("PAINEL_LIMITE_S", "0.3")
    r = cliente.post("/processar_texto", json={"texto": TEXTO})
    assert r.status_code == 504
    time.sleep(1.5)  # deixa o trabalhador terminar antes do proximo teste


def test_resposta_fora_do_contrato_e_500_com_codigo(cliente, monkeypatch):
    """Um motor que devolve uma categoria inventada nao passa: 500 em JSON, com codigo."""
    class Chuveiro:
        descricao = "inventa"
        def analisar(self, texto, tipo):
            return {"categoria": "chuveiro", "confianca": 1.0, "alternativas": [],
                    "trecho": texto, "pistas": []}
    monkeypatch.setitem(motor.MOTORES, "analise", Chuveiro())
    r = cliente.post("/processar_texto", json={"texto": TEXTO})
    assert r.status_code == 500
    assert "codigo" in r.json()["detail"] and "Traceback" not in r.text
