# Instrucoes para agentes

## Filosofia do projeto

Este projeto deve continuar com cara de codigo de estudante.

Nao e objetivo deixar tudo com a melhor arquitetura possivel, nem criar muitas camadas, nem otimizar demais. O objetivo principal e que o projeto funcione, seja facil de apresentar, seja facil de explicar em aula e fique parecido com a evolucao natural das atividades anteriores.

Para futuras alteracoes:

- Preferir codigo simples, direto e facil de ler.
- Evitar refatoracoes grandes sem necessidade.
- Evitar criar muitas classes, abstracoes ou estruturas profissionais demais.
- Manter os scripts principais pequenos e compreensiveis.
- Se alguma parte ficar tecnica demais, deixar separada em outro arquivo auxiliar.
- Preservar o estilo do projeto anterior sempre que possivel.
- Priorizar funcionamento correto para a atividade, nao o melhor desempenho.
- Evitar mudar nomes de arquivos e formatos de saida sem necessidade.
- Documentar aqui o contexto de novas tarefas.

Em resumo: se uma solucao simples resolve a atividade, ela e preferivel a uma solucao bonita demais.

## Estrutura atual

- `scripts/indexar_documentos.py`: indexa os documentos `.sgml` da colecao Folha + Publico.
- `scripts/executar_consultas.py`: executa as consultas no Xapian e gera `saida/resultados.csv`.
- `avaliador.py`: calcula AvP/MAP, executa o pipeline e gera a entrega.
- `scripts/gerar_planilha.py`: parte mais tecnica, usada para criar `saida/avaliacao.xlsx`, `saida/entrega.zip` e calcular o p-valor.
- `dependecias.py`: baixa as stopwords do NLTK.

Arquivos como `saida/resultados.csv`, `saida/avaliacao.xlsx` e `saida/entrega.zip` nao sao codigo-fonte. Eles sao gerados pela execucao do projeto. Se forem apagados, o `python avaliador.py` gera novamente.

## Contexto das tarefas

### [DONE] Trabalho I

Base original do projeto.

O trabalho pedia acessar a Linguateca, baixar as colecoes Folha e Publico, os topicos CLEF 2007 e o arquivo de relevancia. A tarefa era indexar os documentos `.sgml`, executar as primeiras 10 consultas usando modelo vetorial, recuperar ate 100 documentos por consulta e salvar os resultados em CSV com:

1. ID da consulta
2. ID do documento
3. ordem no ranking
4. score

Tambem era necessario implementar um avaliador que recebesse o CSV e calculasse a precisao media de cada consulta e o MAP.

Nesta etapa, a configuracao era padrao, sem remocao de stopwords, sem stemming e sem lematizacao.

Entrega anterior:

```text
trabalho anterior
```

### [DONE] Atividade 13.4

Evolucao do trabalho anterior.

A tarefa passou a pedir a execucao de todas as consultas, ainda usando a configuracao padrao e o modelo vetorial. Os resultados continuam no mesmo formato CSV:

1. ID da consulta
2. ID do documento
3. ordem no ranking
4. score

Tambem foi pedido calcular a AvP de cada consulta, o MAP da ferramenta, o tempo para indexar e o tempo para consultar. A entrega deveria conter o CSV e uma planilha com esses dados.

Importante: esta configuracao ainda nao remove stopwords.

Entrega anterior:

```text
arquivo zip da atividade 13.4
```

### [DONE] Atividade 13.5

Atividade atual deste projeto.

A tarefa e parecida com a 13.4, mas agora deve remover stopwords. A configuracao continua simples: Xapian com modelo vetorial, ate 100 documentos por consulta, todas as consultas e CSV no mesmo formato.

Nesta versao, as stopwords sao as stopwords em portugues do NLTK.

Tambem e necessario comparar com a atividade 13.4. A planilha deve conter:

- MAP da configuracao 13.5.
- MAP da configuracao 13.4.
- tempo para indexar das duas configuracoes.
- tempo para consultar das duas configuracoes.
- p-valor do teste t aplicado sobre as AvP das consultas.

O arquivo `scripts/gerar_planilha.py` existe para manter essa parte mais tecnica fora dos scripts principais.

Resultado da ultima execucao neste projeto:

```text
MAP 13.5 = 0.1094
MAP 13.4 = 0.1057
p-valor teste-t = 0.006115219856121623
tempo indexacao 13.5 = 204.853s
tempo consulta 13.5 = 0.506s
```

## Como adicionar novas tarefas

Ao fazer uma nova atividade:

1. Adicionar uma nova secao em `Contexto das tarefas`.
2. Quando a atividade estiver concluida, colocar `[DONE]` no subtitulo, por exemplo `### [DONE] Atividade 13.6`.
3. Na secao da tarefa, explicar:
   - o que a tarefa pedia;
   - qual configuracao foi usada;
   - quais arquivos foram gerados;
   - quais numeros principais foram obtidos.
4. Tentar alterar o minimo possivel do codigo existente.

## Aviso final

Nao transformar este projeto em algo sofisticado demais.

Se precisar melhorar algo, faca de forma pequena e localizada. O codigo deve continuar simples, meio manual e facil de defender como trabalho de disciplina. A prioridade e entregar a atividade corretamente, nao impressionar com engenharia.
