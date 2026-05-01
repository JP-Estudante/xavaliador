import xapian
import xml.etree.ElementTree as ET
import csv

db = xapian.Database("db")

qp = xapian.QueryParser()
qp.set_database(db)

# Sem stemming (configuração padrão)
qp.set_default_op(xapian.Query.OP_OR)

# Ler XML de tópicos
tree = ET.parse("folha/topicos.xml")
root = tree.getroot()

topics = root.findall(".//top")[:10]

results = []

for top in topics:
    qid = top.find("num").text.strip()
    title = top.find("title").text.strip()

    query = qp.parse_query(title)

    enquire = xapian.Enquire(db)
    enquire.set_query(query)

    # TF-IDF clássico
    enquire.set_weighting_scheme(xapian.TfIdfWeight())

    matches = enquire.get_mset(0, 100)

    rank = 1
    for m in matches:
        docno = m.document.get_value(0).decode("utf-8")

        results.append([qid, docno, rank, m.weight])
        rank += 1

# salvar CSV
with open("resultados.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["ID da consulta", "ID do documento", "ordem no ranking", "score"])
    writer.writerows(results)

print("Consultas executadas e salvas!")
