# Prompts do painel

Os prompts ficam aqui, fora do código, para serem lidos, versionados e
justificados como qualquer outro artefato. O código só preenche os campos
entre chaves.

## `conversa_sistema.txt` (página Conversa, `POST /conversa`)

| Trecho | Por quê |
|---|---|
| Papel e público ("quem pergunta trabalha com programas de emprego para jovens") | Define o tom e o nível: resposta para quem decide, não para estatístico. |
| "No máximo 4 frases" | Respostas longas escondem o número que importa e gastam tokens do plano gratuito. |
| Regra 1: só os números de FATOS, sem calcular | É a regra central contra invenção. O Python calcula, o modelo redige. A página confere a regra depois (`src/checagem.py`). |
| Regra 2: lugar, grupo e trimestre junto do número | Um "11,1%" sozinho não diz nada; com a referência, a resposta pode ser conferida. |
| Regra 3: dizer que não tem o dado | Sem essa saída, o modelo tende a completar com algo plausível. |
| Regra 4: "e em São Paulo?" continua a conversa | É o que a memória precisa resolver; a regra diz ao modelo onde olhar (mensagens e NOTAS). |
| Regra 5: sem conselho de carreira nem política | Mantém o assistente no escopo dos dados. |
| `{notas}` | Só na memória de notas: a lista de lugares e grupos que a pessoa já citou, anotada pelo Python. |
| `{fatos}` | O bloco de `src/fatos.py`: IBGE (Brasil + os lugares em foco + ranking das UFs) e as notícias. |

## `conversa_resumo.txt` (memória de resumo)

Uma chamada **a mais** ao modelo, que resume as mensagens que saíram da
janela. Pede para guardar lugares, grupos e números na ordem, porque é isso
que a conversa precisa reencontrar depois.

## O prompt do Analisador

Fica em `src/analisador_llm.py` e `src/tarefas.py` (TP4): pergunta + opções
com definição + notícia, e a resposta é a **letra** de maior probabilidade.
