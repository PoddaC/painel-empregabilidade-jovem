"""
dados.py - de onde vem o dado, e por onde o usuario acrescenta o dele.

"""

import csv
import io

import streamlit as st

from comum import CAMPOS, obter_todas, guarda_sem_dados


def ler_csv_upload(arquivo):
    """Le o CSV enviado. Retorna (lista, erro). Valida na BORDA, nunca levanta."""
    try:
        bruto = arquivo.getvalue().decode("utf-8")
    except UnicodeDecodeError:
        return [], "O arquivo nao esta em UTF-8. Salve o CSV como UTF-8 e tente de novo."

    linhas = list(csv.DictReader(io.StringIO(bruto)))
    if not linhas:
        return [], "O CSV esta vazio."
    if "titulo" not in linhas[0]:
        return [], "O CSV precisa ter ao menos a coluna 'titulo'."

    noticias = []
    for l in linhas:
        n = {c: (l.get(c) or "").strip() for c in CAMPOS}
        if not n["editoria"]:
            n["editoria"] = "n/d"
        if not n["ano_mes"]:
            n["ano_mes"] = "n/d"
        if n["titulo"]:
            noticias.append(n)

    if not noticias:
        return [], "Nenhuma linha com titulo valido no CSV."
    return noticias, None


def chave(n):
    """Chave de deduplicacao: usa a url, e cai no titulo se a url faltar."""
    return n["url"] or n["titulo"]


st.title("Dados e método")

todas, fonte = obter_todas()
guarda_sem_dados(todas)

# -------------------------------------------------------------------
# UPLOAD - o dado entra por onde o usuario quiser
# -------------------------------------------------------------------
st.header("Acrescentar noticias por CSV")
st.caption(
    "O CSV precisa ter ao menos a coluna 'titulo'. As colunas editoria, "
    "ano_mes e url sao opcionais. O que voce enviar vale so para esta sessao."
)

enviado = st.file_uploader(
    "Escolha um CSV",
    type="csv",
    key=f"uploader_{st.session_state.uploader_key}",
)

if enviado is not None:
    novas, erro = ler_csv_upload(enviado)
    if erro:
        st.error(erro)
    else:
        # O uploader devolve o MESMO arquivo a cada rerun. Sem deduplicar,
        # 3 linhas virariam 6 no proximo clique.
        ja_tenho = {chave(n) for n in st.session_state.enviadas}
        adicionar = [n for n in novas if chave(n) not in ja_tenho]
        st.session_state.enviadas.extend(adicionar)
        st.success(f"{len(novas)} lidas | {len(adicionar)} novas adicionadas.")

if st.session_state.enviadas:
    st.info(f"{len(st.session_state.enviadas)} noticias enviadas nesta sessao.")
    if st.button("Limpar enviadas"):
        st.session_state.enviadas = []
        st.session_state.uploader_key += 1  # troca a key = zera o uploader
        st.rerun()

st.divider()

# -------------------------------------------------------------------
# AMOSTRA DO IBGE (TP1) - contexto do projeto, fora do scraping
# -------------------------------------------------------------------
st.header("Ocupação por setor (amostra IBGE)")
st.caption(
    "Amostra do TP1, coletada via API do IBGE / PNAD Continua. Nao faz parte "
    "do scraping; fica aqui pela continuidade do projeto."
)

amostra_setores = [
    {"setor": "Comercio, reparacao de veiculos", "ocupados_milhoes": 19.5, "variacao_ano_pct": 0.3},
    {"setor": "Adm. publica, educacao, saude", "ocupados_milhoes": 19.0, "variacao_ano_pct": 5.0},
    {"setor": "Informacao, comunicacao, financas", "ocupados_milhoes": 13.4, "variacao_ano_pct": 6.8},
    {"setor": "Industria geral", "ocupados_milhoes": 13.3, "variacao_ano_pct": 2.3},
    {"setor": "Servicos domesticos", "ocupados_milhoes": 5.7, "variacao_ano_pct": -4.1},
]
st.dataframe(amostra_setores, use_container_width=True)

st.divider()
st.caption(f"Fonte das noticias: {fonte}")