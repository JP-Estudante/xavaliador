# Recuperacao de Informacao - Atividade 15.5

1-) criar e ativar o ambiente:

```bash
python -m venv --system-site-packages .venv
source .venv/bin/activate
```

2-) instalar as dependencias:

```bash
pip install -r requirements.txt
```

3-) garantir que a base esteja na pasta `folha/`:

```text
folha/topicos.xml
folha/avaliacao.txt
folha/FSP94/
folha/FSP95/
folha/publico94/
folha/publico95/
```

4-) executar avaliacao completa:

```bash
python avaliador.py
```

5-) configuracao usada:

```text
modelo vetorial
remocao de stopwords em portugues
lematizacao simples em portugues
sem stemming
ate 100 documentos por consulta
todas as consultas
```

6-) arquivos gerados:

```text
saida/resultados.csv
saida/avaliacao.xlsx
saida/entrega.zip
```
