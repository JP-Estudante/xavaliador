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


def valor_para_largura(valor):
    if isinstance(valor, dict) and "valor" in valor:
        valor = valor["valor"]

    return str(valor)


def larguras_colunas(linhas):
    max_colunas = max(len(linha) for linha in linhas)
    larguras = []

    for col_idx in range(max_colunas):
        maior = 0

        for linha in linhas:
            if col_idx < len(linha):
                maior = max(maior, len(valor_para_largura(linha[col_idx])))

        largura = min(max(maior + 2, 12), 32)
        larguras.append(largura)

    return "".join(
        f'<col min="{i}" max="{i}" width="{largura}" customWidth="1"/>'
        for i, largura in enumerate(larguras, start=1)
    )


def estilo_celula(row_idx, col_idx, valor):
    if row_idx in (1, 7):
        return 1

    if row_idx <= 5 and col_idx == 1:
        return 2

    if row_idx >= 8 and col_idx in (7, 8):
        return 5

    if isinstance(valor, (int, float)) or isinstance(valor, dict):
        return 4

    if valor != "":
        return 3

    return 0


def estilos_planilha():
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
  <numFmts count="1">
    <numFmt numFmtId="164" formatCode="0.0000"/>
  </numFmts>
  <fonts count="2">
    <font><sz val="11"/><name val="Calibri"/></font>
    <font><b/><sz val="11"/><name val="Calibri"/></font>
  </fonts>
  <fills count="3">
    <fill><patternFill patternType="none"/></fill>
    <fill><patternFill patternType="gray125"/></fill>
    <fill><patternFill patternType="solid"><fgColor rgb="FFD9D9D9"/><bgColor indexed="64"/></patternFill></fill>
  </fills>
  <borders count="2">
    <border><left/><right/><top/><bottom/><diagonal/></border>
    <border>
      <left style="thin"><color rgb="FFBFBFBF"/></left>
      <right style="thin"><color rgb="FFBFBFBF"/></right>
      <top style="thin"><color rgb="FFBFBFBF"/></top>
      <bottom style="thin"><color rgb="FFBFBFBF"/></bottom>
      <diagonal/>
    </border>
  </borders>
  <cellStyleXfs count="1">
    <xf numFmtId="0" fontId="0" fillId="0" borderId="0"/>
  </cellStyleXfs>
  <cellXfs count="6">
    <xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/>
    <xf numFmtId="0" fontId="1" fillId="2" borderId="1" xfId="0" applyFont="1" applyFill="1" applyBorder="1" applyAlignment="1"><alignment horizontal="center" vertical="center" wrapText="1"/></xf>
    <xf numFmtId="0" fontId="1" fillId="0" borderId="1" xfId="0" applyFont="1" applyBorder="1" applyAlignment="1"><alignment vertical="center"/></xf>
    <xf numFmtId="0" fontId="0" fillId="0" borderId="1" xfId="0" applyBorder="1" applyAlignment="1"><alignment vertical="center" wrapText="1"/></xf>
    <xf numFmtId="164" fontId="0" fillId="0" borderId="1" xfId="0" applyNumberFormat="1" applyBorder="1" applyAlignment="1"><alignment vertical="center"/></xf>
    <xf numFmtId="1" fontId="0" fillId="0" borderId="1" xfId="0" applyNumberFormat="1" applyBorder="1" applyAlignment="1"><alignment vertical="center"/></xf>
  </cellXfs>
  <cellStyles count="1">
    <cellStyle name="Normal" xfId="0" builtinId="0"/>
  </cellStyles>
</styleSheet>"""


COMENTARIOS = [
    (
        "A2",
        "MAP e a media das AvP das consultas. Quanto mais perto de 1, melhor o ranking; quanto mais perto de 0, pior.",
    ),
    (
        "A5",
        "p-valor do teste-t entre 15.5 e 13.5. Valor menor que 0.05 costuma indicar diferenca estatisticamente significativa.",
    ),
    (
        "B5",
        "Compara as AvP da configuracao 15.5 com a melhor configuracao anterior sem stemming, 13.5.",
    ),
    (
        "B7",
        "AvP de cada consulta usando a configuracao 15.5: stopwords + lematizacao.",
    ),
    (
        "C7",
        "AvP de cada consulta na configuracao 14.7, com stopwords e stemming.",
    ),
    (
        "D7",
        "AvP de cada consulta na configuracao 13.5, que remove stopwords e foi a melhor configuracao anterior sem stemming.",
    ),
    (
        "E7",
        "AvP de cada consulta na configuracao 13.4, sem remocao de stopwords e sem stemming.",
    ),
    (
        "F7",
        "Diferenca calculada como AvP 15.5 menos AvP 13.5. Positivo indica melhora com lematizacao; negativo indica piora.",
    ),
    (
        "G7",
        "Quantidade de documentos relevantes que apareceram entre os resultados recuperados da consulta.",
    ),
    (
        "H7",
        "Total de documentos relevantes existentes no arquivo de avaliacao para aquela consulta.",
    ),
]


def comentarios_planilha():
    comentarios_xml = []

    for celula, texto in COMENTARIOS:
        comentarios_xml.append(
            f'<comment ref="{celula}" authorId="0">'
            f'<text><r><t>{escape(texto)}</t></r></text>'
            f'</comment>'
        )

    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<comments xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
  <authors>
    <author>Avaliador</author>
  </authors>
  <commentList>
    {''.join(comentarios_xml)}
  </commentList>
</comments>"""


def posicao_celula(celula):
    letras = ""
    numeros = ""

    for char in celula:
        if char.isalpha():
            letras += char
        else:
            numeros += char

    coluna = 0
    for letra in letras:
        coluna = coluna * 26 + (ord(letra.upper()) - 64)

    return int(numeros) - 1, coluna - 1


def desenho_comentarios():
    shapes = []

    for i, (celula, _) in enumerate(COMENTARIOS, start=1):
        row, col = posicao_celula(celula)
        shape_id = 1024 + i
        anchor = f"{col + 1}, 15, {row}, 10, {col + 4}, 15, {row + 4}, 10"

        shapes.append(f"""
  <v:shape id="_x0000_s{shape_id}" type="#_x0000_t202" style="position:absolute;margin-left:{80 + col * 30}pt;margin-top:{20 + row * 12}pt;width:220pt;height:70pt;z-index:{i};visibility:hidden" fillcolor="#ffffe1" o:insetmode="auto">
    <v:fill color2="#ffffe1"/>
    <v:shadow on="t" color="black" obscured="t"/>
    <v:path o:connecttype="none"/>
    <v:textbox style="mso-direction-alt:auto"/>
    <x:ClientData ObjectType="Note"><x:MoveWithCells/><x:SizeWithCells/><x:Anchor>{anchor}</x:Anchor><x:AutoFill>False</x:AutoFill><x:Row>{row}</x:Row><x:Column>{col}</x:Column></x:ClientData>
  </v:shape>""")

    return f"""<xml xmlns:v="urn:schemas-microsoft-com:vml" xmlns:o="urn:schemas-microsoft-com:office:office" xmlns:x="urn:schemas-microsoft-com:office:excel">
  <o:shapelayout v:ext="edit">
    <o:idmap v:ext="edit" data="1"/>
  </o:shapelayout>
  <v:shapetype id="_x0000_t202" coordsize="21600,21600" o:spt="202" path="m,l,21600r21600,l21600,xe">
    <v:stroke joinstyle="miter"/>
    <v:path gradientshapeok="t" o:connecttype="rect"/>
  </v:shapetype>
  {''.join(shapes)}
</xml>"""

def rels_planilha():
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/comments" Target="../comments1.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/vmlDrawing" Target="../drawings/vmlDrawing1.vml"/>
</Relationships>"""


def gerar_planilha(linhas, arquivo_saida="avaliacao.xlsx"):
    rows_xml = []

    for row_idx, linha in enumerate(linhas, start=1):
        cells = []

        for col_idx, valor in enumerate(linha, start=1):
            ref = f"{coluna_excel(col_idx)}{row_idx}"
            tem_formula = isinstance(valor, dict) and "formula" in valor
            numero = isinstance(valor, (int, float)) and not isinstance(valor, bool)
            tipo = "" if tem_formula or numero else ' t="inlineStr"'
            estilo = estilo_celula(row_idx, col_idx, valor)
            estilo_xml = f' s="{estilo}"' if estilo else ""
            cells.append(f'<c r="{ref}"{estilo_xml}{tipo}>{valor_celula(valor)}</c>')

        altura = ' ht="22" customHeight="1"' if row_idx in (1, 7) else ""
        rows_xml.append(f'<row r="{row_idx}"{altura}>{"".join(cells)}</row>')

    cols_xml = larguras_colunas(linhas)

    sheet_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <cols>{cols_xml}</cols>
  <sheetData>
    {''.join(rows_xml)}
  </sheetData>
  <legacyDrawing r:id="rId2"/>
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
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
</Relationships>"""

    root_rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>
</Relationships>"""

    content_types = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Default Extension="vml" ContentType="application/vnd.openxmlformats-officedocument.vmlDrawing"/>
  <Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
  <Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
  <Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>
  <Override PartName="/xl/comments1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.comments+xml"/>
</Types>"""

    with zipfile.ZipFile(arquivo_saida, "w", compression=zipfile.ZIP_DEFLATED) as xlsx:
        xlsx.writestr("[Content_Types].xml", content_types)
        xlsx.writestr("_rels/.rels", root_rels)
        xlsx.writestr("xl/workbook.xml", workbook_xml)
        xlsx.writestr("xl/_rels/workbook.xml.rels", workbook_rels)
        xlsx.writestr("xl/styles.xml", estilos_planilha())
        xlsx.writestr("xl/comments1.xml", comentarios_planilha())
        xlsx.writestr("xl/drawings/vmlDrawing1.vml", desenho_comentarios())
        xlsx.writestr("xl/worksheets/_rels/sheet1.xml.rels", rels_planilha())
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
