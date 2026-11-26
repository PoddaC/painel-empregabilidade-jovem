"""
llm_api.py - o modelo de linguagem ONLINE que conversa (pagina Conversa).

Por que online, e nao o Qwen local: o Qwen2.5-1.5B so ESCOLHE uma categoria
no Analisador (bom e rapido nisso). Conversar exige ESCREVER em portugues,
seguir instrucoes e nao inventar numero - trabalho para um modelo maior, que
nao cabe aqui (e na CPU cada analise ja leva ~15 s).

Provedores, na ordem (PAINEL_LLM_ORDEM, padrao "groq,gemini"):
- Groq   (OpenAI-compativel)  GROQ_API_KEY    modelo PAINEL_GROQ_MODELO   (openai/gpt-oss-120b)
- Gemini (Google AI Studio)   GEMINI_API_KEY  modelo PAINEL_GEMINI_MODELO (gemini-3.8-flash)

Se o primeiro falha (sem chave, 429, 503, tempo esgotado), tenta o proximo.
Se todos falham, levanta LLMIndisponivel com o motivo de cada um.
Tempo limite curto (PAINEL_LLM_LIMITE_S, padrao 30 s) e NENHUMA repeticao
automatica: medido em 25/11/2026, a biblioteca do Google repetiu um 503
por mais de 10 minutos.

As chaves vem do ambiente ou do arquivo .env na raiz (fora do Git).
"""

import os
import time

import requests

from src.data_access import BASE


def carregar_env(caminho=BASE / ".env"):
    """Le CHAVE=valor do .env para o ambiente (sem sobrescrever o que ja existe)."""
    if not caminho.exists():
        return
    for linha in caminho.read_text(encoding="utf-8-sig").splitlines():
        linha = linha.strip()
        if linha and not linha.startswith("#") and "=" in linha:
            k, v = linha.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


carregar_env()


class LLMIndisponivel(Exception):
    """Nenhum provedor respondeu. .motivos = {provedor: frase}."""

    def __init__(self, motivos):
        self.motivos = motivos
        super().__init__(" | ".join(f"{p}: {m}" for p, m in motivos.items()))


class _Falhou(Exception):
    pass


def limite_segundos():
    return float(os.environ.get("PAINEL_LLM_LIMITE_S", "30"))


def ordem():
    return [p.strip() for p in os.environ.get("PAINEL_LLM_ORDEM", "groq,gemini").split(",") if p.strip()]


def modelo_de(provedor):
    return {"groq": os.environ.get("PAINEL_GROQ_MODELO", "openai/gpt-oss-120b"),
            "gemini": os.environ.get("PAINEL_GEMINI_MODELO", "gemini-3.8-flash")}[provedor]


def _chave(provedor):
    return os.environ.get({"groq": "GROQ_API_KEY", "gemini": "GEMINI_API_KEY"}[provedor], "")


def configurados():
    """Os provedores com chave, na ordem de uso."""
    return [p for p in ordem() if p in ("groq", "gemini") and _chave(p)]


def _http(metodo, url, **kw):
    try:
        r = requests.request(metodo, url, timeout=limite_segundos(), **kw)
    except requests.Timeout:
        raise _Falhou(f"não respondeu em {limite_segundos():g} s")
    except requests.RequestException as e:
        raise _Falhou(f"sem conexão ({type(e).__name__})")
    if r.status_code == 429:
        raise _Falhou("limite de uso do plano gratuito atingido (429); tente em instantes")
    if r.status_code >= 500:
        raise _Falhou(f"o provedor está indisponível ({r.status_code})")
    if r.status_code != 200:
        raise _Falhou(f"recusou o pedido ({r.status_code}): {r.text[:150]}")
    return r.json()


def _groq(instrucoes, mensagens, max_tokens):
    corpo = {
        "model": modelo_de("groq"),
        "messages": [{"role": "system", "content": instrucoes}]
                    + [{"role": m["papel"], "content": m["texto"]} for m in mensagens],
        "temperature": 0.2,
        "max_tokens": max_tokens,
    }
    if "gpt-oss" in corpo["model"]:
        corpo["reasoning_effort"] = "low"  # modelo que "pensa" antes: pouco, para responder rapido
    d = _http("POST", "https://api.groq.com/openai/v1/chat/completions",
              headers={"Authorization": f"Bearer {_chave('groq')}"}, json=corpo)
    texto = (d["choices"][0]["message"].get("content") or "").strip()
    uso = d.get("usage", {})
    return texto, uso.get("prompt_tokens"), uso.get("completion_tokens")


def _gemini(instrucoes, mensagens, max_tokens):
    corpo = {
        "systemInstruction": {"parts": [{"text": instrucoes}]},
        "contents": [{"role": "model" if m["papel"] == "assistant" else "user",
                      "parts": [{"text": m["texto"]}]} for m in mensagens],
        "generationConfig": {"temperature": 0.2, "maxOutputTokens": max_tokens},
    }
    d = _http("POST", f"https://generativelanguage.googleapis.com/v1beta/models/{modelo_de('gemini')}:generateContent",
              headers={"x-goog-api-key": _chave("gemini")}, json=corpo)
    try:
        texto = "".join(p.get("text", "") for p in d["candidates"][0]["content"]["parts"]).strip()
    except (KeyError, IndexError):
        raise _Falhou("resposta vazia (bloqueada ou cortada)")
    uso = d.get("usageMetadata", {})
    return texto, uso.get("promptTokenCount"), uso.get("candidatesTokenCount")


CHAMADAS = {"groq": _groq, "gemini": _gemini}


def completar(instrucoes, mensagens, max_tokens=700):
    """
    mensagens: [{"papel": "user"|"assistant", "texto": str}, ...] - a ultima e a pergunta.
    Devolve {"texto", "provedor", "modelo", "tokens_entrada", "tokens_saida",
             "segundos", "tentativas"} ou levanta LLMIndisponivel.
    """
    motivos = {}
    for provedor in ordem():
        if provedor not in CHAMADAS:
            continue
        if not _chave(provedor):
            motivos[provedor] = "sem chave configurada (.env)"
            continue
        inicio = time.perf_counter()
        try:
            texto, t_in, t_out = CHAMADAS[provedor](instrucoes, mensagens, max_tokens)
        except _Falhou as e:
            motivos[provedor] = str(e)
            continue
        if not texto:
            motivos[provedor] = "resposta vazia"
            continue
        return {"texto": texto, "provedor": provedor, "modelo": modelo_de(provedor),
                "tokens_entrada": t_in, "tokens_saida": t_out,
                "segundos": round(time.perf_counter() - inicio, 2),
                "tentativas": motivos}  # quem falhou antes deste, e por que
    raise LLMIndisponivel(motivos or {"nenhum": "nenhum provedor configurado em PAINEL_LLM_ORDEM"})
