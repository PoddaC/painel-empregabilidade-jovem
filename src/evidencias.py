"""
evidencias.py - grava a prova de chamadas REAIS a API que esta no ar.

Com a API ligada (uvicorn api.main:app), em outro terminal:

    python -m src.evidencias --nome gpu

Faz, contra a API de verdade:
    GET  /saude
    POST /processar_texto  (tendencia) com uma noticia real do acervo
    POST /processar_texto  (setor)     com a mesma noticia

e grava em docs/evidencias/:
    <nome>.json   pedido resumido + status + resposta completa + tempo medido
                  pelo cliente + as linhas do logs/api.jsonl desta rodada
    <nome>.md     o mesmo, legivel, para colar no relatorio

Para os casos de erro, suba a API de outro jeito antes (PowerShell):
    $env:PAINEL_MODELO="nao-existe";   uvicorn api.main:app  ->  --nome erro_503
    $env:PAINEL_LIMITE_S="0.01";       uvicorn api.main:app  ->  --nome erro_504
    $env:PAINEL_DISPOSITIVO="cpu";     uvicorn api.main:app  ->  --nome cpu
(Remove-Item Env:PAINEL_MODELO etc. para voltar ao normal.)
"""

import argparse
import json
import sys
import time
from datetime import datetime

import requests

from api.registro import caminho_do_log
from src.cliente_api import API_URL
from src.data_access import BASE

PASTA = BASE / "docs" / "evidencias"


def chamar(metodo, rota, corpo=None):
    inicio = time.perf_counter()
    try:
        r = requests.request(metodo, API_URL + rota, json=corpo, timeout=180)
    except requests.RequestException as e:
        sys.exit(f"[erro] a API nao respondeu em {API_URL} ({type(e).__name__}). "
                 "Ela esta ligada? uvicorn api.main:app")
    seg = round(time.perf_counter() - inicio, 3)
    try:
        resposta = r.json()
    except ValueError:
        resposta = r.text
    pedido = None
    if corpo:
        pedido = {k: (f"<{len(v)} caracteres>" if k == "texto" else v) for k, v in corpo.items()}
    print(f"  {metodo} {rota} -> {r.status_code} em {seg} s")
    return {"metodo": metodo, "rota": rota, "pedido": pedido, "status": r.status_code,
            "segundos_no_cliente": seg, "resposta": resposta}


def noticia_real():
    """Uma noticia do acervo COM texto integral, pedida a propria API."""
    lista = requests.get(API_URL + "/noticias", params={"limite": 50}, timeout=30).json()
    for n in lista.get("noticias", []):
        if n.get("tem_texto"):
            completa = requests.get(f"{API_URL}/noticias/{n['id']}", timeout=30).json()
            texto = "\n\n".join(x for x in (completa.get("titulo"), completa.get("resumo"),
                                             completa.get("texto")) if x)
            return completa["titulo"], texto[:19000]  # o contrato aceita ate 20.000
    sys.exit("[erro] nenhuma noticia com texto no acervo. Rode python -m src.coletar_textos.")


def linhas_do_log(desde):
    caminho = caminho_do_log()
    if not caminho or not caminho.exists():
        return []
    linhas = []
    for bruta in caminho.read_text(encoding="utf-8").splitlines():
        try:
            l = json.loads(bruta)
        except ValueError:
            continue
        if l.get("quando", "") >= desde:
            linhas.append(l)
    return linhas


def em_markdown(nome, titulo, chamadas, log):
    md = [f"# Evidência: {nome}", "",
          f"Gravada em {datetime.now():%d/%m/%Y %H:%M:%S} por `python -m src.evidencias`, "
          f"contra a API em `{API_URL}`.", ""]
    if titulo:
        md += [f"Notícia usada (real, do acervo): **{titulo}**", ""]
    md += ["| Chamada | Status | Segundos (cliente) | Resultado |", "|---|---|---|---|"]
    for c in chamadas:
        r = c["resposta"] if isinstance(c["resposta"], dict) else {}
        if c["status"] == 200 and "categoria" in r:
            res = f"{r['rotulo']} · confiança {r['confianca']:.2f} · {r['motor']} · {r['segundos']} s no modelo"
        elif c["status"] == 200:
            res = f"modelo carregado: {r.get('modelo_carregado')} · {r.get('motor') or r.get('motivo')}"
        else:
            res = str(r.get("detail", c["resposta"]))[:160]
        tipo = (c["pedido"] or {}).get("tipo_analise", "")
        md.append(f"| `{c['metodo']} {c['rota']}` {tipo} | {c['status']} | {c['segundos_no_cliente']} | {res} |")
    md += ["", "## Linhas do log da API (`logs/api.jsonl`) desta rodada", "", "```json"]
    md += [json.dumps(l, ensure_ascii=False) for l in log] or ["(log vazio ou desligado)"]
    md += ["```", "", "## Respostas completas", "", "```json",
           json.dumps(chamadas, ensure_ascii=False, indent=2), "```"]
    return "\n".join(md)


def main():
    p = argparse.ArgumentParser(description="Grava evidencias de chamadas reais a API.")
    p.add_argument("--nome", required=True, help="ex.: gpu, cpu, erro_503, erro_504")
    args = p.parse_args()

    desde = datetime.now().isoformat(timespec="milliseconds")
    print(f"API: {API_URL}")
    chamadas = [chamar("GET", "/saude")]
    titulo, texto = noticia_real()
    for tipo in ("tendencia", "setor"):
        chamadas.append(chamar("POST", "/processar_texto", {"texto": texto, "tipo_analise": tipo}))
    time.sleep(0.2)  # a ultima linha do log e escrita depois da resposta sair
    log = linhas_do_log(desde)

    PASTA.mkdir(parents=True, exist_ok=True)
    (PASTA / f"{args.nome}.json").write_text(
        json.dumps({"api": API_URL, "noticia": titulo, "chamadas": chamadas, "log": log},
                   ensure_ascii=False, indent=2), encoding="utf-8")
    (PASTA / f"{args.nome}.md").write_text(em_markdown(args.nome, titulo, chamadas, log), encoding="utf-8")
    print(f"Gravado: docs/evidencias/{args.nome}.json e .md")


if __name__ == "__main__":
    main()
