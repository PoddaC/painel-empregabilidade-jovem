"""
indicadores.py - os numeros do IBGE que as paginas mostram, ja calculados.

So calculo, nada de tela: as paginas (paginas/*.py) e os graficos
(graficos.py) recebem o dicionario pronto. Assim a mesma conta nao e refeita
- de jeito diferente - em cada pagina.
"""

GRUPOS = ("18 a 24 anos", "14 a 17 anos", "total")
NOME_GRUPO = {"18 a 24 anos": "18 a 24 anos", "14 a 17 anos": "14 a 17 anos", "total": "Todas as idades"}


def _ano_antes(codigo):
    return f"{int(codigo[:4]) - 1}{codigo[4:]}"


def resumo_ibge(linhas):
    """
    Recebe as linhas de carregar_ibge() e devolve None (sem dados) ou:
      periodo, periodo_codigo        o ultimo trimestre ('2026-T3', '202603')
      brasil      {grupo: taxa}      Brasil no ultimo trimestre
      brasil_antes {grupo: taxa}     Brasil um ano antes
      ufs         [(uf, taxa), ...]  18 a 24 anos no ultimo trimestre, da maior para a menor
      serie       [{'trimestre', <grupo>: taxa, ...}]  Brasil, trimestre a trimestre
      coletado_em
    """
    if not linhas:
        return None
    idx = {(l["localidade"], l["grupo_idade"], l["periodo_codigo"]): l["taxa_desocupacao_pct"] for l in linhas}
    nome = {l["periodo_codigo"]: l["periodo"] for l in linhas}
    ult = max(nome)
    codigos = sorted(nome)

    serie = []
    for c in codigos:
        ponto = {"trimestre": nome[c]}
        for g in GRUPOS:
            if (v := idx.get(("Brasil", g, c))) is not None:
                ponto[g] = v
        serie.append(ponto)

    ufs = sorted(((l["localidade"], l["taxa_desocupacao_pct"]) for l in linhas
                  if l["nivel"] == "UF" and l["periodo_codigo"] == ult and l["grupo_idade"] == "18 a 24 anos"),
                 key=lambda x: x[1], reverse=True)
    return {
        "periodo": nome[ult],
        "periodo_codigo": ult,
        "brasil": {g: idx.get(("Brasil", g, ult)) for g in GRUPOS},
        "brasil_antes": {g: idx.get(("Brasil", g, _ano_antes(ult))) for g in GRUPOS},
        "ufs": ufs,
        "serie": serie,
        "coletado_em": linhas[0]["coletado_em"],
    }


def pct(x, casas=1):
    """11.1 -> '11,1%'."""
    return "—" if x is None else f"{x:.{casas}f}%".replace(".", ",")


def milhar(n):
    """1787 -> '1.787'."""
    return f"{n:,}".replace(",", ".")


def trimestre_de(ano_mes):
    """'2025-08' -> '2025-T3' (para cruzar noticias com o IBGE)."""
    ano, mes = ano_mes.split("-")
    return f"{ano}-T{(int(mes) - 1) // 3 + 1}"
