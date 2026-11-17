"""
analisador.py - o modelo de linguagem local, pela tela.

A pagina nao carrega modelo nenhum: ela PEDE a analise a API
(POST /processar_texto), e mostra o que a API disse - inclusive quando
diz que nao deu. Por isso o painel publicado (Streamlit Cloud) nao precisa
de torch: o peso mora na API, na sua maquina.
"""

import streamlit as st

from comum import obter_todas
from src import cliente_api
from src.tarefas import TAREFAS, montar_texto

st.title("Analisador")
st.caption(
    "Um modelo de linguagem rodando na sua máquina lê a notícia e sugere a "
    "tendência do emprego que ela aponta, ou o setor da economia de que ela fala."
)

todas, _ = obter_todas()


def mostrar_falha(f):
    """O status decide a cor: aviso (nada a corrigir) ou erro (corrija / avise)."""
    texto = "\n".join(f"- {m}" for m in f.mensagens) if len(f.mensagens) > 1 else f.mensagens[0]
    if f.e_aviso:
        st.warning(texto)
    else:
        st.error(texto)


# -------------------------------------------------------------------
# A API e o modelo estao de pe? Pergunta antes, para nao deixar a
# pessoa escrever um texto e so depois descobrir.
# -------------------------------------------------------------------
try:
    estado = cliente_api.saude()
except cliente_api.APIForaDoAr as e:
    st.warning(
        f"{e} O Analisador precisa da API do projeto, que roda na sua "
        "máquina. Em outro terminal, na raiz do projeto:\n\n"
        "```\nuvicorn api.main:app\n```"
    )
    st.stop()

if not estado["modelo_carregado"]:
    st.warning(
        f"A API está no ar, mas o modelo não carregou: {estado['motivo']}\n\n"
        "As outras páginas funcionam normalmente."
    )
    st.page_link("paginas/noticias.py", label="Ver as notícias", icon="📰")
    st.stop()

st.caption(f"Motor carregado: `{estado['motor']}`")

# -------------------------------------------------------------------
# O PEDIDO
# -------------------------------------------------------------------
tipo = st.radio(
    "O que analisar",
    options=list(TAREFAS),
    format_func=lambda t: TAREFAS[t]["nome"],
    horizontal=True,
)
if tipo == "setor":
    st.caption(
        "⚠️ Experimental: na bancada de testes, a análise de setor não superou "
        "o chute \"sempre mercado em geral\" (25 contra 31 de 42 notícias). "
        "Use como pista, não como resposta."
    )
with st.expander("O que cada categoria quer dizer"):
    for dados in TAREFAS[tipo]["categorias"].values():
        st.markdown(f"- **{dados['rotulo']}**: {dados['definicao']}")

fonte = st.radio("Texto", ["Uma notícia do acervo", "Colar um texto"], horizontal=True)

texto = ""
if fonte == "Uma notícia do acervo":
    com_texto = [n for n in todas if n.get("tem_texto")]
    if not com_texto:
        st.info("Nenhuma notícia do acervo tem o texto integral coletado. "
                "Rode `python -m src.coletar_textos`, ou cole um texto.")
    else:
        escolhida = st.selectbox(
            f"Notícia ({len(com_texto)} com texto integral)",
            com_texto,
            format_func=lambda n: f"{n['ano_mes']} · {n['titulo']}",
        )
        try:
            detalhe = cliente_api.obter_noticia(escolhida["id"])
            texto = montar_texto(detalhe["titulo"], detalhe["resumo"], detalhe["texto"])
        except cliente_api.FalhaDaAPI as f:
            mostrar_falha(f)
        except cliente_api.APIForaDoAr as e:
            st.warning(str(e))
        if texto:
            with st.expander("Ver o texto que vai para o modelo"):
                st.text(texto)
else:
    texto = st.text_area(
        "Cole o texto",
        height=180,
        placeholder="Ex: Brasil gerou mais de 235 mil novos postos de trabalho em agosto...",
    )

# -------------------------------------------------------------------
# A ANALISE - o resultado fica no session_state para sobreviver aos reruns
# -------------------------------------------------------------------
if st.button("Analisar", type="primary", disabled=not texto.strip()):
    st.session_state.pop("ultima_analise", None)
    with st.spinner("O modelo está lendo..."):
        try:
            st.session_state["ultima_analise"] = cliente_api.analisar(texto, tipo)
        except cliente_api.FalhaDaAPI as f:
            mostrar_falha(f)
        except cliente_api.APIForaDoAr as e:
            st.warning(f"{e} A análise não foi feita.")

r = st.session_state.get("ultima_analise")
if r:
    st.divider()
    nome_tarefa = TAREFAS[r["tipo_analise"]]["nome"]
    if r["categoria"] is None:
        st.info(f"{nome_tarefa}: o motor não encontrou pistas e preferiu não responder.")
    else:
        col1, col2 = st.columns([1, 2])
        col1.metric(nome_tarefa, r["rotulo"])
        col1.metric("Confiança do modelo", f"{r['confianca']:.0%}")
        col2.bar_chart(
            {a["rotulo"]: a["probabilidade"] for a in r["alternativas"]},
            horizontal=True,
        )

    st.caption(
        "A confiança é a nota que o modelo deu à própria resposta, **não** a "
        "chance de ela estar certa: na bancada de testes, houve erros com "
        "confiança alta. Confira com o trecho abaixo, que é o que o modelo leu."
    )
    with st.expander(f"Trecho analisado ({len(r['trecho_analisado'])} de {r['caracteres_recebidos']} caracteres)"):
        st.write(r["trecho_analisado"])
    if r["pistas"]:
        st.caption("Pistas: " + ", ".join(r["pistas"]))
    st.caption(f"Analisado por `{r['motor']}` em {r['segundos']:.2f} s, nesta máquina, sem internet.")
