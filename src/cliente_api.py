"""
cliente_api.py - o painel falando com a API do projeto por HTTP.

Cada resposta e lida pelo status: no 422 o "detail" e uma lista de
problemas (traduzidos aqui); nos outros erros, uma frase.
Endereco da API: PAINEL_API_URL (padrao http://127.0.0.1:8000).
"""

import os

import requests

API_URL = os.environ.get("PAINEL_API_URL", "http://127.0.0.1:8000").rstrip("/")


class APIForaDoAr(Exception):
    """A API nao respondeu: desligada, endereco errado ou demorou demais."""


class FalhaDaAPI(Exception):
    """A API respondeu - e disse que nao deu. Guarda o status e as frases dela."""

    def __init__(self, status, mensagens):
        super().__init__(f"{status}: {' | '.join(mensagens)}")
        self.status = status
        self.mensagens = mensagens

    @property
    def e_aviso(self):
        """
        409, 404, 503 e 504 sao AVISO: nao ha nada a corrigir no que foi
        enviado. 422 e 500 sao ERRO: corrigir o envio, ou avisar quem mantem.
        """
        return self.status in (404, 409, 503, 504)


# Os erros de validacao mais provaveis, na lingua de quem usa o painel.
TRADUCOES = {
    ("texto", "string_too_short"): "O texto precisa ter pelo menos 15 caracteres.",
    ("texto", "string_too_long"): "O texto passou de 20.000 caracteres - cole um trecho menor.",
    ("titulo", "string_too_short"): "O título precisa ter pelo menos 10 caracteres.",
    ("titulo", "string_too_long"): "O título passou de 300 caracteres.",
    ("ano_mes", "string_pattern_mismatch"): "O ano-mês precisa estar no formato AAAA-MM, ex: 2026-10.",
    ("tipo_analise", "literal_error"): "Tipo de análise desconhecido.",
}


def traduzir(erro):
    """Um item do 422 -> uma frase. O que nao estiver no dicionario sai como veio."""
    campo = erro.get("loc", ["", ""])[-1]
    tipo = erro.get("type", "")
    if tipo == "extra_forbidden":
        return f"A API não aceita o campo '{campo}'."
    if tipo == "missing":
        return f"Falta o campo '{campo}'."
    return TRADUCOES.get((campo, tipo), f"{campo}: {erro.get('msg', 'valor inválido')}")


def _falha(r):
    if r.status_code == 422:  # uma LISTA
        try:
            return FalhaDaAPI(422, [traduzir(e) for e in r.json()["detail"]])
        except (ValueError, KeyError, TypeError):
            pass
    try:
        frase = r.json()["detail"]  # uma FRASE
        if not isinstance(frase, str):
            raise TypeError
    except (ValueError, KeyError, TypeError):
        frase = f"A API respondeu {r.status_code} sem explicar o motivo."
    return FalhaDaAPI(r.status_code, [frase])


def _pedir(metodo, caminho, timeout=10, **kwargs):
    try:
        r = requests.request(metodo, f"{API_URL}{caminho}", timeout=timeout, **kwargs)
    except requests.Timeout:
        raise APIForaDoAr(f"A API não respondeu em {timeout} s.")
    except requests.ConnectionError:
        raise APIForaDoAr(f"Não há API respondendo em {API_URL}.")
    if not r.ok:  # confere a FAMILIA (2xx), nao o numero: o POST responde 201
        raise _falha(r)
    return r.json()


# -------------------------------------------------------------------
# AS CHAMADAS QUE O PAINEL FAZ
# -------------------------------------------------------------------
def saude():
    return _pedir("GET", "/saude", timeout=3)


def listar_noticias(limite=500):
    return _pedir("GET", "/noticias", params={"limite": limite})["noticias"]


def obter_noticia(id_noticia):
    return _pedir("GET", f"/noticias/{id_noticia}")


def analisar(texto, tipo_analise):
    # O modelo pode levar alguns segundos (mais na CPU); a propria API corta
    # em PAINEL_LIMITE_S e responde 504 - aqui so esperamos um pouco mais.
    return _pedir("POST", "/processar_texto", timeout=90,
                  json={"texto": texto, "tipo_analise": tipo_analise})


def enviar_noticia(titulo, editoria, ano_mes, url):
    corpo = {"titulo": titulo, "editoria": editoria or "n/d",
             "ano_mes": ano_mes or "n/d", "url": url}
    return _pedir("POST", "/noticias", json=corpo)
