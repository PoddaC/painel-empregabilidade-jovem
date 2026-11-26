# Relatório de Modelos (TDSP: Model Report) — Painel de Empregabilidade Jovem

> Os dois usos de modelo de linguagem do projeto, o que cada um faz, como foi
> escolhido e como foi medido. Os detalhes ficam nos relatórios gerados pelo
> código, sempre citados aqui.

## Visão geral

| | Analisador (TP4) | Conversa (TP5) |
|---|---|---|
| **Tarefa** | Classificar uma notícia: tendência e setor | Responder perguntas sobre os dados, com memória |
| **Tipo de saída** | Uma categoria entre poucas (a letra de maior probabilidade) | Texto livre em português, até 4 frases |
| **Modelo** | Qwen2.5-1.5B-Instruct, **local** | gpt-oss-120b pelo **Groq** (Gemini 3.8 Flash de reserva), **online** |
| **Onde roda** | Na API, carregado uma vez; GPU (float16) ou CPU (float32) | Provedor externo, chamado pela API |
| **Escolhido por** | Bancada: 4 modelos e 2 linhas de base, 42 notícias rotuladas à mão | Teste de provedores (disponibilidade e tempo) e teste de 10 perguntas (memória) |
| **Relatórios** | `escolha_do_modelo.md`, `bancada_resultados.md`, `bancada_resultados_cpu.md` | `teste_memoria.md` |

**Por que dois modelos, e não um:** escolher uma categoria é tarefa pequena,
que um modelo de 1,5B faz bem, rápido, sem internet e sem custo. Redigir uma
conversa em português, seguindo regras e mantendo o contexto, é tarefa de
modelo grande, que não cabe na máquina do projeto (na CPU, o Qwen leva ~15 s
só para classificar). Cada modelo fica onde é bom.

## 1. Analisador (modelo local)

**Método:** em vez de gerar texto, o modelo recebe a pergunta, as categorias
(com definição) e a notícia, e a API lê a probabilidade de cada letra de
resposta. Fica com a mais provável. A confiança volta junto, com o aviso de que
não é chance de acerto.

**Resultado (42 notícias):**

| Candidato | Tendência | Setor | s por análise |
|---|---|---|---|
| Sempre a categoria mais comum (base) | 26 | 31 | 0 |
| Regras (palavras-chave) | 29 | 27 | 0,001 |
| mDeBERTa (zero-shot) | 19 | 16 | 0,105 |
| Qwen2.5-0.5B | 26 | 4 | 0,034 |
| **Qwen2.5-1.5B** | **29** | **25** | **0,074 (GPU) · 14,4 (CPU)** |
| Qwen3-1.7B | 17 | 3 | 0,081 |

**Decisão:** Qwen2.5-1.5B. Empata com as regras em tendência, mas lendo o texto:
acerta 29 de 30 notícias otimistas ou pessimistas. **Limitações declaradas:**
nunca responde "neutra", e em setor ninguém supera a linha de base, por isso o
setor está marcado como **experimental** na tela. Na CPU, acerta o mesmo, mas
leva ~200 vezes mais tempo.

## 2. Conversa (modelo online)

**Método:** o modelo **não calcula**. A cada pergunta:
1. A **memória** escolhida decide o que ele lê da conversa (`src/memoria.py`).
2. O **Python calcula os FATOS** dos lugares em foco, a partir do CSV do IBGE e
   das notícias (`src/fatos.py`).
3. O **prompt** (`prompts/conversa_sistema.txt`) manda usar só esses números e
   citar lugar, grupo e trimestre.
4. O modelo redige, com temperatura 0,2.
5. O **Python confere**: número com vírgula ou % que não está nos FATOS vira
   aviso (`src/checagem.py`).

**Escolha do provedor** (25/11/2026, mesma pergunta, 30 s de limite):

| Provedor · modelo | Resultado |
|---|---|
| Groq · openai/gpt-oss-120b | 200 em 1,2 s, resposta correta |
| Gemini · 3.8, 3.7, 3.6 e 3.5 Flash | 503 "alta demanda" nos quatro, em dois horários |

Groq como principal; Gemini como reserva automática. A biblioteca do Google
repetiu um 503 por mais de 10 minutos, por isso as chamadas são feitas sem
repetição automática e com limite de 30 s.

**Escolha da memória:** o teste de 10 perguntas (`docs/teste_memoria.md`).
As perguntas 2 a 10 dependem da conversa ("E em São Paulo?"); a 10ª volta ao
primeiro estado. Cada resposta é corrigida pelo Python, com o mesmo CSV que o
painel lê.

| Memória | Acertos | 10ª | Tokens lidos: 1ª → 10ª | Chamadas a mais |
|---|---|---|---|---|
| **notas** | **10/10** | ✓ | 868 → 1.386 | 0 |
| inteira | 10/10 | ✓ | 833 → 1.951 | 0 |
| janela | 9/10 | ✗ | 833 → 1.196 | 0 |
| resumo | 10/10 | ✓ | 833 → 1.674 | 6 |

**Decisão:** a memória de **notas** é a padrão. Entre as que acertam tudo, é a
que lê menos e não paga chamada extra. A janela é mais barata, mas esqueceu a
Bahia e respondeu sobre Sergipe na 10ª. Nenhuma das 40 respostas teve número
sem fonte. Tempo médio: ~1 s por resposta.

**Limitações declaradas:**
- O teste tem 10 perguntas e uma sequência; outra conversa pode expor outros
  erros. O teste é reprodutível (`python -m src.teste_memoria`) para ser rodado de novo.
- A checagem pega taxas e percentuais inventados, não frases erradas sem número
  (como dizer "subiu" quando caiu). Mitigação: os FATOS já trazem o sentido
  ("caiu 4,8 pontos percentuais") escrito pelo Python.
- O plano gratuito do Groq limita os tokens por minuto; uso intenso recebe 429,
  que vira a mensagem "tente em instantes".

## 3. Engenharia de prompts

| Prompt | Onde | O que garante |
|---|---|---|
| Classificação (TP4) | `src/analisador_llm.py`, `src/tarefas.py` | Categorias com definição; saída por probabilidade da letra, sem texto livre |
| Conversa | `prompts/conversa_sistema.txt` | Só números dos FATOS; lugar, grupo e trimestre; "não tenho esse dado"; escopo |
| Resumo | `prompts/conversa_resumo.txt` | Guardar lugares, grupos e números na ordem (memória de resumo) |

A justificativa de cada regra está em `prompts/LEIA-ME.md`.
