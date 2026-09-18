# Data Summary Report (primeiro esboço) — Painel de Empregabilidade Jovem

Este é o primeiro esboço do Data Summary Report do projeto, elaborado ainda na
fase de Aquisição de Dados do TDSP. Aqui irei mapear, antes de comecar
a coleta, de onde os dados vão vir, em que formato eles chegam e para que
cada um serve dentro do painel. 

## Fonte principal: ocupação por setor (PNAD Contínua / IBGE)

A espinha dorsal do projeto é a PNAD Contínua, do IBGE, acessada pela API pública
de dados (servicodados / SIDRA). Dela vamos extrair o número de pessoas ocupadas
por grupamento de atividade e, principalmente, como esse número varia ao longo do
tempo. Esse é o indicador central do painel: é a variação da ocupação de cada
setor que nos diz quais estão de fato absorvendo trabalhadores e quais estão
encolhendo, a informação que a ONG precisa para decidir onde qualificar os jovens.

O dado chega em JSON, ou seja, é semi-estruturado: tem uma estrutura definida,
mas não é uma tabela pronta. Parte do trabalho técnico da próxima etapa vai ser
justamente converter esse JSON aninhado em uma tabela (uma lista de dicionários
em Python) para conseguir comparar os setores. A API é aberta e gratuita, não
exige autenticação, o que simplifica bastante a coleta. Nesta etapa ainda
usamos uma amostra manual desses dados; a coleta ao vivo via API entra na Etapa 2.

## Fonte complementar: rendimento médio por setor (PNAD Contínua / IBGE)

Da mesma PNAD Contínua, e pela mesma API, dá para puxar o rendimento médio mensal
por grupamento de atividade. Esse dado também é semi-estruturado (JSON). A intenção
é usá-lo para enriquecer a análise: não basta mostrar onde há vagas surgindo, é útil
mostrar também quanto cada setor paga, para que a decisão de qualificação leve em
conta a qualidade do emprego, e não só a quantidade. Fica previsto para uma iteração
futura, depois que a coleta da ocupação estiver funcionando.

## Fonte de ambição futura: saldo de vagas (Novo CAGED / MTE)

Por fim, registro uma fonte que ainda não entra agora, mas que faz parte do plano.
O Novo CAGED, do Ministério do Trabalho, publica o saldo de empregos formais
(admissões menos desligamentos) por setor, em formato estruturado (CSV). Enquanto a
PNAD mostra o estoque de quem está ocupado, o CAGED mostra o fluxo, ou seja, a
criação líquida de vagas — o que chega mais perto de medir a tal "falta de mão de
obra". Deixo essa fonte mapeada desde já porque ela é o caminho natural para
aprofundar o projeto mais adiante, possivelmente na fase de coleta por outras vias.

## Sobre o formato dos dados

Vale reforçar o fio condutor: a maior parte do que consumimos vem em JSON, um
formato semi-estruturado típico de APIs, e o projeto sempre faz o mesmo movimento —
transformar esse JSON em uma tabela estruturada para poder analisar e visualizar.
É o caminho semi-estruturado → estruturado que organiza toda a parte de dados.