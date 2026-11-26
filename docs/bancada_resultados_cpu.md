# Resultados da bancada — 25/11/2026 19:29

Gerado por `python -m src.bancada`. Não edite à mão: rode de novo.

**Máquina:** Windows 11 · Python 3.12.10 · CPU: Intel64 Family 6 Model 183 Stepping 1, GenuineIntel · 16 nucleos logicos · torch 2.15.0+cu132 · GPU: NVIDIA GeForce RTX 4060 Ti

**Banco de provas:** 42 notícias reais do acervo, rotuladas à mão antes da medição (`data/analisador/banco_de_provas.csv`). Cada notícia é analisada nas duas tarefas.

**Dispositivo pedido:** `PAINEL_DISPOSITIVO=cpu` (o dispositivo de cada modelo aparece embaixo do nome).

Tempos sem a 1ª análise (aquecimento). p95 = o tempo que 95% das análises não passam.

| Candidato | Tendência (certos/erros/calados) | Setor (certos/erros/calados) | Erros com confiança ≥ 0,9 | Memória dos pesos | Pico na GPU | Pico de RAM | Carga | s por análise (média · mediana · p95) |
|---|---|---|---|---|---|---|---|---|
| sempre-a-mais-comum<br><sub>chuta a categoria mais frequente do banco</sub> | 26/42 · 16 · 0 | 31/42 · 11 · 0 | 0 | 0 MB | —  | —  | 0 s | 0 · 0 · 0 |
| regras<br><sub>regras (palavras-chave)</sub> | 29/42 · 11 · 2 | 27/42 · 10 · 5 | 8 | 0 MB | —  | 567 MB | 0.0 s | 0.001 · 0.001 · 0.001 |
| qwen15<br><sub>Qwen/Qwen2.5-1.5B-Instruct · float32 · cpu</sub> | 29/42 · 13 · 0 | 25/42 · 17 · 0 | 6 | 5889 MB | —  | 7374 MB | 7.3 s | 14.459 · 14.441 · 16.424 |

## Onde cada candidato errou

**regras** — 28 respostas fora do rótulo

- [tendencia] Ocupação de pessoas 60+ sobe 53% em 10 anos; ritmo supera o dos jovens — esperado *neutra*, veio *otimista* (1.00)
- [tendencia] Taxa de informalidade cai no mercado de trabalho, mostra IBGE — esperado *otimista*, veio *(calou)* (0.00)
- [tendencia] Marinho diz que juros pesaram mais que tarifaço no emprego em 2025 — esperado *pessimista*, veio *otimista* (0.50)
- [setor] Brasil cria 85,8 mil vagas de trabalho em novembro — esperado *geral*, veio *industria* (0.17)
- [tendencia] Jovens veem conhecimento em IA como diferencial para emprego — esperado *neutra*, veio *otimista* (1.00)
- [setor] Jovens veem conhecimento em IA como diferencial para emprego — esperado *geral*, veio *(calou)* (0.00)
- [setor] Brasileiros acreditam que economia verde trará novos empregos — esperado *geral*, veio *industria* (1.00)
- [tendencia] Brasil abre 129,8 mil postos formais de trabalho em julho — esperado *pessimista*, veio *otimista* (0.50)
- [tendencia] Metade das demissões em 2024 foi causada por questões comportamentais — esperado *neutra*, veio *pessimista* (1.00)
- [setor] Metade das demissões em 2024 foi causada por questões comportamentais — esperado *geral*, veio *(calou)* (0.00)
- [tendencia] Jornada 6x1 é cruel, diz ministro do Trabalho, Luiz Marinho — esperado *neutra*, veio *otimista* (0.33)
- [setor] Jornada 6x1 é cruel, diz ministro do Trabalho, Luiz Marinho — esperado *geral*, veio *construcao* (1.00)
- [setor] Entenda nova rodada de saques do FGTS a quem tem saque-aniversário — esperado *geral*, veio *servicos* (1.00)
- [tendencia] Carteira de Trabalho Digital agora permite consultas a vagas do Sine — esperado *neutra*, veio *otimista* (0.50)
- [setor] Carteira de Trabalho Digital agora permite consultas a vagas do Sine — esperado *geral*, veio *servicos* (0.67)
- [setor] Caged registra a criação de 106,6 mil postos de trabalho em novembro — esperado *geral*, veio *construcao* (0.29)
- [tendencia] Confiança do consumidor mantém estabilidade em novembro, aponta ACSP — esperado *neutra*, veio *otimista* (0.50)
- [setor] Confiança do consumidor mantém estabilidade em novembro, aponta ACSP — esperado *geral*, veio *(calou)* (0.00)
- [tendencia] PEC 6x1: cresce a pressão pela aprovação da proposta — esperado *neutra*, veio *otimista* (0.50)
- [setor] PEC 6x1: cresce a pressão pela aprovação da proposta — esperado *geral*, veio *servicos* (1.00)
- [tendencia] Fórmula 1 injetará R$ 2 bilhões na economia paulistana, estima SPTuris — esperado *otimista*, veio *(calou)* (0.00)
- [setor] Brasil gerou mais de 235 mil novos postos de trabalho em agosto — esperado *geral*, veio *industria* (0.40)
- [tendencia] Indústria cria menos vagas de trabalho, mas paga salários mais altos — esperado *neutra*, veio *otimista* (1.00)
- [setor] Países da OCDE reduzem percentual de jovens nem-nem — esperado *geral*, veio *(calou)* (0.00)
- [setor] Renda média dos trabalhadores tem crescimento interanual de 5,8% — esperado *geral*, veio *setor_publico* (0.50)
- [tendencia] Dólar cai para R$ 5,46 e tem primeira queda semanal em um mês e meio — esperado *neutra*, veio *otimista* (0.50)
- [setor] Dólar cai para R$ 5,46 e tem primeira queda semanal em um mês e meio — esperado *geral*, veio *(calou)* (0.00)
- [setor] Mesmo na pandemia, emprego na construção cresceu 21,6%, revela IBGE — esperado *construcao*, veio *industria* (0.33)

**qwen15** — 30 respostas fora do rótulo

- [setor] Transpetro abre concurso público com salário inicial de até R$ 15 mil — esperado *setor_publico*, veio *industria* (0.83)
- [tendencia] Ocupação de pessoas 60+ sobe 53% em 10 anos; ritmo supera o dos jovens — esperado *neutra*, veio *otimista* (0.99)
- [setor] Marinho diz que juros pesaram mais que tarifaço no emprego em 2025 — esperado *geral*, veio *agropecuaria* (0.41)
- [setor] Brasil cria 85,8 mil vagas de trabalho em novembro — esperado *geral*, veio *servicos* (0.53)
- [tendencia] Jovens veem conhecimento em IA como diferencial para emprego — esperado *neutra*, veio *otimista* (1.00)
- [setor] Taxa de desemprego cai para 5,4%, a menor desde 2012 — esperado *geral*, veio *servicos* (0.69)
- [setor] Com mercado aquecido, 53,8% descartam perda de emprego — esperado *geral*, veio *industria* (0.44)
- [setor] Brasil abre 129,8 mil postos formais de trabalho em julho — esperado *geral*, veio *comercio* (0.33)
- [tendencia] Metade das demissões em 2024 foi causada por questões comportamentais — esperado *neutra*, veio *pessimista* (0.95)
- [tendencia] TV Brasil discute as jornadas de trabalho e propostas no Congresso — esperado *neutra*, veio *pessimista* (0.80)
- [setor] Brasil tem saldo positivo de 148,9 mil empregos com carteira assinada — esperado *geral*, veio *servicos* (0.79)
- [setor] iFood anuncia mudanças, mas representantes de entregadores criticam — esperado *servicos*, veio *geral* (0.50)
- [setor] Sindicato promove feira de empregabilidade na semana LGBTQIA+ — esperado *comercio*, veio *geral* (0.68)
- [tendencia] Jornada 6x1 é cruel, diz ministro do Trabalho, Luiz Marinho — esperado *neutra*, veio *pessimista* (1.00)
- [setor] Jornada 6x1 é cruel, diz ministro do Trabalho, Luiz Marinho — esperado *geral*, veio *agropecuaria* (0.30)
- [tendencia] Entenda nova rodada de saques do FGTS a quem tem saque-aniversário — esperado *neutra*, veio *pessimista* (0.98)
- [setor] Entenda nova rodada de saques do FGTS a quem tem saque-aniversário — esperado *geral*, veio *industria* (0.25)
- [setor] Empregos com carteira assinada fecham 2024 com volume recorde — esperado *geral*, veio *servicos* (0.64)
- [tendencia] Carteira de Trabalho Digital agora permite consultas a vagas do Sine — esperado *neutra*, veio *otimista* (0.90)
- [tendencia] Dólar sobe para R$ 6,10 após dados sobre emprego nos Estados Unidos — esperado *neutra*, veio *pessimista* (0.68)
- [setor] Caged registra a criação de 106,6 mil postos de trabalho em novembro — esperado *geral*, veio *comercio* (0.70)
- [tendencia] Confiança do consumidor mantém estabilidade em novembro, aponta ACSP — esperado *neutra*, veio *otimista* (0.64)
- [tendencia] PEC 6x1: cresce a pressão pela aprovação da proposta — esperado *neutra*, veio *pessimista* (0.83)
- [setor] Fórmula 1 injetará R$ 2 bilhões na economia paulistana, estima SPTuris — esperado *servicos*, veio *industria* (0.36)
- [setor] Brasil gerou mais de 235 mil novos postos de trabalho em agosto — esperado *geral*, veio *servicos* (0.80)
- [tendencia] Indústria cria menos vagas de trabalho, mas paga salários mais altos — esperado *neutra*, veio *pessimista* (0.99)
- [tendencia] Países da OCDE reduzem percentual de jovens nem-nem — esperado *otimista*, veio *pessimista* (0.86)
- [tendencia] Dólar cai para R$ 5,46 e tem primeira queda semanal em um mês e meio — esperado *neutra*, veio *otimista* (0.64)
- [setor] Dólar cai para R$ 5,46 e tem primeira queda semanal em um mês e meio — esperado *geral*, veio *industria* (0.56)
- [setor] Mesmo na pandemia, emprego na construção cresceu 21,6%, revela IBGE — esperado *construcao*, veio *comercio* (0.83)
