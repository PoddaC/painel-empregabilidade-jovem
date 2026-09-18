# Project Charter — Painel de Empregabilidade Jovem por Setor

## 1. Contexto e Problema de Negócio
Organizações de empregabilidade juvenil (ONGs, programas de primeiro emprego)
precisam decidir para quais setores da economia capacitar jovens, mas
frequentemente tomam essa decisão sem dados sobre onde o mercado realmente
cria vagas. O resultado são cursos de qualificação desalinhados da demanda real.

**Pergunta(descritiva):** quais setores da economia estão absorvendo
mais trabalhadores e, portanto, devem ser priorizados na qualificação de jovens
em busca do primeiro emprego?

## 2. Escopo
**Dentro do escopo:**
- Coleta de dados de ocupação por setor (grupamento de atividade) via API do IBGE.
- Painel Streamlit comparando setores e sua variação de ocupação.
- Recorte nacional (Brasil).

**Fora do escopo (por ora):**
- Dados de vagas em aberto / falta de mão de obra (fonte CAGED — iteração futura).
- Recorte por UF ou município.
- Medição do impacto dos cursos da ONG (exige dados internos da organização).

## 3. Objetivos e Indicadores de Sucesso (KPIs)
- **Cobertura:** exibir 100% dos grupamentos de atividade da PNAD Contínua.
- **Automação:** coletar via API do IBGE, com atualização a cada trimestre divulgado.
- **Usabilidade:** identificar os 3 setores que mais cresceram no último ano em ate 3 cliques.
- **Outcome:** permitir a selecao de pelo menos 1 setor em expansao para direcionar um curso.

## 4. ODS Atendido
**ODS 8 — Trabalho Decente e Crescimento Econômico**, com foco na **meta 8.6**
(reduzir a proporção de jovens sem emprego, educação ou formação — os "nem-nem").
O painel direciona a qualificação profissional para setores em expansão,
atacando a empregabilidade juvenil de forma concreta. Conecta-se também às
metas 8.5 (emprego para os jovens) e 8.3 (criação de emprego produtivo).

## 5. Público-Alvo (Stakeholders)
- **Quem usa:** coordenação de programas / analista da ONG.
- **Quem decide:** direção da ONG ou financiador que aprova a abertura do curso.
- **Beneficiário final:** jovens de 14 a 24 anos em busca do primeiro emprego.

## 6. Riscos e Mitigações
- **API do IBGE fora do ar:** mitigação com cache/fallback de amostra (Etapa 2).
- **Estrutura do JSON mudar:** isolar a coleta em `src/`, longe da interface.
- **Dado desatualizado:** exibir a fonte e o período na tela.

## 7. Metodologia
Projeto conduzido segundo o TDSP (Team Data Science Process), tendo o CRISP-DM
como base conceitual. Documento vivo, revisado ao fim de cada etapa.