import xapian

db = xapian.Database("db")

qp = xapian.QueryParser()
qp.set_database(db)

#modelo por bolleano
#qp.set_default_op(xapian.Query.OP_AND)

#modelo por vetor
qp.set_default_op(xapian.Query.OP_OR)

stemmer = xapian.Stem("portuguese")
qp.set_stemmer(stemmer)
qp.set_stemming_strategy(xapian.QueryParser.STEM_SOME)

while True:
    query_str = input("Digite a consulta (ou 'sair'): ").strip()
    if query_str.lower() == "sair":
        break
    query = qp.parse_query(query_str)

    enquire = xapian.Enquire(db)
    enquire.set_query(query)

    #modelo por vetor TF-IDF
    enquire.set_weighting_scheme(xapian.TfIdfWeight())
    #modelo por vetor mais "inteligente" BM25, mistura escalado ao fator b dos BM 11 e 15
    #enquire.set_weighting_scheme(xapian.BM25Weight())

    matches = enquire.get_mset(0, 10)

    print("\nResultados:\n")

    for m in matches:
        data = m.document.get_data().decode("utf-8", errors="ignore")
        docno, text = data.split("||", 1)
        text = " ".join(text.split())

        print("ID:", docno)
        print("Score:", m.percent)
        print(text[:200])
        print("-" * 50)
