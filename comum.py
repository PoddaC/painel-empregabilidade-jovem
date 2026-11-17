"""
comum.py - o que mais de uma pagina usa.

"""

import streamlit as st

from src import cliente_api
from src.data_access import carregar_noticias, id_da_noticia

CAMPOS = ["titulo", "editoria", "ano_mes", "url"]


# -------------------------------------------------------------------
# CACHE: o acervo e o mesmo para todos e caro de buscar -> cache. Com
# prazo (ttl): se a API cair ou voltar, o painel percebe em ate 30 s.
#
# O painel PEDE os dados a API, como qualquer outro programa. Se ela nao
# responder (desligada, ou no Streamlit Cloud, onde ela nao existe), o
# plano B le o disco direto - e a barra lateral DIZ isso. Uma API fora do
# ar degrada a origem do dado; nao derruba a interface.
# -------------------------------------------------------------------
@st.cache_data(ttl=30, show_spinner=False)
def obter_noticias_coletadas():
    """Devolve (lista, fonte, via) - via e 'api' ou 'disco'."""
    try:
        return cliente_api.listar_noticias(), "API do projeto (GET /noticias)", "api"
    except (cliente_api.APIForaDoAr, cliente_api.FalhaDaAPI):
        noticias, fonte = carregar_noticias()
        lidas = [{**n, "id": id_da_noticia(n), "origem": "coletada",
                  "tem_texto": bool(n.get("arquivo_texto"))} for n in noticias]
        return lidas, fonte + " - lida do disco (a API nao respondeu)", "disco"


def obter_todas():
    """
    Devolve (lista, fonte) com o acervo e as enviadas pelo usuario nesta
    sessao, cada linha marcada com sua origem (coletada, via_api, enviada).

    A origem importa: dado sem procedencia ninguem audita - e e isso que o
    Data Summary Report cobra.
    """
    noticias, fonte, via = obter_noticias_coletadas()
    enviadas = [{**n, "origem": "enviada"} for n in st.session_state.enviadas]
    if via == "api":
        st.sidebar.caption("Dados: via API do projeto")
    else:
        st.sidebar.warning(
            "A API do projeto não respondeu: as notícias foram lidas direto do "
            "disco, e o Analisador fica indisponível. Para ligá-la: "
            "`uvicorn api.main:app`"
        )
    return noticias + enviadas, fonte


def guarda_sem_dados(todas):
    """Se nao ha dado nenhum, nao adianta desenhar o resto da pagina."""
    if not todas:
        st.warning(
            "Ainda nao ha noticias coletadas. Rode a coleta no terminal, "
            "a partir da raiz do projeto:\n\n"
            "```\npython -m src.coletar\n```"
        )
        st.stop()


def filtros_sidebar(todas):
    """
    Os filtros na BARRA LATERAL, porque sao compartilhados: a tabela, a nuvem
    e as estatisticas olham todas o mesmo recorte.

    O detalhe que faz o filtro ATRAVESSAR as paginas: o valor NAO mora numa
    chave de widget. O Streamlit limpa o estado dos widgets quando voce troca
    de pagina - entao um selectbox com key='f_editoria' volta ao padrao na
    pagina seguinte (medido: escolhi 'cultura', fui para a Analise, e voltou
    para '(todas)').

    Por isso o valor vive numa chave COMUM do session_state, que o Streamlit
    nao limpa, e o widget e semeado a partir dela com index=/value=.
    """
    st.sidebar.header("Filtros")

    editorias = sorted({n["editoria"] for n in todas})
    opcoes = ["(todas)"] + editorias

    # GUARDA: a editoria guardada pode nao existir mais na lista - por exemplo
    # se o usuario enviou um CSV e depois limpou as enviadas.
    if st.session_state.get("filtro_editoria") not in opcoes:
        st.session_state["filtro_editoria"] = "(todas)"

    escolhida = st.sidebar.selectbox(
        "Editoria",
        opcoes,
        index=opcoes.index(st.session_state["filtro_editoria"]),
    )
    st.session_state["filtro_editoria"] = escolhida

    busca = st.sidebar.text_input(
        "Buscar no titulo",
        value=st.session_state.get("filtro_busca", ""),
        placeholder="ex: desemprego, vagas...",
    )
    st.session_state["filtro_busca"] = busca

    filtradas = todas
    if escolhida != "(todas)":
        filtradas = [n for n in filtradas if n["editoria"] == escolhida]
    if busca.strip():
        termo = busca.lower().strip()
        filtradas = [n for n in filtradas if termo in n["titulo"].lower()]

    st.sidebar.caption(f"{len(filtradas)} de {len(todas)} noticias no recorte.")
    return filtradas