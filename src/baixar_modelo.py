"""
baixar_modelo.py - o download do modelo, como passo A PARTE.

    python -m src.baixar_modelo              # o modelo da API (uma vez, com internet)
    python -m src.baixar_modelo --bancada    # + os candidatos que a bancada compara
    python -m src.baixar_modelo --so qwen15,qwen3_17     # so alguns (apelidos da bancada)

E o mesmo principio da coleta (src/coletar.py): o que depende da internet
roda separado, antes. A API so le do disco (local_files_only=True) - sem o
modelo baixado, ela sobe do mesmo jeito e responde 503 explicando o que
falta, em vez de ficar muda baixando gigabytes na subida (Aula 16: 71 s).

O modelo vai para o cache do HuggingFace (~/.cache/huggingface, ou a pasta
em HF_HOME). Nada disso vai para o Git: sao gigabytes.
"""

from pathlib import Path
import sys

from src.analisador_llm import nome_do_modelo
from src.bancada import CANDIDATOS as DA_BANCADA

# Os candidatos da bancada (src/bancada.py), por apelido.
CANDIDATOS = {apelido: modelo for apelido, _, modelo in DA_BANCADA if modelo}


def baixar(repo):
    """Baixa so o necessario: configuracao, tokenizador e UM formato de pesos."""
    from huggingface_hub import HfApi, snapshot_download

    arquivos = HfApi().list_repo_files(repo)
    # safetensors quando existe (mais seguro e rapido de carregar); senao o .bin
    pesos = "*.safetensors" if any(a.endswith(".safetensors") for a in arquivos) else "*.bin"
    padroes = ["*.json", "*.txt", "*.model", "tokenizer*", pesos]

    print(f"[baixar] {repo} (pesos: {pesos})...")
    pasta = snapshot_download(repo, allow_patterns=padroes)
    tamanho = sum(p.stat().st_size for p in Path(pasta).rglob("*") if p.is_file())
    print(f"[baixar] ok - {tamanho / 2**30:.2f} GB em {pasta}")


def main():
    repos = [nome_do_modelo()]
    if "--bancada" in sys.argv:
        repos += [r for r in CANDIDATOS.values() if r not in repos]
    if "--so" in sys.argv:
        apelidos = sys.argv[sys.argv.index("--so") + 1].split(",")
        desconhecidos = [a for a in apelidos if a not in CANDIDATOS]
        if desconhecidos:
            sys.exit(f"Apelidos desconhecidos: {desconhecidos}. Validos: {list(CANDIDATOS)}")
        repos = [CANDIDATOS[a] for a in apelidos]

    falhas = 0
    for repo in repos:
        try:
            baixar(repo)
        except Exception as e:  # rede, nome errado, repo gated...
            falhas += 1
            print(f"[erro] {repo}: {type(e).__name__}: {e}")

    if falhas:
        print(f"\n{falhas} download(s) falharam. Confira a internet e o nome do modelo.")
        sys.exit(1)
    print("\nPronto. A partir daqui a API roda offline: uvicorn api.main:app")


if __name__ == "__main__":
    main()
