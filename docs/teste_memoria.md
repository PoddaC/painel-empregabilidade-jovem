# Teste de 10 perguntas — 25/11/2026 23:17

Gerado por `python -m src.teste_memoria`. Não edite à mão: rode de novo.

As mesmas 10 perguntas para cada memória, contra a API de verdade e o modelo online. As perguntas 2 a 10 dependem da conversa; a 10ª volta ao primeiro estado. Cada resposta é corrigida pelo Python, com os valores do mesmo CSV do IBGE que o painel lê.

| Memória | Acertos | 10ª (volta ao 1º estado) | Tokens de entrada: 1ª → 10ª | Tokens no total | Chamadas a mais | Segundos por resposta (média) | Números sem fonte |
|---|---|---|---|---|---|---|---|
| **notas** | 10/10 | ✓ | 868 → 1386 | 12951 | 0 | 1.0 | 0 |
| **inteira** | 10/10 | ✓ | 833 → 1951 | 14606 | 0 | 0.9 | 0 |
| **janela** | 9/10 | ✗ | 833 → 1196 | 11590 | 0 | 0.9 | 0 |
| **resumo** | 10/10 | ✓ | 833 → 1674 | 13671 | 6 | 0.9 | 0 |

Chamadas a mais: só a memória de resumo paga (uma chamada para resumir o que saiu da janela). Os tokens dessa chamada não entram na coluna de tokens.

## A 10ª pergunta, em cada memória

**notas** — acertou (esperado: Bahia + 14,4 + caiu)

> Na Bahia, a taxa de desocupação para a faixa de 18 a 24 anos foi de 14,4 % no 3º trimestre de 2026, e ela **caiu** 4,8 pontos percentuais em relação ao ano anterior.

**inteira** — acertou (esperado: Bahia + 14,4 + caiu)

> Na Bahia, no 3º trimestre de 2026, a taxa de desocupação dos jovens de 18 a 24 anos foi de 14,4 %; comparada ao ano anterior (19,2 %), a taxa **caiu** 4,8 pontos percentuais.

**janela** — errou (esperado: Bahia + 14,4 + caiu)

> No 3º trimestre de 2026, Sergipe apresentava taxa de desocupação de 18,3 % para a faixa de 18 a 24 anos; o painel não traz informação sobre a variação dessa taxa em relação ao ano anterior.

**resumo** — acertou (esperado: Bahia + 14,4 + caiu)

> Em Bahia, a taxa de desocupação para a faixa de 18 a 24 anos foi de 14,4 % no 3º trimestre de 2026, e ela **caiu** em relação ao ano anterior (de 19,2 % para 14,4 %).

## Onde cada memória errou

- **janela**, pergunta 10 ("Voltando ao primeiro estado que eu perguntei: qual era a taxa lá, e ela subiu ou caiu em um ano?"): esperado *Bahia + 14,4 + caiu*; veio: No 3º trimestre de 2026, Sergipe apresentava taxa de desocupação de 18,3 % para a faixa de 18 a 24 anos; o painel não traz informação sobre a variação dessa taxa em relação ao ano anterior.

Quem respondeu: groq · openai/gpt-oss-120b. Respostas completas: `data/teste_memoria/respostas.csv`.