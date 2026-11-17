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
- **Análise por IA:** o modelo local superar as linhas de base no banco de provas,
  em até ~2 s por análise. Resultado: tempo atingido (0,07 s); acerto em parte
  (empata em tendência, perde em setor, que ficou como experimental).
- **Funcionamento offline:** após um único download, a análise roda sem internet.

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
- **Notícias recebidas pela API** — JSON enviado via `POST /noticias`, validado
  e gravado separadamente das coletadas.
- **Análises do modelo (novo)** — tendência e setor atribuídos pelo modelo local
  via `POST /processar_texto`. Dado derivado, não gravado.
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
- **API fora do ar:** não derruba o painel, que lê o disco direto e avisa na
  barra lateral; só o Analisador fica indisponível.
- **Fonte de vagas inacessível:** a via de acesso ao Novo CAGED foi
  investigada nesta etapa. O painel oficial é um relatório Power BI publicado na
  web, cujos números não existem no HTML em momento algum — inviável por
  raspagem, mesmo com navegador automatizado. A via viável são os microdados por
  FTP, de custo alto (arquivos de milhões de linhas, exigindo agregação prévia).
  Decisão: manter fora do escopo desta etapa, com o caminho documentado.
- **O modelo erra, às vezes com confiança alta:** a página mostra o trecho lido
  e as probabilidades, e avisa que confiança não é chance de acerto.
- **O modelo não carrega:** a API sobe mesmo assim; a análise responde 503 com o
  motivo e as outras rotas seguem funcionando.
- **Máquina lenta para o modelo:** limite de tempo por análise (504) e plano B
  sem modelo: o motor de regras (`PAINEL_MOTOR=regras`).
- **Licença do modelo:** só modelos abertos (Apache 2.0 / MIT) e sem pedido de
  acesso.

## 8. Arquitetura (revista no TP4)
Quatro peças, com **um dono para cada escrita**:

1. **Coleta** (`src/`) — roda à parte, no terminal. Grava em `data/raw/` e
   `data/processed/`.
2. **API** (`api/`) — a única que lê e grava o acervo para os outros, e onde
   mora o modelo de linguagem, carregado uma vez.
3. **Painel** (`app.py` + `paginas/`) — **cliente da API**: pede notícias e
   análises por HTTP. Se a API não responder, lê o disco e avisa.
4. **Modelo** — fica no disco, baixado à parte, e só a API o acessa.

No TP3, painel e API liam a mesma pasta lado a lado, e o painel não usava a
própria API — o ponto apontado na revisão. Agora ele é o primeiro cliente dela.
O modelo mora na API para o painel publicado seguir leve, sem `torch`.

**Ambientes separados:** `requirements.txt` declara o que o painel importa; os
de coleta, API e testes acrescentam o que é específico de cada processo.

## 9. Inteligência Artificial com LLM (TP4)
O texto integral das notícias passou a ser lido por um **modelo de linguagem
local** (`POST /processar_texto` e página **Analisador**), que classifica cada
notícia em duas perguntas: a *tendência* para o emprego (otimista, pessimista,
neutra) e o *setor* de que ela fala. Cruzadas, indicam quais setores aparecem
com notícias de expansão. Resumo e perguntas e respostas ficam para o TP5.

O modelo foi escolhido por medição: quatro candidatos e duas linhas de base num
banco de provas de 42 notícias rotuladas à mão. Detalhes em
`docs/escolha_do_modelo.md`.

## 10. Metodologia
Projeto conduzido segundo o **TDSP** (Team Data Science Process), tendo o
**CRISP-DM** como base conceitual. A separação de camadas descrita na seção 8
reflete a organização em fases do processo. O caráter iterativo aparece na
evolução do próprio produto: v1 com amostra manual (TP1) → v2 com raspagem,
cache e upload (TP2) → v3 multipáginas, com texto integral e API própria (TP3)
→ v4 com modelo de linguagem local e o painel como cliente da API (TP4). Documento vivo, revisado ao fim de cada etapa.

