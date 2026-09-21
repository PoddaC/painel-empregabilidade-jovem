"""
app.py - Painel de Empregabilidade Jovem
TP2 - Projeto de Bloco: IA Aplicada | Etapa 2

Consome as noticias coletadas da Agencia Brasil (scraping da Etapa 2).
"""

import streamlit as st
import re
import io
from collections import Counter
import csv
from wordcloud import WordCloud
import simplemma
from src.data_access import carregar_noticias

st.set_page_config(page_title="Empregabilidade Jovem", layout="wide")

CAMPOS = ["titulo", "editoria", "ano_mes", "url"]

# Palavras vazias (stopwords) - DECISAO EDITORIAL: o que nao agrega a nuvem.
# Esta lista cresce olhando o resultado; por isso fica visivel aqui.
STOPWORDS = {
    "de", "a", "o", "e", "do", "da", "em", "um", "uma", "para", "com", "nao",
    "que", "os", "as", "no", "na", "por", "mais", "dos", "das", "ao", "pelo",
    "pela", "se", "como", "mas", "ou", "ser", "ter", "dizer", "seu", "sua", "ano", "anos","diz",
    "apos", "sobre", "entre", "ate", "e", "sao", "tem", "foi", "pode", "ja",
}


# -------------------------------------------------------------------
# CACHE: le o CSV do scraping UMA vez e reaproveita entre reruns .
# O dado e o mesmo para todos e caro de reler -> vai para o cache.
# -------------------------------------------------------------------
@st.cache_data
def obter_noticias_coletadas():
    return carregar_noticias()

def contar_palavras(noticias):
    """Conta as palavras dos titulos, reduzidas a forma de dicionario (lema).
    Assim 'emprego', 'empregos' e ate 'cresce'/'cresceram' contam juntos."""
    texto = " ".join(n["titulo"].lower() for n in noticias)
    palavras = re.findall(r"[a-záàâãéêíóôõúç]+", texto)
    lemas = [simplemma.lemmatize(p, lang="pt") for p in palavras]
    lemas = [p for p in lemas if len(p) >= 3 and p not in STOPWORDS]
    return Counter(lemas)

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
 
 
def para_csv(noticias):
    """Serializa a lista (com origem) para bytes CSV, para o download."""
    buf = io.StringIO()
    campos = CAMPOS + ["origem"]
    w = csv.DictWriter(buf, fieldnames=campos)
    w.writeheader()
    for n in noticias:
        w.writerow({c: n.get(c, "") for c in campos})
    return buf.getvalue().encode("utf-8")
 
 
def chave(n):
    """Chave de deduplicacao: usa a url, e cai no titulo se a url faltar."""
    return n["url"] or n["titulo"]
 
 
# ESTADO DE SESSAO: guarda o que ESTE usuario enviou, entre reruns.
if "enviadas" not in st.session_state:
    st.session_state.enviadas = []

if "uploader_key" not in st.session_state:
    st.session_state.uploader_key = 0

# -------------------------------------------------------------------
# Cabecalho
# -------------------------------------------------------------------
st.title("Painel de Empregabilidade Jovem")
st.caption("TP2 - Projeto de Bloco: IA Aplicada | ODS 8 - Trabalho Decente e Crescimento Economico")

# -------------------------------------------------------------------
# Carrega os dados coletados
# -------------------------------------------------------------------
noticias, fonte = obter_noticias_coletadas()

# GUARDA: se a coleta ainda nao rodou, nao adianta desenhar o resto (Aula 6)
if not noticias:
    st.warning(
        "Ainda nao ha noticias coletadas. Rode a coleta no terminal, "
        "a partir da raiz do projeto:\n\n"
        "```\npython -m src.coletar\n```"
    )
    st.stop()

with st.expander("Adicionar noticias por CSV (upload)"):
        enviado = st.file_uploader(
        "Escolha um CSV", type="csv",
        key=f"uploader_{st.session_state.uploader_key}",
    )
if enviado is not None:
        novas, erro = ler_csv_upload(enviado)
        if erro:
            st.error(erro)
        else:
            ja_tenho = {chave(n) for n in st.session_state.enviadas}
            adicionar = [n for n in novas if chave(n) not in ja_tenho]
            st.session_state.enviadas.extend(adicionar)
            st.success(f"{len(novas)} lidas | {len(adicionar)} novas adicionadas.")
if st.session_state.enviadas and st.button("Limpar enviadas"):
        st.session_state.enviadas = []
        st.session_state.uploader_key += 1
        st.rerun()

coletadas = [{**n, "origem": "coletada"} for n in noticias]
enviadas = [{**n, "origem": "enviada"} for n in st.session_state.enviadas]
todas = coletadas + enviadas
# -------------------------------------------------------------------
# FILTROS - cada widget devolve o valor atual; ao mexer,
# o script inteiro roda de novo (rerun) e redesenha a tela filtrada.
# -------------------------------------------------------------------
st.header("Noticias de emprego")
 
# monta a lista de editorias disponiveis a partir dos proprios dados
editorias = sorted({n["editoria"] for n in todas})
opcoes = ["(todas)"] + editorias
 
col_f1, col_f2 = st.columns([1, 2])
with col_f1:
    editoria_escolhida = st.selectbox("Editoria", opcoes)
with col_f2:
    busca = st.text_input("Buscar no titulo", placeholder="ex: desemprego, IBGE, vagas...")
 
# aplica os filtros (Python puro sobre a lista de dicionarios)
filtradas = todas
if editoria_escolhida != "(todas)":
    filtradas = [n for n in filtradas if n["editoria"] == editoria_escolhida]
if busca.strip():
    termo = busca.lower().strip()
    filtradas = [n for n in filtradas if termo in n["titulo"].lower()]
 
# -------------------------------------------------------------------
# Resultado
# -------------------------------------------------------------------
st.caption(f"Mostrando {len(filtradas)} de {len(todas)} noticias.")

if not filtradas:
    st.info("Nenhuma noticia bate com esse filtro. Tente outro termo ou editoria.")
else:
    st.dataframe(filtradas, use_container_width=True)
    st.download_button(
        "Baixar estas noticias (CSV)",
        data=para_csv(filtradas),
        file_name="noticias_filtradas.csv",
        mime="text/csv",
    )

# -------------------------------------------------------------------
# NUVEM DE PALAVRAS + ESTATISTICAS (a partir das noticias FILTRADAS)
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
        top = dict(contagem.most_common(12))
        st.bar_chart(top, horizontal=True)
        st.caption("A nuvem mostra destaque; o grafico mostra a escala real.")
else:
    st.info("Poucas palavras para montar a nuvem com esse filtro.")
 
# --- estatisticas basicas ---
st.header("Estatisticas")
 
col_e1, col_e2 = st.columns(2)
with col_e1:
    st.subheader("Noticias por editoria")
    por_editoria = Counter(n["editoria"] for n in filtradas)
    st.bar_chart(dict(por_editoria))
with col_e2:
    st.subheader("Noticias por mes")
    por_mes = Counter(n["ano_mes"] for n in filtradas)
    st.bar_chart(dict(sorted(por_mes.items())))

# -------------------------------------------------------------------
# Amostra do IBGE (TP1) - nao faz parte do scraping, mas ajuda a dar contexto e para continuidade do projeto. O TP1 coletou via API do IBGE, mas nao foi integrado ao scraping.
# -------------------------------------------------------------------
with st.expander("Ver dados de ocupacao por setor (amostra IBGE - TP1)"):
    amostra_setores = [
        {"setor": "Comercio, reparacao de veiculos", "ocupados_milhoes": 19.5, "variacao_ano_pct": 0.3},
        {"setor": "Adm. publica, educacao, saude", "ocupados_milhoes": 19.0, "variacao_ano_pct": 5.0},
        {"setor": "Informacao, comunicacao, financas", "ocupados_milhoes": 13.4, "variacao_ano_pct": 6.8},
        {"setor": "Industria geral", "ocupados_milhoes": 13.3, "variacao_ano_pct": 2.3},
        {"setor": "Servicos domesticos", "ocupados_milhoes": 5.7, "variacao_ano_pct": -4.1},
    ]
    st.dataframe(amostra_setores, use_container_width=True)
    st.caption("Fonte: IBGE / PNAD Continua. Amostra do TP1; coleta via API prevista.")

st.divider()

st.caption(f"Fonte: {fonte}")