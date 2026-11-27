"""
inicio.py - a porta de entrada: o problema em numeros, logo na primeira tela.

Quem abre o painel ve primeiro o que importa (o jovem procura e nao acha
mais que a media, e isso varia muito entre estados) e so depois os atalhos.
O texto longo sobre o projeto fica recolhido em "Sobre o painel".
"""

import streamlit as st

from comum import obter_todas
from graficos import cartao_link, metricas_jovens, ranking_ufs, serie_jovens
from src.data_access import carregar_ibge
from src.indicadores import pct, resumo_ibge

st.title("Painel de Empregabilidade Jovem")
st.caption("Onde o jovem mais procura emprego e não acha, e o que o mercado está sinalizando. "
           "ODS 8 (metas 8.5, 8.6 e 8.b) · dados do IBGE e da Agência Brasil.")

todas, fonte = obter_todas()
ibge, fonte_ibge = carregar_ibge()
r = resumo_ibge(ibge)

if r is None:
    st.warning("Os dados do IBGE ainda não foram coletados. Rode: `python -m src.coletar_ibge`")
else:
    # --- 1. o problema, em tres numeros ---
    metricas_jovens(r)

    jovens, total = r["brasil"]["18 a 24 anos"], r["brasil"]["total"]
    maior, menor = r["ufs"][0], r["ufs"][-1]
    vezes = f"{jovens / total:.1f}".replace(".", ",")
    st.markdown(
        f"No {r['periodo']}, o jovem de 18 a 24 anos ficou desocupado **{vezes} vezes** mais que a "
        f"média ({pct(jovens)} contra {pct(total)}). Entre os estados, vai de **{pct(menor[1])}** em "
        f"{menor[0]} a **{pct(maior[1])}** em {maior[0]}: um programa nacional uniforme não atende "
        "igual a todos."
    )

    # --- 2. onde (estados) e para onde vai (tempo) ---
    col_uf, col_serie = st.columns([1, 1], gap="large")
    with col_uf:
        st.subheader("Onde é maior")
        st.caption(f"18 a 24 anos, por UF, {r['periodo']}. Em laranja, os estados acima do Brasil.")
        ranking_ufs(r)
    with col_serie:
        st.subheader("Para onde vai")
        st.caption("Brasil, trimestre a trimestre. O jovem segue acima da média, mas a taxa vem caindo.")
        serie_jovens(r, grupos=("18 a 24 anos", "14 a 17 anos", "total"))

st.divider()

# --- 3. para onde ir agora ---
st.subheader("Explore")
c1, c2, c3 = st.columns(3)
with c1:
    cartao_link("paginas/conversa.py", "Pergunte ao assistente", "Em português, com memória, só com os números do painel.", "💬")
with c2:
    cartao_link("paginas/noticias.py", "Leia as notícias", f"{len(todas)} notícias de emprego, filtráveis e baixáveis.", "📰")
with c3:
    cartao_link("paginas/ciclo.py", "Veja como foi feito", "Da coleta ao insight, com os números de cada etapa.", "🔄")

with st.expander("Sobre o painel: o problema e para quem ele é"):
    st.markdown(
        """
**O problema.** Organizações de empregabilidade juvenil e quem as financia precisam
decidir **onde** e **para o quê** qualificar jovens, e costumam decidir sem dado.

**As perguntas que o painel responde.**
1. **Onde o desemprego jovem é maior?** Por estado e faixa de idade, e para onde ele vai (IBGE).
2. **O que o mercado está sinalizando?** O tom e os setores das notícias de emprego, lidas por um modelo de linguagem.
3. **E se eu quiser perguntar do meu jeito?** O assistente responde em português, só com os números do painel, e lembra da conversa.

**Para quem.** Coordenação e analistas de ONGs de empregabilidade; a direção ou o
financiador (inclusive a área de ESG de empresas) que aprova um programa; e, ao fim
da linha, jovens de 14 a 24 anos.
"""
    )

st.caption(f"Fontes: {fonte_ibge} · {fonte}")
