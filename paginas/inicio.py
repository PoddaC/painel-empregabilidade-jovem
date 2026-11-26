"""
inicio.py - a porta de entrada: o que o painel responde e para quem.

Esta pagina nao usa filtro: ela apresenta o projeto e aponta para as outras.
"""

import streamlit as st

from comum import obter_todas, guarda_sem_dados
from src.data_access import carregar_ibge

st.title("Painel de Empregabilidade Jovem")
st.caption(
    "Projeto de Bloco: IA Aplicada | ODS 8 - Trabalho Decente e "
    "Crescimento Econômico, metas 8.5, 8.6 e 8.b"
)

todas, fonte = obter_todas()
guarda_sem_dados(todas)

st.markdown(
    """
**O problema.** Organizações de empregabilidade juvenil e quem as financia
precisam decidir **onde** e **para o quê** qualificar jovens, e costumam
decidir sem dado sobre onde o jovem mais procura emprego e não acha.

**As perguntas que o painel responde.**
1. **Onde o desemprego jovem é maior?** Em que estados e em que faixa de idade
   (14 a 17 ou 18 a 24 anos), e para onde ele vai. Dados do IBGE.
2. **O que o mercado está sinalizando?** O tom e os setores das notícias de
   emprego, lidas por um modelo de linguagem.
3. **E se eu quiser perguntar do meu jeito?** O assistente da página Conversa
   responde em português, só com os números do painel, e lembra do que você
   já perguntou.

**Para quem.** Coordenação e analistas de ONGs de empregabilidade; a direção
ou o financiador (inclusive a área de ESG de empresas) que aprova um programa;
e, ao fim da linha, jovens de 14 a 24 anos.
"""
)

st.divider()

# --- os numeros que resumem o problema e o tamanho do acervo ---
ibge, _ = carregar_ibge()
col1, col2, col3 = st.columns(3)
if ibge:
    ult = max(l["periodo_codigo"] for l in ibge)
    br = {l["grupo_idade"]: l for l in ibge
          if l["localidade"] == "Brasil" and l["periodo_codigo"] == ult}
    periodo = br["total"]["periodo"]
    fmt = lambda x: f"{x:.1f}%".replace(".", ",")
    col1.metric(f"Desocupação, 18 a 24 anos ({periodo})", fmt(br["18 a 24 anos"]["taxa_desocupacao_pct"]),
                help="IBGE, PNAD Contínua, Brasil. Desocupado é quem procurou trabalho e não achou.")
    col2.metric(f"Desocupação, todas as idades ({periodo})", fmt(br["total"]["taxa_desocupacao_pct"]))
else:
    col1.metric("Desocupação, 18 a 24 anos", "—", help="Rode python -m src.coletar_ibge.")
col3.metric("Notícias de emprego no acervo", len(todas))

st.divider()

st.subheader("Por onde começar")

# page_link: o mesmo link do menu, dentro da pagina. A Inicio funciona
# como um indice das outras.
st.page_link("paginas/ciclo.py", label="Do dado ao insight — o ciclo inteiro, com os números de cada etapa", icon="🔄")
st.page_link("paginas/conversa.py", label="Conversa (IA) — pergunte sobre os dados, com memória", icon="💬")
st.page_link("paginas/noticias.py", label="Notícias — a tabela, filtrada e baixável", icon="📰")
st.page_link("paginas/analise.py", label="Análise — o que essas notícias mais falam", icon="📊")
st.page_link("paginas/analisador.py", label="Analisador (IA) — o modelo local lê a notícia: tendência e setor", icon="🤖")
st.page_link("paginas/dados.py", label="Dados e método — fontes, gráficos do IBGE, upload e limites", icon="🗂️")

st.divider()
st.caption(f"Fontes: {fonte} · IBGE, PNAD Contínua (tabela 4094)")
