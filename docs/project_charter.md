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
- **Acesso programático:** 100% do acervo exibido no painel disponível
  também por endpoint documentado, consultável sem passar pela interface.
  - **Prontidão para LLM :** todas as notícias coletadas possuem texto integral armazenado,
   e não apenas manchete 
  
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
- **Quem integra :** equipe técnica da ONG ou organização parceira que
  precisa dos dados dentro do próprio sistema, sem passar pela interface. É para
  esse público que a API existe: para um programa, o painel é uma casca de
  JavaScript.

## 6. Fontes de Dados

Detalhamento completo em `docs/data_summary_report.md`.
 
- **Notícias de emprego** — Agência Brasil / EBC (raspagem de HTML → CSV +
  arquivos de texto). Agora com linha fina e **texto integral** de cada matéria.
- **Upload do usuário** — CSV enviado na aplicação, válido para a sessão.
- **Notícias recebidas pela API (novo)** — JSON enviado por outro programa via
  `POST /noticias`, validado e gravado separadamente das coletadas.
- **Ocupação por setor** — IBGE / PNAD Contínua (amostra; API prevista).

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
- **Dado recebido pela API :** entrada vinda de fora é **não confiável**.
  O corpo do `POST` é validado por tipo antes de qualquer processamento
  (tamanho do título, formato do ano-mês), duplicatas são recusadas, e o que
  entra é gravado em arquivo separado, preservando a procedência.
- **API fora do ar :** não derruba o painel. A API e a aplicação são
  **irmãs**, não camadas: as duas leem a mesma pasta `data/processed/`. Nenhuma
  depende da outra estar de pé.
- **Fonte de vagas inacessível:** a via de acesso ao Novo CAGED foi
  investigada nesta etapa. O painel oficial é um relatório Power BI publicado na
  web, cujos números não existem no HTML em momento algum — inviável por
  raspagem, mesmo com navegador automatizado. A via viável são os microdados por
  FTP, de custo alto (arquivos de milhões de linhas, exigindo agregação prévia).
  Decisão: manter fora do escopo desta etapa, com o caminho documentado.
- **Ambiguidade dos modelos de LLM (futuro):** resultados de
  resumo e classificação de sentimento não são determinísticos. Mitigação
  prevista: sempre exibir o texto-fonte ao lado da saída do modelo, para que o
  usuário possa conferir.
- **Dado desatualizado:** a fonte e o período são exibidos na tela.

## 8. Arquitetura (nova seção)
O projeto tem **três camadas que não se bloqueiam**:
 
1. **Coleta** (`src/`) — roda à parte, no terminal, nunca dentro do app.
   Grava em `data/raw/` (snapshot bruto, prova do que a página dizia) e em
   `data/processed/` (tabela limpa). Se a raspagem quebrar, o produto continua
   de pé com o último dado coletado.
2. **Dados** (`data/processed/`) — o ponto de encontro. Tudo que consome dados
   lê daqui.
3. **Consumo** — dois consumidores independentes da mesma pasta:
   - a **aplicação** (`app.py` + `paginas/` + `comum.py`), para pessoas;
   - a **API** (`api/main.py`), para programas.
A decisão de deixar app e API lado a lado, em vez de empilhar o app sobre a API,
é deliberada: evita que uma indisponibilidade da API derrube a interface, e
mantém o deploy da aplicação inalterado.
 
**Ambientes separados:** `requirements.txt` declara o que a aplicação publicada
importa; `requirements-coleta.txt` e `requirements-api.txt` acrescentam o que é
específico de cada processo. O que se importa, se declara — no arquivo do
ambiente que importa.

## 9. Preparação para Inteligência Artificial com LLMs (nova seção)
Até o TP2, cada notícia era título, editoria, ano-mês e link. Manchete tem cerca
de oito palavras: não há o que resumir, o sentimento classificado seria raso e
não existe conteúdo sobre o qual responder perguntas. Nenhuma das tarefas
previstas se sustentava sobre esse dado.

Nesta etapa passou-se a coletar a **linha fina e o texto integral** de cada
matéria (detalhamento em `docs/data_summary_report.md`), o que habilita **quatro
tarefas** na etapa seguinte:

1. **Resumo automático** — condensar as matérias de um período ou editoria num
   panorama curto para a coordenação da ONG, substituindo a leitura de dezenas
   de textos.
2. **Classificação de sentimento** — rotular cada matéria entre otimista,
   pessimista ou neutra quanto ao mercado de trabalho e cruzar com a série
   temporal já existente (`ano_mes`), produzindo uma leitura de clima ao longo
   do tempo que nenhuma das fontes quantitativas oferece.
3. **Perguntas e respostas** — responder consultas diretas sobre o acervo ("o
   que as notícias dizem sobre o primeiro emprego neste semestre?"), usando os
   textos como base e citando a matéria de origem.
4. **Geração de texto** — redigir automaticamente a leitura de cenário que hoje
   o usuário precisa fazer de cabeça, a partir das estatísticas e das notícias.

## 10. Metodologia
Projeto conduzido segundo o **TDSP** (Team Data Science Process), tendo o
**CRISP-DM** como base conceitual. A separação de camadas descrita na seção 8
reflete a organização em fases do processo. O caráter iterativo aparece na
evolução do próprio produto: v1 com amostra manual (TP1) → v2 com raspagem,
cache e upload (TP2) → v3 multipáginas, com texto integral e API própria (TP3)
→ v4 com recursos de IA via LLM. Documento vivo, revisado ao fim de cada etapa.

