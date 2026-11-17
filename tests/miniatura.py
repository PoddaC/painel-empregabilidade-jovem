"""
miniatura.py - um modelo de conversa MINUSCULO e aleatorio, criado na hora.

Serve para testar o CAMINHO do codigo do AnalisadorLLM (tokenizador, chat
template, pontuacao das letras, softmax, dispositivo) sem baixar gigabytes.
Ele nao sabe nada - as respostas sao ao acaso. O ACERTO de um modelo de
verdade so a bancada mede (python -m src.bancada).
"""

from tokenizers import Tokenizer, models, pre_tokenizers, decoders, trainers


TEMPLATE = (
    "{% for m in messages %}<|{{ m['role'] }}|>{{ m['content'] }}<|fim|>{% endfor %}"
    "{% if add_generation_prompt %}<|assistant|>{% endif %}"
)


def criar_modelo_miniatura(pasta):
    import torch
    from transformers import PreTrainedTokenizerFast, Qwen2Config, Qwen2ForCausalLM

    torch.manual_seed(0)
    tok = Tokenizer(models.BPE())
    tok.pre_tokenizer = pre_tokenizers.ByteLevel(add_prefix_space=False)
    tok.decoder = decoders.ByteLevel()
    especiais = ["<|fim|>", "<|system|>", "<|user|>", "<|assistant|>"]
    treino = trainers.BpeTrainer(
        vocab_size=400, special_tokens=especiais,
        initial_alphabet=pre_tokenizers.ByteLevel.alphabet(),
    )
    corpus = ["Brasil gerou vagas de emprego em agosto.", "A B C D E F G opções notícia"] * 50
    tok.train_from_iterator(corpus, treino)

    tokenizador = PreTrainedTokenizerFast(tokenizer_object=tok, eos_token="<|fim|>", pad_token="<|fim|>")
    tokenizador.chat_template = TEMPLATE
    tokenizador.save_pretrained(pasta)

    config = Qwen2Config(
        vocab_size=tokenizador.vocab_size, hidden_size=32, intermediate_size=64,
        num_hidden_layers=2, num_attention_heads=2, num_key_value_heads=1,
        max_position_embeddings=4096,
    )
    Qwen2ForCausalLM(config).save_pretrained(pasta)
    return str(pasta)
