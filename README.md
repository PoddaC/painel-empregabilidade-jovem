# Painel de Empregabilidade Jovem

Painel para ONGs de empregabilidade juvenil decidirem **para quais setores
capacitar jovens**, a partir de dados públicos de emprego e de notícias lidas
por um **modelo de linguagem que roda na própria máquina**.

Projeto de Bloco: IA Aplicada (Infnet) · ODS 8 — Trabalho Decente e
Crescimento Econômico, meta 8.6.

## Como as partes se ligam

```
Agência Brasil ──(raspagem, à parte)──┐
                                      ├──► data/processed/ ◄──lê── API (FastAPI) ◄──HTTP── Painel (Streamlit)
API do IBGE ─────(coleta, à parte)────┘          ▲                 │
                                                 │     modelo de linguagem local
                                     painel lê o IBGE    (carregado uma vez, sem internet)
```

- **Coleta** (`src/coletar.py`, `src/coletar_textos.py`, `src/coletar_ibge.py`) roda à parte e grava em `data/`.
- **API** (`api/`) é a única que lê e grava os dados, e é onde mora o modelo.
- **Painel** (`app.py`, `paginas/`) pede tudo à API. Se ela estiver desligada,
  o painel lê o disco direto e avisa na barra lateral; só o Analisador fica
  indisponível.

## Rodar na sua máquina

Com Python 3.11+ e, de preferência, um ambiente virtual:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-api.txt      # painel + API + modelo
```

**Placa de vídeo NVIDIA (opcional, recomendado):** no Windows, o
`pip install torch` comum instala a versão só de CPU. Para usar a GPU, instale
antes o torch com CUDA, usando o comando que o seletor de
<https://pytorch.org/get-started/locally/> mostrar. Para conferir, rode
`python -c "import torch; print(torch.cuda.is_available())"`, que deve
imprimir `True`.

Depois, na raiz do projeto:

```powershell
# 1. Os dados (já vêm no repositório; rode só para atualizar)
pip install -r requirements-coleta.txt
python -m src.coletar
python -m src.coletar_textos
python -m src.coletar_ibge      # desocupação dos jovens, pela API do IBGE

# 2. O modelo: uma vez, com internet (~3,1 GB)
python -m src.baixar_modelo

# 3. A API, no terminal 1 (sem --reload: cada reinício recarrega o modelo)
uvicorn api.main:app            # http://127.0.0.1:8000/docs

# 4. O painel, no terminal 2
streamlit run app.py            # http://localhost:8501
```

Depois do passo 2, a API e o painel funcionam **sem internet**.

## O modelo de linguagem

| | |
|---|---|
| Modelo | `Qwen/Qwen2.5-1.5B-Instruct` (Apache 2.0) |
| O que faz | Classifica uma notícia em **tendência do emprego** (otimista, pessimista, neutra) ou **setor da economia** |
| Download | ~3,1 GB, para o cache do HuggingFace (`~/.cache/huggingface`, ou a pasta em `HF_HOME`) |
| Memória | ~3,1 GB na GPU (float16) · ~6,2 GB de RAM na CPU (float32) |
| Tempo na GPU | 0,07 s por análise na RTX 4060 Ti (0,26 s de ponta a ponta no painel) · carga de 6 a 15 s |
| Tempo na CPU | 14,4 s por análise (mediana; p95 16,4 s) · carga de 7,3 s · pico de 7,4 GB de RAM (float32), medidos na bancada ([`docs/bancada_resultados_cpu.md`](docs/bancada_resultados_cpu.md)) · ~16 s de ponta a ponta pela API ([`docs/evidencias/cpu.md`](docs/evidencias/cpu.md)). Acerta o mesmo que na GPU (29 e 25 de 42). |
| Por que este | [`docs/escolha_do_modelo.md`](docs/escolha_do_modelo.md), com a bancada em [`docs/bancada_resultados.md`](docs/bancada_resultados.md) |

**Modelos testados e descartados:**

| Modelo | Até onde foi | Por que não foi usado |
|---|---|---|
| mDeBERTa (zero-shot) | Medido | Abaixo do chute nas duas tarefas (19 e 16 de 42) |
| Qwen2.5-0.5B | Medido | Respondeu a mesma opção (A) nas 42 notícias |
| Qwen3-1.7B | Medido | Entende a pergunta, mas erra com convicção sem o modo de "pensar" (17 e 3 de 42) |
| Tucano 2 1.5B / 3.7B | Não baixados | Usam o Qwen3 como base; o 3.7B não cabe em 8 GB sem 4-bit |
| Granite 4.1 3B | Download interrompido | ~6,8 GB, no limite da placa de 8 GB; ficaria lento |

O escolhido, Qwen2.5-1.5B, empatou com as regras em tendência (29 de 42) e acertou 29 de 30 notícias otimistas ou pessimistas. Em setor, nenhum candidato superou o chute "mercado em geral", por isso a análise de setor aparece no painel como experimental.

Para refazer a medição dos candidatos:

```powershell
python -m src.baixar_modelo --bancada   # baixa os candidatos medidos (~9 GB)
python -m src.baixar_modelo --so qwen15,qwen3_17   # ou só alguns
python -m src.bancada                   # mede e reescreve docs/bancada_resultados.md

# a mesma medição na CPU, em arquivos _cpu (não apaga a da GPU)
$env:PAINEL_DISPOSITIVO="cpu"; python -m src.bancada --so regras,qwen15
Remove-Item Env:PAINEL_DISPOSITIVO
```

Configuração por variáveis de ambiente (todas opcionais):

| Variável | Padrão | Para quê |
|---|---|---|
| `PAINEL_MODELO` | `Qwen/Qwen2.5-1.5B-Instruct` | Trocar de modelo (qualquer apelido da bancada, pelo nome no Hub) |
| `PAINEL_MOTOR` | `llm` | `regras` sobe a API sem modelo nenhum (palavras-chave), declarado na resposta |
| `PAINEL_DISPOSITIVO` | `auto` | Forçar `cpu` ou `cuda` |
| `PAINEL_LIMITE_S` | `60` | Segundos máximos por análise antes do 504 |
| `PAINEL_API_URL` | `http://127.0.0.1:8000` | Onde o painel procura a API |
| `PAINEL_LOG` | `logs/api.jsonl` | Onde a API anota cada chamada (vazio = desligado) |

## A Conversa (TP5): memória conversacional

A página **Conversa (IA)** responde perguntas sobre os dados do painel e
lembra do que já foi dito ("E em São Paulo?", "voltando ao primeiro estado").

```
pergunta ─► memória escolhida (o que o modelo lê da conversa)  src/memoria.py
        ─► FATOS calculados pelo Python (IBGE + notícias)      src/fatos.py
        ─► modelo online redige a resposta                      src/llm_api.py
        ─► conferência: número fora dos fatos vira aviso        src/checagem.py
        ─► conversa gravada na API, por id                      api/conversas.py
```

- **Quem responde:** Groq (`openai/gpt-oss-120b`), com o Google Gemini
  (`gemini-3.8-flash`) de reserva. O Qwen local continua no Analisador:
  escolher uma categoria ele faz bem; escrever uma conversa em português, não.
- **As chaves** ficam no `.env` (fora do Git):
  ```
  GROQ_API_KEY=gsk_...
  GEMINI_API_KEY=...
  ```
  Sem chave, a Conversa responde 503 com o motivo; o resto do painel segue.
- **As quatro memórias** (Aula 17–18): inteira, janela, resumo e **notas**
  (padrão). Qual mantém o contexto, e a que custo, quem decide é o teste:
  ```powershell
  python -m src.teste_memoria          # ~10 min; grava docs/teste_memoria.md
  ```
- **Os prompts** estão em [`prompts/`](prompts/), cada um com a justificativa.
- **A conversa é dado pessoal:** mora em `data/conversas/<id>.json` (fora do
  Git), só na máquina da API; o botão "Apagar conversa" (ou
  `DELETE /conversa/{id}`) apaga de vez. A pergunta vai ao provedor externo.

| Variável | Padrão | Para quê |
|---|---|---|
| `PAINEL_LLM_ORDEM` | `groq,gemini` | Ordem dos provedores (o primeiro que responder) |
| `PAINEL_GROQ_MODELO` | `openai/gpt-oss-120b` | Modelo do Groq |
| `PAINEL_GEMINI_MODELO` | `gemini-3.8-flash` | Modelo do Gemini |
| `PAINEL_LLM_LIMITE_S` | `30` | Segundos por chamada, sem repetição automática |

## A API

Documentação interativa em `/docs`. Toda rota declara o que devolve
(*response model*), e todo erro tem um status e uma frase:

| Rota | O que faz | Erros possíveis |
|---|---|---|
| `POST /processar_texto` | Analisa um texto com o modelo local | 422 texto fora do contrato · 503 modelo não carregado · 504 tempo esgotado |
| `GET /saude` | A API e o modelo estão de pé? Quais provedores da Conversa têm chave? | — |
| `POST /conversa` | Pergunta ao assistente, com memória | 422 pergunta ou memória inválida · 404 conversa inexistente · 503 nenhum modelo online respondeu |
| `GET /conversa/{id}` | A conversa guardada | 404 |
| `DELETE /conversa/{id}` | Apaga a conversa (204) | 404 |
| `GET /noticias` | Lista, com filtros `editoria`, `busca` e `limite` | 422 parâmetro inválido · 503 coleta não rodou |
| `GET /noticias/{id}` | Uma notícia, com o texto integral | 404 id inexistente |
| `GET /noticias/estatisticas` | Contagens por editoria, mês e origem | 503 coleta não rodou |
| `GET /editorias` | As editorias do acervo | 503 coleta não rodou |
| `POST /noticias` | Grava uma notícia nova | 422 campos inválidos ou a mais · 409 já existe |

Qualquer erro não previsto vira um **500 em JSON, com um código** que também
aparece no terminal da API, junto com o traceback.

**O diário da API.** Cada chamada vira uma linha JSON em `logs/api.jsonl`
(fora do repositório): hora, rota, status, segundos e, na análise, o motor, a
tarefa, a categoria e a confiança. O texto enviado **não** é gravado, só o
tamanho dele.

**Evidências de chamadas reais.** Com a API ligada, `python -m src.evidencias --nome gpu`
analisa uma notícia real do acervo pela API e grava, em `docs/evidencias/`, as
respostas completas e as linhas do log daquela rodada. As evidências guardadas:

| Arquivo | Como a API estava | O que mostra |
|---|---|---|
| [`gpu.md`](docs/evidencias/gpu.md) | normal (GPU) | 200 com categoria, confiança e alternativas |
| [`cpu.md`](docs/evidencias/cpu.md) | `PAINEL_DISPOSITIVO=cpu` | 200, e o tempo de ponta a ponta na CPU |
| [`erro_503.md`](docs/evidencias/erro_503.md) | `PAINEL_MODELO=nao-existe` | 503 com o motivo; `/saude` diz por quê |
| [`erro_504.md`](docs/evidencias/erro_504.md) | `PAINEL_LIMITE_S=0.01` | 504, tempo esgotado |

**O que significa cada aviso no painel:**

- *"Não há API respondendo"*: ligue a API (passo 3).
- *"O modelo não carregou: não foi encontrado nesta máquina"*: rode
  `python -m src.baixar_modelo`.
- *"A análise passou de 60 s"*: a máquina está lenta para o modelo. Use a GPU
  ou o plano B sem modelo (`PAINEL_MOTOR=regras`).

## Testes

```powershell
pip install -r requirements-dev.txt
pytest
```

Os testes não precisam do modelo baixado. Os da API usam o motor de regras e
motores falsos para provocar cada status (200, 201, 404, 409, 422, 500, 503 e
504), e conferem que o log grava cada chamada sem o texto. O coletor do IBGE é
testado com respostas no formato da API, sem internet. Os do analisador usam um modelo minúsculo, gerado na hora, para
exercitar o caminho do código. Quanto o modelo de verdade acerta, quem mede é
a bancada.

## Estrutura

```
app.py                  roteador do painel (st.navigation)
comum.py                o que as páginas compartilham (pede o acervo à API)
paginas/                Início · Notícias · Análise · Analisador (IA) · Conversa (IA) · Dados e método
prompts/                os prompts da Conversa, com a justificativa (LEIA-ME.md)
api/
  main.py               monta a API: lifespan, routers, rede de segurança do 500
  modelos.py            os contratos de entrada e de saída (Pydantic)
  motor.py              carrega o modelo uma vez; guarda o motivo se falhar
  erros.py              o 500 com código
  registro.py           o diário: uma linha JSON por chamada em logs/api.jsonl
  conversas.py          onde a conversa mora: um arquivo por id, com trava
  rotas/conversa.py     POST/GET/DELETE /conversa
  rotas/noticias.py     GET/POST de notícias
  rotas/analise.py      POST /processar_texto, GET /saude
src/
  coletar.py            1ª passada da coleta (listagem)
  coletar_textos.py     2ª passada (texto integral)
  coletar_ibge.py       desocupação por grupo de idade, pela API do IBGE (SIDRA 4094)
  data_access.py        leitura do disco
  tarefas.py            as perguntas e as categorias que o modelo responde
  analisador_llm.py     o modelo de linguagem local (pontua as categorias)
  baixar_modelo.py      o download, como passo à parte
  bancada.py            mede os candidatos no banco de provas
  motor_regras.py       linha de base: palavras-chave
  motor_zeroshot.py     candidato zero-shot (só na bancada)
  cliente_api.py        o painel falando com a API (lê pelo status)
  evidencias.py         grava chamadas reais à API em docs/evidencias/
  fatos.py              o que o modelo da Conversa lê: números calculados + entidades
  memoria.py            as 4 memórias (inteira, janela, resumo, notas)
  llm_api.py            Groq e Gemini, com reserva e tempo limite
  checagem.py           números da resposta que não estão nos fatos
  teste_memoria.py      o teste de 10 perguntas
data/
  raw/                  o que cada fonte devolveu, sem mexer (HTML, JSON do IBGE)
  processed/            notícias (CSV), textos (.txt) e desocupação dos jovens (CSV)
  analisador/           banco de provas rotulado e previsões da bancada
docs/                   TDSP: Project Charter, Data Summary, Relatório de Modelos, Relatório Final;
                        escolha do modelo, bancada (GPU e CPU), teste de memória
  evidencias/           chamadas reais à API, com o log de cada rodada
tests/                  pytest
```

## Publicação

O painel publicado no Streamlit Cloud instala só o `requirements.txt` (sem
`torch`). Lá não há API, então:

- **Do dado ao insight, Notícias, Análise e Dados** leem os arquivos do
  repositório e funcionam normalmente.
- **Conversa** funciona no **modo direto**: o painel chama o modelo online sem
  passar pela API, com a mesma regra (`src/conversa.py`). A conversa fica só na
  sessão do navegador. As chaves vão nos *secrets* do app (Settings → Secrets),
  no formato TOML, na raiz:
  ```toml
  GROQ_API_KEY = "gsk_..."
  GEMINI_API_KEY = "..."
  ```
- **Analisador** depende do modelo local e roda só na máquina de quem instala o
  projeto; no link publicado, mostra o aviso.

Nunca suba o `.env` nem o `.streamlit/secrets.toml`: os dois estão no `.gitignore`.
