import xapian
import re
import os
from nltk.corpus import stopwords

# Configurar as stopwords
stopwords_pt = stopwords.words("portuguese")
stopper = xapian.SimpleStopper()

for w in stopwords_pt:
    stopper.add(w)

db = xapian.WritableDatabase("db", xapian.DB_CREATE)

termgen = xapian.TermGenerator()
termgen.set_database(db)

# Configuracao da ferramenta para usar stopwords
termgen.set_stopper(stopper)

def index_file(path):
    with open(path, "r", encoding="latin-1") as f:
        content = f.read()

    docs = re.findall(r"<DOC>(.*?)</DOC>", content, re.DOTALL)

    for d in docs:
        docno_match = re.search(r"<DOCNO>(.*?)</DOCNO>", d)
        text_match = re.search(r"<TEXT>(.*?)</TEXT>", d, re.DOTALL)

        if not docno_match or not text_match:
            continue

        docno = docno_match.group(1).strip()
        text = " ".join(text_match.group(1).split())

        doc = xapian.Document()
        termgen.set_document(doc)

        # Indexação padrão
        termgen.index_text(text)

        doc.add_value(0, docno)
        doc.set_data(text)

        db.add_document(doc)

def index_directory(base_path):
    for root, dirs, files in os.walk(base_path):
        for file in files:
            if file.endswith(".sgml"):
                full_path = os.path.join(root, file)
                print(f"Indexando: {full_path}")
                index_file(full_path)

# Caminho raiz para indexar
index_directory("folha")

print("Indexação concluída!")
