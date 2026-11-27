"""test_indicadores.py - as contas que as paginas mostram (sem tela)."""

from src.indicadores import milhar, pct, resumo_ibge, trimestre_de


def linha(lugar, nivel, grupo, codigo, taxa):
    return {"localidade": lugar, "nivel": nivel, "grupo_idade": grupo, "periodo_codigo": codigo,
            "periodo": f"{codigo[:4]}-T{int(codigo[4:])}", "taxa_desocupacao_pct": taxa,
            "coletado_em": "2026-11-25T19:00:00"}


LINHAS = [
    linha("Brasil", "Brasil", "18 a 24 anos", "202503", 12.3),
    linha("Brasil", "Brasil", "18 a 24 anos", "202603", 11.1),
    linha("Brasil", "Brasil", "total", "202603", 5.2),
    linha("Bahia", "UF", "18 a 24 anos", "202603", 14.4),
    linha("Santa Catarina", "UF", "18 a 24 anos", "202603", 4.7),
    linha("Bahia", "UF", "18 a 24 anos", "202503", 19.2),  # ano anterior: fora do ranking
]


def test_resumo():
    r = resumo_ibge(LINHAS)
    assert r["periodo"] == "2026-T3"
    assert r["brasil"]["18 a 24 anos"] == 11.1 and r["brasil_antes"]["18 a 24 anos"] == 12.3
    assert r["brasil"]["14 a 17 anos"] is None                      # sem dado: None, nao zero
    assert r["ufs"] == [("Bahia", 14.4), ("Santa Catarina", 4.7)]   # so o ultimo trimestre, maior primeiro
    assert [p["trimestre"] for p in r["serie"]] == ["2025-T3", "2026-T3"]


def test_sem_dados():
    assert resumo_ibge([]) is None


def test_formatos():
    assert pct(11.1) == "11,1%" and pct(None) == "—"
    assert milhar(1787) == "1.787"
    assert trimestre_de("2025-08") == "2025-T3" and trimestre_de("2026-01") == "2026-T1"
