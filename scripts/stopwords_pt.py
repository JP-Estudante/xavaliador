STOPWORDS_FALLBACK = """
a ao aos aquela aquelas aquele aqueles aquilo as ate com como da das de dela
delas dele deles depois do dos e ela elas ele eles em entre era eram essa
essas esse esses esta estamos estao estar estas estava estavam este estes eu
foi foram fosse fossem ha isso isto ja lhe lhes mais mas me mesmo meu meus
minha minhas muito na nao nas nem no nos nossa nossas nosso nossos num numa o
os ou para pela pelas pelo pelos por qual quando que quem se sem ser seu seus
sua suas tambem te tem tendo tenho ter teu teus tua tuas um uma voce voces
""".split()


def stopwords_portugues():
    try:
        import nltk
        from nltk.corpus import stopwords

        return stopwords.words("portuguese")
    except ImportError:
        return STOPWORDS_FALLBACK
    except LookupError:
        nltk.download("stopwords")
        return stopwords.words("portuguese")
