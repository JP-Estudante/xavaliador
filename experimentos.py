# formato do qrels: qid 0 docid relevance
import csv
import os
import re
import shutil
import sys
import time
import unicodedata
import xml.etree.ElementTree as ET
import zipfile
from collections import defaultdict
from pathlib import Path

import xapian

from scripts.gerar_planilha import gerar_planilha, p_valor_t_pareado
from scripts.lematizador import lematizar_texto
from scripts.stopwords_pt import stopwords_portugues


BASE_DIR = Path(__file__).resolve().parent
FOLHA_DIR = BASE_DIR / "folha"
SAIDA_DIR = BASE_DIR / "saida"
DB_DIR = BASE_DIR / "db_experimentos"
RESULTADOS_DIR = SAIDA_DIR / "experimentos"


PRE_PROCESSAMENTOS = [
    {
        "id": "tokenizacao",
        "nome": "Tokenização (baseline)",
        "tokenizacao": True,
    },
    {
        "id": "minusculas",
        "nome": "Normalização para minúsculas",
        "minusculas": True,
    },
    {
        "id": "sem_pontuacao",
        "nome": "Remoção de pontuação",
        "sem_pontuacao": True,
    },
    {
        "id": "sem_acentos",
        "nome": "Remoção de acentos",
        "sem_acentos": True,
    },
    {
        "id": "stopwords",
        "nome": "Remoção de stopwords",
        "stopwords": True,
    },
    {
        "id": "stemming",
        "nome": "Stemming",
        "stemming": True,
    },
    {
        "id": "lematizacao",
        "nome": "Lematização simples",
        "lematizacao": True,
    },
    {
        "id": "sem_numeros",
        "nome": "Remoção de números",
        "sem_numeros": True,
    },
    {
        "id": "termos_curtos",
        "nome": "Remoção de termos muito curtos",
        "termos_curtos": True,
    },
    {
        "id": "termos_longos",
        "nome": "Remoção de termos muito longos",
        "termos_longos": True,
    },
]


MODELOS = [
    ("tfidf", "TF-IDF", lambda: xapian.TfIdfWeight()),
    ("bm25", "BM25", lambda: xapian.BM25Weight()),
    ("bm25plus", "BM25Plus", lambda: xapian.BM25PlusWeight()),
    ("pl2", "PL2", lambda: xapian.PL2Weight()),
    ("inl2", "InL2", lambda: xapian.InL2Weight()),
]


COMENTARIOS_PRE_PROCESSAMENTO = {
    "Tokenização (baseline)": "Tokenização: separa o texto em termos. Foi usada como baseline inicial para comparar as demais configurações.",
    "Normalização para minúsculas": "Normalização para minúsculas: padroniza palavras como Informação e informação, evitando diferenças apenas por capitalização.",
    "Remoção de pontuação": "Remoção de pontuação: elimina sinais que normalmente não carregam conteúdo semântico relevante para a recuperação.",
    "Remoção de acentos": "Remoção de acentos: aproxima formas como informação e informacao, reduzindo variações de escrita.",
    "Remoção de stopwords": "Remoção de stopwords: remove palavras muito frequentes, como de, a, o, para e com, que costumam adicionar pouco valor ao ranking.",
    "Stemming": "Stemming: reduz palavras ao radical aproximado, agrupando variações morfológicas de uma mesma família de termos.",
    "Lematização simples": "Lematização simples: tenta reduzir palavras para uma forma base, diminuindo variações flexionadas sem usar o stemming do Xapian.",
    "Remoção de números": "Remoção de números: retira tokens numéricos para avaliar se datas, anos e valores estavam ajudando ou gerando ruído.",
    "Remoção de termos muito curtos": "Remoção de termos muito curtos: remove tokens com menos de 3 caracteres para reduzir ruído que não aparece necessariamente na lista de stopwords.",
    "Remoção de termos muito longos": "Remoção de termos muito longos: remove tokens com mais de 30 caracteres, comuns em erros de marcação, concatenações ou ruído textual.",
}


def remover_acentos(texto):
    texto = unicodedata.normalize("NFD", texto)
    return "".join(char for char in texto if unicodedata.category(char) != "Mn")


def tokenizar(texto):
    return re.findall(r"\w+", texto, flags=re.UNICODE)


def limpar_texto(texto, config):
    texto = " ".join(texto.split())

    if config.get("minusculas"):
        texto = texto.lower()

    if config.get("sem_pontuacao"):
        texto = re.sub(r"[^\w\s]", " ", texto, flags=re.UNICODE)

    if config.get("sem_acentos"):
        texto = remover_acentos(texto)

    if config.get("lematizacao"):
        texto = lematizar_texto(texto)

    if config.get("sem_numeros"):
        texto = re.sub(r"\d+", " ", texto)

    if config.get("termos_curtos"):
        texto = " ".join(termo for termo in tokenizar(texto) if len(termo) >= 3)

    if config.get("termos_longos"):
        texto = " ".join(termo for termo in tokenizar(texto) if len(termo) <= 30)

    if config.get("tokenizacao"):
        texto = " ".join(tokenizar(texto))

    return texto


def criar_stopper(config):
    if not config.get("stopwords"):
        return None

    stopper = xapian.SimpleStopper()

    for palavra in stopwords_portugues():
        for termo in limpar_texto(palavra, config).split():
            stopper.add(termo)

    return stopper


def configurar_termgen(db, config):
    termgen = xapian.TermGenerator()
    termgen.set_database(db)

    stopper = criar_stopper(config)
    if stopper:
        termgen.set_stopper(stopper)

    if config.get("stemming"):
        termgen.set_stemmer(xapian.Stem("portuguese"))
        termgen.set_stemming_strategy(xapian.TermGenerator.STEM_ALL)

    return termgen


def configurar_query_parser(db, config):
    qp = xapian.QueryParser()
    qp.set_database(db)
    qp.set_default_op(xapian.Query.OP_OR)

    stopper = criar_stopper(config)
    if stopper:
        qp.set_stopper(stopper)

    if config.get("stemming"):
        qp.set_stemmer(xapian.Stem("portuguese"))
        qp.set_stemming_strategy(xapian.QueryParser.STEM_ALL)

    return qp


def carregar_documentos():
    documentos = []

    for path in sorted(FOLHA_DIR.rglob("*.sgml")):
        with open(path, "r", encoding="latin-1") as arquivo:
            content = arquivo.read()

        docs = re.findall(r"<DOC>(.*?)</DOC>", content, re.DOTALL)

        for doc_texto in docs:
            docno_match = re.search(r"<DOCNO>(.*?)</DOCNO>", doc_texto)
            text_match = re.search(r"<TEXT>(.*?)</TEXT>", doc_texto, re.DOTALL)

            if not docno_match or not text_match:
                continue

            docno = docno_match.group(1).strip()
            texto = " ".join(text_match.group(1).split())
            documentos.append((docno, texto))

    return documentos


def carregar_consultas():
    tree = ET.parse(FOLHA_DIR / "topicos.xml")
    root = tree.getroot()
    consultas = []

    for top in root.findall(".//top"):
        qid = top.find("num").text.strip()
        title = top.find("title").text.strip()
        consultas.append((qid, title))

    return consultas


def carregar_qrels():
    qrels = defaultdict(dict)

    with open(FOLHA_DIR / "avaliacao.txt", "r", encoding="utf-8") as arquivo:
        for linha in arquivo:
            qid, _, docid, rel = linha.split()
            qrels[qid][docid] = int(rel)

    return qrels


def indexar_config(config, documentos):
    db_path = DB_DIR / config["id"]

    if db_path.exists():
        shutil.rmtree(db_path)

    db_path.mkdir(parents=True, exist_ok=True)
    db = xapian.WritableDatabase(str(db_path), xapian.DB_CREATE_OR_OVERWRITE)
    termgen = configurar_termgen(db, config)

    inicio = time.perf_counter()

    for docno, texto in documentos:
        doc = xapian.Document()
        termgen.set_document(doc)
        termgen.index_text(limpar_texto(texto, config))
        doc.add_value(0, docno)
        doc.set_data(texto)
        db.add_document(doc)

    db.commit()
    return time.perf_counter() - inicio, db_path


def executar_consultas(config, db_path, modelo_id, modelo_nome, weighting, consultas):
    db = xapian.Database(str(db_path))
    qp = configurar_query_parser(db, config)
    enquire = xapian.Enquire(db)
    enquire.set_weighting_scheme(weighting)

    resultados = defaultdict(list)
    linhas_csv = []

    inicio = time.perf_counter()

    for qid, title in consultas:
        texto_consulta = limpar_texto(title, config)

        if not texto_consulta.strip():
            continue

        query = qp.parse_query(texto_consulta)
        enquire.set_query(query)
        matches = enquire.get_mset(0, 100)

        for rank, match in enumerate(matches, start=1):
            docno = match.document.get_value(0).decode("utf-8")
            score = match.weight
            resultados[qid].append((rank, docno))
            linhas_csv.append([qid, docno, rank, score])

    tempo_total = time.perf_counter() - inicio
    tempo_medio = tempo_total / len(consultas) if consultas else 0
    nome_csv = f"{config['id']}__{modelo_id}.csv"
    salvar_resultados_csv(RESULTADOS_DIR / nome_csv, linhas_csv)

    return resultados, linhas_csv, tempo_total, tempo_medio, nome_csv


def salvar_resultados_csv(path, linhas):
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", newline="", encoding="utf-8") as arquivo:
        writer = csv.writer(arquivo)
        writer.writerow(["ID da consulta", "ID do documento", "ordem no ranking", "score"])
        writer.writerows(linhas)


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


def avaliar_resultados(qrels, consultas, resultados):
    avps = []
    linhas = []

    for qid, _ in consultas:
        avp, rel_rec, total_rel = average_precision(qid, qrels, resultados)
        avps.append(avp)
        linhas.append([qid, avp, rel_rec, total_rel])

    mapa = sum(avps) / len(avps) if avps else 0
    return mapa, avps, linhas


def salvar_resumo_csv(linhas):
    path = SAIDA_DIR / "resumo_experimentos.csv"

    with open(path, "w", newline="", encoding="utf-8") as arquivo:
        campos = [
            "preprocessamento",
            "modelo",
            "MAP",
            "tempo_indexacao_s",
            "tempo_consulta_total_s",
            "tempo_medio_consulta_s",
            "melhor_anterior",
            "MAP_melhor_anterior",
            "p_valor_vs_melhor_anterior",
            "decisao",
            "arquivo_resultados",
        ]
        writer = csv.DictWriter(arquivo, fieldnames=campos)
        writer.writeheader()
        writer.writerows(linhas)


def salvar_avps_csv(avps_por_experimento):
    path = SAIDA_DIR / "avp_consultas.csv"

    with open(path, "w", newline="", encoding="utf-8") as arquivo:
        writer = csv.writer(arquivo)
        writer.writerow(["preprocessamento", "modelo", "ID da consulta", "AvP"])

        for experimento in avps_por_experimento:
            for qid, avp in zip(experimento["qids"], experimento["avps"]):
                writer.writerow([experimento["preprocessamento"], experimento["modelo"], qid, avp])


def gerar_planilha_resumo(resumo, melhor, baseline):
    linhas = [
        [
            "Pré-processamento",
            "Modelo",
            "MAP",
            "Tempo de indexação (s)",
            "Tempo total de consulta (s)",
            "Tempo médio de consulta (s)",
            "Melhor configuração anterior",
            "MAP da melhor anterior",
            "p-valor vs melhor anterior",
            "Decisão",
            "Arquivo CSV",
        ],
    ]

    comentarios = [
        (
            "A1",
            "Cada linha resume uma combinação de pré-processamento e modelo de recuperação.",
        ),
        (
            "C1",
            "MAP é a média das AvP das consultas. Quanto mais perto de 1, melhor o ranking.",
        ),
        (
            "D1",
            "Tempo gasto para criar o índice Xapian daquela técnica de pré-processamento.",
        ),
        (
            "F1",
            "Tempo médio de consulta: tempo total de consulta dividido pelo número de consultas.",
        ),
        (
            "G1",
            "Configuração que era a melhor antes de o experimento desta linha ser avaliado.",
        ),
        (
            "I1",
            "p-valor do teste-t pareado contra a melhor configuração anterior. Valor menor que 0,05 costuma indicar diferença estatisticamente significativa.",
        ),
        (
            "J1",
            "Indica se o experimento substituiu ou não a melhor configuração anterior.",
        ),
        (
            "K1",
            "Arquivo CSV com os resultados daquele experimento específico.",
        ),
    ]
    vistos = set()

    for item in sorted(resumo, key=lambda x: x["MAP"], reverse=True):
        linhas.append([
            item["preprocessamento"],
            item["modelo"],
            item["MAP"],
            item["tempo_indexacao_s"],
            item["tempo_consulta_total_s"],
            item["tempo_medio_consulta_s"],
            item["melhor_anterior"],
            item["MAP_melhor_anterior"],
            item["p_valor_vs_melhor_anterior"],
            item["decisao"],
            item["arquivo_resultados"],
        ])

        if item["preprocessamento"] not in vistos:
            vistos.add(item["preprocessamento"])
            comentarios.append(
                (
                    f"A{len(linhas)}",
                    COMENTARIOS_PRE_PROCESSAMENTO[item["preprocessamento"]],
                )
            )

    linhas.extend([
        [],
        ["Melhor configuração", melhor["preprocessamento"], melhor["modelo"], melhor["MAP"]],
        ["Baseline", baseline["preprocessamento"], baseline["modelo"], baseline["MAP"]],
        ["Regra de comparação", "Cada experimento foi comparado com a melhor configuração encontrada antes dele.", "", ""],
    ])

    linha_regra = len(linhas)
    gerar_planilha(
        linhas,
        SAIDA_DIR / "avaliacao.xlsx",
        comentarios=comentarios,
        mesclagens=[f"B{linha_regra}:D{linha_regra}"],
        celulas_negrito={f"A{linha_regra}"},
    )


def gerar_apresentacao(melhor, baseline, total_pre, total_modelos):
    texto = f"""# Apresentacao - Trabalho 2

## Objetivo da ferramenta

Avaliar a recuperacao de informacao em portugues usando Xapian sobre as colecoes Folha e Publico de 1994 e 1995.

## Principais funcionalidades

- Indexar documentos SGML da base Linguateca.
- Executar todas as consultas CLEF 2007.
- Recuperar ate 100 documentos por consulta.
- Comparar tecnicas de pre-processamento.
- Comparar modelos de recuperacao do Xapian.
- Calcular AvP, MAP, tempos e teste-t pareado.

## Experimentos realizados

Foram testadas {total_pre} tecnicas de pre-processamento e {total_modelos} modelos de recuperacao, totalizando {total_pre * total_modelos} experimentos.

## Melhor configuracao

- Pre-processamento: {melhor['preprocessamento']}
- Modelo: {melhor['modelo']}
- MAP: {melhor['MAP']:.4f}
- Tempo para indexar: {melhor['tempo_indexacao_s']:.3f}s
- Tempo total para consultar: {melhor['tempo_consulta_total_s']:.3f}s
- Tempo medio por consulta: {melhor['tempo_medio_consulta_s']:.6f}s

## Comparacao com a melhor configuracao anterior

- Melhor anterior da configuracao vencedora: {melhor['melhor_anterior']}
- MAP da melhor anterior: {melhor['MAP_melhor_anterior']:.4f}
- p-valor do teste-t pareado: {melhor['p_valor_vs_melhor_anterior']}

## Decisao

Por MAP, a configuracao vencedora e {melhor['preprocessamento']} + {melhor['modelo']}. Porem, como o p-valor contra a melhor configuracao anterior foi {melhor['p_valor_vs_melhor_anterior']}, a diferenca nao foi estatisticamente significativa considerando 0.05 como referencia. A conclusao conservadora e que as duas configuracoes sao muito proximas; a vencedora pode ser apresentada por ter maior MAP e bom tempo de consulta, mas sem afirmar ganho estatisticamente significativo.

## Baseline inicial

- Baseline: {baseline['preprocessamento']} + {baseline['modelo']}
- MAP baseline: {baseline['MAP']:.4f}

## Consideracoes finais

O Xapian permitiu comparar rapidamente diferentes funcoes de ranking e variacoes de pre-processamento. As tecnicas linguisticas podem ajudar, mas tambem podem remover informacao util; por isso a decisao deve considerar MAP, tempo de execucao e significancia estatistica.

## Stopwords x termos muito curtos

A remocao de stopwords elimina palavras comuns conhecidas, como de, a, o, para e com. Ela usa uma lista de palavras frequentes e remove termos pelo significado/frequencia esperada.

A remocao de termos muito curtos elimina tokens pelo tamanho, mesmo que eles nao estejam na lista de stopwords. Ela ajuda a reduzir ruido de tokenizacao, siglas quebradas, caracteres soltos e fragmentos gerados pelo texto SGML. A diferenca pratica e que stopwords depende de uma lista linguistica, enquanto termos muito curtos depende de uma regra objetiva de comprimento.
"""
    (SAIDA_DIR / "apresentacao.md").write_text(texto, encoding="utf-8")


def gerar_zip_entrega():
    arquivos = [
        SAIDA_DIR / "resultados.csv",
        SAIDA_DIR / "resumo_experimentos.csv",
        SAIDA_DIR / "avp_consultas.csv",
        SAIDA_DIR / "avaliacao.xlsx",
        SAIDA_DIR / "apresentacao.md",
    ]

    with zipfile.ZipFile(SAIDA_DIR / "entrega.zip", "w", compression=zipfile.ZIP_DEFLATED) as entrega:
        for arquivo in arquivos:
            if arquivo.exists():
                entrega.write(arquivo, arquivo.name)


def validar_base():
    faltantes = []

    for caminho in [FOLHA_DIR, FOLHA_DIR / "topicos.xml", FOLHA_DIR / "avaliacao.txt"]:
        if not caminho.exists():
            faltantes.append(str(caminho.relative_to(BASE_DIR)))

    if faltantes:
        print("Erro: faltam arquivos da base Linguateca:")
        for item in faltantes:
            print(f"- {item}")
        sys.exit(1)


def main():
    os.chdir(BASE_DIR)
    validar_base()

    if RESULTADOS_DIR.exists():
        shutil.rmtree(RESULTADOS_DIR)

    if DB_DIR.exists():
        shutil.rmtree(DB_DIR)

    SAIDA_DIR.mkdir(exist_ok=True)
    RESULTADOS_DIR.mkdir(parents=True, exist_ok=True)
    DB_DIR.mkdir(exist_ok=True)

    documentos = carregar_documentos()
    consultas = carregar_consultas()
    qrels = carregar_qrels()
    qids = [qid for qid, _ in consultas]

    print(f"Documentos carregados: {len(documentos)}")
    print(f"Consultas carregadas: {len(consultas)}")

    resumo = []
    avps_por_experimento = []
    melhor = None
    melhor_avps = None
    melhor_linhas_csv = None
    baseline = None

    for config in PRE_PROCESSAMENTOS:
        print(f"\nIndexando: {config['nome']}")
        tempo_indexacao, db_path = indexar_config(config, documentos)

        for modelo_id, modelo_nome, criar_modelo in MODELOS:
            print(f"Consultando: {config['nome']} + {modelo_nome}")
            resultados, linhas_csv, tempo_total, tempo_medio, arquivo_csv = executar_consultas(
                config,
                db_path,
                modelo_id,
                modelo_nome,
                criar_modelo(),
                consultas,
            )
            mapa, avps, _ = avaliar_resultados(qrels, consultas, resultados)

            if melhor is None:
                melhor_anterior = ""
                map_melhor_anterior = ""
                p_valor = ""
                decisao = "Baseline inicial"
            else:
                melhor_anterior = f"{melhor['preprocessamento']} + {melhor['modelo']}"
                map_melhor_anterior = melhor["MAP"]
                p_valor = p_valor_t_pareado(avps, melhor_avps)

                if mapa > melhor["MAP"]:
                    if p_valor != "" and p_valor < 0.05:
                        decisao = "Substitui a melhor anterior com ganho significativo"
                    else:
                        decisao = "MAP maior, mas sem diferença estatisticamente significativa"
                else:
                    decisao = "Não substitui a melhor anterior"

            item = {
                "preprocessamento": config["nome"],
                "modelo": modelo_nome,
                "MAP": mapa,
                "tempo_indexacao_s": tempo_indexacao,
                "tempo_consulta_total_s": tempo_total,
                "tempo_medio_consulta_s": tempo_medio,
                "melhor_anterior": melhor_anterior,
                "MAP_melhor_anterior": map_melhor_anterior,
                "p_valor_vs_melhor_anterior": p_valor,
                "decisao": decisao,
                "arquivo_resultados": arquivo_csv,
            }
            resumo.append(item)
            avps_por_experimento.append({
                "preprocessamento": config["nome"],
                "modelo": modelo_nome,
                "qids": qids,
                "avps": avps,
            })

            if baseline is None:
                baseline = item

            if melhor is None or mapa > melhor["MAP"]:
                melhor = item
                melhor_avps = avps
                melhor_linhas_csv = linhas_csv

    salvar_resultados_csv(SAIDA_DIR / "resultados.csv", melhor_linhas_csv)
    salvar_resumo_csv(resumo)
    salvar_avps_csv(avps_por_experimento)
    gerar_planilha_resumo(resumo, melhor, baseline)
    gerar_apresentacao(melhor, baseline, len(PRE_PROCESSAMENTOS), len(MODELOS))
    gerar_zip_entrega()

    print("\nMelhor configuracao:")
    print(f"Pre-processamento: {melhor['preprocessamento']}")
    print(f"Modelo: {melhor['modelo']}")
    print(f"MAP: {melhor['MAP']:.4f}")
    print(f"Tempo indexacao: {melhor['tempo_indexacao_s']:.3f}s")
    print(f"Tempo consulta total: {melhor['tempo_consulta_total_s']:.3f}s")
    print("Arquivos gerados em saida/")


if __name__ == "__main__":
    main()
