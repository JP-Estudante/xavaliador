import re


def lematizar_palavra(palavra):
    palavra = palavra.lower()

    excecoes = {
        "acoes": "acao",
        "ações": "ação",
        "avioes": "aviao",
        "aviões": "avião",
        "capitais": "capital",
        "cidades": "cidade",
        "crises": "crise",
        "homens": "homem",
        "maes": "mae",
        "mães": "mãe",
        "mulheres": "mulher",
        "paises": "pais",
        "países": "país",
    }

    if palavra in excecoes:
        return excecoes[palavra]

    finais_verbos_ar = [
        "ariam", "arao", "avam", "asse", "ando", "aram", "adas", "ados",
        "ada", "ado", "ava", "ou", "am", "ei",
    ]
    finais_verbos_er = [
        "eriam", "erao", "eram", "esse", "endo", "eram", "idas", "idos",
        "ida", "ido", "eu", "em", "i",
    ]
    finais_verbos_ir = [
        "iriam", "irao", "iram", "isse", "indo", "iram", "idas", "idos",
        "ida", "ido", "iu", "em", "i",
    ]

    for final in finais_verbos_ar:
        if palavra.endswith(final) and len(palavra) > len(final) + 2:
            return palavra[: -len(final)] + "ar"

    for final in finais_verbos_er:
        if palavra.endswith(final) and len(palavra) > len(final) + 2:
            return palavra[: -len(final)] + "er"

    for final in finais_verbos_ir:
        if palavra.endswith(final) and len(palavra) > len(final) + 2:
            return palavra[: -len(final)] + "ir"

    if palavra.endswith("ões") and len(palavra) > 5:
        return palavra[:-3] + "ão"

    if palavra.endswith("oes") and len(palavra) > 5:
        return palavra[:-3] + "ao"

    if palavra.endswith("ais") and len(palavra) > 5:
        return palavra[:-3] + "al"

    if palavra.endswith("eis") and len(palavra) > 5:
        return palavra[:-3] + "el"

    if palavra.endswith("is") and len(palavra) > 4:
        return palavra[:-2] + "il"

    if palavra.endswith("ns") and len(palavra) > 4:
        return palavra[:-2] + "m"

    if palavra.endswith("s") and len(palavra) > 4:
        return palavra[:-1]

    return palavra


def lematizar_texto(texto):
    palavras = re.findall(r"[A-Za-zÀ-ÿ]+", texto)
    lemas = [lematizar_palavra(palavra) for palavra in palavras]

    return " ".join(lemas)
