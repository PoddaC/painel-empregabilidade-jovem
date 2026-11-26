# Escolha do modelo de linguagem — Painel de Empregabilidade Jovem

> A escolha do modelo pelos critérios de **desempenho**, **custo computacional
> local** e **acessibilidade local**. Os números vêm da bancada
> (`python -m src.bancada`); o relatório completo está em
> [`bancada_resultados.md`](bancada_resultados.md).

## 1. O que o modelo precisa fazer

O painel responde a uma pergunta: **quais setores estão em expansão e devem
ser priorizados na qualificação de jovens?** Os dados quantitativos (PNAD)
dizem *onde* há ocupação. As notícias dizem o que está *acontecendo*, mas
são 42 textos longos que ninguém da ONG tem tempo de ler um a um.

O modelo lê cada notícia e responde a **duas perguntas fechadas**:

| Tarefa | Pergunta | Categorias |
|---|---|---|
| `tendencia` | O que a notícia indica sobre o emprego? | otimista · pessimista · neutra |
| `setor` | De qual setor da economia ela fala? | indústria · construção · comércio · serviços · agropecuária · setor público · mercado em geral |

Cruzadas, as duas respostas produzem o sinal que a ONG procura: *setores com
notícias de expansão*. As definições de cada categoria estão em
`src/tarefas.py` e vão escritas no próprio pedido ao modelo.

Três exigências saem do enunciado e do projeto:

- **Português.** O texto é jornalismo brasileiro, com siglas (Caged, PNAD,
  CNI) e jargão econômico.
- **Resposta dentro do contrato.** A API promete que a categoria é *sempre*
  uma das da lista (`ResultadoAnalise`). Um modelo que escreve livremente pode
  devolver qualquer coisa.
- **Local e offline.** Nada de chave de API nem conexão com a nuvem depois do
  download.

## 2. Critérios — declarados antes de medir

| Critério | O que se exige | Como se mede |
|---|---|---|
| **Desempenho** | Acertar mais que as duas linhas de base: *sempre a categoria mais comum* e *regras de palavras-chave*. | Acertos, **erros** e **silêncios** no banco de provas, contados à parte. |
| **Custo computacional local** | Caber na máquina do projeto (16 GB de RAM, RTX 4060 Ti com 8 GB, CPU Intel de 16 núcleos lógicos, Windows 11) **com o painel e o navegador abertos**; até ~2 s por análise na GPU; subida da API em menos de 30 s. | Memória dos pesos, pico de memória na GPU, tempo de carga e segundos por análise. |
| **Acessibilidade local** | Licença aberta que permita uso por uma ONG; download sem pedido de acesso (*gated*); roda com `transformers` + `torch`; funciona offline depois de baixado. | A ficha (*model card*) no HuggingFace Hub, lida **antes** do download. |

**Regra de decisão**, escrita antes de rodar a bancada: entre os candidatos
que passam em custo e acessibilidade, vence o de **mais acertos somados nas
duas tarefas**. Em empate (diferença de até 2 acertos), vence o **mais leve**.

## 3. Os candidatos — a ficha antes de baixar

O enunciado cita três famílias: GPT (gera texto), BERT (codifica e
classifica) e T5 (texto para texto). A ficha elimina vários candidatos sem
que seja preciso baixar nada:

| Modelo | Família | Parâmetros | Ficha | Situação |
|---|---|---|---|---|
| `facebook/bart-large-mnli` | BART (zero-shot) | 407 mi | o zero-shot mais baixado, mas só em inglês | ✗ descartado: idioma |
| `neuralmind/bert-base-portuguese-cased` (BERTimbau) | BERT | 110 mi | português, mas a tarefa é *fill-mask*: classificar exigiria treinar com exemplos rotulados que o projeto não tem | ✗ descartado: tarefa |
| `google/gemma-3-1b-it`, `meta-llama/Llama-3.2-1B-Instruct` | GPT | ~1 bi | *gated*: exigem aceitar termos e token de acesso | ✗ descartado: acessibilidade |
| `Qwen/Qwen2.5-3B-Instruct` | GPT | 3,1 bi | licença própria (*Qwen Research*), não Apache | ✗ descartado: licença |
| `MoritzLaurer/mDeBERTa-v3-base-xnli-multilingual-nli-2mil7` | BERT (zero-shot NLI) | 279 mi | multilíngue, com português; MIT | ✓ medido |
| `Qwen/Qwen2.5-0.5B-Instruct` | GPT (instruct) | 494 mi | multilíngue; Apache 2.0; não *gated* | ✓ medido |
| `Qwen/Qwen2.5-1.5B-Instruct` | GPT (instruct) | 1,54 bi | multilíngue; Apache 2.0; não *gated* | ✓ medido |
| `Qwen/Qwen3-1.7B` | GPT (instruct, com modo de "pensar") | 1,7 bi | geração mais nova; Apache 2.0 | ✓ medido (rodada 2) |

**A conta de padaria do custo** (parâmetros × bytes por número), feita
antes do download:

| Modelo | float32 (CPU) | float16 (GPU) | Cabe na RTX 4060 (8 GB)? |
|---|---|---|---|
| mDeBERTa | 1,1 GB | 0,56 GB | sim |
| Qwen2.5-0.5B | 2,0 GB | 1,0 GB | sim |
| Qwen2.5-1.5B | 6,2 GB | 3,1 GB | sim, com folga |
| Qwen3-1.7B | 6,8 GB | 3,4 GB | sim |

Na CPU, o float16 é lento. Por isso o projeto usa **float16 na GPU e float32
na CPU**, escolhido sozinho pelo dispositivo.

## 4. O banco de provas

`data/analisador/banco_de_provas.csv`: as **42 notícias reais do acervo**,
rotuladas à mão nas duas tarefas **antes** de qualquer modelo rodar. A
coluna `observacao` marca os casos difíceis, por exemplo um saldo positivo
de vagas que é "o menor desde 2020". O modelo recebe o que o painel manda:
título, linha fina e texto integral. Ele lê os primeiros ~1.500 caracteres
(pirâmide invertida).

Os limites do banco, ditos antes dos números:

- **42 é pouco.** Um acerto vale 2,4 pontos percentuais.
- **É desbalanceado, como o acervo.** 26 das 42 são otimistas, porque o
  mercado de trabalho de 2024–2026 bateu recordes. Em setor, 31 das 42 são
  "mercado em geral". Por isso a linha de base *sempre a mais comum* já
  acerta 26 e 31, e é ela que um modelo precisa bater, não o zero.
- **Os rótulos são de uma pessoa só**, a mesma que escreveu as definições.

## 5. Resultados

Medidos em 16/11/2026 na máquina do projeto (Windows 11, RTX 4060 Ti 8 GB,
torch 2.15 com CUDA), em float16 na GPU. Relatório completo, com cada erro de
cada candidato: [`bancada_resultados.md`](bancada_resultados.md).

| Candidato | Tendência (certos · erros · calados) | Setor (certos · erros · calados) | Memória dos pesos | Pico na GPU | Carga | s por análise |
|---|---|---|---|---|---|---|
| sempre a mais comum | 26 · 16 · 0 | **31** · 11 · 0 | — | — | — | — |
| regras (palavras-chave) | **29** · 11 · 2 | 27 · 10 · 5 | — | — | — | 0,001 |
| mDeBERTa (zero-shot) | 19 · 23 · 0 | 16 · 26 · 0 | 532 MB | 593 MB | 2,1 s | 0,11 |
| Qwen2.5-0.5B | 26 · 16 · 0 | 4 · 38 · 0 | 942 MB | 1,2 GB | 2,3 s | 0,03 |
| **Qwen2.5-1.5B** | **29** · 13 · 0 | 25 · 17 · 0 | 2,9 GB | 3,2 GB | 6,3 s | 0,07 |
| Qwen3-1.7B | 17 · 25 · 0 | 3 · 39 · 0 | 3,3 GB | 3,6 GB | 13,1 s | 0,08 |

**O que a tabela não mostra sozinha:**

- **O Qwen2.5-1.5B separa notícia boa de ruim quase sem errar.** Nas 30
  notícias rotuladas como otimistas ou pessimistas, acertou **29**. Os 13 erros
  de tendência são, quase todos, notícias que rotulei como **neutras**: ele
  *nunca* escolheu "neutra", e tende a ler debates (jornada 6×1, FGTS) como
  pessimistas.
- **As regras chegam a 29 por outro caminho.** Dizem "otimista" em 34 das 42
  notícias, num acervo em que a maioria é otimista. E foram escritas por quem
  já tinha visto estas manchetes, o que as favorece neste banco e não em
  notícias novas.
- **Os dois modelos menores e o mais novo respondem sempre a mesma letra.** O
  Qwen2.5-0.5B escolheu a opção A nas 42 notícias. O Qwen3-1.7B escolheu
  "serviços" em 41 e "pessimista" em 28, com confiança perto de 100%. Um
  diagnóstico (`python -m src.espiar_modelo`) confirmou que o método vale para
  ele: 100% da aposta cai nas letras. Ele entende a pergunta e erra com
  convicção. Essa família foi treinada para "pensar" antes de responder, e sem
  esse modo, que custaria segundos e texto livre por análise, o 1.7B chuta.
- **Setor: nenhum candidato bateu "sempre mercado em geral".** 31 das 42
  notícias falam do mercado como um todo. Os modelos atribuem setor a notícias
  agregadas (o Caged vira "comércio", a taxa de desemprego vira "serviços").

**Errar × calar.** As regras calam quando não acham palavra-chave (7 vezes).
Os modelos sempre respondem e, por isso, erram mais. As duas contagens
aparecem separadas na tabela.

## 6. A decisão

**Escolhido: `Qwen/Qwen2.5-1.5B-Instruct`, em float16 na GPU (float32 na
CPU), pontuando as categorias em vez de escrever.**

**A regra declarada na seção 2 não foi cumprida por nenhum candidato.** Ela
exigia bater as duas linhas de base. O Qwen2.5-1.5B empata com as regras em
tendência (29) e perde para "sempre a mais comum" em setor (25 contra 31). A
escolha abaixo é uma exceção, registrada como tal:

- **Desempenho:** é o único modelo que chega ao nível das regras em
  tendência, e o faz lendo o texto: 29 de 30 entre otimistas e pessimistas.
  As regras dependem de palavras escolhidas olhando estas manchetes, e calam
  diante de um texto sem elas. Para **setor**, o modelo **não é
  recomendado** neste acervo: a análise continua disponível, mas a página
  avisa que ela não superou o chute "mercado em geral".
- **Custo computacional local:** 3,1 GB de download, 2,9 GB de pesos, 3,2 GB de
  pico na GPU (cabe na placa de 8 GB com folga), 6 a 15 s para carregar,
  **0,07 s por análise** na RTX 4060 Ti (0,26 s de ponta a ponta no painel).
  **Na CPU** (float32, 16 núcleos lógicos): **14,4 s por análise**
  (mediana; p95 16,4 s), 7,3 s para carregar e 7,4 GB de pico de RAM
  ([`bancada_resultados_cpu.md`](bancada_resultados_cpu.md)); pela API, de
  ponta a ponta, ~16 s ([`evidencias/cpu.md`](evidencias/cpu.md)). A seção 2
  só declarou limite de tempo **na GPU**; o número da CPU fica registrado sem
  mudar o critério depois de medir. Na CPU o modelo acerta o mesmo (29 e 25
  de 42), mas cada análise leva cerca de 200 vezes o tempo da GPU. Sem GPU,
  o Analisador continua usável para uma notícia de cada vez, dentro do
  limite de 60 s da API, mas não para analisar o acervo inteiro de uma vez.
- **Acessibilidade:** Apache 2.0, sem *gated*, `transformers` + `torch`,
  offline depois de `python -m src.baixar_modelo`.

**O que pesou contra:** o ponto cego em "neutra" e a fraqueza em setor. Os
dois aparecem na página do Analisador: as probabilidades de todas as
categorias, o trecho lido e o aviso de que a **confiança não é a chance de
acerto**. Entre os 30 erros do escolhido, 6 vieram com confiança ≥ 0,9.

As outras tentativas, e por que ficaram de fora, estão no `README.md`.

**Plano B:** o motor de regras, com `PAINEL_MOTOR=regras`. Mede o mesmo em
tendência, não exige GPU nem download, e a resposta diz que foi ele que
analisou.

## 7. Como o modelo entrou na API

| Decisão | Por quê |
|---|---|
| **Pontuar, não escrever.** As opções viram letras (A, B, C…), e se lê a nota que o modelo dá a cada letra como *próxima palavra*; o `softmax` dessas notas vira a probabilidade de cada categoria. | A resposta é sempre uma categoria da lista: o contrato `ResultadoAnalise` nunca quebra. Um modelo que escreve pode devolver qualquer palavra. |
| **O prompt traz a definição de cada categoria.** | Com só os nomes, modelos pequenos confundem as categorias. |
| **Carregar uma vez, no `lifespan`.** | Carregar a cada pedido custa segundos por análise. Com o `lifespan`, a carga acontece só quando a API sobe. |
| **Falhar em pedaços.** O carregamento nunca levanta exceção; se o modelo não sobe, o motivo fica guardado. | A API sobe do mesmo jeito: notícias respondem 200, `/processar_texto` responde **503** com o motivo, e `/saude` mostra o estado. |
| **`local_files_only=True` + `src/baixar_modelo.py`.** | O modelo está no disco ou não está. Sem isso, a subida tentaria baixar gigabytes e ficaria muda por um minuto. |
| **Rota `def`, um trabalhador, limite de tempo.** | Rodar o modelo é calcular, não esperar: numa `async def` a API inteira travaria. Um trabalhador só evita que dois pedidos dividam a GPU. Passou de `PAINEL_LIMITE_S` (60 s), a resposta é **504** com a explicação. |
| **GPU se houver; o tipo dos números conforme o dispositivo.** | float16 na GPU (metade da memória), float32 na CPU (onde float16 é lento). |
| **O painel não carrega o modelo.** | O Streamlit pede a análise à API. O app publicado no Streamlit Cloud segue sem `torch`. |
