# Painel de Empregabilidade Jovem

Painel para ONGs de empregabilidade juvenil decidirem **para quais setores
capacitar jovens**, a partir de dados públicos de emprego e de notícias lidas
por um **modelo de linguagem que roda na própria máquina**.

Projeto de Bloco: IA Aplicada (Infnet) · ODS 8 — Trabalho Decente e
Crescimento Econômico, meta 8.6.

## Como as partes se ligam

```
Agência Brasil ──(coleta, à parte)──► data/processed/ ◄──lê── API (FastAPI) ◄──HTTP── Painel (Streamlit)
                                                              │
                                              modelo de linguagem local
                                              (carregado uma vez, sem internet)
```

- **Coleta** (`src/coletar.py`, `src/coletar_textos.py`) roda à parte e grava em `data/`.
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
| Tempo | 0,07 s por análise na RTX 4060 Ti (0,26 s de ponta a ponta no painel) · carga de 6 a 15 s · na CPU, ~3 s (não medido aqui) |
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
```

Configuração por variáveis de ambiente (todas opcionais):

| Variável | Padrão | Para quê |
|---|---|---|
| `PAINEL_MODELO` | `Qwen/Qwen2.5-1.5B-Instruct` | Trocar de modelo (qualquer apelido da bancada, pelo nome no Hub) |
| `PAINEL_MOTOR` | `llm` | `regras` sobe a API sem modelo nenhum (palavras-chave), declarado na resposta |
| `PAINEL_DISPOSITIVO` | `auto` | Forçar `cpu` ou `cuda` |
| `PAINEL_LIMITE_S` | `60` | Segundos máximos por análise antes do 504 |
| `PAINEL_API_URL` | `http://127.0.0.1:8000` | Onde o painel procura a API |

## A API

Documentação interativa em `/docs`. Toda rota declara o que devolve
(*response model*), e todo erro tem um status e uma frase:

| Rota | O que faz | Erros possíveis |
|---|---|---|
| `POST /processar_texto` | Analisa um texto com o modelo local | 422 texto fora do contrato · 503 modelo não carregado · 504 tempo esgotado |
| `GET /saude` | A API e o modelo estão de pé? | — |
| `GET /noticias` | Lista, com filtros `editoria`, `busca` e `limite` | 422 parâmetro inválido · 503 coleta não rodou |
| `GET /noticias/{id}` | Uma notícia, com o texto integral | 404 id inexistente |
| `GET /noticias/estatisticas` | Contagens por editoria, mês e origem | 503 coleta não rodou |
| `GET /editorias` | As editorias do acervo | 503 coleta não rodou |
| `POST /noticias` | Grava uma notícia nova | 422 campos inválidos ou a mais · 409 já existe |

Qualquer erro não previsto vira um **500 em JSON, com um código** que também
aparece no terminal da API, junto com o traceback.

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
504). Os do analisador usam um modelo minúsculo, gerado na hora, para
exercitar o caminho do código. Quanto o modelo de verdade acerta, quem mede é
a bancada.

## Estrutura

```
app.py                  roteador do painel (st.navigation)
comum.py                o que as páginas compartilham (pede o acervo à API)
paginas/                Início · Notícias · Análise · Analisador (IA) · Dados e método
api/
  main.py               monta a API: lifespan, routers, rede de segurança do 500
  modelos.py            os contratos de entrada e de saída (Pydantic)
  motor.py              carrega o modelo uma vez; guarda o motivo se falhar
  erros.py              o 500 com código
  rotas/noticias.py     GET/POST de notícias
  rotas/analise.py      POST /processar_texto, GET /saude
src/
  coletar.py            1ª passada da coleta (listagem)
  coletar_textos.py     2ª passada (texto integral)
  data_access.py        leitura do disco
  tarefas.py            as perguntas e as categorias que o modelo responde
  analisador_llm.py     o modelo de linguagem local (pontua as categorias)
  baixar_modelo.py      o download, como passo à parte
  bancada.py            mede os candidatos no banco de provas
  motor_regras.py       linha de base: palavras-chave
  motor_zeroshot.py     candidato zero-shot (só na bancada)
  cliente_api.py        o painel falando com a API (lê pelo status)
data/
  processed/            notícias (CSV) e textos (.txt)
  analisador/           banco de provas rotulado e previsões da bancada
docs/                   Project Charter, Data Summary, escolha do modelo, bancada
tests/                  pytest
```

## Publicação

O painel publicado no Streamlit Cloud instala só o `requirements.txt` (sem
`torch`). Lá não há API, então ele lê o disco e mostra o aviso. O
Analisador, que depende do modelo local, roda na máquina de quem instala o
projeto.
