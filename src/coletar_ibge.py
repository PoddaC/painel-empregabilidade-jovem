"""
coletar_ibge.py - desocupacao dos JOVENS pela API do IBGE (PNAD Continua).

Roda SEPARADO do app, como a coleta de noticias:
    python -m src.coletar_ibge                # ultimos 20 trimestres
    python -m src.coletar_ibge --trimestres 8

Fonte:   IBGE - PNAD Continua trimestral, tabela SIDRA 4094
         "taxa de desocupacao, por grupo de idade"
API:     https://servicodados.ibge.gov.br/api/v3/agregados (aberta, sem chave)
Licenca: dados publicos do IBGE (citar a fonte).

Por que esta tabela: a meta 8.6 do ODS 8 fala de JOVENS. A taxa de
desocupacao por grupo de idade da os dois grupos que importam ao painel:
14 a 17 anos e 18 a 24 anos, ao lado do total.

O script NAO confia em numeros de codigo digitados aqui: ele le os
METADADOS da tabela primeiro e descobre sozinho qual e a variavel da taxa,
qual e a classificacao de idade e quais categorias sao os grupos jovens.
Se o IBGE mudar a tabela, o script para com uma frase dizendo o que nao
achou - em vez de gravar numero errado.

Saidas:
    data/raw/ibge_4094_<carimbo>.json             a resposta bruta (prova)
    data/processed/ibge_desocupacao_jovem.csv     a tabela que o painel le
"""

import argparse
import csv
import json
import sys
import unicodedata
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
RAW = BASE / "data" / "raw"
PROCESSED = BASE / "data" / "processed"
CSV_IBGE = PROCESSED / "ibge_desocupacao_jovem.csv"

API = "https://servicodados.ibge.gov.br/api/v3/agregados"
TABELA = 4094
CABECALHO = {"User-Agent": "EmpregabilidadeJovem/1.0 (projeto academico)"}

# Os grupos que o painel quer, pelo NOME (o codigo e descoberto nos metadados).
GRUPOS = {"14 a 17 anos": "14 a 17 anos", "18 a 24 anos": "18 a 24 anos", "total": "Total"}

# Niveis territoriais, do mais fino ao mais grosso: N3 = UF, N2 = Grande Regiao, N1 = Brasil.
NIVEIS = {"N1": "Brasil", "N2": "Grande Região", "N3": "UF"}

CAMPOS = ["periodo", "periodo_codigo", "nivel", "localidade", "grupo_idade",
          "taxa_desocupacao_pct", "tabela", "coletado_em"]


def _sem_acento(s):
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()


# -------------------------------------------------------------------
# 1. Descobrir, nos metadados, os codigos certos (funcoes puras: testaveis)
# -------------------------------------------------------------------
def descobrir(meta):
    """
    Recebe o JSON de /metadados e devolve um dict com:
    variavel (id), classificacao (id), categorias {id: nome do grupo}, niveis [N1,...].
    Levanta ValueError com uma frase se algo nao estiver la.
    """
    variavel = next((v for v in meta.get("variaveis", [])
                     if _sem_acento(v["nome"]).startswith("taxa de desocupacao")), None)
    if variavel is None:
        raise ValueError(f"a tabela {TABELA} nao tem mais uma variavel 'Taxa de desocupacao'.")

    classe = next((c for c in meta.get("classificacoes", [])
                   if "idade" in _sem_acento(c["nome"])), None)
    if classe is None:
        raise ValueError(f"a tabela {TABELA} nao tem mais uma classificacao por idade.")

    categorias = {}
    for cat in classe["categorias"]:
        nome = _sem_acento(cat["nome"])
        for grupo, procurado in GRUPOS.items():
            if nome == _sem_acento(procurado):
                categorias[str(cat["id"])] = grupo
    faltam = set(GRUPOS) - set(categorias.values())
    if faltam:
        raise ValueError(f"grupos de idade nao encontrados na tabela {TABELA}: {sorted(faltam)}.")

    disponiveis = set(meta.get("nivelTerritorial", {}).get("Administrativo", []))
    niveis = [n for n in NIVEIS if n in disponiveis] or ["N1"]

    return {"variavel": str(variavel["id"]), "classificacao": str(classe["id"]),
            "categorias": categorias, "niveis": niveis}


def nome_do_periodo(codigo):
    """'202502' -> '2025-T2'. A PNAD trimestral usa AAAA0T."""
    codigo = str(codigo)
    if len(codigo) == 6 and codigo[:4].isdigit() and codigo[4:].isdigit():
        return f"{codigo[:4]}-T{int(codigo[4:])}"
    return codigo


def numero(valor):
    """O IBGE usa '...', '-', 'X' para 'sem dado'. Devolve float ou None."""
    try:
        return float(str(valor).replace(",", "."))
    except (TypeError, ValueError):
        return None


def para_linhas(resposta, achado, coletado_em):
    """
    Achata o JSON aninhado da API (variavel > resultados > series > serie)
    numa lista de linhas com o schema CAMPOS. Valor ausente e PULADO - nao
    vira zero.
    """
    linhas = []
    for var in resposta:
        for resultado in var.get("resultados", []):
            grupo = None
            for cls in resultado.get("classificacoes", []):
                for cat_id in cls.get("categoria", {}):
                    grupo = achado["categorias"].get(str(cat_id), grupo)
            if grupo is None:
                continue
            for serie in resultado.get("series", []):
                loc = serie["localidade"]
                nivel = NIVEIS.get(loc["nivel"]["id"], loc["nivel"]["nome"])
                for per, valor in serie.get("serie", {}).items():
                    taxa = numero(valor)
                    if taxa is None:
                        continue
                    linhas.append({
                        "periodo": nome_do_periodo(per), "periodo_codigo": per,
                        "nivel": nivel, "localidade": loc["nome"], "grupo_idade": grupo,
                        "taxa_desocupacao_pct": taxa, "tabela": TABELA,
                        "coletado_em": coletado_em,
                    })
    linhas.sort(key=lambda l: (l["periodo_codigo"], l["nivel"], l["localidade"], l["grupo_idade"]))
    return linhas


# -------------------------------------------------------------------
# 2. Rede e disco
# -------------------------------------------------------------------
def pedir(url):
    import requests
    try:
        r = requests.get(url, headers=CABECALHO, timeout=60)
    except requests.RequestException as e:
        sys.exit(f"[erro] falha de rede ao falar com o IBGE: {e}")
    if r.status_code != 200:
        sys.exit(f"[erro] o IBGE respondeu HTTP {r.status_code} em {url}")
    try:
        return r.json()
    except ValueError:
        sys.exit(f"[erro] o IBGE nao devolveu JSON em {url} (instabilidade? tente de novo).")


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    p.add_argument("--trimestres", type=int, default=20, help="quantos trimestres, do mais recente para tras")
    args = p.parse_args()

    print(f"[1/3] metadados da tabela {TABELA}...")
    meta = pedir(f"{API}/{TABELA}/metadados")
    try:
        achado = descobrir(meta)
    except ValueError as e:
        sys.exit(f"[erro] {e} Confira a tabela em https://sidra.ibge.gov.br/tabela/{TABELA}")
    print(f"      variavel {achado['variavel']} · classificacao {achado['classificacao']} · "
          f"niveis {','.join(achado['niveis'])}")

    cats = ",".join(achado["categorias"])
    locais = "|".join(f"{n}[all]" for n in achado["niveis"])
    url = (f"{API}/{TABELA}/periodos/-{args.trimestres}/variaveis/{achado['variavel']}"
           f"?localidades={locais}&classificacao={achado['classificacao']}[{cats}]")
    print(f"[2/3] dados: {url}")
    resposta = pedir(url)

    carimbo = datetime.now()
    RAW.mkdir(parents=True, exist_ok=True)
    bruto = RAW / f"ibge_{TABELA}_{carimbo:%Y%m%d_%H%M%S}.json"
    bruto.write_text(json.dumps({"url": url, "metadados_usados": achado, "resposta": resposta},
                                ensure_ascii=False, indent=1), encoding="utf-8")

    linhas = para_linhas(resposta, achado, carimbo.isoformat(timespec="seconds"))
    if not linhas:
        sys.exit("[erro] a resposta veio sem nenhum valor. Nada foi gravado.")

    PROCESSED.mkdir(parents=True, exist_ok=True)
    with CSV_IBGE.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=CAMPOS)
        w.writeheader()
        w.writerows(linhas)

    periodos = sorted({l["periodo"] for l in linhas})
    print(f"[3/3] {len(linhas)} linhas · {periodos[0]} a {periodos[-1]}")
    print(f"      bruto:  {bruto.relative_to(BASE)}")
    print(f"      tabela: {CSV_IBGE.relative_to(BASE)}")


if __name__ == "__main__":
    main()
