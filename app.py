"""
app.py - roteador do Painel de Empregabilidade Jovem.
 
    streamlit run app.py
 
Cada pagina vive em paginas/; o que e compartilhado vive em comum.py.
O arquivo principal continua sendo este, entao nada muda no deploy.
"""
 
import streamlit as st
 
st.set_page_config(page_title="Empregabilidade Jovem", layout="wide")
 
# ESTADO DE SESSAO: criado aqui no roteador, que roda a cada rerun ANTES da
# pagina escolhida. Assim qualquer pagina ja encontra o estado de pe.
if "enviadas" not in st.session_state:
    st.session_state.enviadas = []
if "uploader_key" not in st.session_state:
    st.session_state.uploader_key = 0
 
# Uma pergunta, uma pagina. O menu deixa de ser a listagem de uma pasta e
# vira codigo: titulo, icone e secoes sao decisao nossa - e cada pagina
# ganha um endereco proprio, que da para mandar por link.
pagina = st.navigation({
    "Painel": [
        st.Page("paginas/inicio.py", title="Início", icon="🏠", default=True),
        st.Page("paginas/noticias.py", title="Notícias", icon="📰"),
        st.Page("paginas/analise.py", title="Análise", icon="📊"),
    ],
    "Sobre o projeto": [
        st.Page("paginas/dados.py", title="Dados e método", icon="🗂️"),
    ],
})
 
pagina.run()  # roda a pagina escolhida - e SO ela
 