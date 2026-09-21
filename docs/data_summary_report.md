# Data Summary Report — Painel de Empregabilidade Jovem
 
> Versão da Etapa 2 (TP2). Mapeia de onde vêm os dados, em que formato chegam
> e para que cada um serve dentro do painel.
 
Nesta etapa o projeto passou a ter uma fonte **coletada ao vivo** (raspagem de
notícias) e um canal de **entrada pelo usuário** (upload de CSV), além da fonte
de ocupação por setor que já vinha do TP1. O fio condutor de dados continua o
mesmo: trazer o dado bruto de cada fonte e transformá-lo numa tabela limpa
(estruturada) que a interface consome.
 
## Fonte 1 (implementada): notícias de emprego — Agência Brasil / EBC
 
A fonte coletada nesta etapa é a página da tag "emprego" da Agência Brasil, a
agência pública de notícias da EBC. Dela extraímos, com **Beautiful Soup**, as
matérias listadas: título, editoria, ano-mês de publicação e link.
 
- **Como chega:** HTML de página web (conteúdo não-estruturado). A coleta roda
  **separada da aplicação** (`src/coletar.py`): baixa a página, salva um
  *snapshot* do HTML bruto em `data/raw/` (prova do que a página dizia) e grava
  a tabela limpa em `data/processed/noticias_emprego.csv`.
- **Estratégia de extração:** filtrar os links cujo endereço contém o padrão das
  matérias (`/noticia/`), do qual também se derivam a editoria e o ano-mês. Esse
  padrão de URL é mais estável que classes CSS, que mudam sem aviso.
- **Permissão:** o `robots.txt` foi verificado antes da coleta — a raspagem da
  tag é permitida; há `Crawl-delay: 10`, respeitado entre requisições. Conteúdo
  público da EBC, uso educacional, com a fonte citada na aplicação.
- **Uso no painel:** tabela de notícias filtrável; **nuvem de palavras** dos
  títulos (com lematização em português, unindo singular/plural e conjugações);
  e **estatísticas** por editoria e por mês.
- **Campos:** `titulo`, `editoria`, `ano_mes`, `url`.
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
- **Uso no painel:** complementa a tabela, a nuvem e as estatísticas.
## Fonte 3 (amostra; coleta futura): ocupação por setor — PNAD Contínua / IBGE
 
A fonte quantitativa que originou o projeto é a PNAD Contínua, do IBGE, com o
número de pessoas ocupadas por grupamento de atividade e sua variação no tempo —
o indicador que aponta quais setores absorvem trabalhadores.
 
- **Como chega:** JSON (semi-estruturado) pela API pública (servicodados/SIDRA),
  aberta e sem autenticação. O trabalho técnico é converter esse JSON aninhado
  numa tabela para comparar os setores.
- **Status:** nesta etapa é exibida como **amostra** de referência; a coleta ao
  vivo via API fica prevista para a próxima iteração.
## Fontes de ambição futura
 
- **Rendimento médio por setor (PNAD / IBGE):** mesmo formato JSON; enriqueceria
  a análise mostrando *quanto* cada setor paga, não só onde há vagas.
- **Saldo de vagas (Novo CAGED / MTE):** CSV estruturado com admissões menos
  desligamentos por setor — mede o *fluxo* de criação de vagas, complementando o
  *estoque* da PNAD.
## Sobre os formatos dos dados
 
O projeto passou a lidar com três formatos, e sempre faz o mesmo movimento em
direção a uma tabela limpa que a interface consome:
- **HTML** (não-estruturado) da raspagem de notícias → CSV estruturado;
- **CSV** (estruturado) do upload do usuário → usado direto, após validação;
- **JSON** (semi-estruturado) da API do IBGE → tabela estruturada (uso futuro).
É esse caminho **bruto → estruturado** que organiza toda a parte de dados.