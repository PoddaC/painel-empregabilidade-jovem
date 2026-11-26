"""
test_conversa.py - o assistente, sem internet e sem gastar cota.

Um modelo FALSO responde (monkeypatch de llm_api.completar): os testes
conferem o caminho - memoria, fatos, gravacao, erros, log. O que o modelo
de verdade responde, quem mede e o teste de 10 perguntas
(python -m src.teste_memoria), contra a API online.
"""

import json

import pytest
from fastapi.testclient import TestClient

from api.main import app
from src import fatos, llm_api, memoria
from src.checagem import numeros_sem_fonte

P1 = "Como está a desocupação dos jovens de 18 a 24 anos na Bahia?"


@pytest.fixture
def chamadas(monkeypatch):
    """Substitui o modelo online. Guarda o que ele recebeu; responde algo neutro."""
    log = []

    def falso(instrucoes, mensagens, max_tokens=700):
        log.append({"instrucoes": instrucoes, "mensagens": mensagens})
        return {"texto": "Resposta de teste.", "provedor": "falso", "modelo": "falso-1",
                "tokens_entrada": 100, "tokens_saida": 10, "segundos": 0.01, "tentativas": {}}

    monkeypatch.setattr(llm_api, "completar", falso)
    return log


@pytest.fixture
def cliente(monkeypatch, tmp_path):
    monkeypatch.setenv("PAINEL_MOTOR", "regras")
    monkeypatch.setenv("PAINEL_CONVERSAS_DIR", str(tmp_path / "conversas"))
    monkeypatch.setenv("PAINEL_LOG", str(tmp_path / "api.jsonl"))
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


def perguntar(cliente, pergunta, cid=None, mem="notas"):
    corpo = {"pergunta": pergunta, "memoria": mem}
    if cid:
        corpo["conversa_id"] = cid
    return cliente.post("/conversa", json=corpo)


# --- entidades e fatos ------------------------------------------------
def test_entidades_sem_falso_positivo():
    assert fatos.achar_entidades(P1) == {"lugares": ["Bahia"], "grupos": ["18 a 24 anos"]}
    assert fatos.achar_entidades("vale para adolescentes do país")["lugares"] == ["Brasil"]  # "para" nao e o Pará
    assert fatos.achar_entidades("se a taxa to alta")["lugares"] == []                          # "se", "to" minusculos
    assert fatos.achar_entidades("MS e Mato Grosso")["lugares"] == ["Mato Grosso do Sul", "Mato Grosso"]


def test_checagem_acha_numero_inventado():
    f = "Bahia, 18 a 24 anos: 14,4% (um ano antes: 19,2%)"
    assert numeros_sem_fonte("Na Bahia, 14,4% no 3º trimestre de 2026; 3 UFs.", f) == []
    assert numeros_sem_fonte("Na Bahia, 14.4%, contra 12% no país.", f) == ["12%"]


# --- a rota ---------------------------------------------------------
def test_primeira_pergunta_abre_conversa(cliente, chamadas):
    r = perguntar(cliente, P1)
    assert r.status_code == 200
    d = r.json()
    assert len(d["conversa_id"]) == 32 and d["resposta"] == "Resposta de teste."
    assert d["leitura"]["lugares_em_foco"] == ["Bahia"]
    assert "Bahia" in chamadas[0]["instrucoes"] and "FATOS" in chamadas[0]["instrucoes"]
    salva = cliente.get(f"/conversa/{d['conversa_id']}").json()
    assert [m["papel"] for m in salva["mensagens"]] == ["user", "assistant"]


def _conversa(cliente, perguntas, mem):
    cid = None
    for p in perguntas:
        d = perguntar(cliente, p, cid, mem).json()
        cid = d["conversa_id"]
    return d


SEQ = [P1, "E em São Paulo?", "E no Rio Grande do Sul?", "E em Santa Catarina?", "E Pernambuco?",
       "Voltando ao primeiro estado: subiu ou caiu?"]


def test_notas_lembram_o_primeiro_estado(cliente, chamadas):
    d = _conversa(cliente, SEQ, "notas")
    assert d["leitura"]["lugares_em_foco"][0] == "Bahia"
    assert "Bahia" in chamadas[-1]["instrucoes"]                       # fatos da Bahia entraram
    assert d["leitura"]["mensagens_enviadas"] == 2 * memoria.NOTAS_TROCAS + 1  # custo fixo


def test_janela_esquece_o_primeiro_estado(cliente, chamadas):
    d = _conversa(cliente, SEQ, "janela")
    assert "Bahia" not in d["leitura"]["lugares_em_foco"]
    assert d["leitura"]["mensagens_enviadas"] == 2 * memoria.JANELA + 1


def test_inteira_le_tudo(cliente, chamadas):
    d = _conversa(cliente, SEQ, "inteira")
    assert d["leitura"]["mensagens_enviadas"] == 2 * len(SEQ) - 1


def test_resumo_paga_uma_chamada_a_mais(cliente, chamadas):
    d = _conversa(cliente, SEQ, "resumo")
    # 6 perguntas; a partir da 5a ha mensagens fora da janela de 3 trocas
    assert d["chamada_de_resumo"] is True
    assert len(chamadas) == len(SEQ) + 2


def test_conversa_inexistente_404_e_id_invalido_422(cliente, chamadas):
    assert perguntar(cliente, "oi", "0" * 32).status_code == 404
    assert perguntar(cliente, "oi", "../../segredo").status_code == 422
    assert cliente.get("/conversa/..%2F..%2Fsegredo").status_code == 404
    r = cliente.post("/conversa", json={"pergunta": "oi", "memoria": "eterna"})
    assert r.status_code == 422


def test_apagar(cliente, chamadas):
    cid = perguntar(cliente, P1).json()["conversa_id"]
    assert cliente.delete(f"/conversa/{cid}").status_code == 204
    assert cliente.get(f"/conversa/{cid}").status_code == 404
    assert cliente.delete(f"/conversa/{cid}").status_code == 404


def test_sem_modelo_503_e_nada_gravado(cliente, monkeypatch, tmp_path):
    def fora(*a, **k):
        raise llm_api.LLMIndisponivel({"groq": "limite de uso (429)", "gemini": "indisponível (503)"})
    monkeypatch.setattr(llm_api, "completar", fora)
    r = perguntar(cliente, P1)
    assert r.status_code == 503 and "groq" in r.json()["detail"] and "gemini" in r.json()["detail"]
    assert list((tmp_path / "conversas").glob("*.json")) == []
    assert cliente.get("/noticias").status_code == 200  # o resto do painel segue no ar


def test_log_sem_a_pergunta(cliente, chamadas, tmp_path):
    perguntar(cliente, P1)
    log = (tmp_path / "api.jsonl").read_text(encoding="utf-8")
    linha = json.loads(log.splitlines()[-1])
    assert linha["rota"] == "/conversa" and linha["provedor"] == "falso" and linha["memoria"] == "notas"
    assert P1 not in log


# --- provedores -----------------------------------------------------
def test_reserva_quando_o_primeiro_falha(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "x")
    monkeypatch.setenv("GEMINI_API_KEY", "y")
    monkeypatch.setenv("PAINEL_LLM_ORDEM", "groq,gemini")

    def groq(*a):
        raise llm_api._Falhou("limite de uso do plano gratuito atingido (429)")
    monkeypatch.setitem(llm_api.CHAMADAS, "groq", groq)
    monkeypatch.setitem(llm_api.CHAMADAS, "gemini", lambda *a: ("ok", 5, 1))
    r = llm_api.completar("instr", [{"papel": "user", "texto": "oi"}])
    assert r["provedor"] == "gemini" and "429" in r["tentativas"]["groq"]


def test_sem_chave_nenhuma(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    with pytest.raises(llm_api.LLMIndisponivel) as e:
        llm_api.completar("instr", [{"papel": "user", "texto": "oi"}])
    assert "sem chave" in str(e.value)
