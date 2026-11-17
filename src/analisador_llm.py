"""
analisador_llm.py - o modelo de linguagem LOCAL que analisa as noticias.

    python -m src.baixar_modelo        # UMA vez, com internet
    uvicorn api.main:app               # depois, offline

- Carrega so do disco (local_files_only): sem o modelo baixado, falha na hora.
- Nao escreve: pontua as letras das opcoes, entao a resposta e sempre uma
  categoria da lista.
- float16 na GPU, float32 na CPU (onde float16 e lento).
"""

import os
import time

from src.tarefas import TAREFAS, categorias, recortar

# O escolhido na bancada (docs/escolha_do_modelo.md). Troca-se sem mexer no
# codigo: PAINEL_MODELO=<outro modelo do Hub>. Plano B sem modelo: PAINEL_MOTOR=regras.
MODELO_PADRAO = "Qwen/Qwen2.5-1.5B-Instruct"

LETRAS = "ABCDEFGHIJ"

INSTRUCAO = (
    "Você é um analista do mercado de trabalho brasileiro. Leia a notícia e "
    "escolha UMA opção. Responda apenas com a letra."
)


def nome_do_modelo():
    return os.environ.get("PAINEL_MODELO", MODELO_PADRAO)


def escolher_dispositivo(torch):
    """'cuda' se houver placa de video NVIDIA com o torch certo; senao 'cpu'."""
    pedido = os.environ.get("PAINEL_DISPOSITIVO", "auto")
    if pedido != "auto":
        return pedido
    return "cuda" if torch.cuda.is_available() else "cpu"


def montar_pergunta(trecho, tipo):
    """O prompt: a pergunta, as opcoes COM o que cada uma quer dizer, e a noticia."""
    tarefa = TAREFAS[tipo]
    opcoes = "\n".join(
        f"{LETRAS[i]}) {dados['rotulo']}: {dados['definicao']}"
        for i, dados in enumerate(tarefa["categorias"].values())
    )
    return (
        f"{tarefa['pergunta']}\n\nOpções:\n{opcoes}\n\n"
        f"Notícia:\n\"\"\"\n{trecho}\n\"\"\"\n\nResponda só com a letra da opção."
    )


class AnalisadorLLM:
    """
    Carrega um modelo de conversa (instruct) do disco e pontua as categorias.

    Pesado de criar (segundos, gigabytes); leve de usar. Por isso a API cria
    UM, quando sobe (o lifespan), e reaproveita em todo pedido.
    """

    def __init__(self, modelo=None, dispositivo=None, apenas_local=True):
        # import aqui dentro: o painel (Streamlit Cloud) nunca importa torch.
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer

        self.torch = torch
        self.modelo_nome = modelo or nome_do_modelo()
        self.dispositivo = dispositivo or escolher_dispositivo(torch)

        nome_dtype = os.environ.get(
            "PAINEL_DTYPE", "float16" if self.dispositivo == "cuda" else "float32"
        )
        self.dtype = getattr(torch, nome_dtype)

        inicio = time.perf_counter()
        self.tokenizador = AutoTokenizer.from_pretrained(
            self.modelo_nome, local_files_only=apenas_local
        )
        self.modelo = AutoModelForCausalLM.from_pretrained(
            self.modelo_nome, dtype=self.dtype, local_files_only=apenas_local
        ).to(self.dispositivo)
        self.modelo.eval()
        self.segundos_para_carregar = time.perf_counter() - inicio

        # Cada letra precisa ser UM token, senao a nota da "proxima palavra"
        # nao representa a opcao inteira.
        self.ids_letras = []
        for letra in LETRAS:
            ids = self.tokenizador.encode(letra, add_special_tokens=False)
            if len(ids) != 1:
                raise ValueError(
                    f"O tokenizador de {self.modelo_nome} quebra a letra "
                    f"{letra!r} em {len(ids)} pedacos - este modelo nao serve "
                    "para a pontuacao por letras."
                )
            self.ids_letras.append(ids[0])

        self.memoria_mb = round(self.modelo.get_memory_footprint() / 2**20, 1)

    @property
    def descricao(self):
        return f"{self.modelo_nome} · {str(self.dtype).replace('torch.', '')} · {self.dispositivo}"

    def analisar(self, texto, tipo):
        """
        Devolve {"categoria", "confianca", "alternativas", "trecho", "pistas"}.

        "confianca" e a probabilidade que o modelo deu a categoria escolhida.
        NAO e a chance de acerto - a bancada mostra erros com confianca alta.
        """
        torch = self.torch
        trecho = recortar(texto)
        nomes = categorias(tipo)
        mensagens = [
            {"role": "system", "content": INSTRUCAO},
            {"role": "user", "content": montar_pergunta(trecho, tipo)},
        ]
        entrada = self.tokenizador.apply_chat_template(
            mensagens,
            add_generation_prompt=True,
            return_tensors="pt",
            return_dict=True,
            enable_thinking=False,  # modelos que "pensam" (Qwen3) respondem direto
        ).to(self.dispositivo)

        with torch.no_grad():
            saida = self.modelo(**entrada)

        # a nota da PROXIMA palavra - so das letras das opcoes desta tarefa
        notas = saida.logits[0, -1, self.ids_letras[: len(nomes)]].float()
        probabilidades = torch.softmax(notas, dim=0).tolist()

        ordem = sorted(zip(nomes, probabilidades), key=lambda par: par[1], reverse=True)
        return {
            "categoria": ordem[0][0],
            "confianca": round(ordem[0][1], 4),
            "alternativas": [(c, round(p, 4)) for c, p in ordem],
            "trecho": trecho,
            "pistas": [],  # um modelo nao aponta palavras: ele le o trecho todo
        }
