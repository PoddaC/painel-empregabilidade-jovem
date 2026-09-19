"""
data_access.py - camada de LEITURA dos dados (Aula 6)
 
O app importa daqui e NUNCA le o CSV direto. Se a fonte mudar (outra pagina,
outro formato), muda-se so este arquivo e a interface continua de pe.
"""
 
from pathlib import Path
import csv
 
BASE = Path(__file__).resolve().parent.parent
CSV_NOTICIAS = BASE / "data" / "processed" / "noticias_emprego.csv"
 
FONTE = "Agencia Brasil / EBC - tag 'emprego' (coleta via scraping)"
 
 
def carregar_noticias():
    """
    Devolve (lista_de_noticias, fonte).
 
    Cada noticia e um dict: titulo, editoria, ano_mes, url.
    Se o CSV ainda nao existe (a coleta nao rodou), devolve lista vazia
    e avisa na fonte - o app decide o que mostrar nesse caso.
    """
    if not CSV_NOTICIAS.exists():
        return [], FONTE + " [ainda nao coletado - rode: python -m src.coletar]"
    with CSV_NOTICIAS.open(encoding="utf-8") as f:
        linhas = list(csv.DictReader(f))
    return linhas, FONTE