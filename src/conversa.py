"""
conversa.py - responder UMA pergunta da conversa. O mesmo codigo para:

- a API (POST /conversa), que guarda a conversa em arquivo, por id;
- o painel no Streamlit Cloud, onde a API nao roda: la a pagina Conversa
  chama esta funcao direto e guarda a conversa so na sessao do navegador.

Um lugar so para a regra: memoria -> fatos -> modelo online -> conferencia.
Quem chama decide onde a conversa mora.
"""

from datetime import datetime

from src import llm_api, memoria
from src.checagem import numeros_sem_fonte


def nova(memoria_escolhida="notas"):
    agora = datetime.now().isoformat(timespec="seconds")
    return {"id": None, "criada_em": agora, "atualizada_em": agora,
            "memoria": memoria_escolhida, "mensagens": [], "notas": None,
            "resumo": "", "resumo_ate": 0, "chamadas_de_resumo": 0}


def responder(conversa, pergunta, memoria_escolhida):
    """
    Altera `conversa` (acrescenta a troca, as notas e, se for o caso, o resumo)
    e devolve o dicionario da resposta, no formato de RespostaConversa (sem o id).
    Levanta llm_api.LLMIndisponivel se nenhum provedor responder - e entao
    `conversa` fica como estava.
    """
    resumiu = False
    resumo_novo = None
    if memoria_escolhida == "resumo" and memoria.precisa_resumir(conversa):
        instr, msgs, ate = memoria.pedido_de_resumo(conversa)
        r = llm_api.completar(instr, msgs, max_tokens=300)  # UMA chamada a mais
        resumo_novo = (r["texto"], ate)
        conversa = {**conversa, "resumo": r["texto"], "resumo_ate": ate}
        resumiu = True

    instrucoes, mensagens, leitura = memoria.montar(conversa, pergunta, memoria_escolhida)
    r = llm_api.completar(instrucoes, mensagens)
    suspeitos = numeros_sem_fonte(r["texto"], leitura["fatos"])

    # So agora, com a resposta em maos, a conversa muda.
    return resumo_novo, r, leitura, suspeitos, resumiu


def registrar(conversa, pergunta, memoria_escolhida, resultado):
    """Grava na conversa (em memoria) a troca que `responder` produziu."""
    resumo_novo, r, leitura, suspeitos, resumiu = resultado
    agora = datetime.now().isoformat(timespec="seconds")
    if resumo_novo:
        conversa["resumo"], conversa["resumo_ate"] = resumo_novo
        conversa["chamadas_de_resumo"] = conversa.get("chamadas_de_resumo", 0) + 1
    conversa["memoria"] = memoria_escolhida
    conversa["notas"] = memoria.anotar(conversa.get("notas"), pergunta)  # sempre anota (e barato)
    conversa["mensagens"] += [
        {"papel": "user", "texto": pergunta, "quando": agora},
        {"papel": "assistant", "texto": r["texto"], "quando": agora,
         "provedor": f"{r['provedor']} · {r['modelo']}", "numeros_sem_fonte": suspeitos},
    ]
    conversa["atualizada_em"] = agora
    return {
        "conversa_id": conversa.get("id"), "resposta": r["texto"], "provedor": r["provedor"],
        "modelo": r["modelo"], "segundos": r["segundos"], "tokens_entrada": r["tokens_entrada"],
        "tokens_saida": r["tokens_saida"], "chamada_de_resumo": resumiu,
        "numeros_sem_fonte": suspeitos, "falhas_antes": r["tentativas"], "leitura": leitura,
    }
