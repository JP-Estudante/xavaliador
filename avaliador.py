# formato: qid 0 docid relevance
import csv
import os
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
os.chdir(BASE_DIR)

db_path = BASE_DIR / "db"
csv_entrada = sys.argv[1] if len(sys.argv) > 1 else "resultados.csv"

if len(sys.argv) == 1:
    if not db_path.exists() or not any(db_path.iterdir()):
        subprocess.run([sys.executable, "scripts/indexar_documentos.py"], check=True)

    subprocess.run([sys.executable, "scripts/executar_consultas.py"], check=True)

# carregar qrels
qrels = defaultdict(dict)

with open("folha/avaliacao.txt", "r") as f:
    for line in f:
        qid, _, docid, rel = line.split()
        qrels[qid][docid] = int(rel)

# carregar resultados
results = defaultdict(list)

with open(csv_entrada, "r") as f:
    reader = csv.DictReader(f)
    for row in reader:
        qid = row["ID da consulta"]
        docid = row["ID do documento"]
        rank = int(row["ordem no ranking"])

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
        return 0, num_rel, total_rel

    return sum_prec / total_rel, num_rel, total_rel

# calcular MAP
aps = []

for qid in results:
    ap, num_rel, total_rel = average_precision(qid)
    aps.append(ap)
    print(f"Consulta {qid} → relevantes recuperados = {num_rel}/{total_rel} | AP = {ap:.4f}")

MAP = sum(aps) / len(aps)

print(f"\nMAP = {MAP:.4f}")
