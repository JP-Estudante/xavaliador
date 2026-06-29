# Recuperacao de Informacao - Trabalho 2

Este projeto executa experimentos com a base Linguateca usando Xapian.

## Preparar ambiente

```bash
python -m venv --system-site-packages .venv
source .venv/bin/activate
pip install -r requirements.txt
```

O modulo `xapian` normalmente vem do sistema operacional. No Linux, use um pacote como `python3-xapian` e crie a `.venv` com `--system-site-packages`.

## Base esperada

A pasta `folha/` deve conter:

```text
folha/topicos.xml
folha/avaliacao.txt
folha/FSP94/
folha/FSP95/
folha/publico94/
folha/publico95/
```

## Executar todos os experimentos

```bash
python experimentos.py
```

O script testa 10 tecnicas de pre-processamento e 5 modelos de recuperacao, recuperando ate 100 documentos por consulta.

Cada experimento é comparado com a melhor configuração encontrada antes dele, seguindo a regra usada para decidir se a nova configuração substitui a melhor anterior.

## Pre-processamentos testados

```text
tokenização
normalização para minúsculas
remoção de pontuação
remoção de acentos
remoção de stopwords
stemming
lematização simples
remoção de números
remoção de termos muito curtos
remoção de termos muito longos
```

## Modelos testados

```text
TF-IDF
BM25
BM25Plus
PL2
InL2
```

## Arquivos gerados

```text
saida/resultados.csv
saida/resumo_experimentos.csv
saida/avp_consultas.csv
saida/avaliacao.xlsx
saida/apresentacao.md
saida/entrega.zip
```

`saida/resultados.csv` contem o resultado da melhor configuracao encontrada, nas colunas exigidas:

```text
ID da consulta
ID do documento
ordem no ranking
score
```
