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

st.caption(f"Mostrando {len(filtradas)} de {len(todas)} notícias. Use os filtros na barra lateral.")

if not filtradas:
    st.info("Nenhuma notícia bate com esse filtro. Tente outro termo ou editoria.")
else:
    st.dataframe(
        filtradas,
        width="stretch",
        column_order=["titulo", "editoria", "ano_mes", "origem", "resumo", "url"],
        column_config={
            "titulo": st.column_config.TextColumn("Título", width="large"),
            "editoria": "Editoria",
            "ano_mes": "Mês",
            "origem": "Origem",
            "resumo": "Linha fina",
            "url": st.column_config.LinkColumn("Matéria", display_text="abrir"),
        },
        hide_index=True,
    )

    # Baixa o RECORTE, nao a base inteira: o usuario leva o que esta vendo.
    st.download_button(
        "Baixar estas notícias (CSV)",
        data=para_csv(filtradas),
        file_name="noticias_filtradas.csv",
        mime="text/csv",
    )

st.divider()
st.caption(f"Fonte: {fonte}")