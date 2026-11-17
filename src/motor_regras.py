"""
motor_regras.py - a linha de base: palavras-chave, sem modelo nenhum.

Nao e o motor do produto. Esta aqui por dois motivos:
1. MEDIR: a bancada compara cada modelo com ele. Um modelo de centenas de MB
   so se justifica se acertar mais do que uma lista de palavras.
2. ALTERNATIVA DECLARADA: numa maquina que nao aguenta o modelo, a API pode
   subir com PAINEL_MOTOR=regras - e a resposta diz que foi este motor.

Quando nenhuma palavra aparece, ele CALA (categoria None) em vez de chutar.
Errar e calar nao sao a mesma coisa - a bancada conta os dois.
"""

import re
import unicodedata

from src.tarefas import recortar

# As listas crescem olhando os erros. Sem acento: o texto e normalizado antes.
PALAVRAS = {
    "tendencia": {
        "otimista": [
            "recorde", "cresce", "cresceu", "crescimento", "aumento", "aumentar",
            "alta", "abre", "abriu", "gerou", "criacao", "cria", "saldo positivo",
            "menor desemprego", "cai a taxa", "diminui", "recupera", "aquecido",
            "novas vagas", "novos postos", "oportunidade",
        ],
        "pessimista": [
            "demissao", "demissoes", "desaceleracao", "recuar", "recuo",
            "queda no emprego", "fechamento", "perda", "piora", "crise",
            "tarifaco", "menor nivel", "critica", "risco", "cruel",
        ],
        "neutra": [
            "entenda", "proposta", "debate", "pec", "regra", "aplicativo",
            "saque", "fgts", "dolar", "bolsa",
        ],
    },
    "setor": {
        "industria": ["industria", "fabrica", "fabricacao", "transformacao", "cni"],
        "construcao": ["construcao", "obras", "incorporac", "imobiliari"],
        "comercio": ["comercio", "varejo", "supermercado", "lojas", "vendedor"],
        "servicos": ["servicos", "turismo", "aplicativo", "plataforma", "entregador", "evento"],
        "agropecuaria": ["agro", "agricultura", "pecuaria", "safra", "rural"],
        "setor_publico": ["concurso", "servidor", "estatal", "setor publico"],
        "geral": ["desemprego", "caged", "pnad", "taxa de", "mercado de trabalho", "carteira assinada"],
    },
}

NOME = "regras (palavras-chave)"


def _normalizar(texto):
    texto = unicodedata.normalize("NFKD", texto.lower())
    return texto.encode("ascii", "ignore").decode()


def analisar(texto, tipo):
    """
    Conta quantas palavras de cada categoria aparecem no trecho.

    Devolve o mesmo formato de todo motor:
    {"categoria", "confianca", "alternativas", "trecho", "pistas"}.
    A "confianca" aqui e a fatia das pistas que apontam para a vencedora.
    """
    trecho = recortar(texto)
    alvo = _normalizar(trecho)

    achadas = {}
    for categoria, palavras in PALAVRAS[tipo].items():
        hits = [p for p in palavras if re.search(rf"\b{re.escape(p)}", alvo)]
        if hits:
            achadas[categoria] = hits

    total = sum(len(h) for h in achadas.values())
    # todas as categorias, da mais a menos citada (as sem pista, com 0)
    ordem = sorted(PALAVRAS[tipo], key=lambda c: len(achadas.get(c, [])), reverse=True)
    alternativas = [(c, round(len(achadas.get(c, [])) / total, 4) if total else 0.0) for c in ordem]
    if not total:
        return {"categoria": None, "confianca": 0.0, "alternativas": alternativas,
                "trecho": trecho, "pistas": []}

    vencedora = ordem[0]
    return {
        "categoria": vencedora,
        "confianca": round(len(achadas[vencedora]) / total, 4),
        "alternativas": alternativas,
        "trecho": trecho,
        "pistas": achadas[vencedora],
    }


class MotorRegras:
    """O mesmo jeito de chamar que o AnalisadorLLM - a API nao sabe a diferenca."""

    descricao = NOME
    memoria_mb = 0.0

    def analisar(self, texto, tipo):
        return analisar(texto, tipo)
