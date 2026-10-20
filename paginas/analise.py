"""
analise.py - o que as noticias do recorte mais falam, e como se distribuem.

"""

import re
from collections import Counter

import simplemma
import streamlit as st
from wordcloud import WordCloud

from comum import obter_todas, guarda_sem_dados, filtros_sidebar

# Palavras vazias (stopwords) - DECISAO EDITORIAL: o que nao agrega a nuvem.
# Esta lista cresce olhando o resultado; por isso fica visivel aqui.
STOPWORDS = {
    "de", "a", "o", "e", "do", "da", "em", "um", "uma", "para", "com", "nao",
    "que", "os", "as", "no", "na", "por", "mais", "dos", "das", "ao", "pelo",
    "pela", "se", "como", "mas", "ou", "ser", "ter", "dizer", "seu", "sua",
    "ano", "anos", "diz", "apos", "sobre", "entre", "ate", "sao", "tem",
    "foi", "pode", "ja",
}


def contar_palavras(noticias):
    """Conta as palavras dos titulos, reduzidas a forma de dicionario (lema).
    Assim 'emprego', 'empregos' e ate 'cresce'/'cresceram' contam juntos."""
    texto = " ".join(n["titulo"].lower() for n in noticias)
    palavras = re.findall(r"[a-záàâãéêíóôõúç]+", texto)
    lemas = [simplemma.lemmatize(p, lang="pt") for p in palavras]
    lemas = [p for p in lemas if len(p) >= 3 and p not in STOPWORDS]
    return Counter(lemas)


st.title("Análise")

todas, fonte = obter_todas()
guarda_sem_dados(todas)
filtradas = filtros_sidebar(todas)

st.caption(f"Analisando {len(filtradas)} de {len(todas)} noticias.")

# -------------------------------------------------------------------
# NUVEM DE PALAVRAS + FREQUENCIA
# -------------------------------------------------------------------
st.header("O que essas noticias mais falam")

contagem = contar_palavras(filtradas)

if contagem:
    col_n, col_b = st.columns(2)

    with col_n:
        st.subheader("Nuvem de palavras")
        nuvem = WordCloud(
            width=800, height=400, background_color="white", colormap="viridis",
        ).generate_from_frequencies(contagem)
        st.image(nuvem.to_array(), use_container_width=True)

    with col_b:
        st.subheader("Palavras mais frequentes")
        st.bar_chart(dict(contagem.most_common(12)), horizontal=True)
        st.caption("A nuvem mostra destaque; o grafico mostra a escala real.")
else:
    st.info("Poucas palavras para montar a nuvem com esse filtro.")

st.divider()

# -------------------------------------------------------------------
# ESTATISTICAS BASICAS
# -------------------------------------------------------------------
st.header("Estatísticas")

col_e1, col_e2 = st.columns(2)
with col_e1:
    st.subheader("Noticias por editoria")
    st.bar_chart(dict(Counter(n["editoria"] for n in filtradas)))
with col_e2:
    st.subheader("Noticias por mes")
    por_mes = Counter(n["ano_mes"] for n in filtradas)
    st.bar_chart(dict(sorted(por_mes.items())))

st.divider()
st.caption(f"Fonte: {fonte}")