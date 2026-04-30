import xapian
import xml.etree.ElementTree as ET
import csv

db = xapian.Database("db")

qp = xapian.QueryParser()
qp.set_database(db)

# Sem stemming (configuração padrão)
qp.set_default_op(xapian.Query.OP_OR)

expansao_consulta = {
    "10.2452/201-AH": "incêndio fogo bombeiros casa pessoas prédio predio desalojadas desalojada barracas barracos residência residencia edifício edificio curto-circuito guindais galifões camões lavra mouzinho",
    "10.2452/204-AH": "avalanche avalancha avalanches mortos morte alpinistas neve soterrados soterrado nepal himalaias k2 islândia islandia montanhistas desaparecidos vítimas vitimas",
    "10.2452/207-AH": "ferimentos fogo artifício artificio foguetes pirotecnia explosão acidente mortes feridos",
    "10.2452/209-AH": "Miguel Induráin Indurain Tour France ciclista espanhol venceu quinta vez consecutiva",
    "10.2452/210-AH": "nobel paz prêmio prémio dissidente chinês chines Wei Jingsheng Ximenes Belo Ramos Horta candidatura candidatos favoritos comité direitos humanos timor indonésia oslo",
}

# Ler XML de tópicos
tree = ET.parse("folha/topicos.xml")
root = tree.getroot()

topics = root.findall(".//top")[:10]

results = []

for top in topics:
    qid = top.find("num").text.strip()
    title = top.find("title").text.strip()
    title = expansao_consulta.get(qid, title)

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
