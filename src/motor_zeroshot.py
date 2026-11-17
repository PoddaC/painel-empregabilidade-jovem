"""
motor_zeroshot.py - o candidato da familia "BERT": classificacao zero-shot.

Usado pela BANCADA, nao pela API. Um modelo treinado em inferencia textual
(NLI) responde "esta frase decorre do texto?" para cada categoria, e a que
mais "decorre" vence. Nao precisa de exemplos rotulados - dai o zero-shot.
"""

import os
import time

from src.analisador_llm import escolher_dispositivo
from src.tarefas import TAREFAS, categorias, recortar

MODELO_PADRAO = "MoritzLaurer/mDeBERTa-v3-base-xnli-multilingual-nli-2mil7"

# A frase que o modelo testa contra o texto, com a definicao no lugar de {}.
HIPOTESES = {
    "tendencia": "Esta notícia {}.",
    "setor": "Esta notícia é sobre {}.",
}


class MotorZeroShot:
    def __init__(self, modelo=None, dispositivo=None, apenas_local=True):
        import torch
        from transformers import (AutoModelForSequenceClassification,
                                  AutoTokenizer, pipeline)

        self.modelo_nome = modelo or MODELO_PADRAO
        self.dispositivo = dispositivo or escolher_dispositivo(torch)
        nome_dtype = os.environ.get(
            "PAINEL_DTYPE", "float16" if self.dispositivo == "cuda" else "float32"
        )
        self.dtype = getattr(torch, nome_dtype)

        inicio = time.perf_counter()
        tokenizador = AutoTokenizer.from_pretrained(
            self.modelo_nome, local_files_only=apenas_local
        )
        modelo = AutoModelForSequenceClassification.from_pretrained(
            self.modelo_nome, dtype=self.dtype, local_files_only=apenas_local
        )
        self.pipe = pipeline(
            "zero-shot-classification", model=modelo, tokenizer=tokenizador,
            device=self.dispositivo,
        )
        self.segundos_para_carregar = time.perf_counter() - inicio
        self.memoria_mb = round(
            sum(p.numel() * p.element_size() for p in modelo.parameters()) / 2**20, 1
        )

    @property
    def descricao(self):
        return f"{self.modelo_nome} · {str(self.dtype).replace('torch.', '')} · {self.dispositivo}"

    def analisar(self, texto, tipo):
        trecho = recortar(texto)
        nomes = categorias(tipo)
        definicoes = {
            TAREFAS[tipo]["categorias"][c]["definicao"]: c for c in nomes
        }
        r = self.pipe(
            trecho,
            candidate_labels=list(definicoes),
            hypothesis_template=HIPOTESES[tipo],
        )
        ordem = [(definicoes[l], round(s, 4)) for l, s in zip(r["labels"], r["scores"])]
        return {
            "categoria": ordem[0][0],
            "confianca": ordem[0][1],
            "alternativas": ordem,
            "trecho": trecho,
            "pistas": [],
        }
