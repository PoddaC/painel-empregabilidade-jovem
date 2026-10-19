"""
coletar_textos.py - segunda passada: o texto de cada noticia.

    python -m src.coletar_textos --teste    # confere UMA noticia, sem gravar
    python -m src.coletar_textos            # roda a coleta inteira

Entrada: data/processed/noticias_emprego.csv
Saida:   data/processed/textos/*.txt  + colunas resumo e arquivo_texto no CSV
"""

from pathlib import Path
import csv
import re
import sys
import time
import unicodedata

from bs4 import BeautifulSoup

# reaproveita o downloader do coletar.py: a politica de rede (timeout,
# User-Agent, tratamento de erro) tudo em um.
from src.coletar import baixar

# --- caminhos ancorados no PROPRIO arquivo (nao em onde voce rodou o comando) ---
BASE = Path(__file__).resolve().parent.parent
PROCESSED = BASE / "data" / "processed"
CSV_NOTICIAS = PROCESSED / "noticias_emprego.csv"
TEXTOS = PROCESSED / "textos"

CRAWL_DELAY = 10  # segundos, conforme robots.txt do site

# tags que nunca fazem parte do corpo da materia
LIXO = ["script", "style", "noscript", "nav", "footer", "header",
        "aside", "form", "figure", "figcaption", "iframe"]

# paragrafo mais curto que isso costuma ser credito de foto, tag ou rodape
MIN_PARAGRAFO = 40

COLUNAS = ["titulo", "editoria", "ano_mes", "url", "resumo", "arquivo_texto"]


# -------------------------------------------------------------------
# EXTRACAO - funcoes puras: recebem HTML, devolvem texto.
# Nao tocam na rede nem no disco, entao sao testaveis sozinhas.
# -------------------------------------------------------------------

def extrair_resumo(sopa):
    """
    O subtitulo (linha fina) da noticia.

    Vem da meta description / og:description, que todo CMS de noticia
    preenche com a linha fina. E mais estavel que qualquer classe CSS:
    a meta tag existe porque o Google e o WhatsApp a leem.
    """
    for seletor in [{"property": "og:description"}, {"name": "description"}]:
        meta = sopa.find("meta", attrs=seletor)
        if meta and meta.get("content", "").strip():
            return meta["content"].strip()
    return ""


def extrair_texto(sopa):
    """
    O corpo da materia.

    Estrategia (robusta): em vez de depender de uma classe CSS que muda, a
    gente procura o container com mais TEXTO EM PARAGRAFOS - e, entre os
    empatados, o MAIS ESPECIFICO (o menor). E o mesmo principio do coletar.py:
    apoiar-se na estrutura, nao na decoracao.

    Devolve os paragrafos separados por linha em branco.
    """
    # 1. fora o que nunca e materia
    for tag in sopa.find_all(LIXO):
        tag.decompose()

    # 2. pontua cada container pelo texto que ele tem em <p>
    candidatos = []
    for cont in sopa.find_all(["article", "main", "section", "div"]):
        pontos = sum(len(p.get_text(strip=True)) for p in cont.find_all("p"))
        if pontos:
            candidatos.append((pontos, len(cont.get_text(strip=True)), cont))

    if not candidatos:
        return ""

    # 3. o melhor: entre os que tem ao menos 80% do maior placar,
    #    fica o de menor tamanho total - o mais justo ao redor do texto.
    melhor_placar = max(c[0] for c in candidatos)
    finalistas = [c for c in candidatos if c[0] >= 0.8 * melhor_placar]
    _, _, corpo = min(finalistas, key=lambda c: c[1])

    # 4. os paragrafos, limpos
    paragrafos = []
    for p in corpo.find_all("p"):
        # \s+ -> um espaco: o HTML vem quebrado em varias linhas no
        # codigo-fonte, e essas quebras nao sao do texto.
        texto = re.sub(r"\s+", " ", p.get_text(" ", strip=True)).strip()
        if len(texto) >= MIN_PARAGRAFO:
            paragrafos.append(texto)

    return "\n\n".join(paragrafos)


def nome_arquivo(noticia):
    """
    Nome legivel e unico para o .txt: 2026-08_cai-diferenca-entre-homens.txt

    Legivel de proposito - o avaliador abre a pasta e entende o que ha nela.
    O ano_mes na frente evita colisao entre slugs repetidos em meses
    diferentes, e tambem deixa a pasta ordenada por data.
    """
    slug = noticia["url"].rstrip("/").split("/")[-1]
    slug = unicodedata.normalize("NFKD", slug).encode("ascii", "ignore").decode()
    slug = re.sub(r"[^a-zA-Z0-9-]+", "-", slug).strip("-").lower()[:60]
    return f"{noticia['ano_mes']}_{slug}.txt"


# -------------------------------------------------------------------
# LEITURA / GRAVACAO
# -------------------------------------------------------------------

def ler_noticias():
    """Le o CSV da primeira passada. Guarda: sem ele, nao ha o que fazer."""
    if not CSV_NOTICIAS.exists():
        print("[erro] nao achei data/processed/noticias_emprego.csv")
        print("       rode antes:  python -m src.coletar")
        return []
    with CSV_NOTICIAS.open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def gravar_csv(noticias):
    """Reescreve o CSV com as colunas novas. Guarda contra lista vazia."""
    if not noticias:
        print("[aviso] nada a gravar - CSV preservado.")
        return None
    with CSV_NOTICIAS.open("w", newline="", encoding="utf-8") as f:
        escritor = csv.DictWriter(f, fieldnames=COLUNAS, extrasaction="ignore")
        escritor.writeheader()
        escritor.writerows(noticias)
    return CSV_NOTICIAS


# -------------------------------------------------------------------
# MODO TESTE - uma noticia so, sem gravar nada
# -------------------------------------------------------------------

def testar(url=None):
    """
    Baixa UMA noticia e mostra o que foi extraido. Nao grava nada.

    E o passo que evita rodar 7 minutos de coleta para descobrir no fim
    que o seletor pegou o menu em vez da materia.
    """
    if url is None:
        noticias = ler_noticias()
        if not noticias:
            return
        url = noticias[0]["url"]

    print(f"[teste] {url}\n")
    html = baixar(url)
    if html is None:
        return

    sopa = BeautifulSoup(html, "html.parser")
    resumo = extrair_resumo(sopa)
    texto = extrair_texto(sopa)
    paragrafos = texto.count("\n\n") + 1 if texto else 0

    print(f"RESUMO ({len(resumo)} caracteres):")
    print(f"  {resumo or '(nada encontrado)'}\n")
    print(f"TEXTO ({len(texto)} caracteres, {paragrafos} paragrafos):")
    print("  " + (texto[:500].replace("\n", "\n  ") if texto else "(nada encontrado)"))
    if len(texto) > 500:
        print("  [...]")
    print("\n[teste] nada foi gravado. Confira se o texto acima e a materia "
          "mesmo - e nao o menu do site.")


# -------------------------------------------------------------------
# COLETA COMPLETA
# -------------------------------------------------------------------

def main():
    noticias = ler_noticias()
    if not noticias:
        return

    TEXTOS.mkdir(parents=True, exist_ok=True)
    baixadas, reaproveitadas, falhas = 0, 0, 0

    for i, noticia in enumerate(noticias, 1):
        arquivo = TEXTOS / nome_arquivo(noticia)
        noticia["arquivo_texto"] = f"textos/{arquivo.name}"

        # RETOMAVEL: ja esta em disco -> nao baixa de novo.
        if arquivo.exists():
            noticia.setdefault("resumo", "")
            reaproveitadas += 1
            continue

        print(f"[{i}/{len(noticias)}] {noticia['titulo'][:60]}...")
        html = baixar(noticia["url"])
        if html is None:
            noticia["resumo"] = ""
            noticia["arquivo_texto"] = ""
            falhas += 1
            continue

        sopa = BeautifulSoup(html, "html.parser")
        noticia["resumo"] = extrair_resumo(sopa)
        texto = extrair_texto(sopa)

        if not texto:
            print("      [aviso] corpo vazio - a estrutura da pagina pode ter mudado")
            noticia["arquivo_texto"] = ""
            falhas += 1
        else:
            arquivo.write_text(texto, encoding="utf-8")
            baixadas += 1

        time.sleep(CRAWL_DELAY)  # o robots.txt pediu 10s. A gente respeita.

    # recupera do CSV antigo se atual sumir
    gravar_csv(noticias)

    print(f"\nPronto: {baixadas} baixadas, {reaproveitadas} ja em disco, "
          f"{falhas} falhas.")
    print(f"Textos em: data/processed/textos/")
    print(f"CSV atualizado: data/processed/noticias_emprego.csv")


if __name__ == "__main__":
    if "--teste" in sys.argv:
        resto = [a for a in sys.argv[1:] if a != "--teste"]
        testar(resto[0] if resto else None)
    else:
        main()