"""
Coleta de noticias de emprego da Agencia Brasil (EBC)
 
Este script roda SEPARADO do app 
    Uso (a partir da RAIZ do projeto, com o .venv ativo):
        python -m src.coletar
    Ele grava um CSV limpo em data/processed/ que o app apenas LE.
 
Fonte:   https://agenciabrasil.ebc.com.br/tags/emprego
Licenca: conteudo da EBC (uso educacional, fonte citada no app).
robots.txt verificado: /tags/ liberado; Crawl-delay: 10 (respeitado abaixo).
"""
 
from pathlib import Path
from datetime import datetime
from urllib.parse import urljoin
import csv
import re
import time
 
import requests
from bs4 import BeautifulSoup
 
# --- caminhos ancorados no PROPRIO arquivo (nao em onde voce rodou o comando) ---
BASE = Path(__file__).resolve().parent.parent
RAW = BASE / "data" / "raw"
PROCESSED = BASE / "data" / "processed"
 
URL = "https://agenciabrasil.ebc.com.br/tags/emprego"
CRAWL_DELAY = 10  # segundos, conforme robots.txt do site
CABECALHO = {"User-Agent": "TP2-EmpregabilidadeJovem/1.0 (projeto academico)"}
N_PAGINAS = 3   # quantas paginas coletar (1 = so a primeira)
 
def baixar(url):
    """Baixa a pagina UMA vez. Retorna o HTML (str) ou None se falhar."""
    try:
        resp = requests.get(url, headers=CABECALHO, timeout=20)
    except requests.RequestException as e:
        print(f"[erro] falha de rede: {e}")
        return None
    if resp.status_code != 200:
        print(f"[erro] HTTP {resp.status_code} ao acessar {url}")
        return None
    resp.encoding = resp.apparent_encoding  # cuida dos acentos
    return resp.text
 
 
def salvar_snapshot(html):
    """Grava o HTML bruto em data/raw/ - prova do que a pagina dizia."""
    RAW.mkdir(parents=True, exist_ok=True)
    carimbo = datetime.now().strftime("%Y%m%d_%H%M%S")
    caminho = RAW / f"emprego_{carimbo}.html"
    caminho.write_text(html, encoding="utf-8")
    return caminho
 
 
def extrair(html):
    """
    Extrai as noticias da pagina de tag.
 
    Estrategia (robusta): filtrar links cujo href tem '/noticia/' - o padrao
    estavel das materias - em vez de depender de classes CSS, que mudam.
    Da propria URL saem a editoria e o ano-mes.
    """
    sopa = BeautifulSoup(html, "html.parser")
    vistos = set()
    noticias = []
 
    for link in sopa.find_all("a", href=True):
        href = urljoin(URL, link["href"])       # resolve relativo -> absoluto
        if "/noticia/" not in href:
            continue
        titulo = link.get_text(" ", strip=True)
        if not titulo:                           # o link da imagem vem sem texto
            continue
        if href in vistos:                       # dedup: imagem + titulo = mesma URL
            continue
        vistos.add(href)
 
        # editoria e ano-mes saem do caminho: /economia/noticia/2026-08/slug
        editoria, ano_mes = "n/d", "n/d"
        m = re.search(r"/([a-z-]+)/noticia/(\d{4}-\d{2})/", href)
        if m:
            editoria = m.group(1).replace("-", " ")
            ano_mes = m.group(2)
 
        noticias.append({
            "titulo": titulo,
            "editoria": editoria,
            "ano_mes": ano_mes,
            "url": href,
        })
 
    return noticias
 
 
def gravar_csv(noticias):
    """Grava o CSV limpo em data/processed/. Guarda contra lista vazia."""
    if not noticias:
        print("[aviso] nada foi extraido - CSV nao gravado. A estrutura do site "
              "pode ter mudado; confira o snapshot em data/raw/.")
        return None
    PROCESSED.mkdir(parents=True, exist_ok=True)
    caminho = PROCESSED / "noticias_emprego.csv"
    with caminho.open("w", newline="", encoding="utf-8") as f:
        escritor = csv.DictWriter(f, fieldnames=["titulo", "editoria", "ano_mes", "url"])
        escritor.writeheader()
        escritor.writerows(noticias)
    return caminho
 
 
def main():
    todas = []
    for page in range(N_PAGINAS):
        html = baixar(f"{URL}?page={page}")
        if html is None:
            break
        todas.extend(extrair(html))
        time.sleep(CRAWL_DELAY)

    gravar_csv(todas)
 
 
if __name__ == "__main__":
    main()