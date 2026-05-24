import xapian
import xml.etree.ElementTree as ET
import csv
import os
from nltk.corpus import stopwords

os.chdir(os.path.dirname(os.path.dirname(__file__)))

os.makedirs("saida", exist_ok=True)

db = xapian.Database("db")

qp = xapian.QueryParser()
qp.set_database(db)

# Modelo vetorial usando OR como antes
qp.set_default_op(xapian.Query.OP_OR)

# Melhor configuracao anterior: remocao de stopwords
stopper = xapian.SimpleStopper()

for w in stopwords.words("portuguese"):
    stopper.add(w)

qp.set_stopper(stopper)

# Atividade 14.7: adicionar stemming em portugues
stemmer = xapian.Stem("portuguese")
qp.set_stemmer(stemmer)
qp.set_stemming_strategy(xapian.QueryParser.STEM_SOME)

# Ler XML de topicos
tree = ET.parse("folha/topicos.xml")
root = tree.getroot()

topics = root.findall(".//top")

results = []

for top in topics:
    qid = top.find("num").text.strip()
    title = top.find("title").text.strip()

    query = qp.parse_query(title)

    enquire = xapian.Enquire(db)
    enquire.set_query(query)

    # TF-IDF classico
    enquire.set_weighting_scheme(xapian.TfIdfWeight())

    matches = enquire.get_mset(0, 100)

    rank = 1
    for m in matches:
        docno = m.document.get_value(0).decode("utf-8")

        results.append([qid, docno, rank, m.weight])
        rank += 1

# salvar CSV
with open("saida/resultados.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["ID da consulta", "ID do documento", "ordem no ranking", "score"])
    writer.writerows(results)

print("Consultas executadas e salvas em saida/resultados.csv!")
