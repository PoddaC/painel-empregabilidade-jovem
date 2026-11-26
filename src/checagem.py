"""
checagem.py - a resposta usou algum numero que NAO esta nos fatos?

O prompt manda usar so os numeros dos FATOS. Esta checagem confere depois,
sem modelo: pega os numeros com casa decimal ou com % da resposta e procura
cada um no texto dos fatos. Os que nao estao la voltam numa lista, e a
pagina mostra um aviso ao lado da resposta.

Nao confere anos, trimestres nem contagens inteiras pequenas ("3 UFs"):
esses aparecem a toda hora sem ser dado. O que se inventa com mais
facilidade - uma taxa - tem virgula ou %.
"""

import re

NUMERO = re.compile(r"(?<![\w,.])(\d{1,3}(?:\.\d{3})+(?:,\d+)?|\d+[.,]\d+|\d+)(\s*%)?")


def _formas(n):
    """'11,1' -> {'11,1', '11.1'}: o modelo pode trocar o separador."""
    return {n, n.replace(",", "."), n.replace(".", ",")}


def numeros_sem_fonte(resposta, fatos):
    suspeitos = []
    for m in NUMERO.finditer(resposta):
        n, pct = m.group(1), m.group(2)
        decimal = bool(re.search(r"[.,]\d{1,2}$", n)) and not re.fullmatch(r"\d{1,3}(\.\d{3})+", n)
        if not (decimal or pct):
            continue
        if not any(f in fatos for f in _formas(n)):
            achado = n + ("%" if pct else "")
            if achado not in suspeitos:
                suspeitos.append(achado)
    return suspeitos
