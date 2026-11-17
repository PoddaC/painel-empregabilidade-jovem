"""
motor_regras.py - a linha de base: palavras-chave, sem modelo nenhum.

Serve de comparacao na bancada e de plano B na API (PAINEL_MOTOR=regras).
Sem nenhuma palavra encontrada, nao responde (categoria None).
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
