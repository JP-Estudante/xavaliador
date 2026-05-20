# formato do qrels: qid 0 docid relevance
import csv
import os
import subprocess
import sys
import time
from collections import defaultdict
from pathlib import Path

from scripts.dados_13_4 import AVPS_13_4, TEMPO_CONSULTA_13_4, TEMPO_INDEXACAO_13_4
from scripts.gerar_planilha import formula, gerar_planilha, gerar_zip, ler_tempos_planilha, p_valor_t_pareado

BASE_DIR = Path(__file__).resolve().parent
os.chdir(BASE_DIR)

os.makedirs("saida", exist_ok=True)

csv_entrada = sys.argv[1] if len(sys.argv) > 1 else "saida/resultados.csv"
planilha_saida = "saida/avaliacao.xlsx"
zip_saida = "saida/entrega.zip"

def executar_pipeline():
    if not Path("folha").exists():
        print("Erro: a pasta folha/ precisa existir com os documentos, topicos.xml e avaliacao.txt.")
        sys.exit(1)

    if not Path("folha/topicos.xml").exists() or not Path("folha/avaliacao.txt").exists():
        print("Erro: faltam folha/topicos.xml ou folha/avaliacao.txt.")
        sys.exit(1)

    inicio = time.perf_counter()
    subprocess.run([sys.executable, "scripts/indexar_documentos.py"], check=True)
    tempo_indexacao = time.perf_counter() - inicio

    inicio = time.perf_counter()
    subprocess.run([sys.executable, "scripts/executar_consultas.py"], check=True)
    tempo_consultas = time.perf_counter() - inicio

    return tempo_indexacao, tempo_consultas


def carregar_consultas():
    import xml.etree.ElementTree as ET

    tree = ET.parse("folha/topicos.xml")
    root = tree.getroot()

    consultas = []

    for top in root.findall(".//top"):
        consultas.append(top.find("num").text.strip())

    return consultas


def carregar_qrels():
    qrels = defaultdict(dict)

    with open("folha/avaliacao.txt", "r", encoding="utf-8") as f:
        for line in f:
            qid, _, docid, rel = line.split()
            qrels[qid][docid] = int(rel)

    return qrels


def carregar_resultados(caminho):
    resultados = defaultdict(list)

    if not Path(caminho).exists():
        return resultados

    with open(caminho, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
            qid = row["ID da consulta"]
            docid = row["ID do documento"]
            rank = int(row["ordem no ranking"])
            resultados[qid].append((rank, docid))

    for qid in resultados:
        resultados[qid].sort()

    return resultados


def average_precision(qid, qrels, resultados):
    rel_docs = qrels[qid]
    recuperados = resultados[qid]

    num_rel = 0
    soma_prec = 0

    for i, (_, docid) in enumerate(recuperados, start=1):
        if rel_docs.get(docid, 0) == 1:
            num_rel += 1
            soma_prec += num_rel / i

    total_rel = sum(rel_docs.values())

    if total_rel == 0:
        return 0, num_rel, total_rel

    return soma_prec / total_rel, num_rel, total_rel


tempo_indexacao = ""
tempo_consultas = ""

if len(sys.argv) == 1:
    tempo_indexacao, tempo_consultas = executar_pipeline()
else:
    tempos_135 = ler_tempos_planilha(planilha_saida)
    tempo_indexacao = tempos_135.get("Tempo para indexar (s)", "")
    tempo_consultas = tempos_135.get("Tempo para consultar (s)", "")

consultas = carregar_consultas()
qrels = carregar_qrels()
resultados = carregar_resultados(csv_entrada)

linhas_consultas = []
aps = []
aps_134 = []

for i, qid in enumerate(consultas):
    linha = i + 8
    ap, num_rel, total_rel = average_precision(qid, qrels, resultados)
    ap_134 = AVPS_13_4[i]

    aps.append(ap)
    aps_134.append(ap_134)
    linhas_consultas.append([qid, ap, ap_134, formula(f"B{linha}-C{linha}", ap - ap_134), num_rel, total_rel])

    print(f"Consulta {qid} -> relevantes recuperados = {num_rel}/{total_rel} | AvP = {ap:.4f}")

mapa = sum(aps) / len(aps)
mapa_134 = sum(aps_134) / len(aps_134)
p_valor = p_valor_t_pareado(aps, aps_134)
ultima_linha = 7 + len(consultas)

linhas_planilha = [
    ["Metrica", "13.5 com remocao de stopwords", "13.4 sem remocao de stopwords"],
    ["MAP", formula(f"AVERAGE(B8:B{ultima_linha})", mapa), formula(f"AVERAGE(C8:C{ultima_linha})", mapa_134)],
    ["Tempo para indexar (s)", tempo_indexacao, TEMPO_INDEXACAO_13_4],
    ["Tempo para consultar (s)", tempo_consultas, TEMPO_CONSULTA_13_4],
    ["p-valor teste-t AvP", formula(f"T.TEST(B8:B{ultima_linha},C8:C{ultima_linha},2,1)", p_valor), ""],
    [],
    ["ID da consulta", "AvP 13.5", "AvP 13.4", "Diferenca", "Relevantes recuperados", "Total relevantes"],
]
linhas_planilha.extend(linhas_consultas)

gerar_planilha(linhas_planilha, planilha_saida)
gerar_zip(csv_entrada, planilha_saida, zip_saida)

print(f"\nMAP = {mapa:.4f}")
print(f"MAP 13.4 = {mapa_134:.4f}")
print(f"p-valor teste-t = {p_valor}")
print(f"Planilha salva em: {planilha_saida}")
print(f"Arquivo compactado salvo em: {zip_saida}")
