"""
tarefas.py - O QUE o modelo responde: as duas perguntas e as categorias.

Fica fora da API e dos motores de proposito. A API usa as listas para o
contrato (a categoria devolvida e SEMPRE uma destas), cada motor usa as
definicoes para perguntar, e a bancada usa as duas para medir. Mudar uma
categoria e mudar aqui - e so aqui.

As duas tarefas respondem a pergunta do projeto por partes:
- "setor":     DE QUE setor a noticia fala?
- "tendencia": o que ela diz sobre o emprego - melhora, piora ou nada claro?
Cruzadas, viram o sinal que a ONG procura: setores com noticias de expansao.
"""

TAREFAS = {
    "tendencia": {
        "nome": "Tendência do emprego",
        "pergunta": (
            "O que esta notícia indica sobre o emprego e as condições de "
            "trabalho no Brasil?"
        ),
        "categorias": {
            "otimista": {
                "rotulo": "Otimista",
                "definicao": (
                    "aponta melhora: mais vagas, menos desemprego, renda maior "
                    "ou iniciativas que abrem oportunidades de trabalho"
                ),
            },
            "pessimista": {
                "rotulo": "Pessimista",
                "definicao": (
                    "aponta piora ou risco: perda ou desaceleração de vagas, "
                    "demissões, condições de trabalho piores"
                ),
            },
            "neutra": {
                "rotulo": "Neutra",
                "definicao": (
                    "é informativa ou sem direção clara: regras, serviços, "
                    "debate de propostas, resultados mistos, ou o assunto não "
                    "é o emprego no Brasil"
                ),
            },
        },
    },
    "setor": {
        "nome": "Setor da economia",
        "pergunta": (
            "Qual setor da economia é o assunto principal desta notícia?"
        ),
        "categorias": {
            "industria": {
                "rotulo": "Indústria",
                "definicao": "fábricas, produção industrial, indústria de transformação",
            },
            "construcao": {
                "rotulo": "Construção",
                "definicao": "construção civil, obras, incorporações imobiliárias",
            },
            "comercio": {
                "rotulo": "Comércio",
                "definicao": "comércio e varejo: lojas, supermercados, vendas ao consumidor",
            },
            "servicos": {
                "rotulo": "Serviços",
                "definicao": (
                    "serviços: turismo, eventos, aplicativos e plataformas, "
                    "tecnologia, transporte"
                ),
            },
            "agropecuaria": {
                "rotulo": "Agropecuária",
                "definicao": "agricultura, pecuária, agronegócio",
            },
            "setor_publico": {
                "rotulo": "Setor público",
                "definicao": "emprego público: concursos, servidores, empresas estatais",
            },
            "geral": {
                "rotulo": "Mercado em geral",
                "definicao": (
                    "o mercado de trabalho como um todo (desemprego, saldo total "
                    "de vagas, renda média, leis e jornada), mesmo citando setores"
                ),
            },
        },
    },
}

TIPOS = tuple(TAREFAS)  # ("tendencia", "setor")

# Todas as categorias, das duas tarefas - para o contrato da resposta.
TODAS_AS_CATEGORIAS = tuple(
    cat for tarefa in TAREFAS.values() for cat in tarefa["categorias"]
)

# Quanto do texto o modelo le. Noticia segue a piramide invertida: o
# essencial esta no titulo, na linha fina e nos primeiros paragrafos.
# Ler o texto inteiro custaria tempo (o custo cresce com o tamanho) para
# pouco ganho - e o recorte vai na resposta, para o usuario conferir.
LIMITE_TRECHO = 1500


def categorias(tipo):
    """As categorias de uma tarefa, na ordem em que sao apresentadas."""
    return list(TAREFAS[tipo]["categorias"])


def rotulo(tipo, categoria):
    """O nome bonito de uma categoria ('setor_publico' -> 'Setor público')."""
    return TAREFAS[tipo]["categorias"][categoria]["rotulo"]


def recortar(texto, limite=LIMITE_TRECHO):
    """
    O trecho que o modelo vai ler: o comeco do texto, cortado num espaco
    (nunca no meio de uma palavra). Espacos repetidos viram um so.
    """
    texto = " ".join(texto.split())
    if len(texto) <= limite:
        return texto
    corte = texto.rfind(" ", 0, limite)
    return texto[: corte if corte > 0 else limite] + " [...]"


def montar_texto(titulo, resumo="", corpo=""):
    """Titulo + linha fina + corpo: o texto de uma noticia do acervo."""
    partes = [p.strip() for p in (titulo, resumo, corpo) if p and p.strip()]
    return "\n\n".join(partes)
