"""
api/main.py - a API do Painel de Empregabilidade Jovem.

    uvicorn api.main:app        ->  http://127.0.0.1:8000/docs

Sem --reload: cada reinicio recarrega o modelo. As rotas estao em api/rotas/.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from api import motor
from api.erros import erro_inesperado
from api.modelos import Raiz
from api.rotas import analise, noticias

logging.basicConfig(level=logging.INFO, format="%(levelname)s:     %(message)s")


@asynccontextmanager
async def lifespan(_: FastAPI):
    motor.carregar()      # quando a API SOBE - uma vez. Nunca levanta (falha em pedaços).
    yield
    motor.descarregar()   # quando a API DESCE


app = FastAPI(
    title="API do Painel de Empregabilidade Jovem",
    version="2.0.0",
    description=(
        "Serve as noticias de emprego coletadas da Agencia Brasil, recebe "
        "noticias de outros programas e **analisa textos com um modelo de "
        "linguagem que roda localmente**, sem internet.\n\n"
        "Projeto de Bloco: IA Aplicada - ODS 8, meta 8.6."
    ),
    lifespan=lifespan,
)

app.add_exception_handler(Exception, erro_inesperado)
app.include_router(noticias.router)
app.include_router(analise.router)


@app.get("/", response_model=Raiz, summary="Identifica a API", tags=["api"])
def raiz():
    """O nome do projeto e as rotas - para um programa descobrir o que existe aqui."""
    return {
        "projeto": "Painel de Empregabilidade Jovem",
        "ods": "8 - Trabalho Decente e Crescimento Economico (meta 8.6)",
        "rotas": [
            "/noticias", "/noticias/estatisticas", "/noticias/{id}", "/editorias",
            "/processar_texto", "/saude", "/docs",
        ],
    }
