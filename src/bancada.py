"""
bancada.py - mede os modelos candidatos no banco de provas.

    python -m src.baixar_modelo --bancada    # uma vez: baixa os candidatos
    python -m src.bancada                    # mede todos os que estao no disco
    python -m src.bancada --so regras,qwen15 # mede so alguns

Anota acertos, erros e silencios, memoria e tempo, nesta maquina.

Saidas:
    data/analisador/bancada_previsoes.csv   cada resposta de cada candidato
    docs/bancada_resultados.md              a tabela que entra na justificativa
"""

import csv
import gc
import os
import platform
import sys
import time
from collections import Counter
from datetime import datetime

from src.data_access import BASE, carregar_noticias, id_da_noticia, ler_texto
from src.tarefas import TIPOS, montar_texto

BANCO = BASE / "data" / "analisador" / "banco_de_provas.csv"
PREVISOES = BASE / "data" / "analisador" / "bancada_previsoes.csv"
RELATORIO = BASE / "docs" / "bancada_resultados.md"

# (apelido, familia, modelo no Hub) - a familia diz qual motor carrega.
# So os candidatos MEDIDOS: os que foram considerados e descartados antes da
# medicao (Tucano 2, Granite 4.1) estao no README.
CANDIDATOS = [
    ("regras", "regras", None),
    ("mdeberta", "zeroshot", "MoritzLaurer/mDeBERTa-v3-base-xnli-multilingual-nli-2mil7"),
    ("qwen05", "llm", "Qwen/Qwen2.5-0.5B-Instruct"),
    ("qwen15", "llm", "Qwen/Qwen2.5-1.5B-Instruct"),
    ("qwen3_17", "llm", "Qwen/Qwen3-1.7B"),
]


def carregar_motor(familia, modelo):
    if familia == "regras":
        from src.motor_regras import MotorRegras
        return MotorRegras()
    if familia == "zeroshot":
        from src.motor_zeroshot import MotorZeroShot
        return MotorZeroShot(modelo)
    from src.analisador_llm import AnalisadorLLM
    return AnalisadorLLM(modelo)


def ler_banco():
    """O banco de provas, com o texto de cada noticia montado como o painel monta."""
    with BANCO.open(encoding="utf-8") as f:
        banco = list(csv.DictReader(f))
    noticias = {id_da_noticia(n): n for n in carregar_noticias()[0]}
    sem_texto = 0
    for item in banco:
        n = noticias.get(item["id"])
        if n is None:
            sys.exit(f"[erro] {item['id']} esta no banco mas nao no acervo. Rode a coleta.")
        corpo = ler_texto(n)
        sem_texto += not corpo
        item["texto"] = montar_texto(n["titulo"], n.get("resumo", ""), corpo)
    if sem_texto:
        print(f"[aviso] {sem_texto} noticias sem texto integral: o modelo le so titulo e "
              "linha fina nelas. Rode python -m src.coletar_textos para completar.")
    return banco


def maquina():
    """A maquina onde os segundos foram medidos - eles so valem para ela."""
    linhas = [f"{platform.system()} {platform.release()} · Python {platform.python_version()}",
              f"CPU: {platform.processor() or '?'} · {os.cpu_count()} nucleos logicos"]
    try:
        import torch
        gpu = torch.cuda.get_device_name(0) if torch.cuda.is_available() else "nenhuma visivel ao torch"
        linhas.append(f"torch {torch.__version__} · GPU: {gpu}")
    except ImportError:
        linhas.append("torch nao instalado")
    return linhas


def medir(apelido, familia, modelo, banco):
    """Roda um candidato no banco inteiro. Devolve (resumo, previsoes) ou None."""
    print(f"\n[{apelido}] carregando {modelo or 'regras'}...")
    try:
        motor = carregar_motor(familia, modelo)
    except OSError:
        print(f"[{apelido}] nao esta no disco - pulei. Baixe: python -m src.baixar_modelo --bancada")
        return None
    except Exception as e:  # nao coube na memoria, tokenizador incompativel...
        print(f"[{apelido}] nao carregou ({type(e).__name__}: {str(e)[:120]}) - pulei.")
        _liberar_gpu()
        return None

    import_torch = familia != "regras"
    if import_torch:
        import torch
        if torch.cuda.is_available():
            torch.cuda.reset_peak_memory_stats()

    carga = getattr(motor, "segundos_para_carregar", 0.0)
    previsoes, tempos = [], []
    for item in banco:
        for tipo in TIPOS:
            inicio = time.perf_counter()
            r = motor.analisar(item["texto"], tipo)
            seg = time.perf_counter() - inicio
            tempos.append(seg)
            previsoes.append({
                "candidato": apelido, "id": item["id"], "tipo": tipo,
                "esperado": item[tipo], "previsto": r["categoria"] or "",
                "confianca": r["confianca"], "segundos": round(seg, 4),
            })

    pico_gpu = None
    if import_torch and torch.cuda.is_available():
        pico_gpu = round(torch.cuda.max_memory_allocated() / 2**20)

    resumo = {"apelido": apelido, "motor": motor.descricao, "memoria_mb": motor.memoria_mb,
              "pico_gpu_mb": pico_gpu, "carga_s": round(carga, 1),
              "s_por_analise": round(sum(tempos[1:]) / max(len(tempos) - 1, 1), 3)}  # sem o 1o (aquecimento)
    for tipo in TIPOS:
        p = [x for x in previsoes if x["tipo"] == tipo]
        certos = sum(x["previsto"] == x["esperado"] for x in p)
        calados = sum(x["previsto"] == "" for x in p)
        erros = [x for x in p if x["previsto"] not in ("", x["esperado"])]
        resumo[tipo] = {"certos": certos, "erros": len(erros), "calados": calados, "n": len(p),
                        "erros_confiantes": sum(x["confianca"] >= 0.9 for x in erros)}
    print(f"[{apelido}] tendencia {resumo['tendencia']['certos']}/{len(banco)} · "
          f"setor {resumo['setor']['certos']}/{len(banco)} · {resumo['s_por_analise']} s por analise")

    del motor
    _liberar_gpu()
    return resumo, previsoes


def _liberar_gpu():
    gc.collect()
    try:
        import torch
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    except ImportError:
        pass


def linha_base(banco):
    """'Sempre a categoria mais comum': o minimo que um modelo precisa bater."""
    base = {"apelido": "sempre-a-mais-comum", "motor": "chuta a categoria mais frequente do banco",
            "memoria_mb": 0, "pico_gpu_mb": None, "carga_s": 0, "s_por_analise": 0}
    for tipo in TIPOS:
        mais_comum, certos = Counter(i[tipo] for i in banco).most_common(1)[0]
        base[tipo] = {"certos": certos, "erros": len(banco) - certos, "calados": 0,
                      "n": len(banco), "erros_confiantes": 0, "mais_comum": mais_comum}
    return base


def escrever_relatorio(resumos, previsoes, banco):
    PREVISOES.parent.mkdir(parents=True, exist_ok=True)
    with PREVISOES.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(previsoes[0]))
        w.writeheader()
        w.writerows(previsoes)

    n = len(banco)
    md = [f"# Resultados da bancada — {datetime.now():%d/%m/%Y %H:%M}", "",
          "Gerado por `python -m src.bancada`. Não edite à mão: rode de novo.", "",
          "**Máquina:** " + " · ".join(maquina()), "",
          f"**Banco de provas:** {n} notícias reais do acervo, rotuladas à mão antes da medição "
          "(`data/analisador/banco_de_provas.csv`). Cada notícia é analisada nas duas tarefas.", "",
          "| Candidato | Tendência (certos/erros/calados) | Setor (certos/erros/calados) "
          "| Erros com confiança ≥ 0,9 | Memória dos pesos | Pico na GPU | Carga | s por análise |",
          "|---|---|---|---|---|---|---|---|"]
    for r in resumos:
        t, s = r["tendencia"], r["setor"]
        md.append(
            f"| {r['apelido']}<br><sub>{r['motor']}</sub> "
            f"| {t['certos']}/{n} · {t['erros']} · {t['calados']} "
            f"| {s['certos']}/{n} · {s['erros']} · {s['calados']} "
            f"| {t['erros_confiantes'] + s['erros_confiantes']} "
            f"| {r['memoria_mb']:.0f} MB | {r['pico_gpu_mb'] or '—'} {'MB' if r['pico_gpu_mb'] else ''} "
            f"| {r['carga_s']} s | {r['s_por_analise']} |")

    md += ["", "## Onde cada candidato errou", ""]
    titulos = {i["id"]: i["titulo"] for i in banco}
    for r in resumos:
        erros = [p for p in previsoes if p["candidato"] == r["apelido"] and p["previsto"] != p["esperado"]]
        if not erros:
            continue
        md.append(f"**{r['apelido']}** — {len(erros)} respostas fora do rótulo")
        md.append("")
        for e in erros:
            prev = e["previsto"] or "(calou)"
            md.append(f"- [{e['tipo']}] {titulos[e['id']]} — esperado *{e['esperado']}*, "
                      f"veio *{prev}* ({e['confianca']:.2f})")
        md.append("")

    RELATORIO.write_text("\n".join(md), encoding="utf-8")
    print(f"\nRelatorio: {RELATORIO.relative_to(BASE)}")
    print(f"Previsoes: {PREVISOES.relative_to(BASE)}")


def main():
    escolhidos = None
    if "--so" in sys.argv:
        escolhidos = set(sys.argv[sys.argv.index("--so") + 1].split(","))

    banco = ler_banco()
    print("Maquina:", " | ".join(maquina()))

    resumos, previsoes = [linha_base(banco)], []
    for apelido, familia, modelo in CANDIDATOS:
        if escolhidos and apelido not in escolhidos:
            continue
        medido = medir(apelido, familia, modelo, banco)
        if medido:
            resumos.append(medido[0])
            previsoes += medido[1]

    if not previsoes:
        sys.exit("Nenhum candidato rodou.")
    escrever_relatorio(resumos, previsoes, banco)


if __name__ == "__main__":
    main()
