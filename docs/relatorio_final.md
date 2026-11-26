# Relatório Final (TDSP: Exit Report) — Painel de Empregabilidade Jovem

> O fechamento do projeto: o problema, o que foi entregue, o que os dados
> mostram, o que ficou de fora e como continuar.

## 1. O problema e a solução

**Problema:** ONGs e financiadores de programas de primeiro emprego decidem onde
e para o quê qualificar jovens sem dado sobre onde o jovem mais procura emprego
e não acha (ODS 8, metas 8.5, 8.6 e 8.b; o S do ESG).

**Solução:** um painel e uma API que:
1. coletam dado real: desocupação por idade e UF (API do IBGE) e notícias de
   emprego com texto integral (raspagem da Agência Brasil);
2. classificam as notícias com um modelo de linguagem **local** (tendência e setor);
3. respondem perguntas em português por um assistente com **memória**, que só
   usa números calculados pelo painel e tem cada resposta conferida;
4. mostram o ciclo inteiro, da coleta ao insight, na página "Do dado ao insight".

## 2. O que os dados mostram (3º trimestre de 2026)

- **O jovem procura e não acha mais que a média:** desocupação de **11,1%** de
  18 a 24 anos e **21,5%** de 14 a 17, contra **5,2%** em todas as idades
  (cerca de 2 e 4 vezes).
- **A diferença entre estados é grande:** de **4,7%** (Santa Catarina) a **18,3%**
  (Sergipe), para 18 a 24 anos. Um programa nacional uniforme não atende igual
  a todos. As três maiores taxas são de Sergipe, Pernambuco e Rio de Janeiro.
- **A tendência é de queda:** de 14,2% (2º tri. 2024) para 11,1% (3º tri. 2026)
  entre 18 e 24 anos no Brasil. Na Bahia, caiu 4,8 pontos percentuais em um ano.
- **O noticiário é otimista:** 26 das 42 notícias. Combina com a queda, mas
  notícia boa no agregado não é vaga para quem tem 18 anos. Por isso o painel
  mostra os dois lado a lado.

## 3. O que foi entregue

| Entrega | Onde |
|---|---|
| Painel Streamlit (7 páginas) | `app.py`, `paginas/` |
| API FastAPI documentada | `api/`, `/docs` |
| Coletas (raspagem, API do IBGE, textos) | `src/coletar*.py` |
| Analisador com modelo local | `src/analisador_llm.py`, `POST /processar_texto` |
| Conversa com memória e conferência dos números | `src/fatos.py`, `src/memoria.py`, `src/llm_api.py`, `src/checagem.py`, `POST /conversa` |
| Testes automáticos | `tests/` (`pytest`) |
| Medições reproduzíveis | `src/bancada.py`, `src/teste_memoria.py`, `src/evidencias.py` |
| Documentação TDSP | `docs/` e `prompts/` |

## 4. As decisões, todas por medição

| Decisão | Evidência |
|---|---|
| Qwen2.5-1.5B para classificar | Bancada de 42 notícias (`bancada_resultados.md`) |
| Setor como "experimental" | Nenhum modelo superou a linha de base em setor |
| Modelo online para conversar, não o local | 14,4 s por classificação na CPU (`bancada_resultados_cpu.md`) |
| Groq como principal, Gemini como reserva | Gemini com 503 em todas as tentativas; Groq em 1,2 s |
| Memória de notas como padrão | Teste de 10 perguntas: 10/10, menos tokens que inteira e resumo, sem chamada extra |
| Sem repetição automática nas chamadas online | Biblioteca do Google presa 10 min repetindo um 503 |

## 5. Limitações

- **Setor** das notícias é experimental (abaixo da linha de base).
- **42 notícias** é um acervo pequeno; o tom do noticiário é um indício, não uma
  medida do mercado.
- **Desocupação** mede quem procura e não acha; não mede os "nem-nem" que
  desistiram de procurar.
- Nas **UFs**, a amostra de jovens é menor e a estimativa oscila mais; dois
  trimestres antigos vieram só com o Brasil.
- A **conversa** depende de um provedor externo e do seu limite gratuito.

## 6. Próximos passos

1. **Novo CAGED** (microdados por FTP): saldo de vagas por setor e UF, o fluxo
   que falta ao lado do estoque da PNAD.
2. **Mais notícias:** coletar mais páginas e classificar com o Analisador, para
   o tom do noticiário por trimestre ter volume.
3. **Taxa "nem-nem"** do IBGE (outra tabela da PNAD), que é a medida exata da meta 8.6.
4. **Teste de memória com mais sequências**, inclusive perguntas fora do escopo.

## 7. Como rodar

Ver o `README.md`: ambiente, coletas, API (`uvicorn api.main:app`), painel
(`streamlit run app.py`), chaves no `.env` e os comandos de medição.
