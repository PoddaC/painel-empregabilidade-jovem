"""
espiar_modelo.py - o que o modelo ESCREVERIA, e quanto da aposta dele cai nas letras.

    python -m src.espiar_modelo Qwen/Qwen3-1.7B
    python -m src.espiar_modelo Qwen/Qwen2.5-1.5B-Instruct

A analise pontua so as letras das opcoes (A, B, C...). Isso so vale se o
modelo de fato QUER responder com uma letra. Se a primeira palavra que ele
escreveria e outra coisa (um "**", um "A resposta e"...), a nota das letras
e um resto de probabilidade - e a "escolha" vira ruido com confianca alta.

Este script mostra, para uma noticia, a "massa nas letras" (quanto da
aposta total do modelo foi para as letras) e o que ele escreveria.
"""

import sys

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from src.analisador_llm import INSTRUCAO, LETRAS, montar_pergunta
from src.data_access import carregar_noticias, ler_texto
from src.tarefas import categorias, montar_texto, recortar

nome = sys.argv[1] if len(sys.argv) > 1 else "Qwen/Qwen2.5-1.5B-Instruct"
disp = "cuda" if torch.cuda.is_available() else "cpu"
tok = AutoTokenizer.from_pretrained(nome, local_files_only=True)
modelo = AutoModelForCausalLM.from_pretrained(
    nome, dtype=torch.float16 if disp == "cuda" else torch.float32, local_files_only=True
).to(disp)

n = carregar_noticias()[0][2]  # "Brasil fecha o mes de junho com saldo positivo..."
texto = recortar(montar_texto(n["titulo"], n.get("resumo", ""), ler_texto(n)))
print(f"Noticia: {n['titulo']}\n")

for tipo in ("tendencia", "setor"):
    mensagens = [{"role": "system", "content": INSTRUCAO},
                 {"role": "user", "content": montar_pergunta(texto, tipo)}]
    entrada = tok.apply_chat_template(
        mensagens, add_generation_prompt=True, return_tensors="pt",
        return_dict=True, enable_thinking=False,
    ).to(disp)
    with torch.no_grad():
        prob = torch.softmax(modelo(**entrada).logits[0, -1].float(), -1)
        saida = modelo.generate(**entrada, max_new_tokens=15, do_sample=False)
    ids = [tok.encode(l, add_special_tokens=False)[0] for l in LETRAS[: len(categorias(tipo))]]
    top = [(tok.decode(i), round(v.item(), 3)) for v, i in zip(*prob.topk(5))]
    print(f"[{tipo}]")
    print(f"  fim do prompt:    {tok.decode(entrada['input_ids'][0][-8:])!r}")
    print(f"  massa nas letras: {prob[ids].sum().item():.3f}   (perto de 1 = o metodo vale)")
    print(f"  5 mais provaveis: {top}")
    print(f"  escreveria:       {tok.decode(saida[0][entrada['input_ids'].shape[1]:])!r}\n")
