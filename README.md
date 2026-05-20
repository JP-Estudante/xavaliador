# Recuperacao de Informacao - Trabalho 2

1-) criar e ativar o ambiente:

```bash
python -m venv --system-site-packages .venv
source .venv/bin/activate
```

2-) instalar a biblioteca nltk:

```bash
pip install nltk
```

3-) baixar a lista de stopwords:

```bash
python dependecias.py
```

4-) garantir que a base esteja na pasta `folha/`:

```text
folha/topicos.xml
folha/avaliacao.txt
folha/FSP94/
folha/FSP95/
folha/publico94/
folha/publico95/
```

5-) executar avaliacao completa:

```bash
python avaliador.py
```

6-) arquivos gerados:

```text
saida/resultados.csv
saida/avaliacao.xlsx
saida/entrega.zip
```
