"""
data_access.py - camada de LEITURA dos dados

Quem le o disco e este arquivo - a API, e o painel quando a API nao
responde. Se a fonte mudar (outra pagina, outro formato), muda-se so aqui.
"""

from pathlib import Path
import csv
import re
import unicodedata

BASE = Path(__file__).resolve().parent.parent
PROCESSED = BASE / "data" / "processed"
CSV_NOTICIAS = PROCESSED / "noticias_emprego.csv"
CSV_IBGE = PROCESSED / "ibge_desocupacao_jovem.csv"

FONTE = "Agência Brasil / EBC, tag 'emprego' (raspagem)"
FONTE_IBGE = "IBGE, PNAD Contínua trimestral, tabela 4094 (API de agregados)"


def carregar_noticias():
    """
    Devolve (lista_de_noticias, fonte).

    Cada noticia e um dict: titulo, editoria, ano_mes, url, resumo,
    arquivo_texto. Se o CSV ainda nao existe (a coleta nao rodou), devolve
    lista vazia e avisa na fonte - quem chama decide o que mostrar.
    """
    if not CSV_NOTICIAS.exists():
        return [], FONTE + " [ainda não coletado; rode: python -m src.coletar]"
    with CSV_NOTICIAS.open(encoding="utf-8") as f:
        linhas = list(csv.DictReader(f))
    return linhas, FONTE


def id_da_noticia(noticia):
    """
    Um identificador estavel e legivel: '2024-09_paises-da-ocde-reduzem...'.

    E o mesmo nome do .txt que a coleta grava (coletar_textos.nome_arquivo),
    entao o id de uma noticia coletada aponta direto para o seu texto. Para
    uma noticia sem arquivo, a mesma regra e aplicada a url (ou ao titulo).
    """
    arquivo = (noticia.get("arquivo_texto") or "").strip()
    if arquivo:
        return Path(arquivo).stem
    base = (noticia.get("url") or "").rstrip("/").split("/")[-1] or noticia.get("titulo", "")
    slug = unicodedata.normalize("NFKD", base).encode("ascii", "ignore").decode()
    slug = re.sub(r"[^a-zA-Z0-9-]+", "-", slug).strip("-").lower()[:60]
    return f"{noticia.get('ano_mes') or 'n-d'}_{slug or 'sem-titulo'}".replace("/", "-")


def ler_texto(noticia):
    """
    O texto integral de uma noticia, lido de data/processed/textos/.
    String vazia se a noticia nao tem texto coletado (ou o arquivo sumiu).
    """
    arquivo = (noticia.get("arquivo_texto") or "").strip()
    if not arquivo:
        return ""
    caminho = (PROCESSED / arquivo).resolve()
    # GUARDA: o caminho vem de um CSV - nao pode apontar para fora da pasta.
    if PROCESSED.resolve() not in caminho.parents or not caminho.exists():
        return ""
    return caminho.read_text(encoding="utf-8")


def carregar_ibge():
    """
    Devolve (linhas, fonte) da desocupacao por grupo de idade (IBGE).

    Cada linha: periodo, periodo_codigo, nivel, localidade, grupo_idade,
    taxa_desocupacao_pct (float), tabela, coletado_em. Sem o CSV (a coleta
    nao rodou), devolve lista vazia e diz na fonte como coletar - o painel
    NAO mostra numero de exemplo no lugar.
    """
    if not CSV_IBGE.exists():
        return [], FONTE_IBGE + " [ainda não coletado; rode: python -m src.coletar_ibge]"
    with CSV_IBGE.open(encoding="utf-8") as f:
        linhas = list(csv.DictReader(f))
    for l in linhas:
        l["taxa_desocupacao_pct"] = float(l["taxa_desocupacao_pct"])
    return linhas, FONTE_IBGE
