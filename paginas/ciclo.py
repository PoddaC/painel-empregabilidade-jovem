"""
ciclo.py - do dado ao insight: o ciclo de ciencia de dados do projeto, com
os numeros de verdade de cada etapa.

Coleta -> preparacao -> modelos -> insights. Esta pagina le SO arquivos do
repositorio (CSVs e resultados medidos), sem a API: funciona tambem no
deploy. Os numeros dos graficos e das metricas saem dos arquivos; o texto
interpreta o que eles mostram.
"""

import csv
from collections import Counter, defaultdict

import streamlit as st

from src.data_access import BASE, carregar_ibge, carregar_noticias, id_da_noticia
from src.tarefas import rotulo

BANCO = BASE / "data" / "analisador" / "banco_de_provas.csv"
BANCADA = BASE / "data" / "analisador" / "bancada_previsoes.csv"
TESTE_MEMORIA = BASE / "data" / "teste_memoria" / "respostas.csv"

NOMES = {"regras": "Regras (palavras-chave)", "mdeberta": "mDeBERTa (zero-shot)",
         "qwen05": "Qwen2.5-0.5B", "qwen15": "Qwen2.5-1.5B (escolhido)", "qwen3_17": "Qwen3-1.7B"}


def ler_csv(caminho):
    if not caminho.exists():
        return []
    with caminho.open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def fmt(x, casas=1):
    return f"{x:.{casas}f}".replace(".", ",")


def trimestre(ano_mes):
    """'2025-08' -> '2025-T3'."""
    ano, mes = ano_mes.split("-")
    return f"{ano}-T{(int(mes) - 1) // 3 + 1}"


noticias, _ = carregar_noticias()
ibge, fonte_ibge = carregar_ibge()
banco = ler_csv(BANCO)
bancada = ler_csv(BANCADA)
teste = ler_csv(TESTE_MEMORIA)

st.title("Do dado ao insight")
st.caption(
    "O ciclo de ciência de dados do projeto (TDSP), etapa por etapa, com os números de "
    "verdade de cada uma. Tudo aqui é lido dos arquivos do repositório."
)

# ===========================================================================
st.header("1. Coleta")
c1, c2, c3 = st.columns(3)
com_texto = sum(1 for n in noticias if (n.get("arquivo_texto") or "").strip())
c1.metric("Notícias coletadas", len(noticias), help="Raspagem da tag 'emprego' da Agência Brasil (src/coletar.py).")
c2.metric("Com texto integral", com_texto, help="Segunda passada, notícia por notícia (src/coletar_textos.py).")
c3.metric("Linhas do IBGE", f"{len(ibge):,}".replace(",", "."),
          help="API de agregados do IBGE, PNAD Contínua, tabela 4094 (src/coletar_ibge.py).")
meses = sorted(n["ano_mes"] for n in noticias if n["ano_mes"] != "n/d")
periodos = sorted({l["periodo"] for l in ibge})
st.markdown(
    f"- **Notícias:** Agência Brasil (Creative Commons), por **raspagem** do HTML, de "
    f"{meses[0] if meses else '—'} a {meses[-1] if meses else '—'}.\n"
    f"- **Desocupação por idade:** IBGE, pela **API** de agregados, de {periodos[0] if periodos else '—'} "
    f"a {periodos[-1] if periodos else '—'}"
    + (f", coletada em {ibge[0]['coletado_em'][:10]}." if ibge else ".")
    + "\n- **A resposta bruta de cada fonte** fica guardada em `data/raw/`, como prova."
)

# ===========================================================================
st.header("2. Preparação")
possiveis = len(periodos) * len({l["localidade"] for l in ibge}) * 3
st.markdown(
    f"- **{len(banco)} notícias rotuladas à mão** (tendência e setor) antes de medir qualquer modelo: "
    "é o gabarito da bancada.\n"
    f"- **IBGE em formato longo** (uma linha por trimestre, lugar e grupo de idade). Valores que o IBGE "
    f"não divulga são **pulados**, não viram zero: {len(ibge):,} de {possiveis:,} possíveis.".replace(
        f"{len(ibge):,}", f"{len(ibge):,}".replace(",", ".")).replace(f"{possiveis:,}", f"{possiveis:,}".replace(",", "."))
    + "\n- **Textos em UTF-8**, um arquivo por notícia; no CSV, só o caminho."
)

# ===========================================================================
st.header("3. Modelos")
st.subheader("Analisador: qual modelo local lê melhor a notícia?")
st.caption("Acertos nas 42 notícias rotuladas à mão (bancada do TP4). A linha de base chuta sempre a categoria mais comum.")
if bancada and banco:
    acertos = defaultdict(Counter)
    for p in bancada:
        acertos[p["candidato"]][p["tipo"]] += p["esperado"] == p["previsto"]
    linhas = [{"modelo": "Sempre a mais comum (base)",
               "Tendência": Counter(b["tendencia"] for b in banco).most_common(1)[0][1],
               "Setor": Counter(b["setor"] for b in banco).most_common(1)[0][1]}]
    linhas += [{"modelo": NOMES.get(c, c), "Tendência": a["tendencia"], "Setor": a["setor"]}
               for c, a in acertos.items()]
    st.bar_chart(linhas, x="modelo", y=["Tendência", "Setor"], stack=False, horizontal=True,
                 x_label="notícias certas (de 42)", y_label="")
    st.markdown(
        "O **Qwen2.5-1.5B** foi escolhido: empata com as regras em tendência e acerta 29 das 30 notícias "
        "que não são neutras. Em setor, nenhum modelo passa a linha de base, e por isso o setor ficou "
        "marcado como **experimental**. Roda em 0,07 s na GPU e em 14 s na CPU "
        "(detalhes em `docs/escolha_do_modelo.md`)."
    )
else:
    st.info("Bancada ainda não rodada (python -m src.bancada).")

st.subheader("Conversa: qual memória mantém o contexto?")
st.caption("Teste de 10 perguntas (python -m src.teste_memoria): a 10ª volta ao primeiro estado citado.")
if teste:
    por_mem = defaultdict(list)
    for t in teste:
        por_mem[t["memoria"]].append(t)
    tabela = []
    for m, ts in por_mem.items():
        dec = next((t for t in ts if t["turno"] == "10"), None)
        tabela.append({
            "memória": m,
            "acertos": f"{sum(t['acertou'] == 'True' for t in ts)}/10",
            "10ª (volta ao 1º estado)": "✓" if dec and dec["acertou"] == "True" else "✗",
            "tokens lidos na 10ª": int(dec["tokens_entrada"]) if dec and dec["tokens_entrada"] else None,
            "chamadas a mais": sum(t["chamada_de_resumo"] == "True" for t in ts),
        })
    st.dataframe(tabela, hide_index=True, width="stretch")
    serie = defaultdict(dict)
    for m, ts in por_mem.items():
        for t in ts:
            if t["tokens_entrada"]:
                serie[int(t["turno"])][m] = int(t["tokens_entrada"])
    st.line_chart([{"pergunta": k, **v} for k, v in sorted(serie.items())], x="pergunta",
                  y=list(por_mem), x_label="pergunta da conversa", y_label="tokens que o modelo leu")
    st.markdown(
        "A **inteira** lembra de tudo, mas o custo cresce a cada pergunta; a **janela** fica barata e "
        "**esquece** o começo (errou a 10ª); o **resumo** acerta, mas paga chamadas a mais. As **notas** "
        "acertam tudo lendo menos que a inteira e o resumo, sem chamada a mais: por isso são a padrão."
    )
else:
    st.info("Teste de memória ainda não rodado (python -m src.teste_memoria).")

# ===========================================================================
st.header("4. Insights")
if ibge:
    idx = {(l["localidade"], l["grupo_idade"], l["periodo_codigo"]): l["taxa_desocupacao_pct"] for l in ibge}
    ult = max(l["periodo_codigo"] for l in ibge)
    nome_ult = next(l["periodo"] for l in ibge if l["periodo_codigo"] == ult)
    br = {g: idx.get(("Brasil", g, ult)) for g in ("14 a 17 anos", "18 a 24 anos", "total")}
    ufs = sorted(((l["localidade"], l["taxa_desocupacao_pct"]) for l in ibge
                  if l["nivel"] == "UF" and l["periodo_codigo"] == ult and l["grupo_idade"] == "18 a 24 anos"),
                 key=lambda x: x[1])
    tend = Counter(b["tendencia"] for b in banco)
    st.markdown(
        f"- **O jovem procura e não acha mais que a média:** no {nome_ult}, a desocupação de 18 a 24 anos "
        f"foi de **{fmt(br['18 a 24 anos'])}%** e a de 14 a 17, de **{fmt(br['14 a 17 anos'])}%**, contra "
        f"**{fmt(br['total'])}%** em todas as idades.\n"
        + (f"- **A distância entre estados é grande:** para 18 a 24 anos, de **{fmt(ufs[0][1])}%** em "
           f"{ufs[0][0]} a **{fmt(ufs[-1][1])}%** em {ufs[-1][0]}. Um programa nacional de "
           "qualificação não serve igual para todos.\n" if ufs else "")
        + (f"- **O noticiário é otimista:** das {len(banco)} notícias, {tend.get('otimista', 0)} têm tom "
           "otimista. Isso combina com a queda da desocupação no gráfico abaixo, mas notícia boa no "
           "agregado não quer dizer vaga para quem tem 18 anos.\n" if banco else "")
    )

    st.subheader("Desocupação dos jovens × tom das notícias, trimestre a trimestre")
    rot = {id_da_noticia(n): n for n in noticias}
    por_tri = defaultdict(Counter)
    for b in banco:
        n = rot.get(b["id"])
        if n and n["ano_mes"] != "n/d":
            por_tri[trimestre(n["ano_mes"])][rotulo("tendencia", b["tendencia"])] += 1
    tris = sorted(por_tri)
    if tris:
        codigo = {l["periodo"]: l["periodo_codigo"] for l in ibge}
        janela_tri = [t for t in sorted({l["periodo"] for l in ibge}) if tris[0] <= t <= max(tris[-1], nome_ult)]
        st.line_chart(
            [{"trimestre": t, "18 a 24 anos": idx.get(("Brasil", "18 a 24 anos", codigo[t])),
              "todas as idades": idx.get(("Brasil", "total", codigo[t]))} for t in janela_tri],
            x="trimestre", y=["18 a 24 anos", "todas as idades"], y_label="desocupação no Brasil (%)",
            x_label="", height=260,
        )
        cats = sorted({c for v in por_tri.values() for c in v})
        st.bar_chart([{"trimestre": t, **{c: por_tri[t].get(c, 0) for c in cats}} for t in janela_tri],
                     x="trimestre", y=cats, y_label="notícias no acervo", x_label="", height=220)
        st.caption("Dois gráficos, um eixo cada: a taxa (IBGE) em cima e a contagem de notícias "
                   "por tom (rótulos à mão) embaixo, nos mesmos trimestres.")
else:
    st.info("Colete os dados do IBGE (python -m src.coletar_ibge) para ver os insights.")

st.divider()
st.markdown("**Quer perguntar do seu jeito?**")
st.page_link("paginas/conversa.py", label="Conversa (IA) — pergunte sobre estes dados, com memória", icon="💬")
st.caption(f"Fontes: Agência Brasil / EBC · {fonte_ibge}")
