import xapian
import re

# Caminho do banco
db = xapian.WritableDatabase("db", xapian.DB_CREATE)

termgen = xapian.TermGenerator()
termgen.set_database(db)

stemmer = xapian.Stem("portuguese")
termgen.set_stemmer(stemmer)

# Ler arquivo SGML
with open("data.sgml", "r", encoding="latin-1") as f:
    content = f.read()

# Separar documentos
docs = re.findall(r"<DOC>(.*?)</DOC>", content, re.DOTALL)

for d in docs:
    # Extrair documento id
    docno_match = re.search(r"<DOCNO>(.*?)</DOCNO>", d)
    # Extrair texto
    text_match = re.search(r"<TEXT>(.*?)</TEXT>", d, re.DOTALL)
    if not docno_match or not text_match:
        continue

    docno = docno_match.group(1).strip()


    if not text_match:
        continue

    text = text_match.group(1)

    doc = xapian.Document()
    termgen.set_document(doc)

    # Indexar ID + texto
    termgen.index_text(text)
    doc.set_data(docno + "||" + text)

    db.add_document(doc)

print(f"{len(docs)} documentos indexados!")
