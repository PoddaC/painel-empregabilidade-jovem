"""
fatos.py - o que o modelo de linguagem LE antes de responder.

O modelo nao calcula nem procura dado: o Python le os CSVs do projeto,
calcula os numeros e entrega um bloco de texto curto ("os fatos"). O modelo
so redige a resposta a partir dele. Assim:
- todo numero da resposta tem origem conhecida (e pode ser conferido, ver
  src/checagem.py);
- a conversa nao depende do que o modelo "lembra" do treino.

Fontes:
- IBGE: data/processed/ibge_desocupacao_jovem.csv (python -m src.coletar_ibge)
- Noticias: data/processed/noticias_emprego.csv + os rotulos de tendencia e
  setor do banco de provas (data/analisador/banco_de_provas.csv, feitos a mao)

Tambem acha as ENTIDADES de um texto (UFs, regioes, grupos de idade): e o
que a memoria de notas anota e o que decide quais fatos entram.
"""

import csv
import re
import unicodedata
from collections import Counter
from functools import lru_cache

from src.data_access import BASE, carregar_ibge, carregar_noticias, id_da_noticia
from src.tarefas import rotulo

BANCO = BASE / "data" / "analisador" / "banco_de_provas.csv"

UFS = {
    "AC": "Acre", "AL": "Alagoas", "AP": "Amapá", "AM": "Amazonas", "BA": "Bahia",
    "CE": "Ceará", "DF": "Distrito Federal", "ES": "Espírito Santo", "GO": "Goiás",
    "MA": "Maranhão", "MT": "Mato Grosso", "MS": "Mato Grosso do Sul", "MG": "Minas Gerais",
    "PA": "Pará", "PB": "Paraíba", "PR": "Paraná", "PE": "Pernambuco", "PI": "Piauí",
    "RJ": "Rio de Janeiro", "RN": "Rio Grande do Norte", "RS": "Rio Grande do Sul",
    "RO": "Rondônia", "RR": "Roraima", "SC": "Santa Catarina", "SP": "São Paulo",
    "SE": "Sergipe", "TO": "Tocantins",
}
REGIOES = ["Norte", "Nordeste", "Sudeste", "Sul", "Centro-Oeste"]
GRUPOS = {"14 a 17 anos": "14 a 17 anos", "18 a 24 anos": "18 a 24 anos", "total": "todas as idades"}


def _norm(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


# -------------------------------------------------------------------
# ENTIDADES: o que um texto menciona (sem modelo - so Python)
# -------------------------------------------------------------------
def achar_entidades(texto):
    """
    Devolve {"lugares": [...], "grupos": [...]} na ordem em que aparecem.
    Lugares: nomes das UFs como o IBGE escreve, 'Brasil' ou uma regiao.
    Siglas so contam em MAIUSCULAS e soltas ("SP"), para "se", "pa", "to"
    do portugues nao virarem estado.
    """
    achados = []  # (posicao, lugar)
    norm = " " + _norm(texto) + " "
    # Nomes mais longos primeiro: "Mato Grosso do Sul" antes de "Mato Grosso".
    nomes = sorted(list(UFS.values()) + REGIOES + ["Brasil"], key=len, reverse=True)
    ocupado = [False] * len(norm)
    for nome in nomes:
        # "Pará" sem acento e a preposicao "para": so vale com o acento.
        if nome == "Pará" and not re.search(r"\bpará\b", texto, re.IGNORECASE):
            continue
        alvo = " " + _norm(nome) + " "
        inicio = 0
        while (i := norm.find(alvo, inicio)) >= 0:
            if not any(ocupado[i:i + len(alvo)]):
                achados.append((i, nome))
                for j in range(i + 1, i + len(alvo) - 1):
                    ocupado[j] = True
            inicio = i + 1
    for m in re.finditer(r"\b([A-Z]{2})\b", texto):
        if m.group(1) in UFS:
            achados.append((m.start() * len(norm) / max(len(texto), 1), UFS[m.group(1)]))
    if re.search(r"\b(pais|nacional)\b", norm):
        achados.append((norm.find("pais") if "pais" in norm else norm.find("nacional"), "Brasil"))

    lugares = []
    for _, nome in sorted(achados):
        if nome not in lugares:
            lugares.append(nome)

    grupos = []
    if re.search(r"\b14 (a|e) 17\b|adolescente", norm):
        grupos.append("14 a 17 anos")
    if re.search(r"\b18 (a|e) 24\b|\bjove(m|ns)\b", norm):
        grupos.append("18 a 24 anos")
    if re.search(r"\b(total|geral|todas as idades|media)\b", norm):
        grupos.append("total")
    return {"lugares": lugares, "grupos": grupos}


# -------------------------------------------------------------------
# IBGE
# -------------------------------------------------------------------
@lru_cache(maxsize=1)
def _ibge():
    linhas, fonte = carregar_ibge()
    idx = {(l["localidade"], l["grupo_idade"], l["periodo_codigo"]): l for l in linhas}
    periodos = sorted({l["periodo_codigo"] for l in linhas})
    return linhas, idx, periodos, fonte


def recarregar():
    """Esquece o cache (depois de uma coleta nova)."""
    _ibge.cache_clear()
    _noticias.cache_clear()


def _fmt(x):
    return f"{x:.1f}".replace(".", ",")


def _nome_periodo(codigo):
    return f"{int(codigo[4:])}º trimestre de {codigo[:4]}"


def _ano_antes(codigo):
    return f"{int(codigo[:4]) - 1}{codigo[4:]}"


def linha_lugar(lugar, grupo, ultimo):
    """Uma linha de fato: taxa no ultimo trimestre, e um ano antes, se houver."""
    _, idx, _, _ = _ibge()
    agora = idx.get((lugar, grupo, ultimo))
    if agora is None:
        return None
    antes = idx.get((lugar, grupo, _ano_antes(ultimo)))
    txt = f"{lugar}, {GRUPOS[grupo]}: {_fmt(agora['taxa_desocupacao_pct'])}%"
    if antes:
        dif = agora["taxa_desocupacao_pct"] - antes["taxa_desocupacao_pct"]
        sentido = "subiu" if dif > 0.05 else "caiu" if dif < -0.05 else "ficou estável"
        txt += (f" (um ano antes: {_fmt(antes['taxa_desocupacao_pct'])}%; {sentido}"
                + (f" {_fmt(abs(dif))} pontos percentuais)" if sentido != "ficou estável" else ")"))
    return txt


def fatos_ibge(lugares, grupos):
    linhas, _, periodos, fonte = _ibge()
    if not linhas:
        return ["Dados do IBGE: ainda não coletados nesta máquina."]
    ultimo = periodos[-1]
    out = [f"IBGE, PNAD Contínua (tabela 4094), taxa de desocupação, {_nome_periodo(ultimo)} "
           "(o último disponível). Desocupado = procurou trabalho e não achou."]

    # Sempre: o Brasil nos tres grupos (a referencia de qualquer comparacao).
    for g in GRUPOS:
        if (l := linha_lugar("Brasil", g, ultimo)):
            out.append("- " + l)

    # Os lugares citados (ou anotados) - nos grupos citados, ou 18-24 + total.
    gs = grupos or ["18 a 24 anos", "total"]
    for lugar in lugares:
        if lugar == "Brasil":
            continue
        achou = False
        for g in gs + [x for x in ("18 a 24 anos", "total") if x not in gs]:
            if (l := linha_lugar(lugar, g, ultimo)):
                out.append("- " + l)
                achou = True
        if not achou:
            out.append(f"- {lugar}: o IBGE não divulgou valor no {_nome_periodo(ultimo)}.")

    # Sempre: quem esta melhor e pior entre as UFs, para 18 a 24 anos.
    ufs = sorted((l for l in linhas if l["nivel"] == "UF" and l["periodo_codigo"] == ultimo
                  and l["grupo_idade"] == "18 a 24 anos"), key=lambda l: l["taxa_desocupacao_pct"])
    if ufs:
        def lista(xs):
            return ", ".join(f"{l['localidade']} {_fmt(l['taxa_desocupacao_pct'])}%" for l in xs)
        out.append(f"- UFs com MAIOR desocupação de 18 a 24 anos: {lista(ufs[::-1][:3])}.")
        out.append(f"- UFs com MENOR desocupação de 18 a 24 anos: {lista(ufs[:3])}.")
    return out


# -------------------------------------------------------------------
# NOTICIAS
# -------------------------------------------------------------------
@lru_cache(maxsize=1)
def _noticias():
    noticias, _ = carregar_noticias()
    rotulos = {}
    if BANCO.exists():
        with BANCO.open(encoding="utf-8") as f:
            rotulos = {r["id"]: r for r in csv.DictReader(f)}
    out = []
    for n in noticias:
        r = rotulos.get(id_da_noticia(n))
        if r:
            out.append({"titulo": n["titulo"], "ano_mes": n["ano_mes"],
                        "tendencia": r["tendencia"], "setor": r["setor"]})
    return sorted(out, key=lambda n: n["ano_mes"])


def fatos_noticias():
    ns = _noticias()
    if not ns:
        return ["Notícias: nenhuma com tendência rotulada no acervo."]
    tend = Counter(n["tendencia"] for n in ns)
    setores = Counter(n["setor"] for n in ns)
    out = [f"Notícias de emprego da Agência Brasil no acervo do painel: {len(ns)}, de "
           f"{ns[0]['ano_mes']} a {ns[-1]['ano_mes']}, com tendência e setor rotulados à mão.",
           "- Tendência: " + ", ".join(f"{rotulo('tendencia', t)} {c}" for t, c in tend.most_common()),
           "- Setor: " + ", ".join(f"{rotulo('setor', s)} {c}" for s, c in setores.most_common()),
           "- As 3 mais recentes:"]
    for n in ns[::-1][:3]:
        out.append(f"  - {n['ano_mes']}: \"{n['titulo']}\" ({rotulo('tendencia', n['tendencia'])})")
    return out


def montar_fatos(lugares=(), grupos=(), com_noticias=True):
    """O bloco de texto que vai nas instrucoes do modelo."""
    partes = fatos_ibge(list(lugares), list(grupos))
    if com_noticias:
        partes += [""] + fatos_noticias()
    return "\n".join(partes)
