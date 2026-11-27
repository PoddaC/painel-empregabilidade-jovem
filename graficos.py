"""
graficos.py - os graficos e blocos visuais que mais de uma pagina usa.

Regras de cor, iguais em todas as paginas:
- LARANJA = jovens de 18 a 24 anos (o foco do painel) e o que e destaque;
- AZUL    = adolescentes de 14 a 17 anos;
- CINZA tracejado = todas as idades (a referencia), para nao depender so da cor.
As duas cores foram conferidas para daltonismo e para tema claro e escuro.

Os graficos sao Altair (vem junto com o Streamlit): da para fixar a cor por
serie, tracejar a referencia e mostrar o valor ao passar o mouse.
"""

import altair as alt
import streamlit as st

from src.indicadores import NOME_GRUPO, pct

LARANJA = "#eb6834"
AZUL = "#2a78d6"
CINZA = "#8a8f98"

COR_GRUPO = {"18 a 24 anos": LARANJA, "14 a 17 anos": AZUL, "Todas as idades": CINZA}


def metricas_jovens(r):
    """Tres numeros grandes: 18-24, 14-17 e todas as idades, com a variacao em um ano."""
    cols = st.columns(3)
    for col, g in zip(cols, ("18 a 24 anos", "14 a 17 anos", "total")):
        agora, antes = r["brasil"].get(g), r["brasil_antes"].get(g)
        delta = None
        if agora is not None and antes is not None:
            delta = f"{agora - antes:+.1f}".replace(".", ",") + " p.p. em um ano"
        col.metric(f"Desocupação · {NOME_GRUPO[g]}", pct(agora), delta,
                   delta_color="inverse",  # cair e bom: verde
                   help=f"Brasil, {r['periodo']}. IBGE, PNAD Contínua. "
                        "Desocupado é quem procurou trabalho e não achou.")


def ranking_ufs(r):
    """As UFs da maior para a menor desocupação de 18 a 24 anos; a linha marca o Brasil."""
    altura = 22 * len(r["ufs"]) + 40  # uma linha por UF, para nenhum nome sumir
    brasil = r["brasil"]["18 a 24 anos"]
    dados = [{"UF": uf, "taxa": t, "acima": "Acima do Brasil" if t > brasil else "Até o Brasil"}
             for uf, t in r["ufs"]]
    barras = alt.Chart(alt.Data(values=dados)).mark_bar(cornerRadiusEnd=3).encode(
        y=alt.Y("UF:N", sort="-x", title=None, axis=alt.Axis(labelOverlap=False, labelLimit=160)),
        x=alt.X("taxa:Q", title="desocupação de 18 a 24 anos (%)"),
        color=alt.Color("acima:N", title=None, legend=alt.Legend(orient="bottom"),
                        scale=alt.Scale(domain=["Acima do Brasil", "Até o Brasil"], range=[LARANJA, CINZA])),
        tooltip=[alt.Tooltip("UF:N"), alt.Tooltip("taxa:Q", title="desocupação (%)", format=".1f")],
    )
    linha = alt.Chart(alt.Data(values=[{"x": brasil}])).mark_rule(strokeDash=[4, 3]).encode(x="x:Q")
    rotulo = alt.Chart(alt.Data(values=[{"x": brasil, "t": f"Brasil {pct(brasil)}"}])).mark_text(
        align="left", dx=4, dy=-6, fontSize=11).encode(x="x:Q", y=alt.value(0), text="t:N")
    st.altair_chart((barras + linha + rotulo).properties(height=altura), width="stretch")


def serie_jovens(r, desde=None, grupos=("18 a 24 anos", "total"), altura=300):
    """Brasil, trimestre a trimestre. desde='2024-T2' corta o comeco."""
    pontos = []
    for p in r["serie"]:
        if desde and p["trimestre"] < desde:
            continue
        for g in grupos:
            if g in p:
                pontos.append({"trimestre": p["trimestre"], "grupo": NOME_GRUPO[g], "taxa": p[g]})
    nomes = [NOME_GRUPO[g] for g in grupos]
    graf = alt.Chart(alt.Data(values=pontos)).mark_line(point=True, strokeWidth=2).encode(
        x=alt.X("trimestre:O", title=None, axis=alt.Axis(labelAngle=-45)),
        y=alt.Y("taxa:Q", title="desocupação no Brasil (%)"),
        color=alt.Color("grupo:N", title=None, legend=alt.Legend(orient="bottom"),
                        scale=alt.Scale(domain=nomes, range=[COR_GRUPO[n] for n in nomes])),
        strokeDash=alt.StrokeDash("grupo:N", legend=None,
                                  scale=alt.Scale(domain=nomes, range=[[4, 3] if n == "Todas as idades" else [1, 0]
                                                                       for n in nomes])),
        tooltip=[alt.Tooltip("trimestre:O"), alt.Tooltip("grupo:N"),
                 alt.Tooltip("taxa:Q", title="desocupação (%)", format=".1f")],
    )
    st.altair_chart(graf.properties(height=altura), width="stretch")


def barras_destaque(dados, destaque, titulo_x, referencia=None, altura=220):
    """
    Barras horizontais com UMA em laranja (o destaque) e as outras em cinza.
    dados: [{"nome": ..., "valor": ...}]. referencia: valor de uma linha tracejada.
    """
    for d in dados:
        d["tipo"] = "destaque" if d["nome"] == destaque else "outro"
    barras = alt.Chart(alt.Data(values=dados)).mark_bar(cornerRadiusEnd=3).encode(
        y=alt.Y("nome:N", sort="-x", title=None, axis=alt.Axis(labelLimit=220)),
        x=alt.X("valor:Q", title=titulo_x),
        color=alt.Color("tipo:N", legend=None,
                        scale=alt.Scale(domain=["destaque", "outro"], range=[LARANJA, CINZA])),
        tooltip=[alt.Tooltip("nome:N", title=" "), alt.Tooltip("valor:Q", title=titulo_x)],
    )
    camadas = barras
    if referencia is not None:
        camadas += alt.Chart(alt.Data(values=[{"x": referencia}])).mark_rule(strokeDash=[4, 3]).encode(x="x:Q")
    st.altair_chart(camadas.properties(height=altura), width="stretch")


def cartao_link(pagina, titulo, texto, icone):
    """Um atalho com uma linha de explicacao: o que a pessoa encontra la."""
    with st.container(border=True):
        st.page_link(pagina, label=f"**{titulo}**", icon=icone)
        st.caption(texto)
