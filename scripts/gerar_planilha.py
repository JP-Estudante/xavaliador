import math
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from xml.sax.saxutils import escape


def formula(expressao, valor=""):
    return {"formula": expressao, "valor": valor}


def coluna_excel(indice):
    nome = ""
    while indice:
        indice, resto = divmod(indice - 1, 26)
        nome = chr(65 + resto) + nome
    return nome


def valor_celula(valor):
    if isinstance(valor, dict) and "formula" in valor:
        xml = f"<f>{escape(valor['formula'])}</f>"

        if valor["valor"] != "":
            xml += f"<v>{valor['valor']}</v>"

        return xml

    if isinstance(valor, (int, float)) and not isinstance(valor, bool):
        return f"<v>{valor}</v>"

    return f'<is><t>{escape(str(valor))}</t></is>'


def gerar_planilha(linhas, arquivo_saida="avaliacao.xlsx"):
    rows_xml = []

    for row_idx, linha in enumerate(linhas, start=1):
        cells = []

        for col_idx, valor in enumerate(linha, start=1):
            ref = f"{coluna_excel(col_idx)}{row_idx}"
            tem_formula = isinstance(valor, dict) and "formula" in valor
            numero = isinstance(valor, (int, float)) and not isinstance(valor, bool)
            tipo = "" if tem_formula or numero else ' t="inlineStr"'
            cells.append(f'<c r="{ref}"{tipo}>{valor_celula(valor)}</c>')

        rows_xml.append(f'<row r="{row_idx}">{"".join(cells)}</row>')

    sheet_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
  <sheetData>
    {''.join(rows_xml)}
  </sheetData>
</worksheet>"""

    workbook_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <sheets>
    <sheet name="Avaliacao" sheetId="1" r:id="rId1"/>
  </sheets>
  <calcPr calcId="0" fullCalcOnLoad="1"/>
</workbook>"""

    workbook_rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>
</Relationships>"""

    root_rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>
</Relationships>"""

    content_types = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
  <Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
</Types>"""

    with zipfile.ZipFile(arquivo_saida, "w", compression=zipfile.ZIP_DEFLATED) as xlsx:
        xlsx.writestr("[Content_Types].xml", content_types)
        xlsx.writestr("_rels/.rels", root_rels)
        xlsx.writestr("xl/workbook.xml", workbook_xml)
        xlsx.writestr("xl/_rels/workbook.xml.rels", workbook_rels)
        xlsx.writestr("xl/worksheets/sheet1.xml", sheet_xml)


def gerar_zip(csv_entrada, planilha_saida="avaliacao.xlsx", zip_saida="entrega.zip"):
    with zipfile.ZipFile(zip_saida, "w", compression=zipfile.ZIP_DEFLATED) as entrega:
        entrega.write(csv_entrada, Path(csv_entrada).name)
        entrega.write(planilha_saida, Path(planilha_saida).name)


def ler_tempos_planilha(caminho):
    tempos = {}

    if not Path(caminho).exists():
        return tempos

    with zipfile.ZipFile(caminho) as arquivo:
        xml = arquivo.read("xl/worksheets/sheet1.xml")

    ns = {"x": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    root = ET.fromstring(xml)

    for row in root.findall(".//x:row", ns):
        valores = []

        for cell in row.findall("x:c", ns):
            texto = cell.find(".//x:t", ns)
            numero = cell.find("x:v", ns)

            if texto is not None:
                valores.append(texto.text)
            elif numero is not None:
                valores.append(float(numero.text))
            else:
                valores.append("")

        if len(valores) >= 2:
            tempos[valores[0]] = valores[1]

    return tempos


def beta_continuada(a, b, x):
    max_iteracoes = 200
    eps = 3e-14
    menor = 1e-300

    qab = a + b
    qap = a + 1.0
    qam = a - 1.0
    c = 1.0
    d = 1.0 - qab * x / qap

    if abs(d) < menor:
        d = menor

    d = 1.0 / d
    h = d

    for m in range(1, max_iteracoes + 1):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d

        if abs(d) < menor:
            d = menor

        c = 1.0 + aa / c

        if abs(c) < menor:
            c = menor

        d = 1.0 / d
        h *= d * c

        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d

        if abs(d) < menor:
            d = menor

        c = 1.0 + aa / c

        if abs(c) < menor:
            c = menor

        d = 1.0 / d
        delta = d * c
        h *= delta

        if abs(delta - 1.0) < eps:
            break

    return h


def beta_regularizada(a, b, x):
    if x <= 0:
        return 0.0

    if x >= 1:
        return 1.0

    bt = math.exp(
        math.lgamma(a + b)
        - math.lgamma(a)
        - math.lgamma(b)
        + a * math.log(x)
        + b * math.log(1.0 - x)
    )

    if x < (a + 1.0) / (a + b + 2.0):
        return bt * beta_continuada(a, b, x) / a

    return 1.0 - bt * beta_continuada(b, a, 1.0 - x) / b


def cdf_t(t, graus_liberdade):
    x = graus_liberdade / (graus_liberdade + t * t)
    ib = beta_regularizada(graus_liberdade / 2.0, 0.5, x)

    if t >= 0:
        return 1.0 - 0.5 * ib

    return 0.5 * ib


def p_valor_t_pareado(valores_a, valores_b):
    diferencas = [a - b for a, b in zip(valores_a, valores_b)]
    n = len(diferencas)

    if n < 2:
        return ""

    media = sum(diferencas) / n
    variancia = sum((d - media) ** 2 for d in diferencas) / (n - 1)
    desvio = math.sqrt(variancia)

    if desvio == 0:
        return 1.0 if media == 0 else 0.0

    t = media / (desvio / math.sqrt(n))
    p = 2.0 * (1.0 - cdf_t(abs(t), n - 1))

    return max(0.0, min(1.0, p))
