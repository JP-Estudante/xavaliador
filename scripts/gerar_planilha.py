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


def larguras_colunas(linhas, larguras_custom=None):
    max_colunas = max(len(linha) for linha in linhas)
    larguras = []

    for col_idx in range(max_colunas):
        if larguras_custom and col_idx < len(larguras_custom):
            larguras.append(larguras_custom[col_idx])
            continue

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


def texto_curto(valor):
    if valor == "":
        return False

    if isinstance(valor, (int, float, dict)) and not isinstance(valor, bool):
        return True

    texto = str(valor)
    return len(texto) <= 26 and "\n" not in texto


def altura_linha(linha, larguras):
    maior_altura = 20

    for col_idx, valor in enumerate(linha):
        texto = valor_para_largura(valor)

        if not texto:
            continue

        largura = larguras[col_idx] if col_idx < len(larguras) else 18
        linhas_estimadas = max(1, math.ceil(len(texto) / max(largura - 2, 8)))
        maior_altura = max(maior_altura, min(18 + linhas_estimadas * 10, 64))

    return maior_altura


def estilo_colorido(valor, cor, centralizado=False):
    if cor == "verde":
        if isinstance(valor, int) and not isinstance(valor, bool):
            return 28 if centralizado else 15

        if isinstance(valor, (float, dict)):
            return 21 if centralizado else 7

        return 20 if centralizado else 6

    if cor == "azul":
        if isinstance(valor, int) and not isinstance(valor, bool):
            return 29 if centralizado else 16

        if isinstance(valor, (float, dict)):
            return 23 if centralizado else 9

        return 22 if centralizado else 8

    if cor == "amarelo":
        if isinstance(valor, int) and not isinstance(valor, bool):
            return 30 if centralizado else 17

        if isinstance(valor, (float, dict)):
            return 25 if centralizado else 11

        return 24 if centralizado else 10

    if cor == "zebra":
        if isinstance(valor, int) and not isinstance(valor, bool):
            return 31 if centralizado else 14

        if isinstance(valor, (float, dict)):
            return 27 if centralizado else 13

        return 26 if centralizado else 12

    return None


def estilo_celula(row_idx, col_idx, valor, ref="", celulas_negrito=None, celulas_cores=None):
    celulas_negrito = celulas_negrito or set()
    celulas_cores = celulas_cores or {}
    centralizado = texto_curto(valor)

    if row_idx == 1:
        return 1

    estilo_cor = estilo_colorido(valor, celulas_cores.get(ref), centralizado)
    if estilo_cor:
        return estilo_cor

    if ref in celulas_negrito:
        return 19 if centralizado else 2

    if row_idx > 1 and col_idx == 1 and valor in (
        "Melhor configuracao",
        "Melhor configuração",
        "Baseline",
        "Decisao",
        "Decisão",
        "Regra de comparacao",
        "Regra de comparação",
    ):
        return 19 if centralizado else 2

    if isinstance(valor, int) and not isinstance(valor, bool):
        return 5

    if isinstance(valor, float) or isinstance(valor, dict):
        return 4

    if valor != "":
        return 18 if centralizado else 3

    return 0


def estilos_planilha():
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
  <numFmts count="1">
    <numFmt numFmtId="164" formatCode="0.0000"/>
  </numFmts>
  <fonts count="3">
    <font><sz val="11"/><name val="Calibri"/></font>
    <font><b/><sz val="11"/><name val="Calibri"/></font>
    <font><b/><sz val="11"/><color rgb="FFFFFFFF"/><name val="Calibri"/></font>
  </fonts>
  <fills count="7">
    <fill><patternFill patternType="none"/></fill>
    <fill><patternFill patternType="gray125"/></fill>
    <fill><patternFill patternType="solid"><fgColor rgb="FF595959"/><bgColor indexed="64"/></patternFill></fill>
    <fill><patternFill patternType="solid"><fgColor rgb="FFE2F0D9"/><bgColor indexed="64"/></patternFill></fill>
    <fill><patternFill patternType="solid"><fgColor rgb="FFDDEBF7"/><bgColor indexed="64"/></patternFill></fill>
    <fill><patternFill patternType="solid"><fgColor rgb="FFFFF2CC"/><bgColor indexed="64"/></patternFill></fill>
    <fill><patternFill patternType="solid"><fgColor rgb="FFF7F9FB"/><bgColor indexed="64"/></patternFill></fill>
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
  <cellXfs count="32">
    <xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/>
    <xf numFmtId="0" fontId="2" fillId="2" borderId="1" xfId="0" applyFont="1" applyFill="1" applyBorder="1" applyAlignment="1"><alignment horizontal="center" vertical="center" wrapText="1"/></xf>
    <xf numFmtId="0" fontId="1" fillId="0" borderId="1" xfId="0" applyFont="1" applyBorder="1" applyAlignment="1"><alignment vertical="center"/></xf>
    <xf numFmtId="0" fontId="0" fillId="0" borderId="1" xfId="0" applyBorder="1" applyAlignment="1"><alignment vertical="center" wrapText="1"/></xf>
    <xf numFmtId="164" fontId="0" fillId="0" borderId="1" xfId="0" applyNumberFormat="1" applyBorder="1" applyAlignment="1"><alignment horizontal="center" vertical="center"/></xf>
    <xf numFmtId="1" fontId="0" fillId="0" borderId="1" xfId="0" applyNumberFormat="1" applyBorder="1" applyAlignment="1"><alignment horizontal="center" vertical="center"/></xf>
    <xf numFmtId="0" fontId="1" fillId="3" borderId="1" xfId="0" applyFont="1" applyFill="1" applyBorder="1" applyAlignment="1"><alignment vertical="center" wrapText="1"/></xf>
    <xf numFmtId="164" fontId="1" fillId="3" borderId="1" xfId="0" applyNumberFormat="1" applyFont="1" applyFill="1" applyBorder="1" applyAlignment="1"><alignment vertical="center"/></xf>
    <xf numFmtId="0" fontId="0" fillId="4" borderId="1" xfId="0" applyFill="1" applyBorder="1" applyAlignment="1"><alignment vertical="center" wrapText="1"/></xf>
    <xf numFmtId="164" fontId="0" fillId="4" borderId="1" xfId="0" applyNumberFormat="1" applyFill="1" applyBorder="1" applyAlignment="1"><alignment vertical="center"/></xf>
    <xf numFmtId="0" fontId="0" fillId="5" borderId="1" xfId="0" applyFill="1" applyBorder="1" applyAlignment="1"><alignment vertical="center" wrapText="1"/></xf>
    <xf numFmtId="164" fontId="0" fillId="5" borderId="1" xfId="0" applyNumberFormat="1" applyFill="1" applyBorder="1" applyAlignment="1"><alignment vertical="center"/></xf>
    <xf numFmtId="0" fontId="0" fillId="6" borderId="1" xfId="0" applyFill="1" applyBorder="1" applyAlignment="1"><alignment vertical="center" wrapText="1"/></xf>
    <xf numFmtId="164" fontId="0" fillId="6" borderId="1" xfId="0" applyNumberFormat="1" applyFill="1" applyBorder="1" applyAlignment="1"><alignment vertical="center"/></xf>
    <xf numFmtId="1" fontId="0" fillId="6" borderId="1" xfId="0" applyNumberFormat="1" applyFill="1" applyBorder="1" applyAlignment="1"><alignment vertical="center"/></xf>
    <xf numFmtId="1" fontId="1" fillId="3" borderId="1" xfId="0" applyNumberFormat="1" applyFont="1" applyFill="1" applyBorder="1" applyAlignment="1"><alignment vertical="center"/></xf>
    <xf numFmtId="1" fontId="0" fillId="4" borderId="1" xfId="0" applyNumberFormat="1" applyFill="1" applyBorder="1" applyAlignment="1"><alignment vertical="center"/></xf>
    <xf numFmtId="1" fontId="0" fillId="5" borderId="1" xfId="0" applyNumberFormat="1" applyFill="1" applyBorder="1" applyAlignment="1"><alignment vertical="center"/></xf>
    <xf numFmtId="0" fontId="0" fillId="0" borderId="1" xfId="0" applyBorder="1" applyAlignment="1"><alignment horizontal="center" vertical="center" wrapText="1"/></xf>
    <xf numFmtId="0" fontId="1" fillId="0" borderId="1" xfId="0" applyFont="1" applyBorder="1" applyAlignment="1"><alignment horizontal="center" vertical="center" wrapText="1"/></xf>
    <xf numFmtId="0" fontId="1" fillId="3" borderId="1" xfId="0" applyFont="1" applyFill="1" applyBorder="1" applyAlignment="1"><alignment horizontal="center" vertical="center" wrapText="1"/></xf>
    <xf numFmtId="164" fontId="1" fillId="3" borderId="1" xfId="0" applyNumberFormat="1" applyFont="1" applyFill="1" applyBorder="1" applyAlignment="1"><alignment horizontal="center" vertical="center"/></xf>
    <xf numFmtId="0" fontId="0" fillId="4" borderId="1" xfId="0" applyFill="1" applyBorder="1" applyAlignment="1"><alignment horizontal="center" vertical="center" wrapText="1"/></xf>
    <xf numFmtId="164" fontId="0" fillId="4" borderId="1" xfId="0" applyNumberFormat="1" applyFill="1" applyBorder="1" applyAlignment="1"><alignment horizontal="center" vertical="center"/></xf>
    <xf numFmtId="0" fontId="0" fillId="5" borderId="1" xfId="0" applyFill="1" applyBorder="1" applyAlignment="1"><alignment horizontal="center" vertical="center" wrapText="1"/></xf>
    <xf numFmtId="164" fontId="0" fillId="5" borderId="1" xfId="0" applyNumberFormat="1" applyFill="1" applyBorder="1" applyAlignment="1"><alignment horizontal="center" vertical="center"/></xf>
    <xf numFmtId="0" fontId="0" fillId="6" borderId="1" xfId="0" applyFill="1" applyBorder="1" applyAlignment="1"><alignment horizontal="center" vertical="center" wrapText="1"/></xf>
    <xf numFmtId="164" fontId="0" fillId="6" borderId="1" xfId="0" applyNumberFormat="1" applyFill="1" applyBorder="1" applyAlignment="1"><alignment horizontal="center" vertical="center"/></xf>
    <xf numFmtId="1" fontId="1" fillId="3" borderId="1" xfId="0" applyNumberFormat="1" applyFont="1" applyFill="1" applyBorder="1" applyAlignment="1"><alignment horizontal="center" vertical="center"/></xf>
    <xf numFmtId="1" fontId="0" fillId="4" borderId="1" xfId="0" applyNumberFormat="1" applyFill="1" applyBorder="1" applyAlignment="1"><alignment horizontal="center" vertical="center"/></xf>
    <xf numFmtId="1" fontId="0" fillId="5" borderId="1" xfId="0" applyNumberFormat="1" applyFill="1" applyBorder="1" applyAlignment="1"><alignment horizontal="center" vertical="center"/></xf>
    <xf numFmtId="1" fontId="0" fillId="6" borderId="1" xfId="0" applyNumberFormat="1" applyFill="1" applyBorder="1" applyAlignment="1"><alignment horizontal="center" vertical="center"/></xf>
  </cellXfs>
  <cellStyles count="1">
    <cellStyle name="Normal" xfId="0" builtinId="0"/>
  </cellStyles>
</styleSheet>"""


COMENTARIOS = [
    (
        "A1",
        "Cada linha resume uma combinacao de pre-processamento e modelo de recuperacao.",
    ),
    (
        "C1",
        "MAP e a media das AvP das consultas. Quanto mais perto de 1, melhor o ranking.",
    ),
    (
        "D1",
        "Tempo gasto para criar o indice Xapian daquela tecnica de pre-processamento.",
    ),
    (
        "F1",
        "Tempo medio de consulta: tempo total de consulta dividido pelo numero de consultas.",
    ),
    (
        "G1",
        "Configuracao que era a melhor antes do experimento desta linha ser avaliado.",
    ),
    (
        "I1",
        "p-valor do teste-t pareado contra a melhor configuracao anterior. Valor menor que 0.05 costuma indicar diferenca estatisticamente significativa.",
    ),
    (
        "J1",
        "Indica se o experimento substituiu ou nao a melhor configuracao anterior.",
    ),
    (
        "K1",
        "Arquivo CSV com os resultados daquele experimento especifico.",
    ),
]


def comentarios_planilha(comentarios=None):
    comentarios = comentarios or COMENTARIOS
    comentarios_xml = []

    for celula, texto in comentarios:
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


def desenho_comentarios(comentarios=None):
    comentarios = comentarios or COMENTARIOS
    shapes = []

    for i, (celula, _) in enumerate(comentarios, start=1):
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

def rels_planilha(indice=1):
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/comments" Target="../comments{indice}.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/vmlDrawing" Target="../drawings/vmlDrawing{indice}.vml"/>
</Relationships>"""


def xml_planilha(
    linhas,
    mesclagens=None,
    celulas_negrito=None,
    celulas_cores=None,
    larguras=None,
    congelar_cabecalho=True,
    auto_filtro=None,
    zoom=95,
    tem_comentarios=True,
):
    rows_xml = []
    mesclagens = mesclagens or []
    celulas_negrito = celulas_negrito or set()
    celulas_cores = celulas_cores or {}
    larguras_finais = larguras or []

    for row_idx, linha in enumerate(linhas, start=1):
        cells = []

        for col_idx, valor in enumerate(linha, start=1):
            ref = f"{coluna_excel(col_idx)}{row_idx}"
            tem_formula = isinstance(valor, dict) and "formula" in valor
            numero = isinstance(valor, (int, float)) and not isinstance(valor, bool)
            tipo = "" if tem_formula or numero else ' t="inlineStr"'
            estilo = estilo_celula(row_idx, col_idx, valor, ref, celulas_negrito, celulas_cores)
            estilo_xml = f' s="{estilo}"' if estilo else ""
            cells.append(f'<c r="{ref}"{estilo_xml}{tipo}>{valor_celula(valor)}</c>')

        if row_idx == 1:
            altura_valor = 34
        else:
            altura_valor = altura_linha(linha, larguras_finais)

        altura = f' ht="{altura_valor}" customHeight="1"'
        rows_xml.append(f'<row r="{row_idx}"{altura}>{"".join(cells)}</row>')

    cols_xml = larguras_colunas(linhas, larguras_finais)
    mesclagens_xml = ""
    sheet_views_xml = f'<sheetViews><sheetView workbookViewId="0" zoomScale="{zoom}">'

    if congelar_cabecalho:
        sheet_views_xml += '<pane ySplit="1" topLeftCell="A2" activePane="bottomLeft" state="frozen"/>'

    sheet_views_xml += "</sheetView></sheetViews>"
    auto_filtro_xml = f'<autoFilter ref="{escape(auto_filtro)}"/>' if auto_filtro else ""

    if mesclagens:
        refs = "".join(f'<mergeCell ref="{escape(ref)}"/>' for ref in mesclagens)
        mesclagens_xml = f'<mergeCells count="{len(mesclagens)}">{refs}</mergeCells>'

    sheet_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  {sheet_views_xml}
  <sheetFormatPr defaultRowHeight="22"/>
  <cols>{cols_xml}</cols>
  <sheetData>
    {''.join(rows_xml)}
  </sheetData>
  {auto_filtro_xml}
  {mesclagens_xml}
  {'<legacyDrawing r:id="rId2"/>' if tem_comentarios else ''}
</worksheet>"""

    return sheet_xml


def gerar_planilhas(planilhas, arquivo_saida="avaliacao.xlsx"):
    sheets_xml = []
    workbook_relationships = []
    content_overrides = [
        '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>',
        '<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>',
    ]

    for indice, planilha in enumerate(planilhas, start=1):
        nome = escape(planilha["nome"])
        sheets_xml.append(f'<sheet name="{nome}" sheetId="{indice}" r:id="rId{indice}"/>')
        workbook_relationships.append(
            f'<Relationship Id="rId{indice}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet{indice}.xml"/>'
        )
        content_overrides.append(
            f'<Override PartName="/xl/worksheets/sheet{indice}.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
        )

        if planilha.get("comentarios"):
            content_overrides.append(
                f'<Override PartName="/xl/comments{indice}.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.comments+xml"/>'
            )

    workbook_relationships.append(
        f'<Relationship Id="rId{len(planilhas) + 1}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>'
    )

    workbook_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <sheets>
    {''.join(sheets_xml)}
  </sheets>
  <calcPr calcId="0" fullCalcOnLoad="1"/>
</workbook>"""

    workbook_rels = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  {''.join(workbook_relationships)}
</Relationships>"""

    root_rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>
</Relationships>"""

    content_types = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Default Extension="vml" ContentType="application/vnd.openxmlformats-officedocument.vmlDrawing"/>
  {''.join(content_overrides)}
</Types>"""

    with zipfile.ZipFile(arquivo_saida, "w", compression=zipfile.ZIP_DEFLATED) as xlsx:
        xlsx.writestr("[Content_Types].xml", content_types)
        xlsx.writestr("_rels/.rels", root_rels)
        xlsx.writestr("xl/workbook.xml", workbook_xml)
        xlsx.writestr("xl/_rels/workbook.xml.rels", workbook_rels)
        xlsx.writestr("xl/styles.xml", estilos_planilha())

        for indice, planilha in enumerate(planilhas, start=1):
            comentarios = planilha.get("comentarios")
            sheet_xml = xml_planilha(
                planilha["linhas"],
                mesclagens=planilha.get("mesclagens"),
                celulas_negrito=planilha.get("celulas_negrito"),
                celulas_cores=planilha.get("celulas_cores"),
                larguras=planilha.get("larguras"),
                congelar_cabecalho=planilha.get("congelar_cabecalho", True),
                auto_filtro=planilha.get("auto_filtro"),
                zoom=planilha.get("zoom", 95),
                tem_comentarios=bool(comentarios),
            )
            xlsx.writestr(f"xl/worksheets/sheet{indice}.xml", sheet_xml)

            if comentarios:
                xlsx.writestr(f"xl/comments{indice}.xml", comentarios_planilha(comentarios))
                xlsx.writestr(f"xl/drawings/vmlDrawing{indice}.vml", desenho_comentarios(comentarios))
                xlsx.writestr(f"xl/worksheets/_rels/sheet{indice}.xml.rels", rels_planilha(indice))


def gerar_planilha(linhas, arquivo_saida="avaliacao.xlsx", comentarios=None, mesclagens=None, celulas_negrito=None):
    gerar_planilhas(
        [
            {
                "nome": "Avaliacao",
                "linhas": linhas,
                "comentarios": comentarios,
                "mesclagens": mesclagens,
                "celulas_negrito": celulas_negrito,
                "celulas_cores": None,
            }
        ],
        arquivo_saida,
    )


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
