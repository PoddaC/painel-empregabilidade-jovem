"""
conversa.py - pergunte ao assistente sobre os dados do painel.

Dois modos, com a MESMA regra (src/conversa.py):
- com a API no ar: o painel pede a ela (POST /conversa), que guarda a
  conversa em arquivo, por id. Aqui fica so o id e o que mostrar.
- sem a API (o Streamlit Cloud so roda o painel): o painel chama o modelo
  online direto, com as chaves dos secrets, e a conversa mora so na sessao
  deste navegador - some ao fechar a aba ou ao apagar.
"""

import os

import streamlit as st

from src import cliente_api, llm_api
from src import conversa as nucleo
from src import memoria as mem


def chaves_dos_secrets():
    """No Streamlit Cloud as chaves vem dos secrets; copia para o ambiente, onde src/llm_api le."""
    try:
        for k in ("GROQ_API_KEY", "GEMINI_API_KEY", "PAINEL_LLM_ORDEM", "PAINEL_GROQ_MODELO", "PAINEL_GEMINI_MODELO"):
            if k in st.secrets:
                os.environ.setdefault(k, str(st.secrets[k]))
    except Exception:  # sem secrets.toml (rodando local): o .env ja foi lido por llm_api
        pass


def conversa_direta_de(msgs):
    """Recomeca, no modo direto, uma conversa que vinha pela API (que caiu no meio)."""
    c = nucleo.nova(st.session_state.conversa_memoria)
    for m in msgs:
        c["mensagens"].append({"papel": m["papel"], "texto": m["texto"], "quando": c["criada_em"]})
        if m["papel"] == "user":
            c["notas"] = mem.anotar(c["notas"], m["texto"])
    return c


def perguntar_direto(pergunta, memoria):
    chaves_dos_secrets()
    if st.session_state.get("conversa_local") is None:
        st.session_state.conversa_local = conversa_direta_de(st.session_state.conversa_msgs[:-1])
    c = st.session_state.conversa_local
    resultado = nucleo.responder(c, pergunta, memoria)  # pode levantar LLMIndisponivel
    return nucleo.registrar(c, pergunta, memoria, resultado)

DESCRICAO = {
    "notas": "Últimas 2 trocas + os lugares e grupos de idade já citados, anotados pelo Python. "
             "Custo quase fixo e lembra o começo da conversa. É a padrão.",
    "inteira": "Reenvia a conversa toda. Lembra de tudo, mas fica mais cara a cada pergunta.",
    "janela": "Reenvia só as últimas 3 trocas. Custo fixo, mas esquece o começo.",
    "resumo": "Últimas 3 trocas + um resumo do resto feito pelo modelo, que custa uma chamada a mais.",
}
EXEMPLOS = [
    "Como está a desocupação dos jovens de 18 a 24 anos na Bahia?",
    "Quais estados estão pior para os jovens?",
    "O que as notícias coletadas dizem sobre o mercado de trabalho?",
]

st.session_state.setdefault("conversa_id", None)
st.session_state.setdefault("conversa_msgs", [])     # o que a tela mostra
st.session_state.setdefault("conversa_memoria", "notas")
st.session_state.setdefault("conversa_modo", None)    # "api" ou "direto", decidido na 1a pergunta
st.session_state.setdefault("conversa_local", None)   # a conversa, no modo direto

st.title("Conversa")
st.caption(
    "Pergunte sobre a desocupação dos jovens (IBGE) e sobre as notícias coletadas. "
    "O painel calcula os números; o assistente só redige a resposta a partir deles, "
    "e o painel confere se algum número veio de fora."
)

# --- controles: a memoria e o recomeco ---------------------------------
c1, c2 = st.columns([3, 1])
with c1:
    memoria = st.selectbox(
        "Memória da conversa", list(DESCRICAO), key="conversa_memoria",
        format_func=lambda m: m.capitalize(),
        help="O modelo não lembra nada sozinho: a cada pergunta o painel reenvia parte da conversa. "
             "A memória decide qual parte.",
    )
    st.caption(DESCRICAO[memoria])
with c2:
    st.write("")
    if st.button("Apagar conversa", disabled=not st.session_state.conversa_msgs,
                 help="Apaga a conversa (na API, o arquivo some de vez) e começa outra."):
        try:
            if st.session_state.conversa_id:
                cliente_api.apagar_conversa(st.session_state.conversa_id)
        except (cliente_api.APIForaDoAr, cliente_api.FalhaDaAPI) as e:
            st.warning(f"Não deu para apagar: {e}")
        else:
            st.session_state.conversa_id = None
            st.session_state.conversa_msgs = []
            st.session_state.conversa_local = None
            st.session_state.conversa_modo = None
            st.session_state.pop("conversa_leitura", None)
            st.rerun()

st.info(
    "As perguntas são enviadas a um serviço externo de IA (Groq; o Google Gemini é a reserva). "
    "Não escreva dados pessoais. "
    + ("A conversa fica só nesta aba do navegador e some ao fechá-la."
       if st.session_state.conversa_modo == "direto"
       else "A conversa fica guardada na API até você apagá-la."),
    icon="🔒",
)

# --- a conversa ----------------------------------------------------------
for m in st.session_state.conversa_msgs:
    with st.chat_message(m["papel"]):
        st.markdown(m["texto"])
        if m.get("aviso"):
            st.warning(m["aviso"], icon="⚠️")
        if m.get("rodape"):
            st.caption(m["rodape"])

if not st.session_state.conversa_msgs:
    st.write("Para começar, escreva abaixo ou use um exemplo:")
    for ex in EXEMPLOS:
        if st.button(ex, key=f"ex_{ex}"):
            st.session_state.pergunta_pronta = ex
            st.rerun()

pergunta = st.chat_input("Pergunte sobre os dados do painel") or st.session_state.pop("pergunta_pronta", None)

if pergunta:
    st.session_state.conversa_msgs.append({"papel": "user", "texto": pergunta})
    with st.chat_message("user"):
        st.markdown(pergunta)
    with st.chat_message("assistant"):
        with st.spinner("Calculando os fatos e consultando o assistente..."):
            d = None
            if st.session_state.conversa_modo != "direto":
                try:
                    d = cliente_api.conversar(pergunta, st.session_state.conversa_id, memoria)
                    st.session_state.conversa_modo = "api"
                except cliente_api.APIForaDoAr:
                    st.session_state.conversa_modo = "direto"  # sem API (ex.: Streamlit Cloud)
                except cliente_api.FalhaDaAPI as f:
                    st.session_state.conversa_msgs.pop()
                    if f.status == 404:  # a conversa foi apagada por fora: comeca outra
                        st.session_state.conversa_id = None
                    (st.warning if f.e_aviso else st.error)("\n".join(f.mensagens))
                    st.stop()
            if d is None:
                try:
                    d = perguntar_direto(pergunta, memoria)
                except llm_api.LLMIndisponivel as e:
                    st.session_state.conversa_msgs.pop()
                    st.warning("O assistente está indisponível agora ("
                               + "; ".join(f"{p}: {m}" for p, m in e.motivos.items())
                               + "). O resto do painel funciona normalmente - tente de novo em instantes.")
                    st.stop()

        st.session_state.conversa_id = d["conversa_id"]
        aviso = None
        if d["numeros_sem_fonte"]:
            aviso = ("Estes números da resposta não estão nos dados do painel: "
                     + ", ".join(d["numeros_sem_fonte"]) + ". Confira antes de usar.")
        l = d["leitura"]
        modo = " · direto, sem API" if st.session_state.conversa_modo == "direto" else ""
        rodape = (f"{d['provedor']} · {d['modelo']} · {d['segundos']:.1f} s{modo} · memória {l['memoria']}: "
                  f"leu {l['mensagens_enviadas']} de {l['mensagens_na_conversa']} mensagens"
                  + (" · +1 chamada de resumo" if d["chamada_de_resumo"] else "")
                  + (" · números conferidos ✓" if not d["numeros_sem_fonte"] else ""))
        st.markdown(d["resposta"])
        if aviso:
            st.warning(aviso, icon="⚠️")
        st.caption(rodape)
        if d["falhas_antes"]:
            st.caption("Antes deste, falharam: " + "; ".join(f"{p} ({m})" for p, m in d["falhas_antes"].items()))
        st.session_state.conversa_msgs.append(
            {"papel": "assistant", "texto": d["resposta"], "aviso": aviso, "rodape": rodape})
        st.session_state.conversa_leitura = l

# --- o que o modelo leu (transparencia) ------------------------------------
if st.session_state.get("conversa_leitura"):
    l = st.session_state.conversa_leitura
    with st.expander("O que o assistente leu para responder a última pergunta"):
        st.write(f"**Memória:** {l['memoria']} · **mensagens lidas:** {l['mensagens_enviadas']} "
                 f"de {l['mensagens_na_conversa']} · **lugares em foco:** {', '.join(l['lugares_em_foco']) or 'nenhum'}")
        if l["notas"]:
            st.write(l["notas"])
        st.code(l["fatos"], language=None)
