"""
api/erros.py - a rede de seguranca e a documentacao dos erros.

Voce nao vai prever tudo (Aula 14). Para o que escapar, a rede: o cliente
recebe um 500 em JSON, com uma frase e um CODIGO; o terminal recebe o
traceback com o mesmo codigo. Ao usuario, a frase; ao log, o traceback -
nunca o caminho de arquivo ou a pilha de chamadas no detail.
"""

import logging
import uuid

from fastapi import Request
from fastapi.responses import JSONResponse

from api.modelos import Erro

log = logging.getLogger("api")


def erro_inesperado(request: Request, exc: Exception) -> JSONResponse:
    codigo = uuid.uuid4().hex[:8]
    log.error(
        "Erro inesperado [%s] em %s %s - %s: %s",
        codigo, request.method, request.url.path, type(exc).__name__, exc,
        exc_info=exc,
    )
    return JSONResponse(
        status_code=500,
        content={"detail": (
            f"Erro interno na API (codigo {codigo}). Nada foi alterado. "
            "Informe esse codigo a quem mantem o painel."
        )},
    )


def erro(descricao):
    """Para o responses= das rotas: o /docs passa a mostrar cada erro possivel."""
    return {"model": Erro, "description": descricao}
