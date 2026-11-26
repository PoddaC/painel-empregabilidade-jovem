"""
memoria.py - o que o modelo LE da conversa a cada pergunta.

O modelo nao lembra nada entre uma chamada e outra: quem lembra e o painel,
que reenvia parte da conversa. As quatro memorias da Aula 17-18:

    inteira  todas as mensagens                 cresce sem parar
    janela   as ultimas JANELA trocas            para de crescer, mas esquece
    resumo   ultimas trocas + resumo do resto    o resumo custa uma chamada a mais
    notas    ultimas NOTAS_TROCAS trocas         para de crescer e lembra:
             + lugares e grupos ja citados,      o Python anota (sem modelo)
               anotados pelo Python

As ENTIDADES (lugares e grupos de idade) que a memoria "ve" decidem tambem
quais FATOS entram nas instrucoes: se a janela esqueceu a Bahia, os fatos da
Bahia tambem saem. E isso que o teste de 10 perguntas mede.
"""

from src.data_access import BASE
from src.fatos import achar_entidades, montar_fatos

MEMORIAS = ("inteira", "janela", "resumo", "notas")
PADRAO = "notas"
JANELA = 3        # trocas (pergunta + resposta) na janela e no resumo
NOTAS_TROCAS = 2  # trocas recentes que acompanham as notas

DESCRICAO = {
    "inteira": "Reenvia a conversa toda. Lembra de tudo, mas o custo cresce a cada pergunta.",
    "janela": f"Reenvia só as últimas {JANELA} trocas. Custo fixo, mas esquece o começo.",
    "resumo": f"Últimas {JANELA} trocas + um resumo do resto, feito pelo modelo (uma chamada a mais).",
    "notas": f"Últimas {NOTAS_TROCAS} trocas + os lugares e grupos já citados, anotados pelo Python. "
             "Custo quase fixo, sem chamada a mais.",
}

PROMPTS = BASE / "prompts"


def _prompt(nome):
    return (PROMPTS / nome).read_text(encoding="utf-8")


def _juntar(entidades_lista):
    """Une listas de entidades mantendo a ordem da primeira aparicao."""
    lugares, grupos = [], []
    for e in entidades_lista:
        lugares += [x for x in e["lugares"] if x not in lugares]
        grupos += [x for x in e["grupos"] if x not in grupos]
    return {"lugares": lugares, "grupos": grupos}


def anotar(notas, pergunta):
    """A memoria de notas: acrescenta o que a pergunta cita. Sem modelo."""
    notas = notas or {"lugares": [], "grupos": []}
    nova = achar_entidades(pergunta)
    juntas = _juntar([notas, nova])
    # O grupo "em foco" e o ultimo citado: "e em SP?" herda o grupo da pergunta anterior.
    juntas["grupo_em_foco"] = nova["grupos"][-1] if nova["grupos"] else notas.get("grupo_em_foco")
    return juntas


def _ultimas(mensagens, trocas):
    return mensagens[-2 * trocas:] if trocas else []


def precisa_resumir(conversa):
    """Na memoria de resumo: ha mensagens fora da janela ainda nao resumidas?"""
    fora = len(conversa["mensagens"]) - 2 * JANELA
    return fora > conversa.get("resumo_ate", 0)


def pedido_de_resumo(conversa):
    """(instrucao, mensagens) para a chamada que atualiza o resumo."""
    fora = len(conversa["mensagens"]) - 2 * JANELA
    novas = conversa["mensagens"][conversa.get("resumo_ate", 0):fora]
    texto = "\n".join(f"{'Pessoa' if m['papel'] == 'user' else 'Assistente'}: {m['texto']}" for m in novas)
    instr = _prompt("conversa_resumo.txt").format(resumo=conversa.get("resumo") or "(vazio)", mensagens=texto)
    return instr, [{"papel": "user", "texto": "Atualize o resumo."}], fora


def montar(conversa, pergunta, memoria):
    """
    Monta o que vai ao modelo. Devolve (instrucoes, mensagens, leitura), onde
    leitura descreve o que o modelo leu - a pagina mostra isso ao usuario.
    """
    msgs = conversa["mensagens"]
    atual = achar_entidades(pergunta)
    notas_txt = ""

    if memoria == "inteira":
        enviadas = list(msgs)
        foco = _juntar([achar_entidades(m["texto"]) for m in msgs if m["papel"] == "user"] + [atual])
    elif memoria == "janela":
        enviadas = _ultimas(msgs, JANELA)
        foco = _juntar([achar_entidades(m["texto"]) for m in enviadas if m["papel"] == "user"] + [atual])
    elif memoria == "resumo":
        enviadas = _ultimas(msgs, JANELA)
        resumo = conversa.get("resumo") or ""
        foco = _juntar([achar_entidades(resumo)]
                       + [achar_entidades(m["texto"]) for m in enviadas if m["papel"] == "user"] + [atual])
        if resumo:
            notas_txt = f"\nRESUMO do começo da conversa (feito pelo modelo): {resumo}\n"
    elif memoria == "notas":
        enviadas = _ultimas(msgs, NOTAS_TROCAS)
        notas = anotar(conversa.get("notas"), pergunta)
        foco = {"lugares": notas["lugares"], "grupos": notas["grupos"]}
        if notas["lugares"] or notas["grupos"]:
            notas_txt = ("\nNOTAS (anotadas pelo painel): lugares que a pessoa já citou, na ordem: "
                         + (", ".join(notas["lugares"]) or "nenhum")
                         + f". Grupo de idade em foco: {notas['grupo_em_foco'] or 'não dito'}.\n")
    else:
        raise ValueError(f"memoria desconhecida: {memoria}")

    # Se a pergunta nao cita grupo, o grupo em foco das notas (ou 18-24) decide os fatos.
    grupos = foco["grupos"]
    fatos = montar_fatos(foco["lugares"], grupos)
    instrucoes = _prompt("conversa_sistema.txt").format(notas=notas_txt, fatos=fatos)
    mensagens = [{"papel": m["papel"], "texto": m["texto"]} for m in enviadas]
    mensagens.append({"papel": "user", "texto": pergunta})
    leitura = {
        "memoria": memoria,
        "mensagens_enviadas": len(mensagens),
        "mensagens_na_conversa": len(msgs) + 1,
        "lugares_em_foco": foco["lugares"],
        "notas": notas_txt.strip() or None,
        "fatos": fatos,
    }
    return instrucoes, mensagens, leitura
