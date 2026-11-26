# Evidência: erro_504

Gravada em 25/11/2026 19:09:00 por `python -m src.evidencias`, contra a API em `http://127.0.0.1:8000`.

Notícia usada (real, do acervo): **Cai diferença entre homens e mulheres no acesso ao emprego formal**

| Chamada | Status | Segundos (cliente) | Resultado |
|---|---|---|---|
| `GET /saude`  | 200 | 0.008 | modelo carregado: True · Qwen/Qwen2.5-1.5B-Instruct · float16 · cuda |
| `POST /processar_texto` tendencia | 504 | 0.027 | A analise passou de 0 s e foi abandonada. O modelo pode estar ocupado com outro pedido ou a maquina esta lenta para ele - tente de novo em instantes ou com um t |
| `POST /processar_texto` setor | 504 | 0.031 | A analise passou de 0 s e foi abandonada. O modelo pode estar ocupado com outro pedido ou a maquina esta lenta para ele - tente de novo em instantes ou com um t |

## Linhas do log da API (`logs/api.jsonl`) desta rodada

```json
{"quando": "2026-11-25T19:09:00.031", "metodo": "GET", "rota": "/saude", "status": 200, "segundos": 0.001}
{"quando": "2026-11-25T19:09:00.055", "metodo": "GET", "rota": "/noticias", "status": 200, "segundos": 0.004}
{"quando": "2026-11-25T19:09:00.086", "metodo": "GET", "rota": "/noticias/2026-08_cai-diferenca-entre-homens-e-mulheres-no-acesso-ao-emprego-f", "status": 200, "segundos": 0.003}
{"quando": "2026-11-25T19:09:00.113", "metodo": "POST", "rota": "/processar_texto", "status": 504, "segundos": 0.022, "tipo_analise": "tendencia", "caracteres": 3072, "motor": "Qwen/Qwen2.5-1.5B-Instruct · float16 · cuda"}
{"quando": "2026-11-25T19:09:00.144", "metodo": "POST", "rota": "/processar_texto", "status": 504, "segundos": 0.026, "tipo_analise": "setor", "caracteres": 3072, "motor": "Qwen/Qwen2.5-1.5B-Instruct · float16 · cuda"}
```

## Respostas completas

```json
[
  {
    "metodo": "GET",
    "rota": "/saude",
    "pedido": null,
    "status": 200,
    "segundos_no_cliente": 0.008,
    "resposta": {
      "ok": true,
      "modelo_carregado": true,
      "motor": "Qwen/Qwen2.5-1.5B-Instruct · float16 · cuda",
      "motivo": null
    }
  },
  {
    "metodo": "POST",
    "rota": "/processar_texto",
    "pedido": {
      "texto": "<3072 caracteres>",
      "tipo_analise": "tendencia"
    },
    "status": 504,
    "segundos_no_cliente": 0.027,
    "resposta": {
      "detail": "A analise passou de 0 s e foi abandonada. O modelo pode estar ocupado com outro pedido ou a maquina esta lenta para ele - tente de novo em instantes ou com um texto menor."
    }
  },
  {
    "metodo": "POST",
    "rota": "/processar_texto",
    "pedido": {
      "texto": "<3072 caracteres>",
      "tipo_analise": "setor"
    },
    "status": 504,
    "segundos_no_cliente": 0.031,
    "resposta": {
      "detail": "A analise passou de 0 s e foi abandonada. O modelo pode estar ocupado com outro pedido ou a maquina esta lenta para ele - tente de novo em instantes ou com um texto menor."
    }
  }
]
```