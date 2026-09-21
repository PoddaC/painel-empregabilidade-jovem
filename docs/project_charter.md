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
- **Contexto qualitativo:** evidenciar os temas de emprego em pauta na imprensa
  (termos mais frequentes das notícias), identificáveis em até 3 cliques via
  nuvem de palavras.
- **Atualidade:** apoiar a leitura de cenário com notícias recentes de emprego,
  filtráveis por editoria e por período, para situar as decisões de qualificação
  no contexto do momento.
  
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

## 6. Fontes de Dados

- Notícias de emprego — Agência Brasil / EBC (raspagem de HTML → CSV).

- Upload do usuário — CSV enviado na aplicação (complementa as notícias).

- Ocupação por setor — IBGE / PNAD Contínua (amostra; API prevista).

## 7. Riscos e Mitigações
- **Estrutura do site de notícias mudar:** a extração se apoia no padrão de URL
  das matérias (mais estável que classes CSS) e a coleta fica isolada em `src/`,
  longe da interface; se quebrar, conserta-se só a coleta.
- **Bloqueio/limite do site:** o `robots.txt` foi verificado (raspagem da tag
  liberada) e o `Crawl-delay` de 10s é respeitado entre requisições.
- **CSV de upload malformado:** validação na borda (codificação e coluna
  obrigatória) devolve erro amigável em vez de quebrar o app.
- **API do IBGE fora do ar (uso futuro):** mitigação com cache/fallback de amostra.
- **Dado desatualizado:** a fonte e o período são exibidos na tela.

## 8. Metodologia
Projeto conduzido segundo o **TDSP** (Team Data Science Process), tendo o
**CRISP-DM** como base conceitual. A separação de camadas (coleta em `src/`,
dados em `data/raw` e `data/processed`, interface em `app.py`) reflete a
organização em fases do processo. Documento vivo, revisado ao fim de cada etapa.

