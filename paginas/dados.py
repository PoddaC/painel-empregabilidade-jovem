"""
dados.py - de onde vem o dado, e por onde o usuario acrescenta o dele.

Primeiro as fontes (o que o painel usa), depois as ferramentas de envio.
O ranking das UFs mora na Inicio; aqui fica a serie completa e a tabela.

"""

import csv
import io

import streamlit as st

from comum import CAMPOS, obter_noticias_coletadas, obter_todas, guarda_sem_dados
from src import cliente_api
from graficos import serie_jovens
from src.data_access import carregar_ibge
from src.indicadores import resumo_ibge


def ler_csv_upload(arquivo):
    """Le o CSV enviado. Retorna (lista, erro). Valida na BORDA, nunca levanta."""
    try:
        bruto = arquivo.getvalue().decode("utf-8")
    except UnicodeDecodeError:
        return [], "O arquivo não está em UTF-8. Salve o CSV como UTF-8 e tente de novo."

    linhas = list(csv.DictReader(io.StringIO(bruto)))
    if not linhas:
        return [], "O CSV está vazio."
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
        return [], "Nenhuma linha com título válido no CSV."
    return noticias, None


def chave(n):
    """Chave de deduplicacao: usa a url, e cai no titulo se a url faltar."""
    return n["url"] or n["titulo"]


st.title("Dados e método")
st.caption("De onde vem cada número do painel, como foi tratado, e como acrescentar os seus dados.")

todas, fonte = obter_todas()
guarda_sem_dados(todas)

# -------------------------------------------------------------------
# FONTES
# IBGE coletado pela API (python -m src.coletar_ibge). Antes (TP2 a TP4)
# aqui havia uma lista digitada no codigo, com legenda dizendo "via API".
# Agora: ou o dado coletado, ou um aviso - nunca numero de exemplo.
# -------------------------------------------------------------------
st.header("As fontes")

st.subheader("Desocupação por idade · IBGE")
ibge, fonte_ibge = carregar_ibge()
r = resumo_ibge(ibge)
if r is None:
    st.warning("Os dados do IBGE ainda não foram coletados nesta máquina. Rode, a partir da raiz "
               "do projeto:\n\n```\npython -m src.coletar_ibge\n```")
else:
    st.markdown(
        "PNAD Contínua trimestral, tabela 4094, pela **API de agregados do IBGE** (aberta, sem chave). "
        "**Desocupado** é quem procurou trabalho e não achou; quem só estuda não entra na conta. "
        "Por isso a taxa não mede os jovens \"nem-nem\" que desistiram de procurar."
    )
    serie_jovens(r, grupos=("14 a 17 anos", "18 a 24 anos", "total"))
    with st.expander(f"Tabela completa ({len(ibge)} linhas: trimestre, lugar e grupo de idade)"):
        st.dataframe(ibge, width="stretch", hide_index=True)
    st.caption(f"Fonte: {fonte_ibge}. Coletado em {r['coletado_em'][:10]}.")

st.subheader("Notícias de emprego · Agência Brasil")
st.markdown(
    f"{len([n for n in todas if n.get('origem') == 'coletada'])} notícias da tag *emprego*, por **raspagem** do "
    "HTML (licença Creative Commons), com o texto integral de cada matéria. Tendência e setor foram "
    "rotulados à mão em todas, como gabarito para escolher o modelo do Analisador."
)
st.caption(f"Fonte: {fonte}")

st.info("O detalhamento completo (dicionário de dados, limpeza, linhagem até a IA e a conversa como "
        "dado pessoal) está em `docs/data_summary_report.md`, no repositório.", icon="📄")

st.divider()

# -------------------------------------------------------------------
# ACRESCENTE SEUS DADOS
# -------------------------------------------------------------------
st.header("Acrescente seus dados")

# Upload: vale so para esta sessao.
st.subheader("Acrescentar notícias por CSV")
st.caption(
    "O CSV precisa ter ao menos a coluna 'titulo'. As colunas editoria, "
    "ano_mes e url são opcionais. O que você enviar vale só para esta sessão."
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
        st.success(f"{len(novas)} lidas · {len(adicionar)} novas adicionadas.")

if st.session_state.enviadas:
    st.info(f"{len(st.session_state.enviadas)} notícias enviadas nesta sessão.")
    if st.button("Limpar enviadas"):
        st.session_state.enviadas = []
        st.session_state.uploader_key += 1  # troca a key = zera o uploader
        st.rerun()


# -------------------------------------------------------------------
# ENVIO PELA API - diferente do upload: a noticia fica GRAVADA no acervo
# (data/processed/noticias_via_api.csv). O painel pede; quem valida e
# grava e a API. O painel so diz "gravada" quando a API disser.
# -------------------------------------------------------------------
st.subheader("Enviar uma notícia ao acervo (pela API)")
st.caption(
    "Diferente do upload acima, que vale só para esta sessão: a notícia "
    "enviada aqui é validada e gravada pela API, e passa a aparecer para "
    "todos, com origem 'via_api'."
)

with st.form("enviar_noticia", clear_on_submit=False):
    titulo = st.text_input("Título (mínimo 10 caracteres)")
    c1, c2 = st.columns(2)
    editoria = c1.text_input("Editoria", placeholder="economia")
    ano_mes = c2.text_input("Ano-mês", placeholder="2026-11")
    url = st.text_input("Endereço da matéria", placeholder="https://...")
    enviar = st.form_submit_button("Enviar pela API")

if enviar:
    try:
        r = cliente_api.enviar_noticia(titulo, editoria, ano_mes, url)
        st.success(f"Gravada no acervo: {r['noticia']['titulo']} (id {r['noticia']['id']}).")
        obter_noticias_coletadas.clear()  # o cache volta a pedir a API: a nova aparece
    except cliente_api.FalhaDaAPI as f:
        mensagem = "\n".join(f"- {m}" for m in f.mensagens)
        if f.e_aviso:
            st.warning(mensagem)   # 409: ja esta la - nada a corrigir, nada a repetir
        else:
            st.error(mensagem)     # 422: corrija o que a API apontou
    except cliente_api.APIForaDoAr as e:
        st.warning(f"{e} Nada foi enviado: o envio grava pela API do projeto, que roda na máquina "
                   "(`uvicorn api.main:app`). No link publicado, ele fica indisponível.")
