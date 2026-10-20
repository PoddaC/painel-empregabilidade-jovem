"""
api/main.py - a API do Painel de Empregabilidade Jovem.

    uvicorn api.main:app --reload     ->  http://127.0.0.1:8000/docs

O painel e para PESSOAS; esta API e para PROGRAMAS. As duas leem a MESMA
pasta data/processed/, lado a lado: uma nao depende da outra estar de pe.
"""

from datetime import datetime
from pathlib import Path
import csv

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

from src.data_access import carregar_noticias

BASE = Path(__file__).resolve().parent.parent
CSV_API = BASE / "data" / "processed" / "noticias_via_api.csv"
COLUNAS_API = ["titulo", "editoria", "ano_mes", "url", "recebida_em"]

app = FastAPI(
    title="API do Painel de Empregabilidade Jovem",
    version="1.0.0",
    description=(
        "Serve as noticias de emprego coletadas da Agencia Brasil e recebe "
        "noticias novas enviadas por outros programas.\n\n"
        "Projeto de Bloco: IA Aplicada - ODS 8, meta 8.6."
    ),
)


# -------------------------------------------------------------------
# MODELO DE ENTRADA - o contrato do POST.
# O tipo nao e enfeite: o Pydantic confere ANTES de a funcao rodar e
# devolve 422 com o motivo. Sem isso, lixo entraria calado.
# -------------------------------------------------------------------
class NoticiaEntrada(BaseModel):
    titulo: str = Field(
        min_length=10,
        max_length=300,
        description="A manchete. Pelo menos 10 caracteres.",
    )
    editoria: str = Field(
        default="n/d",
        max_length=50,
        description="Editoria da materia, ex: economia.",
    )
    ano_mes: str = Field(
        default="n/d",
        pattern=r"^(\d{4}-\d{2}|n/d)$",
        description="Ano e mes da publicacao, no formato AAAA-MM.",
    )
    url: str = Field(
        default="",
        max_length=500,
        description="Endereco da materia. Usado para nao duplicar.",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [{
                "titulo": "Programa de primeiro emprego abre 2 mil vagas",
                "editoria": "economia",
                "ano_mes": "2026-10",
                "url": "https://exemplo.gov.br/noticia/2026-10/primeiro-emprego",
            }]
        }
    }


# -------------------------------------------------------------------
# LEITURA DOS DADOS
# -------------------------------------------------------------------
def ler_recebidas():
    """As noticias que chegaram pelo POST. Lista vazia se ainda nao ha."""
    if not CSV_API.exists():
        return []
    with CSV_API.open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def acervo():
    """Coletadas + recebidas pela API, cada uma com sua origem."""
    coletadas, _ = carregar_noticias()
    return (
        [{**n, "origem": "coletada"} for n in coletadas]
        + [{**n, "origem": "via_api"} for n in ler_recebidas()]
    )


# -------------------------------------------------------------------
# ROTAS GET
#
# ATENCAO A ORDEM: caminho FIXO antes de caminho com PARAMETRO. O FastAPI
# testa as rotas na ordem em que foram declaradas, e um {parametro} casa
# com qualquer palavra - declarada antes, /noticias/estatisticas nunca
# seria alcancada.
# -------------------------------------------------------------------
@app.get(
    "/",
    summary="Identifica a API",
    description="Devolve o nome do projeto e os caminhos disponiveis. "
                "Serve para um programa descobrir o que existe aqui.",
    response_description="Nome, versao e lista de rotas.",
)
def raiz():
    return {
        "projeto": "Painel de Empregabilidade Jovem",
        "ods": "8 - Trabalho Decente e Crescimento Economico (meta 8.6)",
        "rotas": ["/noticias", "/noticias/estatisticas", "/editorias", "/docs"],
    }


@app.get(
    "/noticias",
    summary="Consulta as noticias",
    description=(
        "Devolve as noticias do acervo. Sem parametro nenhum, devolve "
        "tudo (ate o limite). Os parametros podem ser combinados:\n\n"
        "- `editoria`: so as de uma editoria, ex: `economia`\n"
        "- `busca`: so as que tem esse termo no titulo\n"
        "- `limite`: quantas devolver, de 1 a 500\n\n"
        "Exemplo: `/noticias?editoria=economia&busca=desemprego&limite=5`"
    ),
    response_description="Total encontrado, filtros aplicados e a lista.",
)
def listar_noticias(
    editoria: str | None = Query(
        default=None, description="Filtra por editoria (exato)."
    ),
    busca: str | None = Query(
        default=None, min_length=2, description="Termo procurado no titulo."
    ),
    limite: int = Query(
        default=50, ge=1, le=500, description="Quantas noticias devolver."
    ),
):
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


@app.get(
    "/noticias/estatisticas",
    summary="Resume o acervo em numeros",
    description=(
        "Contagem de noticias por editoria, por mes e por origem. E o mesmo "
        "numero que o painel desenha nos graficos - aqui em JSON, para quem "
        "quiser calcular em cima."
    ),
    response_description="Totais por editoria, por mes e por origem.",
)
def estatisticas():
    noticias = acervo()
    if not noticias:
        raise HTTPException(
            status_code=404,
            detail="Acervo vazio. Rode a coleta: python -m src.coletar",
        )

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


@app.get(
    "/editorias",
    summary="Lista as editorias existentes",
    description="As editorias presentes no acervo, em ordem alfabetica. "
                "Serve para montar um filtro sem adivinhar os valores.",
    response_description="Lista de editorias.",
)
def listar_editorias():
    return {"editorias": sorted({n["editoria"] for n in acervo()})}


# -------------------------------------------------------------------
# ROTA POST
# -------------------------------------------------------------------
@app.post(
    "/noticias",
    status_code=201,
    summary="Envia uma noticia nova",
    description=(
        "Recebe uma noticia em JSON e acrescenta ao acervo. O corpo e "
        "validado antes de qualquer coisa: titulo com menos de 10 "
        "caracteres ou `ano_mes` fora do formato AAAA-MM sao recusados "
        "com 422 e o motivo.\n\n"
        "A noticia e gravada em `data/processed/noticias_via_api.csv`, "
        "separada das coletadas - procedencia nao se mistura.\n\n"
        "Enviar a mesma `url` duas vezes devolve 409."
    ),
    response_description="A noticia gravada, com a hora em que chegou.",
)
def receber_noticia(noticia: NoticiaEntrada):
    recebidas = ler_recebidas()
    coletadas, _ = carregar_noticias()

    # GUARDA: nao aceita duas vezes a mesma materia. A url identifica;
    # sem url, o titulo serve.
    identidade = noticia.url or noticia.titulo
    for existente in recebidas + coletadas:
        if (existente.get("url") or existente.get("titulo")) == identidade:
            raise HTTPException(
                status_code=409,
                detail="Esta noticia ja esta no acervo.",
            )

    linha = {
        "titulo": noticia.titulo,
        "editoria": noticia.editoria,
        "ano_mes": noticia.ano_mes,
        "url": noticia.url,
        "recebida_em": datetime.now().isoformat(timespec="seconds"),
    }

    CSV_API.parent.mkdir(parents=True, exist_ok=True)
    novo = not CSV_API.exists()
    with CSV_API.open("a", newline="", encoding="utf-8") as f:
        escritor = csv.DictWriter(f, fieldnames=COLUNAS_API, extrasaction="ignore")
        if novo:
            escritor.writeheader()
        escritor.writerow(linha)

    return {"mensagem": "Noticia recebida.", "noticia": linha}
