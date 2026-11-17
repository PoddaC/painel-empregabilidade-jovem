"""
api/rotas/noticias.py - o acervo de noticias: consultar e receber.

ATENCAO A ORDEM: caminho FIXO antes de caminho com PARAMETRO. O FastAPI
testa as rotas na ordem em que foram declaradas, e /noticias/{id} casaria
com a palavra "estatisticas" se viesse antes.
"""

import csv
import threading
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query, status

from api.erros import erro
from api.modelos import (Editorias, Estatisticas, ListaNoticias,
                         NoticiaComTexto, NoticiaEntrada, NoticiaGravada)
from src.data_access import (CSV_NOTICIAS, PROCESSED, carregar_noticias,
                             id_da_noticia, ler_texto)

router = APIRouter(tags=["noticias"])

CSV_API = PROCESSED / "noticias_via_api.csv"
COLUNAS_API = ["titulo", "editoria", "ano_mes", "url", "recebida_em"]

# Rotas def rodam em paralelo (threads). Dois POSTs ao mesmo tempo
# escreveriam no mesmo arquivo juntos - a trava faz um esperar o outro,
# so durante a gravacao (Aula 12).
TRAVA_GRAVACAO = threading.Lock()

SEM_ACERVO = (
    "Os dados ainda nao foram coletados nesta maquina. Rode a coleta: "
    "python -m src.coletar && python -m src.coletar_textos"
)


# -------------------------------------------------------------------
# LEITURA
# -------------------------------------------------------------------
def ler_recebidas():
    """As noticias que chegaram pelo POST. Lista vazia se ainda nao ha."""
    if not CSV_API.exists():
        return []
    with CSV_API.open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _publica(n, origem):
    """Uma linha do CSV -> o formato que a API PROMETE (modelo Noticia)."""
    return {
        "id": id_da_noticia(n),
        "titulo": n.get("titulo", ""),
        "editoria": n.get("editoria") or "n/d",
        "ano_mes": n.get("ano_mes") or "n/d",
        "url": n.get("url", ""),
        "resumo": n.get("resumo", ""),
        "tem_texto": bool((n.get("arquivo_texto") or "").strip()),
        "origem": origem,
        "recebida_em": n.get("recebida_em"),
    }


def acervo():
    """
    Coletadas + recebidas pela API, cada uma com sua origem.

    Sem coleta nenhuma nesta maquina, levanta 503: "nao coletado" nao e o
    mesmo que "nenhuma noticia" - um 200 vazio faria o cliente concluir que
    nao ha noticias de emprego (o "zero que nao era zero", Aula 13).
    """
    if not CSV_NOTICIAS.exists() and not CSV_API.exists():
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, detail=SEM_ACERVO)
    coletadas, _ = carregar_noticias()
    return (
        [_publica(n, "coletada") for n in coletadas]
        + [_publica(n, "via_api") for n in ler_recebidas()]
    )


# -------------------------------------------------------------------
# ROTAS GET
# -------------------------------------------------------------------
@router.get(
    "/noticias",
    response_model=ListaNoticias,
    summary="Consulta as noticias",
    response_description="Total encontrado, filtros aplicados e a lista.",
    responses={503: erro("A coleta ainda nao rodou nesta maquina.")},
)
def listar_noticias(
    editoria: str | None = Query(default=None, description="Filtra por editoria (exato)."),
    busca: str | None = Query(default=None, min_length=2, description="Termo procurado no titulo."),
    limite: int = Query(default=50, ge=1, le=500, description="Quantas noticias devolver."),
):
    """
    Devolve as noticias do acervo. Os parametros podem ser combinados, ex:
    `/noticias?editoria=economia&busca=desemprego&limite=5`.

    Nenhuma noticia no recorte NAO e erro: e 200 com a lista vazia. Uma
    consulta recorta uma colecao, e "nenhuma" e uma resposta certa.
    """
    noticias = acervo()
    if editoria:
        noticias = [n for n in noticias if n["editoria"] == editoria]
    if busca:
        termo = busca.lower().strip()
        noticias = [n for n in noticias if termo in n["titulo"].lower()]
    return {
        "total": len(noticias),
        "filtros": {"editoria": editoria, "busca": busca, "limite": limite},
        "noticias": noticias[:limite],
    }


@router.get(
    "/noticias/estatisticas",
    response_model=Estatisticas,
    summary="Resume o acervo em numeros",
    response_description="Totais por editoria, por mes e por origem.",
    responses={503: erro("A coleta ainda nao rodou nesta maquina.")},
)
def estatisticas():
    """O mesmo numero que o painel desenha nos graficos - aqui em JSON."""
    noticias = acervo()   # 503 se a coleta nao rodou

    def contar(campo):
        contagem = {}
        for n in noticias:
            chave = n.get(campo) or "n/d"
            contagem[chave] = contagem.get(chave, 0) + 1
        return dict(sorted(contagem.items()))

    return {
        "total": len(noticias),
        "por_editoria": contar("editoria"),
        "por_mes": contar("ano_mes"),
        "por_origem": contar("origem"),
    }


@router.get(
    "/noticias/{id}",
    response_model=NoticiaComTexto,
    summary="Uma noticia, com o texto integral",
    response_description="A noticia e o texto coletado.",
    responses={404: erro("Nao ha noticia com esse id.")},
)
def obter_noticia(id: str):
    """
    O caminho IDENTIFICA uma noticia - se ela nao existe, 404 (e nao 200
    vazio). O id aparece em cada item de `GET /noticias`.
    """
    coletadas, _ = carregar_noticias()
    for n in coletadas:
        if id_da_noticia(n) == id:
            return {**_publica(n, "coletada"), "texto": ler_texto(n)}
    for n in ler_recebidas():
        if id_da_noticia(n) == id:
            return {**_publica(n, "via_api"), "texto": ""}
    raise HTTPException(
        status.HTTP_404_NOT_FOUND,
        detail=f"Nao ha noticia com o id '{id}'. Os ids validos aparecem em GET /noticias.",
    )


@router.get(
    "/editorias",
    response_model=Editorias,
    summary="Lista as editorias existentes",
    response_description="Lista de editorias, em ordem alfabetica.",
    responses={503: erro("A coleta ainda nao rodou nesta maquina.")},
)
def listar_editorias():
    """Serve para montar um filtro sem adivinhar os valores."""
    return {"editorias": sorted({n["editoria"] for n in acervo()})}


# -------------------------------------------------------------------
# ROTA POST
# -------------------------------------------------------------------
@router.post(
    "/noticias",
    status_code=status.HTTP_201_CREATED,
    response_model=NoticiaGravada,
    summary="Envia uma noticia nova",
    response_description="A noticia gravada, com id e a hora em que chegou.",
    responses={409: erro("Essa noticia ja esta no acervo.")},
)
def receber_noticia(noticia: NoticiaEntrada):
    """
    Recebe uma noticia em JSON e acrescenta ao acervo. O corpo e validado
    antes de tudo: titulo curto, `ano_mes` fora de AAAA-MM ou campo que a
    API nao conhece sao recusados com 422 e o motivo.

    A noticia vai para `data/processed/noticias_via_api.csv`, separada das
    coletadas - procedencia nao se mistura. A mesma `url` duas vezes: 409.
    """
    with TRAVA_GRAVACAO:
        coletadas, _ = carregar_noticias()
        identidade = noticia.url or noticia.titulo
        for existente in ler_recebidas() + coletadas:
            if (existente.get("url") or existente.get("titulo")) == identidade:
                raise HTTPException(
                    status.HTTP_409_CONFLICT,
                    detail=f"Esta noticia ja esta no acervo (id {id_da_noticia(existente)}). Nada foi gravado.",
                )

        linha = {**noticia.model_dump(), "recebida_em": datetime.now().isoformat(timespec="seconds")}
        CSV_API.parent.mkdir(parents=True, exist_ok=True)
        novo = not CSV_API.exists()
        with CSV_API.open("a", newline="", encoding="utf-8") as f:   # "a": acrescenta, nunca zera
            escritor = csv.DictWriter(f, fieldnames=COLUNAS_API, extrasaction="ignore")
            if novo:
                escritor.writeheader()
            escritor.writerow(linha)

    return {"mensagem": "Noticia recebida.", "noticia": _publica(linha, "via_api")}
