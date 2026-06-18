# formato do qrels: qid 0 docid relevance
import csv
import os
import subprocess
import sys
import time
from collections import defaultdict
from pathlib import Path

from scripts.dados_13_4 import AVPS_13_4, TEMPO_CONSULTA_13_4, TEMPO_INDEXACAO_13_4
from scripts.dados_13_5 import AVPS_13_5, TEMPO_CONSULTA_13_5, TEMPO_INDEXACAO_13_5
from scripts.dados_14_7 import AVPS_14_7, TEMPO_CONSULTA_14_7, TEMPO_INDEXACAO_14_7
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
    tempos_155 = ler_tempos_planilha(planilha_saida)
    tempo_indexacao = tempos_155.get("Tempo para indexar (s)", "")
    tempo_consultas = tempos_155.get("Tempo para consultar (s)", "")

consultas = carregar_consultas()
qrels = carregar_qrels()
resultados = carregar_resultados(csv_entrada)

linhas_consultas = []
aps = []
aps_135 = []
aps_147 = []
aps_134 = []

for i, qid in enumerate(consultas):
    linha = i + 8
    ap, num_rel, total_rel = average_precision(qid, qrels, resultados)
    ap_135 = AVPS_13_5[i]
    ap_147 = AVPS_14_7[i]
    ap_134 = AVPS_13_4[i]

    aps.append(ap)
    aps_135.append(ap_135)
    aps_147.append(ap_147)
    aps_134.append(ap_134)
    linhas_consultas.append([qid, ap, ap_147, ap_135, ap_134, formula(f"B{linha}-D{linha}", ap - ap_135), num_rel, total_rel])

    print(f"Consulta {qid} -> relevantes recuperados = {num_rel}/{total_rel} | AvP = {ap:.4f}")

mapa = sum(aps) / len(aps)
mapa_135 = sum(aps_135) / len(aps_135)
mapa_147 = sum(aps_147) / len(aps_147)
mapa_134 = sum(aps_134) / len(aps_134)
p_valor = p_valor_t_pareado(aps, aps_135)
ultima_linha = 7 + len(consultas)

linhas_planilha = [
    ["Metrica", "15.5 stopwords + lematizacao", "14.7 stopwords + stemming", "13.5 stopwords", "13.4 sem stopwords"],
    ["MAP", formula(f"AVERAGE(B8:B{ultima_linha})", mapa), formula(f"AVERAGE(C8:C{ultima_linha})", mapa_147), formula(f"AVERAGE(D8:D{ultima_linha})", mapa_135), formula(f"AVERAGE(E8:E{ultima_linha})", mapa_134)],
    ["Tempo para indexar (s)", tempo_indexacao, TEMPO_INDEXACAO_14_7, TEMPO_INDEXACAO_13_5, TEMPO_INDEXACAO_13_4],
    ["Tempo para consultar (s)", tempo_consultas, TEMPO_CONSULTA_14_7, TEMPO_CONSULTA_13_5, TEMPO_CONSULTA_13_4],
    ["p-valor teste-t AvP 15.5 x 13.5", formula(f"T.TEST(B8:B{ultima_linha},D8:D{ultima_linha},2,1)", p_valor), "", "", ""],
    [],
    ["ID da consulta", "AvP 15.5", "AvP 14.7", "AvP 13.5", "AvP 13.4", "Diferenca 15.5 x 13.5", "Relevantes recuperados", "Total relevantes"],
]
linhas_planilha.extend(linhas_consultas)

gerar_planilha(linhas_planilha, planilha_saida)
gerar_zip(csv_entrada, planilha_saida, zip_saida)

print(f"\nMAP = {mapa:.4f}")
print(f"MAP 14.7 = {mapa_147:.4f}")
print(f"MAP 13.5 = {mapa_135:.4f}")
print(f"MAP 13.4 = {mapa_134:.4f}")
print(f"p-valor teste-t 15.5 x 13.5 = {p_valor}")
print(f"Planilha salva em: {planilha_saida}")
print(f"Arquivo compactado salvo em: {zip_saida}")
