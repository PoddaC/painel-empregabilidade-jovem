"""
ciclo.py - do dado ao insight: o ciclo de ciencia de dados do projeto, com
os numeros de verdade de cada etapa.

Coleta -> preparacao -> modelos -> insights. Le SO arquivos do repositorio
(CSVs e resultados medidos), sem a API: funciona tambem no link publicado.
Os numeros saem dos arquivos; o texto interpreta o que eles mostram.
"""

import csv
from collections import Counter, defaultdict

import streamlit as st

from graficos import barras_destaque, serie_jovens
from src.data_access import BASE, carregar_ibge, carregar_noticias, id_da_noticia
from src.indicadores import milhar, pct, resumo_ibge, trimestre_de
from src.tarefas import rotulo

BANCO = BASE / "data" / "analisador" / "banco_de_provas.csv"
BANCADA = BASE / "data" / "analisador" / "bancada_previsoes.csv"
TESTE_MEMORIA = BASE / "data" / "teste_memoria" / "respostas.csv"

# Nomes curtos para os graficos; o escolhido leva a estrela.
MODELOS = {"regras": "Regras", "mdeberta": "mDeBERTa", "qwen05": "Qwen2.5 0.5B",
           "qwen15": "Qwen2.5 1.5B ★", "qwen3_17": "Qwen3 1.7B"}
ESCOLHIDO = MODELOS["qwen15"]


def ler_csv(caminho):
    if not caminho.exists():
        return []
    with caminho.open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


noticias, _ = carregar_noticias()
ibge, fonte_ibge = carregar_ibge()
r = resumo_ibge(ibge)
banco = ler_csv(BANCO)
bancada = ler_csv(BANCADA)
teste = ler_csv(TESTE_MEMORIA)

st.title("Do dado ao insight")
st.caption("O ciclo de ciência de dados do projeto (TDSP), etapa por etapa, com os números de "
           "verdade de cada uma, lidos dos arquivos do repositório.")

# Mapa do ciclo: as quatro etapas lado a lado, cada uma com o seu numero.
etapas = st.columns(4)
etapas[0].metric("1 · Coleta", f"{len(noticias)} + {milhar(len(ibge))}",
                 help="Notícias raspadas + linhas do IBGE pela API.")
etapas[1].metric("2 · Preparação", f"{len(banco)} rótulos", help="Notícias rotuladas à mão: o gabarito.")
etapas[2].metric("3 · Modelos", "2 escolhidos", help="Um local (classifica) e um online (conversa), ambos por medição.")
etapas[3].metric("4 · Insights", f"{r['brasil']['18 a 24 anos'] / r['brasil']['total']:.1f}×".replace(".", ",")
                 if r else "—", help="Quantas vezes a desocupação de 18 a 24 anos supera a média.")
st.divider()

# ===========================================================================
st.header("1. Coleta")
meses = sorted(n["ano_mes"] for n in noticias if n["ano_mes"] != "n/d")
com_texto = sum(1 for n in noticias if (n.get("arquivo_texto") or "").strip())
linhas_coleta = []
if meses:
    linhas_coleta.append(
        f"- **Notícias:** {len(noticias)} da Agência Brasil (Creative Commons), por **raspagem** do HTML, "
        f"de {meses[0]} a {meses[-1]}; {com_texto} com texto integral.")
if r:
    linhas_coleta.append(
        f"- **Desocupação por idade:** {milhar(len(ibge))} linhas do IBGE (PNAD Contínua, tabela 4094), "
        f"pela **API** de agregados, até o {r['periodo']}; coletadas em {r['coletado_em'][:10]}.")
linhas_coleta.append("- **A resposta bruta de cada fonte** fica guardada em `data/raw/`, como prova.")
st.markdown("\n".join(linhas_coleta))

# ===========================================================================
st.header("2. Preparação")
if r:
    possiveis = len({l["periodo"] for l in ibge}) * len({l["localidade"] for l in ibge}) * 3
    faltam = f"{milhar(len(ibge))} de {milhar(possiveis)}"
else:
    faltam = "—"
st.markdown(
    f"- **{len(banco)} notícias rotuladas à mão** (tendência e setor) antes de medir qualquer modelo: "
    "é o gabarito da bancada.\n"
    "- **IBGE em formato longo:** uma linha por trimestre, lugar e grupo de idade. Valores que o IBGE "
    f"não divulga são **pulados**, não viram zero ({faltam} possíveis).\n"
    "- **Textos em UTF-8,** um arquivo por notícia; no CSV, só o caminho."
)

# ===========================================================================
st.header("3. Modelos")

st.subheader("Analisador: qual modelo local lê melhor a notícia?")
if bancada and banco:
    acertos = defaultdict(Counter)
    for p in bancada:
        acertos[p["candidato"]][p["tipo"]] += p["esperado"] == p["previsto"]
    st.caption("Notícias certas, de 42 rotuladas à mão. A linha tracejada é a base: "
               "chutar sempre a categoria mais comum.")
    col_t, col_s = st.columns(2)
    for col, tarefa, nome in ((col_t, "tendencia", "Tendência"), (col_s, "setor", "Setor")):
        base = Counter(b[tarefa] for b in banco).most_common(1)[0][1]
        with col:
            st.markdown(f"**{nome}** · base = {base}")
            barras_destaque([{"nome": MODELOS.get(c, c), "valor": a[tarefa]} for c, a in acertos.items()],
                            ESCOLHIDO, "notícias certas", referencia=base)
    st.markdown(
        f"O **{ESCOLHIDO.rstrip(' ★')}** foi escolhido: empata com as regras em tendência, lendo o "
        "texto, e roda em 0,07 s na GPU (14 s na CPU). Em setor, nenhum modelo passa a base, "
        "por isso o setor está marcado como **experimental**. Detalhes em `docs/escolha_do_modelo.md`."
    )
else:
    st.info("Bancada ainda não rodada (python -m src.bancada).")

st.subheader("Conversa: qual memória mantém o contexto?")
if teste:
    por_mem = defaultdict(list)
    for t in teste:
        por_mem[t["memoria"]].append(t)
    st.caption("Teste de 10 perguntas (python -m src.teste_memoria): a 10ª volta ao primeiro estado citado.")
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("**Acertos, de 10**")
        barras_destaque([{"nome": m, "valor": sum(t["acertou"] == "True" for t in ts)} for m, ts in por_mem.items()],
                        "notas", "acertos")
    with col_b:
        st.markdown("**Tokens lidos na 10ª pergunta** (custo)")
        barras_destaque([{"nome": m, "valor": int(next(t for t in ts if t["turno"] == "10")["tokens_entrada"])}
                         for m, ts in por_mem.items() if any(t["turno"] == "10" and t["tokens_entrada"] for t in ts)],
                        "notas", "tokens")
    extras = {m: sum(t["chamada_de_resumo"] == "True" for t in ts) for m, ts in por_mem.items()}
    st.markdown(
        "A **inteira** lembra de tudo, mas fica mais cara a cada pergunta; a **janela** é barata e "
        f"**esquece** o começo (errou a 10ª); o **resumo** acerta, mas paga {extras.get('resumo', 0)} chamadas "
        "a mais. As **notas** acertam tudo lendo menos que a inteira e o resumo, sem chamada a mais: "
        "por isso são a padrão."
    )
else:
    st.info("Teste de memória ainda não rodado (python -m src.teste_memoria).")

# ===========================================================================
st.header("4. Insights")
if r:
    st.markdown(
        f"- **O jovem procura e não acha mais que a média:** no {r['periodo']}, {pct(r['brasil']['18 a 24 anos'])} "
        f"de 18 a 24 anos e {pct(r['brasil']['14 a 17 anos'])} de 14 a 17, contra {pct(r['brasil']['total'])} "
        "em todas as idades.\n"
        f"- **A distância entre estados é grande:** de {pct(r['ufs'][-1][1])} em {r['ufs'][-1][0]} a "
        f"{pct(r['ufs'][0][1])} em {r['ufs'][0][0]}, para 18 a 24 anos (o ranking completo está na Início)."
    )

    st.subheader("Desocupação dos jovens × tom das notícias")
    rot = {id_da_noticia(n): n for n in noticias}
    por_tri = defaultdict(Counter)
    for b in banco:
        n = rot.get(b["id"])
        if n and n["ano_mes"] != "n/d":
            por_tri[trimestre_de(n["ano_mes"])][rotulo("tendencia", b["tendencia"])] += 1
    if por_tri:
        inicio = min(por_tri)
        tris = [p["trimestre"] for p in r["serie"] if p["trimestre"] >= inicio]
        tom = Counter(b["tendencia"] for b in banco)
        st.markdown(
            f"Das {len(banco)} notícias, **{tom.get('otimista', 0)} têm tom otimista**. Isso combina com "
            "a queda da desocupação no mesmo período, mas notícia boa no agregado não quer dizer vaga "
            "para quem tem 18 anos: por isso o painel mostra os dois lado a lado."
        )
        col_l, col_n = st.columns(2)
        with col_l:
            st.caption("Desocupação no Brasil (IBGE)")
            serie_jovens(r, desde=inicio, altura=260)
        with col_n:
            st.caption("Notícias no acervo, por tom (rótulos à mão)")
            cats = sorted({c for v in por_tri.values() for c in v})
            st.bar_chart([{"trimestre": t, **{c: por_tri[t].get(c, 0) for c in cats}} for t in tris],
                         x="trimestre", y=cats, y_label="notícias", x_label="", height=260)
else:
    st.info("Colete os dados do IBGE (python -m src.coletar_ibge) para ver os insights.")

st.divider()
st.page_link("paginas/conversa.py", label="Quer perguntar do seu jeito? Converse com o assistente", icon="💬")
st.caption(f"Fontes: Agência Brasil / EBC · {fonte_ibge}")
