# Project Charter — Painel de Empregabilidade Jovem

> Versão final (TP5). Documento vivo, revisto ao fim de cada etapa; a
> seção 12 registra o que mudou em cada uma.

## 1. Contexto e Problema de Negócio
Organizações de empregabilidade juvenil (ONGs, programas de primeiro emprego)
precisam decidir **onde** e **para o quê** qualificar jovens, mas costumam
decidir sem dado: sem saber em que estados o jovem mais procura emprego e não
acha, nem o que o mercado está sinalizando. O resultado são programas
desalinhados da necessidade real.

**Perguntas de negócio:**
1. *Onde o desemprego jovem é maior?* Em que estados, e em que faixa de idade
   (14 a 17 ou 18 a 24 anos), a desocupação está mais alta, e para onde ela vai?
2. *O que o mercado está sinalizando?* O que as notícias de emprego dizem: o tom
   (otimista ou pessimista) e os setores em pauta.
3. *Como quem decide chega a essas respostas sem ser analista?* Perguntando em
   português, a um assistente que responde **só com os dados do painel** e lembra
   do que já foi perguntado.

## 2. Escopo
**Dentro do escopo:**
- Desocupação por grupo de idade (14 a 17, 18 a 24 e total), por **UF**, Grande
  Região e Brasil, nos últimos 20 trimestres: API do IBGE (PNAD Contínua).
- Notícias de emprego da Agência Brasil, com texto integral (raspagem).
- Classificação das notícias por um modelo de linguagem **local** (tendência e setor).
- Um assistente de **conversa com memória**, por um modelo de linguagem **online**.
- Painel Streamlit (pessoas) e API FastAPI (programas).

**Fora do escopo:**
- Vagas em aberto e saldo de empregos (Novo CAGED): investigado e documentado
  no Data Summary; exige microdados por FTP.
- Recorte por município (a PNAD não tem amostra para isso).
- Medição do impacto dos cursos de uma ONG (exige dados internos).

## 3. Objetivos e Indicadores de Sucesso (KPIs)

| KPI | Meta | Resultado (TP5) |
|---|---|---|
| **Dado real e automático** | Coleta por API (IBGE) e raspagem (notícias), sem número digitado à mão | ✓ 1.787 linhas do IBGE e 42 notícias com texto integral |
| **Recorte de jovens** | Taxa de 14 a 17 e de 18 a 24 anos por UF, com o último trimestre | ✓ 27 UFs, 2022-T2 a 2026-T3 |
| **Acesso programático** | Todo o acervo e as análises por endpoint documentado | ✓ todas as rotas documentadas em `/docs` |
| **Análise por IA local** | Superar as linhas de base no banco de provas, em até ~2 s por análise | Em parte: 0,07 s (GPU); empata em tendência; setor experimental |
| **Funcionamento offline** | O Analisador roda sem internet após um download | ✓ |
| **Memória conversacional** | Acertar a 10ª pergunta do teste, que volta à 1ª | ✓ notas 10/10 (janela 9/10) |
| **Custo da conversa** | Memória padrão sem chamada extra, lendo menos que a conversa inteira | ✓ notas: 1.386 tokens na 10ª, contra 1.951 da inteira |
| **Sem número inventado** | Nenhuma resposta com número fora dos fatos | ✓ 0 em 40 respostas do teste |
| **Tempo de resposta** | Conversa em até ~5 s por pergunta | ✓ ~1 s (Groq) |
| **Simplicidade** | Achar o principal insight em até 3 cliques | ✓ Início → "Do dado ao insight" |

## 4. ODS e ESG
**ODS 8 — Trabalho Decente e Crescimento Econômico.**
- **Meta 8.6:** reduzir a proporção de jovens sem emprego, educação ou formação.
  O painel mede o pedaço "procura e não acha" (a desocupação) e mostra onde ele é
  maior.
- **Meta 8.5:** emprego pleno e produtivo, inclusive para jovens.
- **Meta 8.b:** estratégia para o emprego jovem. O painel é uma ferramenta de
  apoio a essa estratégia em organizações da sociedade civil.

**ESG:** o projeto serve ao **S** (social). Uma empresa ou fundação que financia
programas de primeiro emprego (investimento social, relatórios de impacto) usa o
painel para justificar **onde** investe, com dado público e conferível. A
governança (**G**) aparece no próprio produto: fonte e período em toda tela,
números conferidos antes de chegar ao usuário, e a conversa tratada como dado
pessoal (seção 9).

## 5. Público-Alvo (Stakeholders)
- **Quem usa:** coordenação de programas e analistas de ONGs de empregabilidade.
- **Quem decide:** direção da ONG ou financiador (inclusive área de ESG de
  empresas) que aprova abrir um programa e onde.
- **Beneficiário final:** jovens de 14 a 24 anos em busca de trabalho.
- **Quem integra:** equipes técnicas que consomem os dados pela API.

## 6. Fontes de Dados
Detalhamento completo em `docs/data_summary_report.md`.
- **Desocupação por idade:** IBGE, PNAD Contínua, tabela 4094, pela **API** de agregados.
- **Notícias de emprego:** Agência Brasil (Creative Commons), por **raspagem**, com texto integral.
- **Rótulos à mão:** 42 notícias rotuladas (tendência e setor), o gabarito dos modelos.
- **Entradas externas:** upload de CSV no painel e `POST /noticias` na API.
- **Dados derivados:** classificações do modelo local, respostas da conversa, resultados da bancada e do teste de memória.
- **A conversa:** dado pessoal, guardado na API por id (seção 9).

## 7. Por que estes dados, esta IA e esta engenharia de prompts

**Os dados respondem às perguntas de negócio.** A desocupação por idade e UF
responde à pergunta 1 diretamente: no 3º trimestre de 2026, 11,1% para 18 a 24
anos e 21,5% para 14 a 17, contra 5,2% no total; de 4,7% (Santa Catarina) a
18,3% (Sergipe) entre os estados, para 18 a 24 anos. As notícias, com texto
integral, respondem à pergunta 2: o que está em pauta e com que tom.

**Cada modelo foi escolhido pela tarefa, e por medição.**
- **Classificar uma notícia** (escolher uma entre poucas categorias) é tarefa
  pequena: o **Qwen2.5-1.5B local** faz em 0,07 s, sem internet e sem custo,
  escolhido numa bancada de 4 modelos e 2 linhas de base (`docs/escolha_do_modelo.md`).
- **Conversar** (redigir em português, seguir regras, manter o contexto) é tarefa
  de modelo maior: o **gpt-oss-120b pelo Groq**, com o **Gemini** de reserva.
  Na CPU, o Qwen local levaria ~15 s só para classificar; para escrever, seria
  pior. O provedor online foi escolhido por teste: em 25/11/2026 o Gemini
  devolveu 503 em todas as tentativas e o Groq respondeu em ~1 s.
- **Qual memória** a conversa usa também foi medido: o teste de 10 perguntas
  (`docs/teste_memoria.md`).

**A engenharia de prompts é o que mantém a IA presa aos dados.** O Python calcula
os números e os entrega ao modelo como **FATOS**; o prompt
(`prompts/conversa_sistema.txt`) manda usar só esses números, citar lugar,
grupo e trimestre, e dizer "o painel não tem esse dado" quando for o caso.
Depois, o Python **confere**: número da resposta que não está nos fatos vira
aviso na tela. Cada regra do prompt está justificada em `prompts/LEIA-ME.md`.

**É ciência de dados, não só um chat.** A IA é a última etapa de um ciclo
mensurável: coleta → limpeza → modelos escolhidos por medição → resposta
conferida contra a fonte. A página "Do dado ao insight" mostra esse ciclo com
os números de cada etapa.

## 8. Riscos e Mitigações
- **O modelo da conversa inventa um número:** só recebe números calculados
  (FATOS), o prompt proíbe calcular, e a resposta é conferida; o que escapar
  aparece com aviso. No teste, 0 de 40 respostas teve número sem fonte.
- **Provedor online fora do ar ou no limite gratuito:** evidência real: o Gemini
  deu 503 ("alta demanda") em todas as tentativas de 25/11/2026, e sua
  biblioteca repetiu a chamada por mais de 10 minutos. Mitigação: dois
  provedores em ordem, 30 s por chamada sem repetição automática, e 503 com o
  motivo. O resto do painel segue funcionando.
- **A memória esquece o contexto:** medido. A janela esqueceu o primeiro estado;
  a padrão é a de notas, que acertou 10/10.
- **Privacidade da conversa:** a pergunta vai a um provedor externo (aviso na
  tela). O Groq não treina com os dados; o plano gratuito do Gemini, sim (por
  isso ele é a reserva, não o principal). A conversa mora só na máquina da API,
  fora do Git, e pode ser apagada.
- **Chaves de API vazarem:** ficam no `.env`, fora do Git; no deploy, nos
  *secrets* do Streamlit Cloud.
- **O modelo local erra, às vezes com confiança alta:** a página mostra o trecho
  lido e as probabilidades; o setor está marcado como experimental.
- **O modelo local não carrega ou é lento:** a API sobe mesmo assim (503 com o
  motivo); limite de tempo (504); plano B por regras (`PAINEL_MOTOR=regras`).
- **API do IBGE fora do ar ou tabela alterada:** coleta à parte; o painel lê o
  último CSV; se a tabela mudar, o coletor para com uma frase em vez de gravar
  número errado. Nunca se mostra número de exemplo como se fosse dado.
- **Estrutura do site de notícias mudar:** a extração se apoia no padrão de URL;
  a coleta fica isolada em `src/`.
- **Entrada externa não confiável** (upload, `POST /noticias`, pergunta): validada
  por tipo e tamanho na borda; o id de conversa é conferido antes de virar nome
  de arquivo.

## 9. Arquitetura
Cinco peças, com um dono para cada escrita:

1. **Coleta** (`src/coletar*.py`): roda à parte. Grava em `data/raw/` (bruto) e `data/processed/`.
2. **API** (`api/`): lê e grava o acervo para os outros; tem o modelo local
   carregado uma vez; conversa com o modelo online; guarda as conversas em
   `data/conversas/<id>.json`, com trava; anota cada chamada em `logs/api.jsonl`
   (nunca o texto da pergunta).
3. **Painel** (`app.py` + `paginas/`): cliente da API. Páginas: Início · Do dado
   ao insight · Notícias · Análise · Analisador (IA) · Conversa (IA) · Dados e método.
4. **Modelo local** (Qwen2.5-1.5B): no disco, só a API acessa.
5. **Modelo online** (Groq, Gemini): chamado pela API, com as chaves do `.env`.
   No Streamlit Cloud, onde a API não roda, o painel o chama direto (**modo
   direto**), com as chaves nos *secrets* e a **mesma regra** (`src/conversa.py`);
   lá a conversa fica só na sessão do navegador.

**A conversa, passo a passo:** pergunta → a memória escolhe o que o modelo lê →
o Python calcula os FATOS → o modelo online redige → o Python confere os números
→ a conversa é gravada.

## 10. Metodologia
Projeto conduzido pelo **TDSP** (Team Data Science Process), com o **CRISP-DM**
como base conceitual. Artefatos em `docs/`:

| Artefato TDSP | Arquivo |
|---|---|
| Project Charter | `docs/project_charter.md` (este) |
| Data Summary Report (fontes, dicionários, linhagem) | `docs/data_summary_report.md` |
| Model Report | `docs/relatorio_de_modelos.md` (com `escolha_do_modelo.md`, `bancada_resultados*.md` e `teste_memoria.md`) |
| Exit Report | `docs/relatorio_final.md` |
| Evidências de funcionamento | `docs/evidencias/` |

## 11. Critério de pronto
Painel e API rodando, testes passando (`pytest`), dados coletados das fontes reais,
modelos escolhidos por medição com o resultado registrado, e a documentação
acima descrevendo o que está no código.

## 12. Evolução
v1 com amostra manual (TP1) → v2 com raspagem, cache e upload (TP2) → v3
multipáginas, com texto integral e API própria (TP3) → v4 com modelo de
linguagem local e o painel como cliente da API (TP4) → **v5 com o IBGE pela
API e recorte de jovens, o assistente de conversa com memória, a conferência
dos números e a página do ciclo de dados (TP5).**
