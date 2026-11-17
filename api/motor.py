"""
api/motor.py - onde mora o modelo carregado, e como ele e carregado.

O modelo e carregado UMA vez, quando a API sobe, e fica em MOTORES.
Se nao carregar, a API sobe mesmo assim: so a analise responde 503.

Variaveis de ambiente (todas opcionais):
    PAINEL_MOTOR       llm (padrao) | regras
    PAINEL_MODELO      nome do modelo no Hub (padrao: o da bancada)
    PAINEL_DISPOSITIVO auto (padrao) | cuda | cpu
    PAINEL_LIMITE_S    segundos maximos por analise (padrao 60)
"""

import logging
import os
import time
from concurrent.futures import ThreadPoolExecutor

log = logging.getLogger("api")

MOTORES = {}            # "analise" -> o motor carregado
ESTADO = {"motivo": None}

# Um trabalhador: as analises fazem fila em vez de dividir a GPU.
# O limite de tempo conta a espera na fila.
EXECUTOR = ThreadPoolExecutor(max_workers=1, thread_name_prefix="motor")


def limite_segundos():
    return float(os.environ.get("PAINEL_LIMITE_S", "60"))


def carregar():
    """Carrega o motor pedido. Nunca levanta: em caso de falha, guarda o motivo."""
    tipo = os.environ.get("PAINEL_MOTOR", "llm")
    inicio = time.perf_counter()
    try:
        if tipo == "regras":
            from src.motor_regras import MotorRegras
            motor = MotorRegras()
        else:
            from src.analisador_llm import AnalisadorLLM
            motor = AnalisadorLLM()
    except ImportError as falha:
        return _falhou(
            f"faltam bibliotecas do modelo ({falha.name}). Instale: "
            "pip install -r requirements-api.txt."
        )
    except OSError as falha:
        # local_files_only=True: o modelo nao esta no disco desta maquina
        log.error("Modelo NAO carregado - %s", falha)
        return _falhou(
            "o modelo nao foi encontrado nesta maquina. Baixe uma vez, com "
            "internet: python -m src.baixar_modelo."
        )
    except Exception as falha:  # memoria insuficiente, modelo incompativel...
        log.error("Modelo NAO carregado - %s: %s", type(falha).__name__, falha)
        return _falhou(f"o modelo nao carregou ({type(falha).__name__}). Veja o terminal da API.")

    MOTORES["analise"] = motor
    ESTADO["motivo"] = None
    log.info("[motor] %s carregado em %.1f s", motor.descricao, time.perf_counter() - inicio)


def _falhou(motivo):
    MOTORES.pop("analise", None)
    ESTADO["motivo"] = motivo
    log.error("[motor] indisponivel: %s", motivo)


def descarregar():
    MOTORES.clear()
