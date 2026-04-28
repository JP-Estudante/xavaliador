# formato: qid 0 docid relevance
import csv
from collections import defaultdict

# carregar qrels
qrels = defaultdict(dict)

with open("folha/avaliacao.txt", "r") as f:
    for line in f:
        qid, _, docid, rel = line.split()
        qrels[qid][docid] = int(rel)

# carregar resultados
results = defaultdict(list)

with open("resultados.csv", "r") as f:
    reader = csv.DictReader(f)
    for row in reader:
        qid = row["query_id"]
        docid = row["doc_id"]
        rank = int(row["rank"])

        results[qid].append((rank, docid))

# ordenar por rank
for qid in results:
    results[qid].sort()

# calcular AP por consulta
def average_precision(qid):
    rel_docs = qrels[qid]
    retrieved = results[qid]

    num_rel = 0
    sum_prec = 0

    for i, (_, docid) in enumerate(retrieved, start=1):
        if rel_docs.get(docid, 0) == 1:
            num_rel += 1
            sum_prec += num_rel / i

    total_rel = sum(rel_docs.values())

    if total_rel == 0:
        return 0

    return sum_prec / total_rel

# calcular MAP
aps = []

for qid in results:
    ap = average_precision(qid)
    aps.append(ap)
    print(f"Consulta {qid} → AP = {ap:.4f}")

MAP = sum(aps) / len(aps)

print(f"\nMAP = {MAP:.4f}")
