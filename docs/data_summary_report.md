# Data Summary Report — Painel de Empregabilidade Jovem

> Versão final (TP5). Mapeia de onde vêm os dados, em que formato chegam,
> como são integrados e para que cada um serve, da coleta até a resposta da IA.

O que mudou no TP5:

1. A **Fonte 4 (IBGE)** deixou de ser uma lista digitada no código e passou a
   ser coletada pela **API do IBGE**, agora com o recorte de **jovens** (14 a
   17 e 18 a 24 anos).
2. Entrou a **Fonte 5: a conversa**, que é dado pessoal, com onde mora, quem lê
   e quem apaga.
3. Os dados passaram a alimentar um **modelo de linguagem online**: o Python
   calcula os FATOS a partir das fontes 1 e 4, e o modelo só redige (seção
   "Como os dados chegam à IA").
4. A API passou a anotar cada chamada num **log** (`logs/api.jsonl`), e as
   chamadas reais guardadas como evidência ficam em `docs/evidencias/`.

O que mudou no TP4:

1. O texto integral passou a ser **lido por um modelo de linguagem local**
   (seção "Dados do analisador").
2. Entrou um **banco de provas rotulado à mão**, para medir e escolher o modelo.
3. O painel agora **pede os dados à API**; ler o disco direto virou plano B.
4. As notícias recebidas pela API saíram do repositório (`.gitignore`).

O que mudou no TP3, em relação ao TP2:

1. A Fonte 1 deixou de ser só a **manchete** e passou a incluir a **linha fina e
   o texto integral** de cada matéria — mudança que viabiliza o uso de LLMs na
   etapa seguinte.
2. Entrou uma **quarta via de entrada**: notícias enviadas por outros programas
   através da API própria do projeto.
3. A decisão sobre **raspagem de páginas dinâmicas** foi investigada e está
   registrada ao fim deste documento, com o motivo.

O fio condutor continua o mesmo: trazer o dado bruto de cada fonte e
transformá-lo numa tabela limpa que a interface — e agora também a API —
consome.

## Fonte 1 (implementada): notícias de emprego — Agência Brasil / EBC

A fonte coletada é a página da tag "emprego" da Agência Brasil, a agência pública
de notícias da EBC. A coleta acontece em **duas passadas**, por razões práticas
explicadas abaixo.

**Primeira passada — a listagem** (`src/coletar.py`). Extrai, com **Beautiful
Soup**, as matérias listadas na página de tag: título, editoria, ano-mês de
publicação e link, percorrendo as primeiras páginas da paginação.

**Segunda passada — o texto** (`src/coletar_textos.py`). Lê o CSV da primeira
passada e visita cada matéria, extraindo a linha fina e o corpo. É um script
separado por três motivos: leva cerca de 7 minutos (um `Crawl-delay` de 10s por
notícia); é **retomável**, pulando o que já está em disco; e mantém a primeira
passada rápida e independente.

- **Como chega:** HTML de página web (conteúdo não-estruturado). A coleta roda
  **separada da aplicação**: baixa a página, salva um *snapshot* do HTML bruto em
  `data/raw/` (prova do que a página dizia) e grava a tabela limpa em
  `data/processed/noticias_emprego.csv`.
- **Estratégia de extração — listagem:** filtrar os links cujo endereço contém o
  padrão das matérias (`/noticia/`), do qual também se derivam a editoria e o
  ano-mês. Esse padrão de URL é mais estável que classes CSS, que mudam sem aviso.
- **Estratégia de extração — linha fina:** lida da meta tag `og:description`.
  Todo gerenciador de conteúdo de notícia a preenche com a linha fina, porque é o
  que buscadores e redes sociais exibem no preview do link — o que a torna mais
  estável que qualquer classe CSS.
- **Estratégia de extração — corpo:** em vez de depender de um seletor fixo, o
  script pontua cada contêiner da página pela quantidade de texto que ele tem em
  parágrafos e escolhe, entre os melhores pontuados, o **mais específico** (o
  menor). Menu, rodapé, legenda de foto e blocos de "leia também" são removidos
  antes. É o mesmo princípio da listagem: apoiar-se na estrutura, não na
  decoração.
- **Onde o texto mora:** `data/processed/textos/`, um `.txt` por notícia, nomeado
  como `<ano_mes>_<slug>.txt`. O corpo **não** entra no CSV: tem milhares de
  caracteres e quebras de linha, e dentro de uma célula estouraria o arquivo. No
  CSV fica o caminho.
- **Permissão e licença:** o `robots.txt` foi verificado antes da coleta — a
  raspagem da tag é permitida; há `Crawl-delay: 10`, respeitado entre
  requisições, nas duas passadas. Conteúdo público da EBC sob licença Creative
  Commons, usado para fins acadêmicos, com a fonte citada na aplicação e um
  arquivo de procedência dentro da própria pasta `textos/`.
- **Uso no painel:** tabela de notícias filtrável; **nuvem de palavras** dos
  títulos (com lematização em português, unindo singular/plural e conjugações);
  e **estatísticas** por editoria e por mês.
- **Uso previsto (etapa seguinte):** o texto integral é a matéria-prima das
  tarefas de LLM — resumo, classificação de sentimento e perguntas e respostas.
- **Campos:** `titulo`, `editoria`, `ano_mes`, `url`, `resumo`, `arquivo_texto`.

## Fonte 2 (implementada): upload de CSV pelo usuário

A aplicação oferece um serviço de **upload** que permite ao usuário acrescentar
notícias além das coletadas. O arquivo enviado é validado na borda (precisa ser
UTF-8 e conter ao menos a coluna `titulo`) e, se válido, suas linhas se somam às
coletadas na tela.

- **Como chega:** CSV (estruturado), enviado pelo usuário na sessão.
- **Tratamento:** os dados enviados ficam no **estado de sessão** (privados
  daquele usuário), nunca no cache — dado de um usuário não deve vazar para
  outro. Cada linha carrega a **origem** ("enviada" × "coletada"), preservando a
  procedência. Há também **download** do recorte filtrado (com a origem), para o
  usuário levar exatamente o que está vendo.
- **Uso no painel:** complementa a tabela, a nuvem e as estatísticas. Na
  aplicação multipáginas, essa entrada vive na página "Dados e método".

## Fonte 3 (TP3): notícias recebidas pela API

A API do projeto (`api/main.py`) expõe uma rota `POST /noticias` que recebe uma
notícia em JSON enviada por **outro programa**. É a contrapartida programática do
upload: o mesmo tipo de dado, entrando sem que ninguém precise abrir uma tela.

- **Como chega:** JSON (estruturado), por requisição HTTP.
- **Validação:** o corpo é checado **por tipo**, antes de qualquer
  processamento — título com no mínimo 10 caracteres, `ano_mes` no formato
  `AAAA-MM`, limites de tamanho. O que não passa é recusado com código 422 e o
  motivo. Duplicatas (mesma URL já presente no acervo) são recusadas com 409.
- **Onde fica:** `data/processed/noticias_via_api.csv`, **separado** das
  coletadas, com o carimbo de hora do recebimento. Procedência não se mistura: no
  acervo, essas linhas aparecem com origem `via_api`. O arquivo está no
  `.gitignore`: o que pessoas e programas enviam não vai para o repositório.
- **Quem envia (TP4):** outros programas e o formulário da página "Dados e
  método", que só diz "gravada" quando a API confirma.
- **Princípio:** dado que vem de fora é **entrada não confiável**. A validação
  não é cortesia com o usuário, é defesa do acervo.

## Dados do analisador (novos no TP4)

### O modelo de linguagem — HuggingFace Hub
O modelo (`Qwen/Qwen2.5-1.5B-Instruct`) tem procedência e licença, como uma fonte.

- **Como chega:** ~3,1 GB de arquivos, baixados uma vez por
  `python -m src.baixar_modelo` para o cache do HuggingFace. Não vai para o Git.
- **Licença:** Apache 2.0, sem pedido de acesso.
- **Depois do download:** a API o carrega do disco, sem internet.

### O banco de provas — `data/analisador/banco_de_provas.csv`
- **O que é:** as 42 notícias do acervo, cada uma com o rótulo esperado nas
  duas tarefas (`tendencia`, `setor`) e uma `observacao` nos casos difíceis.
- **Como foi feito:** rotulado à mão **antes** de rodar qualquer modelo; guarda
  só o `id`, e o texto vem do acervo.
- **Distribuição:** 26 otimistas, 12 neutras e 4 pessimistas; 31 "mercado em
  geral" e 11 em cinco setores. Por isso "sempre a mais comum" entra na comparação.
- **Limites:** 42 itens (um acerto vale 2,4 pontos); rótulos de uma pessoa só.

### As previsões da bancada — `data/analisador/bancada_previsoes.csv`
Cada resposta de cada candidato a cada notícia (esperado, previsto,
confiança, segundos). Gerado por `python -m src.bancada`, junto com
`docs/bancada_resultados.md`.

### As análises — `POST /processar_texto`
- **Entrada (JSON):** `texto` (15 a 20.000 caracteres) e `tipo_analise`
  (`tendencia` ou `setor`). Campo a mais é recusado (422).
- **Saída (JSON, `ResultadoAnalise`):** a categoria (sempre da lista), a
  confiança, as alternativas, o trecho lido, quem analisou e quanto levou.
- **Não são gravadas:** a análise é refeita a cada pedido.

## Fonte 4 (implementada no TP5): desocupação dos jovens — PNAD Contínua / IBGE, via API

**Correção registrada.** Do TP2 ao TP4, a página "Dados e método" mostrava uma
lista de cinco setores **digitada no código**, com a legenda "amostra coletada
via API do IBGE". A legenda não era verdadeira, e os números (ocupados por
setor, todas as idades) nem eram sobre jovens. A lista foi removida. Agora a
página mostra o dado coletado ou, se a coleta não rodou, um aviso. Nunca um
número de exemplo no lugar de dado real.

- **O que é:** a taxa de desocupação por grupo de idade, da PNAD Contínua
  trimestral, tabela SIDRA **4094**. O painel usa três grupos: **14 a 17
  anos**, **18 a 24 anos** e o **total** (para comparar). Os níveis são
  Brasil, Grandes Regiões e UFs.
- **Por que esta tabela:** a meta 8.6 do ODS 8 é sobre jovens. A desocupação
  por idade é o indicador oficial mais direto disso que está na API, e mostra
  o tamanho do problema que o painel quer ajudar a atacar: no 3º trimestre
  de 2026, a desocupação foi de **11,1%** entre 18 e 24 anos e **21,5%**
  entre 14 e 17, contra **5,2%** no total. É cerca de 2 e 4 vezes a média.
- **Como chega:** JSON aninhado pela API de agregados do IBGE
  (`servicodados.ibge.gov.br/api/v3/agregados`), aberta e sem chave. O degrau
  da escada é o 1, uma API, então não há raspagem nem navegador.
- **Como é coletado:** `python -m src.coletar_ibge` roda à parte, como a coleta
  de notícias. Primeiro ele lê os **metadados** da tabela e descobre pelos
  nomes qual é a variável da taxa, qual é a classificação de idade e quais são
  os códigos dos grupos jovens. Se o IBGE mudar a tabela, o script para com uma
  frase dizendo o que não achou, em vez de gravar número errado.
- **Bruto (prova):** `data/raw/ibge_4094_<data>.json`, com a URL pedida, os
  códigos descobertos e a resposta inteira.
- **Limpo:** `data/processed/ibge_desocupacao_jovem.csv`, em formato longo
  (uma linha por período, local e grupo).

| Coluna | Tipo | Exemplo | O que é |
|---|---|---|---|
| `periodo` | texto | `2026-T2` | trimestre, legível |
| `periodo_codigo` | texto | `202602` | o código do IBGE (AAAA0T), ordenável |
| `nivel` | texto | `UF` | Brasil · Grande Região · UF |
| `localidade` | texto | `Bahia` | nome do lugar |
| `grupo_idade` | texto | `18 a 24 anos` | `14 a 17 anos` · `18 a 24 anos` · `total` |
| `taxa_desocupacao_pct` | número | `13.8` | % da força de trabalho do grupo que procurou e não achou trabalho |
| `tabela` | número | `4094` | a tabela SIDRA de origem |
| `coletado_em` | data-hora | `2026-11-24T10:02:11` | quando a coleta rodou |

- **Limpeza:** valores que o IBGE marca como ausentes (`...`, `-`, `X`) são
  **pulados**, não viram zero. Grupos de idade que o painel não usa não são
  pedidos.
- **Cuidado de leitura:** desocupado é quem procurou trabalho e não achou.
  Quem só estuda está fora da força de trabalho e não entra na taxa. Por isso
  a taxa não mede os jovens "nem-nem", só os que procuram emprego. Nas UFs há
  menos jovens entrevistados, então a estimativa oscila mais de um trimestre
  para outro que a do Brasil.
- **Volume:** 1.787 linhas, do 4º trimestre de 2021 ao 3º de 2026 (os últimos
  20 trimestres), coletadas em 25/11/2026. São menos que as 1.980 possíveis
  (20 trimestres × 33 lugares × 3 grupos) porque a API devolveu os dois
  primeiros trimestres (2021-T4 e 2022-T1) **só para o Brasil**, sem regiões
  nem UFs, e no último trimestre não veio um valor (14 a 17 anos no Amapá).
  Os valores que não vieram são pulados. Na prática, a série por região e por
  UF começa em 2022-T2.
- **Para que serve no painel:** na página "Dados e método", os números do
  último trimestre, a série no tempo e o ranking das UFs para 18 a 24 anos. No
  TP5, são os **fatos** que o Python calcula e o modelo lê na conversa.

## Fonte 5 (TP5): a conversa — dado pessoal

O que alguém pergunta na página Conversa é **dado pessoal** (pode revelar a
situação de quem pergunta). Tratamento:

| Pergunta | Resposta |
|---|---|
| **O que é guardado** | As perguntas e respostas, a memória usada, as notas (lugares e grupos citados) e o resumo, se houver. |
| **Onde mora** | Com a API: `data/conversas/<id>.json`, só na máquina onde a API roda, fora do Git (`.gitignore`). No link publicado (modo direto, sem API): só na sessão do navegador; some ao fechar a aba. |
| **Quem lê** | Só quem tem o id (32 caracteres aleatórios), guardado na sessão do navegador de quem conversa. Não há rota que liste conversas. |
| **Quem apaga** | A própria pessoa: botão "Apagar conversa" (ou `DELETE /conversa/{id}`). Sem lixeira. |
| **O que sai da máquina** | A pergunta, as últimas mensagens e os FATOS vão ao provedor do modelo (Groq; Gemini de reserva). A tela avisa para não escrever dado pessoal. O Groq não treina com os dados; o plano gratuito do Gemini, sim. Por isso ele é a reserva. |
| **O que o log guarda** | Rota, status, tempo, provedor, tokens e memória. **Nunca** o texto da pergunta, só o tamanho. |

Esquema de `data/conversas/<id>.json`:

| Campo | Tipo | O que é |
|---|---|---|
| `id` | texto | 32 hexadecimais aleatórios (conferidos antes de virar nome de arquivo) |
| `criada_em`, `atualizada_em` | data-hora | quando |
| `memoria` | texto | `inteira`, `janela`, `resumo` ou `notas` |
| `mensagens` | lista | `{papel, texto, quando, provedor?, numeros_sem_fonte?}` |
| `notas` | objeto | `{lugares, grupos, grupo_em_foco}`, anotados pelo Python |
| `resumo`, `resumo_ate` | texto, número | o resumo feito pelo modelo e até que mensagem ele vai |

## Dados derivados da IA

| Arquivo | Quem gera | O que é |
|---|---|---|
| `data/analisador/bancada_previsoes.csv` (e `_cpu`) | `python -m src.bancada` | A resposta de cada modelo local para cada notícia do banco de provas. |
| `docs/bancada_resultados.md` (e `_cpu`) | idem | Acertos, memória e tempo de cada candidato (GPU e CPU). |
| `data/teste_memoria/respostas.csv` | `python -m src.teste_memoria` | As 40 respostas do teste de 10 perguntas: memória, acerto, tokens, tempo, números sem fonte. |
| `docs/teste_memoria.md` | idem | A tabela que decide a memória padrão. |
| `docs/evidencias/*.md` | `python -m src.evidencias` | Chamadas reais à API, com o log de cada rodada. |

## Como os dados chegam à IA (a linhagem completa)

```
Agência Brasil ─raspagem─► data/raw/*.html ─► noticias_emprego.csv + textos/*.txt ─┐
                                                   │                                │
                           banco_de_provas.csv (rótulos à mão)                      │
                                                   │                                │
API do IBGE ─JSON─► data/raw/ibge_4094_*.json ─► ibge_desocupacao_jovem.csv ────────┤
                                                                                    ▼
                                                             src/fatos.py (o Python calcula)
                                                                                    │ FATOS
            pergunta ─► src/memoria.py (o que o modelo lê da conversa) ─────────────┤
                                                                                    ▼
                                                     modelo online (Groq / Gemini) redige
                                                                                    │
                                     src/checagem.py: número fora dos FATOS vira aviso
                                                                                    ▼
                                                    resposta na tela + data/conversas/
```

Os **FATOS** de cada pergunta têm sempre: a desocupação do Brasil nos 3 grupos
de idade no último trimestre (e um ano antes); a dos lugares em foco (os citados
na pergunta ou lembrados pela memória); as 3 UFs com maior e menor desocupação
de 18 a 24 anos; e o resumo das notícias (contagem por tendência e por setor, e
as 3 mais recentes). O modelo não lê os CSVs nem calcula: lê esse bloco, de algumas
centenas de tokens (o que cada pergunta leu, no total, está em
`docs/teste_memoria.md`).

## Decisão sobre raspagem de páginas dinâmicas (Selenium)

O enunciado desta etapa prevê o uso de **Selenium** para páginas dinâmicas, *se
necessário*. A decisão foi investigada e está registrada aqui.

**O critério.** Subir um degrau de complexidade apenas quando o de baixo não
serve: API documentada → HTML estático → JSON por trás da página → navegador
automatizado.

**A fonte atual está no degrau 2.** A Agência Brasil entrega a matéria pronta no
HTML enviado pelo servidor. Isso não é suposição: a coleta do texto integral,
feita nesta etapa, extraiu o corpo completo das matérias usando apenas
`requests` e Beautiful Soup. Não há conteúdo que só apareça após a execução de
JavaScript. Um navegador automatizado custaria segundos por página para receber
exatamente o mesmo HTML.

**A fonte que justificaria o degrau 4 foi examinada e descartada.** O candidato
natural era o Novo CAGED, que preencheria a lacuna de "vagas em aberto"
registrada no Project Charter desde o TP1. A divulgação oficial é um relatório
**Power BI publicado na web**. Esse formato é o pior caso possível para coleta:
os valores nunca existem no HTML — são desenhados na tela a partir de consultas
internas, e as tabelas são virtualizadas, materializando apenas as linhas
visíveis. Nem Beautiful Soup nem o `page_source` do Selenium alcançariam os
números. A alternativa seria reconstruir a consulta interna do Power BI, com
token assinado e corpo proprietário — fora do escopo e instável por natureza.

**A via viável para essa fonte não é raspagem.** Os microdados do Novo CAGED são
publicados como arquivo, por FTP, em texto delimitado por `;`. Isso é degrau 1:
download e leitura, sem raspagem alguma. O custo está no volume — cada arquivo
mensal traz uma linha por movimentação de emprego do país inteiro, exigindo um
passo de agregação por setor antes de chegar ao painel. Registrado como caminho
conhecido para a próxima iteração.

**Conclusão:** Selenium não foi adotado. A decisão não é por desconhecimento da
ferramenta, mas porque nenhuma fonte do projeto está no degrau que a exige — e a
única candidata que parecia estar revelou-se inacessível por qualquer forma de
raspagem, com uma porta melhor disponível um degrau abaixo.

## Fontes de ambição futura

- **Rendimento médio por setor (PNAD / IBGE):** mesmo formato JSON; enriqueceria
  a análise mostrando *quanto* cada setor paga, não só onde há vagas.
- **Saldo de vagas (Novo CAGED / MTE):** microdados por FTP, conforme descrito
  acima — mede o *fluxo* de criação de vagas, complementando o *estoque* da PNAD.

## Sobre os formatos dos dados

O projeto lida com estes formatos de entrada, e sempre faz o mesmo movimento em
direção a uma tabela limpa que a interface e a API consomem:

| Formato | Origem | Destino |
|---|---|---|
| **HTML** (não-estruturado) | raspagem das notícias | CSV + arquivos de texto |
| **CSV** (estruturado) | upload do usuário | usado direto, após validação |
| **JSON** (estruturado) | `POST /noticias` na API do projeto | CSV separado, após validação |
| **JSON** (estruturado) | `POST /processar_texto` | análise estruturada (não gravada) |
| **CSV** rotulado à mão | banco de provas | métricas da bancada (CSV + Markdown) |
| **JSON** (semi-estruturado) | API do IBGE | tabela estruturada (painel e FATOS da conversa) |
| **JSON** (estruturado) | `POST /conversa` | resposta + conversa em `data/conversas/` |

É esse caminho **bruto → estruturado** que organiza toda a parte de dados. O
destino é sempre `data/processed/`. Quem lê e grava ali para os outros é a
API; o painel pede a ela, e só lê o disco direto quando ela não responde.