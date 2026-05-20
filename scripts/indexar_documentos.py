import xapian
import re
import os
from nltk.corpus import stopwords

os.chdir(os.path.dirname(os.path.dirname(__file__)))

db = xapian.WritableDatabase("db", xapian.DB_CREATE_OR_OVERWRITE)

termgen = xapian.TermGenerator()
termgen.set_database(db)

# Configurar as stopwords
stopper = xapian.SimpleStopper()

for w in stopwords.words("portuguese"):
    stopper.add(w)

termgen.set_stopper(stopper)

def index_file(path):
    with open(path, "r", encoding="latin-1") as f:
        content = f.read()

    docs = re.findall(r"<DOC>(.*?)</DOC>", content, re.DOTALL)

    indexed = 0

    for d in docs:
        docno_match = re.search(r"<DOCNO>(.*?)</DOCNO>", d)
        text_match = re.search(r"<TEXT>(.*?)</TEXT>", d, re.DOTALL)

        if not docno_match or not text_match:
            continue

        docno = docno_match.group(1).strip()
        text = " ".join(text_match.group(1).split())

        doc = xapian.Document()
        termgen.set_document(doc)

        # Indexação padrão com remoção de stopwords
        termgen.index_text(text)

        doc.add_value(0, docno)
        doc.set_data(text)

        db.add_document(doc)
        indexed += 1

    return indexed

def index_directory(base_path):
    total = 0
    for root, dirs, files in os.walk(base_path):
        for file in files:
            if file.endswith(".sgml"):
                full_path = os.path.join(root, file)
                print(f"Indexando: {full_path}")
                total += index_file(full_path)
    return total

# Caminho raiz para indexar
total_docs = index_directory("folha")

print(f"Indexação concluída! Documentos indexados: {total_docs}")
