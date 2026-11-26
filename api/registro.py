"""
api/registro.py - o diario da API: uma linha JSON por chamada.

    logs/api.jsonl   (fora do repositorio - .gitignore)

Cada linha: quando, metodo, rota, status, segundos e, nas rotas que
analisam, o motor, a tarefa, a categoria e a confianca. NUNCA o texto
enviado: so quantos caracteres ele tinha (pode ser dado de outra pessoa).

Serve para tres coisas:
- provar que uma chamada real aconteceu (python -m src.evidencias copia
  as linhas da rodada para docs/evidencias/);
- medir tempo de ponta a ponta com o modelo na GPU ou na CPU;
- no TP5, medir a conversa do mesmo jeito.

Variavel de ambiente: PAINEL_LOG (padrao logs/api.jsonl; vazio = desligado).
"""

import json
import logging
import os
import threading
import time
from datetime import datetime
from pathlib import Path

from fastapi import Request

BASE = Path(__file__).resolve().parent.parent
_trava = threading.Lock()
log = logging.getLogger("api")


def caminho_do_log():
    valor = os.environ.get("PAINEL_LOG", "logs/api.jsonl")
    if not valor:
        return None
    p = Path(valor)
    return p if p.is_absolute() else BASE / p


def anotar(request: Request, **campos):
    """Uma rota acrescenta detalhes a linha do log da chamada dela."""
    extra = getattr(request.state, "registro", {})
    extra.update(campos)
    request.state.registro = extra


def escrever(linha):
    caminho = caminho_do_log()
    if caminho is None:
        return
    try:
        caminho.parent.mkdir(parents=True, exist_ok=True)
        with _trava, caminho.open("a", encoding="utf-8") as f:
            f.write(json.dumps(linha, ensure_ascii=False) + "\n")
    except OSError as e:  # disco cheio, pasta sem permissao: o log nunca derruba a API
        log.warning("[registro] nao gravei o log: %s", e)


async def registrar(request: Request, chamar):
    """Middleware: cronometra a chamada e grava uma linha, ate quando ela quebra."""
    inicio = time.perf_counter()
    status = 500
    try:
        resposta = await chamar(request)
        status = resposta.status_code
        return resposta
    finally:
        if request.url.path not in ("/docs", "/openapi.json", "/favicon.ico", "/redoc"):
            escrever({
                "quando": datetime.now().isoformat(timespec="milliseconds"),
                "metodo": request.method,
                "rota": request.url.path,
                "status": status,
                "segundos": round(time.perf_counter() - inicio, 3),
                **getattr(request.state, "registro", {}),
            })
