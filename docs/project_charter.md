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
- **Prontidão para LLM:** todas as notícias coletadas possuem texto integral
  armazenado, e não apenas manchete.
- **Análise por IA (TP4):** o modelo de linguagem local supera as duas linhas
  de base (sempre a categoria mais comum; palavras-chave) no banco de provas
  de 42 notícias rotuladas, e responde em até ~2 s por análise na GPU da
  máquina do projeto. Medição em `docs/bancada_resultados.md`.
- **Funcionamento offline:** depois de um único download do modelo, a análise
  roda sem conexão com a internet.

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
- **Notícias recebidas pela API** — JSON enviado por outro programa (ou pela
  página "Dados e método") via `POST /noticias`, validado e gravado
  separadamente das coletadas.
- **Análises do modelo de linguagem (novo, TP4)** — dado *derivado*: a
  tendência e o setor que o modelo local atribui a um texto, devolvidos por
  `POST /processar_texto`. Não são gravados; cada resposta diz qual modelo
  analisou.
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
- **API fora do ar:** não derruba o painel. O painel pede os dados à API e,
  se ela não responder, lê o disco direto e **avisa na barra lateral**; só o
  Analisador fica indisponível. No Streamlit Cloud, onde não há API, é esse o
  modo em que o painel roda.
- **Fonte de vagas inacessível:** a via de acesso ao Novo CAGED foi
  investigada nesta etapa. O painel oficial é um relatório Power BI publicado na
  web, cujos números não existem no HTML em momento algum — inviável por
  raspagem, mesmo com navegador automatizado. A via viável são os microdados por
  FTP, de custo alto (arquivos de milhões de linhas, exigindo agregação prévia).
  Decisão: manter fora do escopo desta etapa, com o caminho documentado.
- **O modelo erra — às vezes com confiança alta:** medido na bancada. A
  página do Analisador mostra o trecho que o modelo leu, todas as
  alternativas com suas probabilidades, e avisa que a confiança **não** é a
  chance de acerto. A decisão continua sendo de quem lê.
- **O modelo não carrega** (não baixado, memória insuficiente, biblioteca
  faltando): a API sobe do mesmo jeito; `POST /processar_texto` responde 503
  com o motivo, e as rotas de notícias seguem funcionando.
- **Máquina lenta para o modelo:** cada análise tem limite de tempo (504 com
  explicação), e há um plano B medido que não exige GPU nem modelo: o motor
  de regras (`PAINEL_MOTOR=regras`), que empatou com o modelo em tendência.
- **Licença e acesso do modelo:** só entraram na disputa modelos de licença
  aberta (Apache 2.0 / MIT) e sem pedido de acesso, para que a ONG possa
  usar e reinstalar sem depender de terceiros.

## 8. Arquitetura (revista no TP4)
O projeto tem **quatro peças, com um dono para cada escrita**:

1. **Coleta** (`src/coletar*.py`) — roda à parte, no terminal, nunca dentro
   do app. Grava em `data/raw/` (snapshot bruto) e em `data/processed/`
   (tabela limpa e textos). Se a raspagem quebrar, o produto segue com o
   último dado coletado.
2. **API** (`api/`) — a **única** que lê e grava o acervo para os outros:
   serve as notícias, recebe as enviadas (validando) e hospeda o **modelo de
   linguagem**, carregado uma vez quando ela sobe.
3. **Painel** (`app.py` + `paginas/` + `comum.py`) — **cliente da API**: pede
   as notícias e as análises por HTTP (`src/cliente_api.py`), como qualquer
   outro programa, e lê cada resposta pelo status. Se a API não responder,
   lê o disco direto e avisa.
4. **Modelo** (`src/analisador_llm.py`) — mora no disco (baixado por
   `src/baixar_modelo.py`) e só é acessado pela API.

**O que mudou em relação ao TP3:** no TP3, app e API eram "irmãs" lendo a
mesma pasta, e o painel não consumia a própria API. A revisão do TP3 apontou
justamente isso. Agora o painel é o primeiro cliente da API, e o plano B de
leitura do disco é exceção declarada, não arquitetura.

**Por que o modelo mora na API, e não no painel:** o peso (gigabytes de
memória, segundos de carga) fica num processo só, carregado uma vez; o painel
publicado no Streamlit Cloud segue leve, sem `torch`; e outros programas da
ONG podem pedir a mesma análise sem abrir tela nenhuma.

**Ambientes separados:** `requirements.txt` declara o que o painel importa;
`requirements-coleta.txt`, `requirements-api.txt` e `requirements-dev.txt`
acrescentam o que é específico de cada processo.

## 9. Inteligência Artificial com LLM (TP4)
O texto integral coletado no TP3 virou a entrada de um **modelo de linguagem
local**, exposto pela rota `POST /processar_texto` e usado pela página
**Analisador (IA)**.

**A tarefa escolhida é classificação, em duas perguntas:** a *tendência* que
a notícia aponta para o emprego (otimista, pessimista, neutra) e o *setor da
economia* de que ela fala. É a tarefa que serve diretamente à pergunta do
projeto: cruzadas, as duas respostas indicam quais setores aparecem com
notícias de expansão. Das quatro aplicações levantadas no TP3, a
classificação de sentimento foi a implementada. Resumo, perguntas e
respostas e geração de texto ficam para a etapa final.

**O modelo** foi escolhido por medição, não por fama: quatro candidatos e duas
linhas de base rodaram sobre um banco de provas de 42 notícias reais,
rotuladas à mão antes da medição. Critérios, números e decisão estão em
`docs/escolha_do_modelo.md`.

**Garantias da integração:** a categoria devolvida é sempre uma da lista (o
modelo pontua as opções em vez de escrever); a resposta tem contrato
(`ResultadoAnalise`); e cada falha tem seu status — 422 (texto inválido), 503
(modelo não carregado), 504 (tempo esgotado), 500 com código (imprevisto).

## 10. Metodologia
Projeto conduzido segundo o **TDSP** (Team Data Science Process), tendo o
**CRISP-DM** como base conceitual. A separação de camadas descrita na seção 8
reflete a organização em fases do processo. O caráter iterativo aparece na
evolução do próprio produto: v1 com amostra manual (TP1) → v2 com raspagem,
cache e upload (TP2) → v3 multipáginas, com texto integral e API própria (TP3)
→ v4 com modelo de linguagem local, API com contratos de resposta e
tratamento de erros, e o painel como cliente da API (TP4) → v5 com a
aplicação completa (TP5). Documento vivo, revisado ao fim de cada etapa.

