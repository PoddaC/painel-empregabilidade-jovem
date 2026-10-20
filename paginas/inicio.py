"""
inicio.py - a porta de entrada: o que o painel responde e para quem.

Esta pagina nao usa filtro: ela apresenta o projeto e aponta para as outras.
"""

import streamlit as st

from comum import obter_todas, guarda_sem_dados

st.title("Painel de Empregabilidade Jovem")
st.caption(
    "Projeto de Bloco: IA Aplicada | ODS 8 - Trabalho Decente e "
    "Crescimento Economico, meta 8.6"
)

todas, fonte = obter_todas()
guarda_sem_dados(todas)

st.markdown(
    """
**A pergunta.** Quais setores estao em expansao e devem ser priorizados na
qualificacao de jovens em busca do primeiro emprego?

**O problema.** Organizacoes de empregabilidade juvenil precisam decidir para
quais setores capacitar jovens, e costumam fazer isso sem saber onde o mercado
realmente cria vagas. Este painel apoia essa decisao com dado publico.

**Para quem.** Coordenacao e analistas de ONGs de empregabilidade; a direcao
que aprova a abertura de um curso; e, ao fim da linha, jovens de 14 a 24 anos.
"""
)

st.divider()

# --- numeros do acervo, para a pessoa saber o tamanho do que esta vendo ---
col1, col2, col3 = st.columns(3)
col1.metric("Noticias no acervo", len(todas))
col2.metric("Editorias", len({n["editoria"] for n in todas}))
col3.metric("Meses cobertos", len({n["ano_mes"] for n in todas if n["ano_mes"] != "n/d"}))

st.divider()

st.subheader("Por onde comecar")

# page_link: o mesmo link do menu, dentro da pagina. A Inicio funciona
# como um indice das outras.
st.page_link("paginas/noticias.py", label="Notícias — a tabela, filtrada e baixavel", icon="📰")
st.page_link("paginas/analise.py", label="Análise — o que essas noticias mais falam", icon="📊")
st.page_link("paginas/dados.py", label="Dados e método — fontes, upload e limites", icon="🗂️")

st.divider()
st.caption(f"Fonte: {fonte}")