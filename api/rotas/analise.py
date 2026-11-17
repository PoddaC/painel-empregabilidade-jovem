"""
api/rotas/analise.py - o modelo de linguagem atras de uma rota (TP4).

    POST /processar_texto   PedidoAnalise -> ResultadoAnalise
    GET  /saude             o motor esta carregado?

O contrato veio antes do motor (Aula 13): a rota recebe um texto validado,
devolve sempre o mesmo formato, e cada falha tem um status e uma frase.
"""

import time
from concurrent.futures import TimeoutError as TempoEsgotado

from fastapi import APIRouter, HTTPException, status

from api import motor
from api.erros import erro
from api.modelos import PedidoAnalise, ResultadoAnalise, Saude
from src.tarefas import rotulo

router = APIRouter(tags=["analise"])


@router.post(
    "/processar_texto",
    response_model=ResultadoAnalise,
    summary="Analisa um texto com o modelo de linguagem local",
    response_description="A categoria sugerida, a confianca, as alternativas e quem analisou.",
    responses={
        503: erro("O modelo nao esta carregado nesta maquina (veja GET /saude)."),
        504: erro("A analise passou do tempo limite."),
    },
)
def processar_texto(pedido: PedidoAnalise):
    """
    Recebe um texto e devolve a analise do modelo local, sem internet.

    - `tipo_analise="tendencia"`: a noticia e **otimista**, **pessimista** ou
      **neutra** quanto ao emprego?
    - `tipo_analise="setor"`: de qual **setor da economia** ela fala?

    O modelo le o comeco do texto (titulo, linha fina e primeiros
    paragrafos - a piramide invertida); o trecho lido volta na resposta.
    A `confianca` e a nota do modelo, **nao** a chance de acerto.

    Esta rota e `def`, e nao `async def`, de proposito: rodar o modelo e
    CALCULAR, nao esperar. Numa `async def` o calculo travaria a API inteira
    - nem o /saude responderia (Aula 16: 1,64 s x 0,00 s).
    """
    analisador = motor.MOTORES.get("analise")
    if analisador is None:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                f"O analisador esta indisponivel: {motor.ESTADO['motivo'] or 'motor nao carregado.'} "
                "As outras rotas da API funcionam normalmente."
            ),
        )

    inicio = time.perf_counter()
    tarefa = motor.EXECUTOR.submit(analisador.analisar, pedido.texto, pedido.tipo_analise)
    try:
        r = tarefa.result(timeout=motor.limite_segundos())
    except TempoEsgotado:
        tarefa.cancel()  # se ainda estava na fila, nem comeca
        raise HTTPException(
            status.HTTP_504_GATEWAY_TIMEOUT,
            detail=(
                f"A analise passou de {motor.limite_segundos():.0f} s e foi abandonada. "
                "O modelo pode estar ocupado com outro pedido ou a maquina esta "
                "lenta para ele - tente de novo em instantes ou com um texto menor."
            ),
        )
    tipo = pedido.tipo_analise
    return {
        "tipo_analise": tipo,
        "trecho_analisado": r["trecho"],
        "caracteres_recebidos": len(pedido.texto),
        "categoria": r["categoria"],
        "rotulo": rotulo(tipo, r["categoria"]) if r["categoria"] else None,
        "confianca": r["confianca"],
        "alternativas": [
            {"categoria": c, "rotulo": rotulo(tipo, c), "probabilidade": p}
            for c, p in r["alternativas"]
        ],
        "pistas": r["pistas"],
        "motor": analisador.descricao,
        "segundos": round(time.perf_counter() - inicio, 3),
    }


@router.get(
    "/saude",
    response_model=Saude,
    summary="A API esta de pe? E o modelo?",
    response_description="Se o motor de analise esta carregado - e, se nao, por que.",
)
def saude():
    """Responde sempre 200 enquanto a API estiver no ar; o estado do modelo vem no corpo."""
    analisador = motor.MOTORES.get("analise")
    return {
        "ok": True,
        "modelo_carregado": analisador is not None,
        "motor": analisador.descricao if analisador else None,
        "motivo": None if analisador else motor.ESTADO["motivo"],
    }
