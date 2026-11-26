"""
teste_memoria.py - o teste de 10 perguntas: qual memoria mantem o contexto?

    python -m src.teste_memoria                  # as 4 memorias (~10 min, por causa da pausa)
    python -m src.teste_memoria --so notas,janela

Roda a API de verdade, dentro do proprio processo (TestClient), com o modelo
ONLINE de verdade, a mesma sequencia de 10 perguntas para cada memoria. As
perguntas 2 a 10 sao curtas e dependem da conversa ("E em Sao Paulo?"); a
10a volta a PRIMEIRA ("voltando ao primeiro estado") - e onde a memoria que
esquece tropeca.

Cada resposta e corrigida pelo Python, sem modelo: tem o numero (ou o nome)
que os dados do IBGE mandam? Os valores esperados saem do mesmo CSV que o
painel le - nada digitado aqui.

Pausa entre chamadas (PAINEL_TESTE_PAUSA_S, padrao 12 s): o plano gratuito
do Groq limita os tokens por minuto.

Saidas:
    docs/teste_memoria.md                 a tabela que entra no argumento (Tarefa 4)
    data/teste_memoria/respostas.csv      cada resposta, com tokens e conferencia
"""

import csv
import os
import sys
import tempfile
import time
from datetime import datetime

from src.data_access import BASE
from src.fatos import _fmt, _ibge

RELATORIO = BASE / "docs" / "teste_memoria.md"
CSV = BASE / "data" / "teste_memoria" / "respostas.csv"


def esperado():
    """(pergunta, conferencia) - conferencia recebe a resposta e diz se acertou."""
    _, idx, periodos, _ = _ibge()
    ult = periodos[-1]
    antes = f"{int(ult[:4]) - 1}{ult[4:]}"

    def taxa(lugar, grupo="18 a 24 anos", per=ult):
        return _fmt(idx[(lugar, grupo, per)]["taxa_desocupacao_pct"])

    def tem(*partes):
        def conf(r):
            rn = r.replace(".", ",").lower()
            return all(p.lower() in rn for p in partes)
        conf.esperado = " + ".join(partes)
        return conf

    def tem_um(*opcoes):
        def conf(r):
            return any(o in r.lower() for o in opcoes)
        conf.esperado = " ou ".join(opcoes)
        return conf

    ba_agora = idx[("Bahia", "18 a 24 anos", ult)]["taxa_desocupacao_pct"]
    ba_antes = idx[("Bahia", "18 a 24 anos", antes)]["taxa_desocupacao_pct"]
    sentido = ("caiu", "queda", "diminu", "recu", "menor") if ba_agora < ba_antes else ("subiu", "aument", "alta", "maior")

    def volta(r):
        return tem("Bahia", taxa("Bahia"))(r) and any(s in r.lower() for s in sentido)
    volta.esperado = f"Bahia + {taxa('Bahia')} + {sentido[0]}"

    sp, ba = idx[("São Paulo", "18 a 24 anos", ult)], idx[("Bahia", "18 a 24 anos", ult)]
    pior = "Bahia" if ba["taxa_desocupacao_pct"] > sp["taxa_desocupacao_pct"] else "São Paulo"
    return [
        ("Como está a desocupação dos jovens de 18 a 24 anos na Bahia?", tem(taxa("Bahia"))),
        ("E em São Paulo?", tem(taxa("São Paulo"))),
        ("Qual dos dois está pior?", tem(pior)),
        ("E no Rio Grande do Sul?", tem(taxa("Rio Grande do Sul"))),
        ("E no Brasil como um todo, para essa mesma faixa?", tem(taxa("Brasil"))),
        ("E para os adolescentes de 14 a 17 anos no Brasil?", tem(taxa("Brasil", "14 a 17 anos"))),
        ("O que as notícias coletadas pelo painel dizem sobre o mercado de trabalho?", tem_um("otimista", "positiv")),
        ("Quais estados estão com a maior desocupação nessa faixa de 18 a 24?", tem("Sergipe")
         if idx.get(("Sergipe", "18 a 24 anos", ult)) else tem_um("sergipe", "pernambuco")),
        ("E Santa Catarina, como está?", tem(taxa("Santa Catarina"))),
        ("Voltando ao primeiro estado que eu perguntei: qual era a taxa lá, e ela subiu ou caiu em um ano?", volta),
    ]


def rodar(memoria, perguntas, cliente, pausa):
    cid, linhas = None, []
    for n, (p, conf) in enumerate(perguntas, 1):
        corpo = {"pergunta": p, "memoria": memoria}
        if cid:
            corpo["conversa_id"] = cid
        for tentativa in (1, 2):
            r = cliente.post("/conversa", json=corpo)
            if r.status_code == 503 and tentativa == 1:
                print(f"    503 ({r.json()['detail'][:120]}) - espero 60 s e tento de novo")
                time.sleep(60)
                continue
            break
        if r.status_code != 200:
            print(f"    [{memoria} {n}] HTTP {r.status_code}: {r.text[:200]}")
            linhas.append({"memoria": memoria, "turno": n, "pergunta": p, "acertou": False,
                           "esperado": conf.esperado, "resposta": f"(HTTP {r.status_code})"})
            break
        d = r.json()
        cid = d["conversa_id"]
        ok = conf(d["resposta"])
        linhas.append({
            "memoria": memoria, "turno": n, "pergunta": p, "acertou": ok, "esperado": conf.esperado,
            "resposta": d["resposta"].replace("\n", " "), "provedor": d["provedor"], "modelo": d["modelo"],
            "tokens_entrada": d["tokens_entrada"], "tokens_saida": d["tokens_saida"],
            "segundos": d["segundos"], "mensagens_lidas": d["leitura"]["mensagens_enviadas"],
            "chamada_de_resumo": d["chamada_de_resumo"],
            "numeros_sem_fonte": " ".join(d["numeros_sem_fonte"]),
        })
        print(f"  [{memoria} {n:2}] {'OK ' if ok else 'ERR'} {d['tokens_entrada']} tok · "
              f"{d['segundos']} s · {d['resposta'][:90]!r}")
        time.sleep(pausa)
    cliente.delete(f"/conversa/{cid}") if cid else None
    return linhas


def relatorio(linhas, memorias):
    md = [f"# Teste de 10 perguntas — {datetime.now():%d/%m/%Y %H:%M}", "",
          "Gerado por `python -m src.teste_memoria`. Não edite à mão: rode de novo.", "",
          "As mesmas 10 perguntas para cada memória, contra a API de verdade e o modelo online. "
          "As perguntas 2 a 10 dependem da conversa; a 10ª volta ao primeiro estado. "
          "Cada resposta é corrigida pelo Python, com os valores do mesmo CSV do IBGE que o painel lê.", "",
          "| Memória | Acertos | 10ª (volta ao 1º estado) | Tokens de entrada: 1ª → 10ª | Tokens no total | "
          "Chamadas a mais | Segundos por resposta (média) | Números sem fonte |",
          "|---|---|---|---|---|---|---|---|"]
    for m in memorias:
        ls = [l for l in linhas if l["memoria"] == m]
        if not ls:
            continue
        tok = [l.get("tokens_entrada") or 0 for l in ls]
        seg = [l["segundos"] for l in ls if l.get("segundos") is not None]
        decima = next((l for l in ls if l["turno"] == 10), None)
        md.append(
            f"| **{m}** | {sum(l['acertou'] for l in ls)}/10 | {'✓' if decima and decima['acertou'] else '✗'} "
            f"| {tok[0]} → {tok[-1]} | {sum(tok) + sum(l.get('tokens_saida') or 0 for l in ls)} "
            f"| {sum(1 for l in ls if l.get('chamada_de_resumo'))} "
            f"| {sum(seg) / max(len(seg), 1):.1f} | {sum(1 for l in ls if l.get('numeros_sem_fonte'))} |")
    md += ["", "Chamadas a mais: só a memória de resumo paga (uma chamada para resumir o que saiu da janela). "
           "Os tokens dessa chamada não entram na coluna de tokens.", "",
           "## A 10ª pergunta, em cada memória", ""]
    for m in memorias:
        d = next((l for l in linhas if l["memoria"] == m and l["turno"] == 10), None)
        if d:
            md += [f"**{m}** — {'acertou' if d['acertou'] else 'errou'} (esperado: {d['esperado']})", "",
                   f"> {d['resposta']}", ""]
    md += ["## Onde cada memória errou", ""]
    for l in linhas:
        if not l["acertou"]:
            md.append(f"- **{l['memoria']}**, pergunta {l['turno']} (\"{l['pergunta']}\"): esperado "
                      f"*{l['esperado']}*; veio: {l['resposta'][:220]}")
    if not any(not l["acertou"] for l in linhas):
        md.append("Nenhuma.")
    provs = sorted({f"{l.get('provedor')} · {l.get('modelo')}" for l in linhas if l.get("provedor")})
    md += ["", f"Quem respondeu: {', '.join(provs)}. Respostas completas: `data/teste_memoria/respostas.csv`."]
    RELATORIO.write_text("\n".join(md), encoding="utf-8")


def main():
    memorias = ["notas", "inteira", "janela", "resumo"]
    if "--so" in sys.argv:
        memorias = [m for m in sys.argv[sys.argv.index("--so") + 1].split(",") if m in memorias]
    pausa = float(os.environ.get("PAINEL_TESTE_PAUSA_S", "12"))

    os.environ.setdefault("PAINEL_MOTOR", "regras")  # o teste nao precisa do Qwen carregado
    os.environ["PAINEL_CONVERSAS_DIR"] = tempfile.mkdtemp(prefix="conversas_teste_")
    from fastapi.testclient import TestClient
    from api.main import app
    from src import llm_api

    if not llm_api.configurados():
        sys.exit("[erro] nenhuma chave de API no .env (GROQ_API_KEY ou GEMINI_API_KEY).")
    perguntas = esperado()
    print(f"Provedores: {llm_api.configurados()} · pausa {pausa:g} s · memórias {memorias}")

    linhas = []
    with TestClient(app) as cliente:
        for m in memorias:
            print(f"\n== {m}")
            linhas += rodar(m, perguntas, cliente, pausa)

    CSV.parent.mkdir(parents=True, exist_ok=True)
    campos = ["memoria", "turno", "pergunta", "acertou", "esperado", "resposta", "provedor", "modelo",
              "tokens_entrada", "tokens_saida", "segundos", "mensagens_lidas", "chamada_de_resumo",
              "numeros_sem_fonte"]
    with CSV.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=campos, extrasaction="ignore")
        w.writeheader()
        w.writerows(linhas)
    relatorio(linhas, memorias)
    print(f"\nRelatorio: {RELATORIO}\nRespostas: {CSV}")


if __name__ == "__main__":
    main()
