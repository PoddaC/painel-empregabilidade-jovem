"""
api/conversas.py - onde a conversa mora: na API, uma por id, em arquivo, com trava.

    data/conversas/<id>.json      (fora do Git - .gitignore)

Por que na API e nao so no navegador (session_state): a conversa e DADO
PESSOAL (o que alguem perguntou). Guardada num lugar so, da para dizer
onde mora, quem le e como apagar - e o Data Summary diz. E nenhuma
pessoa ve a conversa de outra: cada uma tem um id aleatorio.

O id e conferido (32 hexadecimais) antes de virar nome de arquivo: um id
como "../../segredo" nunca chega ao disco.
"""

import json
import os
import re
import threading
import uuid
from datetime import datetime
from pathlib import Path

from src import conversa as nucleo

BASE = Path(__file__).resolve().parent.parent
ID_VALIDO = re.compile(r"^[0-9a-f]{32}$")
_trava = threading.Lock()


def pasta():
    p = Path(os.environ.get("PAINEL_CONVERSAS_DIR", BASE / "data" / "conversas"))
    p.mkdir(parents=True, exist_ok=True)
    return p


def _caminho(conversa_id):
    if not ID_VALIDO.match(conversa_id or ""):
        return None
    return pasta() / f"{conversa_id}.json"


def nova(memoria):
    conversa = nucleo.nova(memoria)
    conversa["id"] = uuid.uuid4().hex
    return conversa


def ler(conversa_id):
    caminho = _caminho(conversa_id)
    if caminho is None or not caminho.exists():
        return None
    with _trava:
        return json.loads(caminho.read_text(encoding="utf-8"))


def gravar(conversa):
    conversa["atualizada_em"] = datetime.now().isoformat(timespec="seconds")
    caminho = _caminho(conversa["id"])
    temporario = caminho.with_suffix(".tmp")
    with _trava:
        temporario.write_text(json.dumps(conversa, ensure_ascii=False, indent=1), encoding="utf-8")
        os.replace(temporario, caminho)  # troca inteira: nunca fica um arquivo pela metade


def apagar(conversa_id):
    caminho = _caminho(conversa_id)
    if caminho is None or not caminho.exists():
        return False
    with _trava:
        caminho.unlink()
    return True
