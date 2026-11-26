"""
dados.py - de onde vem o dado, e por onde o usuario acrescenta o dele.

"""

import csv
import io

import streamlit as st

from comum import CAMPOS, obter_noticias_coletadas, obter_todas, guarda_sem_dados
from src import cliente_api
from src.data_access import carregar_ibge


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
# ENVIO PELA API - diferente do upload: a noticia fica GRAVADA no acervo
# (data/processed/noticias_via_api.csv). O painel pede; quem valida e
# grava e a API. O painel so diz "gravada" quando a API disser.
# -------------------------------------------------------------------
st.header("Enviar uma notícia ao acervo")
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
        st.warning(f"{e} Nada foi enviado. Ligue a API com `uvicorn api.main:app`.")

st.divider()

# -------------------------------------------------------------------
# IBGE - desocupacao dos JOVENS, coletada pela API (python -m src.coletar_ibge)
# Antes (TP2 a TP4) aqui havia uma lista digitada no codigo, com legenda
# dizendo "via API". Agora: ou o dado coletado, ou um aviso - nunca numero
# de exemplo passando por dado real.
# -------------------------------------------------------------------
st.header("Desocupação dos jovens (IBGE)")
ibge, fonte_ibge = carregar_ibge()

if not ibge:
    st.warning(
        "Os dados do IBGE ainda não foram coletados nesta máquina. Rode, a "
        "partir da raiz do projeto:\n\n```\npython -m src.coletar_ibge\n```"
    )
else:
    brasil = [l for l in ibge if l["nivel"] == "Brasil"]
    ultimo = max(l["periodo_codigo"] for l in brasil)
    agora = {l["grupo_idade"]: l for l in brasil if l["periodo_codigo"] == ultimo}
    periodo = agora["total"]["periodo"]

    st.caption(
        f"Taxa de desocupação por grupo de idade, Brasil, {periodo}. "
        "Desocupado é quem procurou trabalho e não achou; quem só estuda "
        "não entra na conta."
    )
    c1, c2, c3 = st.columns(3)
    for col, grupo, nome in ((c1, "14 a 17 anos", "14 a 17 anos"),
                             (c2, "18 a 24 anos", "18 a 24 anos"),
                             (c3, "total", "Todas as idades")):
        if grupo in agora:
            col.metric(nome, f"{agora[grupo]['taxa_desocupacao_pct']:.1f}%".replace(".", ","))

    # Serie no tempo: uma linha por grupo, um eixo so (%).
    serie = {}
    for l in brasil:
        nome = "Todas as idades" if l["grupo_idade"] == "total" else l["grupo_idade"]
        serie.setdefault(l["periodo"], {})[nome] = l["taxa_desocupacao_pct"]
    st.subheader("Brasil, trimestre a trimestre")
    st.line_chart(
        [{"periodo": p, **v} for p, v in sorted(serie.items())],
        x="periodo", y=["14 a 17 anos", "18 a 24 anos", "Todas as idades"],
        y_label="taxa de desocupação (%)", x_label="trimestre",
    )

    ufs = sorted(
        (l for l in ibge if l["nivel"] == "UF" and l["periodo_codigo"] == ultimo
         and l["grupo_idade"] == "18 a 24 anos"),
        key=lambda l: l["taxa_desocupacao_pct"], reverse=True,
    )
    if ufs:
        st.subheader(f"18 a 24 anos, por UF ({periodo})")
        st.bar_chart(
            [{"UF": l["localidade"], "taxa (%)": l["taxa_desocupacao_pct"]} for l in ufs],
            x="UF", y="taxa (%)", horizontal=True, sort="-taxa (%)",
        )

    with st.expander("Tabela completa (o que o gráfico mostra)"):
        st.dataframe(ibge, width="stretch", hide_index=True)
    st.caption(f"Fonte: {fonte_ibge}. Coletado em {ibge[0]['coletado_em']}.")

st.divider()
st.caption(f"Fonte das noticias: {fonte}")