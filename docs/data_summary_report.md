# Data Summary Report — Painel de Empregabilidade Jovem

> Versão da Etapa 5–6 (TP3). Mapeia de onde vêm os dados, em que formato chegam
> e para que cada um serve dentro do painel.

O que mudou nesta etapa, em relação ao TP2:

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

## Fonte 3 (nova nesta etapa): notícias recebidas pela API

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
  acervo, essas linhas aparecem com origem `via_api`.
- **Princípio:** dado que vem de fora é **entrada não confiável**. A validação
  não é cortesia com o usuário, é defesa do acervo.

## Fonte 4 (amostra; coleta futura): ocupação por setor — PNAD Contínua / IBGE

A fonte quantitativa que originou o projeto é a PNAD Contínua, do IBGE, com o
número de pessoas ocupadas por grupamento de atividade e sua variação no tempo —
o indicador que aponta quais setores absorvem trabalhadores.

- **Como chega:** JSON (semi-estruturado) pela API pública (servicodados/SIDRA),
  aberta e sem autenticação. O trabalho técnico é converter esse JSON aninhado
  numa tabela para comparar os setores.
- **Status:** exibida como **amostra** de referência na página "Dados e método";
  a coleta ao vivo via API segue prevista.

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

O projeto lida com quatro formatos de entrada, e sempre faz o mesmo movimento em
direção a uma tabela limpa que a interface e a API consomem:

| Formato | Origem | Destino |
|---|---|---|
| **HTML** (não-estruturado) | raspagem das notícias | CSV + arquivos de texto |
| **CSV** (estruturado) | upload do usuário | usado direto, após validação |
| **JSON** (estruturado) | `POST` na API do projeto | CSV separado, após validação |
| **JSON** (semi-estruturado) | API do IBGE | tabela estruturada (uso futuro) |

É esse caminho **bruto → estruturado** que organiza toda a parte de dados. E o
destino é sempre o mesmo lugar: `data/processed/`, de onde tanto a aplicação
quanto a API leem, lado a lado.