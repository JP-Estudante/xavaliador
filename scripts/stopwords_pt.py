import nltk
from nltk.corpus import stopwords


def stopwords_portugues():
    try:
        return stopwords.words("portuguese")
    except LookupError:
        nltk.download("stopwords")
        return stopwords.words("portuguese")
