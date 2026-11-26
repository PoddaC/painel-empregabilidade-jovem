"""
test_ibge.py - o coletor do IBGE, sem internet.

Os JSONs abaixo imitam o formato da API de agregados v3 do IBGE
(metadados e valores). O que a API devolve DE VERDADE so a coleta ao vivo
confere: python -m src.coletar_ibge.
"""

import pytest

from src.coletar_ibge import descobrir, nome_do_periodo, numero, para_linhas

META = {
    "id": 4094,
    "nivelTerritorial": {"Administrativo": ["N1", "N2", "N3"]},
    "variaveis": [
        {"id": 4088, "nome": "Pessoas de 14 anos ou mais de idade", "unidade": "Mil pessoas"},
        {"id": 4099, "nome": "Taxa de desocupação, na semana de referência, das pessoas de 14 anos ou mais de idade", "unidade": "%"},
    ],
    "classificacoes": [{
        "id": 58, "nome": "Grupo de idade",
        "categorias": [
            {"id": 95253, "nome": "Total"},
            {"id": 114535, "nome": "14 a 17 anos"},
            {"id": 100052, "nome": "18 a 24 anos"},
            {"id": 108875, "nome": "25 a 39 anos"},
        ],
    }],
}


def serie(nivel, nome, valores):
    return {"localidade": {"id": "1", "nivel": {"id": nivel, "nome": "x"}, "nome": nome},
            "serie": valores}


RESPOSTA = [{
    "id": "4099", "variavel": "Taxa de desocupação", "unidade": "%",
    "resultados": [
        {"classificacoes": [{"id": "58", "nome": "Grupo de idade", "categoria": {"100052": "18 a 24 anos"}}],
         "series": [serie("N1", "Brasil", {"202501": "14.1", "202502": "13.8"}),
                    serie("N3", "Bahia", {"202501": "...", "202502": "20.5"})]},
        {"classificacoes": [{"id": "58", "nome": "Grupo de idade", "categoria": {"95253": "Total"}}],
         "series": [serie("N1", "Brasil", {"202502": "6.1"})]},
        {"classificacoes": [{"id": "58", "nome": "Grupo de idade", "categoria": {"108875": "25 a 39 anos"}}],
         "series": [serie("N1", "Brasil", {"202502": "5.6"})]},
    ],
}]


def test_descobre_os_codigos_pelos_nomes():
    a = descobrir(META)
    assert a["variavel"] == "4099" and a["classificacao"] == "58"
    assert a["categorias"] == {"95253": "total", "114535": "14 a 17 anos", "100052": "18 a 24 anos"}
    assert a["niveis"] == ["N1", "N2", "N3"]


def test_tabela_mudou_e_erro_com_frase():
    sem_jovens = {**META, "classificacoes": [{"id": 58, "nome": "Grupo de idade",
                                              "categorias": [{"id": 1, "nome": "Total"}]}]}
    with pytest.raises(ValueError, match="14 a 17"):
        descobrir(sem_jovens)
    with pytest.raises(ValueError, match="Taxa de desocupacao"):
        descobrir({**META, "variaveis": []})


def test_achata_e_pula_o_que_nao_tem_valor():
    linhas = para_linhas(RESPOSTA, descobrir(META), "2026-11-23T19:00:00")
    # '...' da Bahia em 2025-T1 e o grupo 25-39 (nao pedido) ficam de fora
    assert len(linhas) == 4
    bahia = [l for l in linhas if l["localidade"] == "Bahia"]
    assert bahia == [{"periodo": "2025-T2", "periodo_codigo": "202502", "nivel": "UF",
                      "localidade": "Bahia", "grupo_idade": "18 a 24 anos",
                      "taxa_desocupacao_pct": 20.5, "tabela": 4094,
                      "coletado_em": "2026-11-23T19:00:00"}]


def test_periodo_e_numero():
    assert nome_do_periodo("202604") == "2026-T4"
    assert numero("13,8") == 13.8
    assert numero("...") is None and numero("-") is None and numero(None) is None
