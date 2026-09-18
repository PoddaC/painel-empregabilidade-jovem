"""
Painel de Empregabilidade Jovem por Setor
TP1 - Projeto de Bloco: IA Aplicada | Etapa 1 - Aplicacao demo

Nesta etapa os dados sao uma AMOSTRA manual (lista de dicionarios).
A coleta ao vivo via API do IBGE entra na Etapa 2.
"""

import streamlit as st

# -------------------------------------------------------------------
# Amostra de dados (manual)
# -------------------------------------------------------------------
amostra_setores = [
    {"setor": "Comercio, reparacao de veiculos", "ocupados_milhoes": 19.5, "variacao_ano_pct": 0.3},
    {"setor": "Adm. publica, educacao, saude e servicos sociais", "ocupados_milhoes": 19.0, "variacao_ano_pct": 5.0},
    {"setor": "Informacao, comunicacao, ativ. financeiras e profissionais", "ocupados_milhoes": 13.4, "variacao_ano_pct": 6.8},
    {"setor": "Industria geral", "ocupados_milhoes": 13.3, "variacao_ano_pct": 2.3},
    {"setor": "Servicos domesticos", "ocupados_milhoes": 5.7, "variacao_ano_pct": -4.1},
]

# -------------------------------------------------------------------
# Configuracao da pagina
# -------------------------------------------------------------------
st.set_page_config(page_title="Empregabilidade Jovem por Setor", layout="wide")

# Titulo
st.title("Painel de Empregabilidade Jovem por Setor")
st.caption("TP1 - Projeto de Bloco: IA Aplicada | ODS 8 - Trabalho Decente e Crescimento Economico")

# Descricao do problema e objetivos
st.header("O problema")
st.write(
    "Organizacoes de empregabilidade juvenil precisam decidir para quais setores "
    "capacitar jovens em busca do primeiro emprego, mas costumam fazer isso sem "
    "dados sobre onde o mercado realmente cria vagas. Este painel mostra quais "
    "setores da economia estao absorvendo mais trabalhadores, apoiando essa decisao."
)

st.subheader("Pergunta que orienta o projeto")
st.write(
    "Quais setores da economia estao em expansao e devem ser priorizados na "
    "qualificacao de jovens em busca do primeiro emprego?"
)

st.subheader("Objetivos")
st.write(
    "- Exibir a ocupacao por setor e sua variacao no ultimo ano.\n"
    "- Coletar os dados via API do IBGE (Etapa 2), com atualizacao trimestral.\n"
    "- Permitir identificar rapidamente os setores em expansao para direcionar cursos.\n"
    "- Contribuir para a meta 8.6 do ODS 8 (jovens sem emprego, educacao ou formacao)."
)

# Metricas rapidas (calculadas a partir da amostra, em Python puro)
st.header("Visao geral (amostra)")
col1, col2, col3 = st.columns(3)
col1.metric("Setores na amostra", len(amostra_setores))
setor_topo = max(amostra_setores, key=lambda s: s["variacao_ano_pct"])
col2.metric("Setor que mais cresceu", setor_topo["setor"].split(",")[0], f'+{setor_topo["variacao_ano_pct"]}%')
total = sum(s["ocupados_milhoes"] for s in amostra_setores)
col3.metric("Ocupados na amostra (milhoes)", f"{total:.1f}")

# Tabela com a amostra dos dados
st.header("Amostra dos dados que serao usados no projeto")
st.dataframe(amostra_setores, use_container_width=True)
st.caption(
    "Fonte: IBGE / PNAD Continua - pessoas ocupadas por grupamento de atividade "
    "(referencia 2025). Amostra manual desta etapa; a coleta via API entra na Etapa 2."
)

# Links uteis
st.header("Links uteis e fontes de inspiracao")
st.write(
    "- [Conecta Brasil](https://conectabrasil.org/home)\n"
    "- [Observatorio do Terceiro Setor](https://observatorio3setor.org.br/)\n"
    "- [PNAD Continua - IBGE](https://www.ibge.gov.br/estatisticas/sociais/trabalho/9173-pesquisa-nacional-por-amostra-de-domicilios-continua-trimestral.html)\n"
    "- [ODS 8 - ONU Brasil](https://brasil.un.org/pt-br/sdgs/8)"
)