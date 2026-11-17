"""
api/modelos.py - os contratos da API, nas duas direcoes.

Quem recebe, valida (Aula 12): os modelos de ENTRADA recusam com 422 o que
nao cabe - inclusive campo a mais (extra="forbid"), em vez de descartar em
silencio.

Quem responde, promete (Aula 13): cada rota declara um modelo de RESPOSTA.
Ele filtra (so sai o que esta no modelo), confere (o que sai passa pela
validacao) e documenta (o /docs mostra os campos, nao "string").

Um contrato para cada direcao: a noticia que ENTRA nao tem id nem origem;
a que SAI, tem.
"""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from src.tarefas import TAREFAS, TIPOS, TODAS_AS_CATEGORIAS

TipoAnalise = Literal[TIPOS]                 # "tendencia" | "setor"
Categoria = Literal[TODAS_AS_CATEGORIAS]     # as 10 categorias das duas tarefas
Origem = Literal["coletada", "via_api"]


# -------------------------------------------------------------------
# ERRO - o formato de todo erro que a API devolve (menos o 422, que e
# uma LISTA de problemas, no formato do proprio FastAPI).
# -------------------------------------------------------------------
class Erro(BaseModel):
    detail: str = Field(description="O que aconteceu, em uma frase.")


# -------------------------------------------------------------------
# NOTICIAS
# -------------------------------------------------------------------
class Noticia(BaseModel):
    id: str = Field(description="Identificador estavel, ex: 2024-09_paises-da-ocde-reduzem...")
    titulo: str
    editoria: str
    ano_mes: str = Field(description="AAAA-MM, ou n/d.")
    url: str
    resumo: str = Field(default="", description="A linha fina da materia.")
    tem_texto: bool = Field(description="Se o texto integral foi coletado.")
    origem: Origem = Field(description="coletada (raspagem) ou via_api (POST).")
    recebida_em: str | None = Field(default=None, description="So para as via_api.")


class NoticiaComTexto(Noticia):
    texto: str = Field(description="O texto integral (vazio se nao foi coletado).")


class ListaNoticias(BaseModel):
    total: int = Field(description="Quantas batem com os filtros (antes do limite).")
    filtros: dict[str, str | int | None]
    noticias: list[Noticia]


class Estatisticas(BaseModel):
    total: int
    por_editoria: dict[str, int]
    por_mes: dict[str, int]
    por_origem: dict[str, int]


class Editorias(BaseModel):
    editorias: list[str]


class NoticiaEntrada(BaseModel):
    model_config = ConfigDict(
        extra="forbid",              # campo a mais: 422, nao descarte calado
        str_strip_whitespace=True,   # espacos das pontas nao contam
        json_schema_extra={"examples": [{
            "titulo": "Programa de primeiro emprego abre 2 mil vagas",
            "editoria": "economia",
            "ano_mes": "2026-10",
            "url": "https://exemplo.gov.br/noticia/2026-10/primeiro-emprego",
        }]},
    )

    titulo: str = Field(min_length=10, max_length=300, description="A manchete.")
    editoria: str = Field(default="n/d", max_length=50, description="Ex: economia.")
    ano_mes: str = Field(
        default="n/d", pattern=r"^(\d{4}-(0[1-9]|1[0-2])|n/d)$",
        description="Ano e mes da publicacao, AAAA-MM.",
    )
    url: str = Field(default="", max_length=500, description="Usada para nao duplicar.")


class NoticiaGravada(BaseModel):
    mensagem: str
    noticia: Noticia


# -------------------------------------------------------------------
# ANALISE - o contrato do POST /processar_texto (TP4, itens 2 e 3)
# -------------------------------------------------------------------
class PedidoAnalise(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        json_schema_extra={"examples": [{
            "texto": (
                "Brasil gerou mais de 235 mil novos postos de trabalho em agosto. "
                "No acumulado do ano, já foram geradas 1.726.489 novas vagas, "
                "segundo o Ministério do Trabalho e Emprego."
            ),
            "tipo_analise": "tendencia",
        }]},
    )

    texto: str = Field(
        min_length=15, max_length=20000,
        description="O texto a analisar. O modelo le os primeiros ~1.500 caracteres.",
    )
    tipo_analise: TipoAnalise = Field(
        default="tendencia",
        description="tendencia (otimista/pessimista/neutra) ou setor (da economia).",
    )


class Alternativa(BaseModel):
    categoria: Categoria
    rotulo: str
    probabilidade: float = Field(ge=0, le=1)


class ResultadoAnalise(BaseModel):
    tipo_analise: TipoAnalise
    trecho_analisado: str = Field(description="O que o modelo leu de fato.")
    caracteres_recebidos: int
    categoria: Categoria | None = Field(
        description="A categoria sugerida - SEMPRE uma da lista da tarefa. "
                    "null so quando o motor de regras nao acha pista nenhuma."
    )
    rotulo: str | None
    confianca: float = Field(
        ge=0, le=1,
        description="A nota que o motor deu a categoria. NAO e chance de acerto.",
    )
    alternativas: list[Alternativa] = Field(description="Todas as categorias, da mais a menos provavel.")
    pistas: list[str] = Field(description="Palavras que decidiram (so o motor de regras tem).")
    motor: str = Field(description="Quem analisou: modelo, precisao e dispositivo.")
    segundos: float = Field(description="Quanto a analise levou.")

    @model_validator(mode="after")
    def categoria_da_tarefa(self):
        """Promessa: a categoria pertence a tarefa pedida ('setor' nunca devolve 'otimista')."""
        validas = TAREFAS[self.tipo_analise]["categorias"]
        if self.categoria is not None and self.categoria not in validas:
            raise ValueError(f"categoria {self.categoria!r} nao pertence a tarefa {self.tipo_analise!r}")
        return self


class Saude(BaseModel):
    ok: bool
    modelo_carregado: bool
    motor: str | None = Field(description="O motor carregado, se houver.")
    motivo: str | None = Field(default=None, description="Por que o modelo nao carregou.")


class Raiz(BaseModel):
    projeto: str
    ods: str
    rotas: list[str]
