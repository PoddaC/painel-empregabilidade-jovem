"""
noticias.py - a tabela de noticias, no recorte escolhido na barra lateral.
"""

import csv
import io

import streamlit as st

from comum import CAMPOS, obter_todas, guarda_sem_dados, filtros_sidebar


def para_csv(noticias):
    """Serializa a lista (com origem) para bytes CSV, para o download."""
    buf = io.StringIO()
    campos = CAMPOS + ["origem"]
    w = csv.DictWriter(buf, fieldnames=campos, extrasaction="ignore")
    w.writeheader()
    for n in noticias:
        w.writerow({c: n.get(c, "") for c in campos})
    return buf.getvalue().encode("utf-8")


st.title("Notícias de emprego")

todas, fonte = obter_todas()
guarda_sem_dados(todas)
filtradas = filtros_sidebar(todas)

st.caption(f"Mostrando {len(filtradas)} de {len(todas)} noticias.")

if not filtradas:
    st.info("Nenhuma noticia bate com esse filtro. Tente outro termo ou editoria.")
else:
    st.dataframe(filtradas, use_container_width=True)

    # Baixa o RECORTE, nao a base inteira: o usuario leva o que esta vendo.
    st.download_button(
        "Baixar estas noticias (CSV)",
        data=para_csv(filtradas),
        file_name="noticias_filtradas.csv",
        mime="text/csv",
    )

st.divider()
st.caption(f"Fonte: {fonte}")