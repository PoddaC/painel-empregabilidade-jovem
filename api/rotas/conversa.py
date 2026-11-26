"""
api/rotas/conversa.py - o assistente que conversa sobre os dados do painel.

    POST   /conversa        pergunta (+ conversa_id, memoria) -> resposta
    GET    /conversa/{id}   a conversa inteira
    DELETE /conversa/{id}   apaga a conversa (dado pessoal)

A regra de cada pergunta mora em src/conversa.py (a mesma que o painel usa
direto no Streamlit Cloud, onde a API nao roda):
1. a memoria escolhida decide o que o modelo le da conversa (src/memoria.py);
2. o Python calcula os FATOS dos lugares em foco (src/fatos.py);
3. o modelo online redige a resposta (src/llm_api.py: Groq, depois Gemini);
4. a resposta e conferida: numero fora dos fatos vira aviso (src/checagem.py);
5. a conversa e gravada (api/conversas.py).
"""

from fastapi import APIRouter, HTTPException, Request, Response, status

from api import conversas
from api.erros import erro
from api.modelos import Conversa, PedidoConversa, RespostaConversa
from api.registro import anotar
from src import conversa as nucleo
from src import llm_api

router = APIRouter(tags=["conversa"])


def _indisponivel(e):
    motivos = "; ".join(f"{p}: {m}" for p, m in e.motivos.items())
    return HTTPException(
        status.HTTP_503_SERVICE_UNAVAILABLE,
        detail=(f"O assistente está indisponível agora ({motivos}). "
                "O resto do painel funciona normalmente - tente de novo em instantes."),
    )


@router.post(
    "/conversa",
    response_model=RespostaConversa,
    summary="Pergunta ao assistente sobre os dados do painel (com memoria)",
    response_description="A resposta, quem respondeu, o que o modelo leu e a conferencia dos numeros.",
    responses={
        404: erro("conversa_id nao existe (ou foi apagada)."),
        503: erro("Nenhum modelo online respondeu (sem chave, limite de uso, provedor fora)."),
    },
)
def conversar(pedido: PedidoConversa, request: Request):
    """
    Responde com base **so** nos fatos que o painel calcula (IBGE e noticias
    coletadas). Sem `conversa_id`, abre uma conversa nova e devolve o id;
    com ele, continua a conversa - e a `memoria` escolhida decide o que o
    modelo le dela. `numeros_sem_fonte` lista os numeros da resposta que nao
    estao nos fatos (vazio = tudo conferido).

    A pergunta vai a um provedor externo (Groq ou Google). Nao envie dado pessoal.
    """
    if pedido.conversa_id:
        conversa = conversas.ler(pedido.conversa_id)
        if conversa is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND,
                                detail="Essa conversa não existe ou foi apagada. Comece uma nova (sem conversa_id).")
    else:
        conversa = conversas.nova(pedido.memoria)
    anotar(request, memoria=pedido.memoria, caracteres=len(pedido.pergunta),
           conversa=conversa["id"][:8], turno=len(conversa["mensagens"]) // 2 + 1)

    try:
        resultado = nucleo.responder(conversa, pedido.pergunta, pedido.memoria)
    except llm_api.LLMIndisponivel as e:
        anotar(request, falhas=e.motivos)
        raise _indisponivel(e)
    resposta = nucleo.registrar(conversa, pedido.pergunta, pedido.memoria, resultado)
    conversas.gravar(conversa)

    anotar(request, provedor=resposta["provedor"], modelo=resposta["modelo"],
           tokens_entrada=resposta["tokens_entrada"], tokens_saida=resposta["tokens_saida"],
           mensagens_enviadas=resposta["leitura"]["mensagens_enviadas"],
           chamada_de_resumo=resposta["chamada_de_resumo"], numeros_sem_fonte=len(resposta["numeros_sem_fonte"]))
    return resposta


@router.get(
    "/conversa/{conversa_id}",
    response_model=Conversa,
    summary="Le uma conversa",
    responses={404: erro("conversa_id nao existe (ou foi apagada).")},
)
def ler_conversa(conversa_id: str):
    """A conversa inteira, com as notas e o resumo que o painel guardou."""
    conversa = conversas.ler(conversa_id)
    if conversa is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Essa conversa não existe ou foi apagada.")
    return conversa


@router.delete(
    "/conversa/{conversa_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    summary="Apaga uma conversa",
    responses={404: erro("conversa_id nao existe (ou ja foi apagada).")},
)
def apagar_conversa(conversa_id: str):
    """Apaga o arquivo da conversa. Nao ha lixeira: some de vez."""
    if not conversas.apagar(conversa_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Essa conversa não existe ou já foi apagada.")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
