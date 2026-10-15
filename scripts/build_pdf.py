#!/usr/bin/env python3
"""Build A4 print editions from the repository's simple Markdown and SVG."""
from html import escape
from io import BytesIO
from pathlib import Path
import re
from urllib.parse import quote, unquote

import fitz
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Image, KeepTogether, PageBreak, Paragraph, SimpleDocTemplate,
    Spacer, Table, TableStyle,
)

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / 'Тех карты/Уровень/Endress+Hauser/Prosonic'
OUT = ROOT / 'Материалы'
BASE_URL = 'https://github.com/MaximValishevskiyNZ/KIPiA/blob/main/'
INK = colors.HexColor('#14283F')
TEAL = colors.HexColor('#007F78')
MUTED = colors.HexColor('#526477')
PALE = colors.HexColor('#F3F6FA')
WIDTH = A4[0] - 36 * mm


def fonts():
    candidates = [Path('/usr/share/fonts/truetype/dejavu'), Path('/usr/share/fonts/truetype/noto')]
    for base in candidates:
        normal = next(iter(base.glob('*Sans-Regular.ttf')), None) or next(iter(base.glob('DejaVuSans.ttf')), None)
        bold = next(iter(base.glob('*Sans-Bold.ttf')), None) or next(iter(base.glob('DejaVuSans-Bold.ttf')), None)
        if normal and bold:
            pdfmetrics.registerFont(TTFont('KIP', str(normal)))
            pdfmetrics.registerFont(TTFont('KIP-Bold', str(bold)))
            pdfmetrics.registerFontFamily('KIP', normal='KIP', bold='KIP-Bold', italic='KIP', boldItalic='KIP-Bold')
            return
    raise SystemExit('Install Noto Sans or DejaVu Sans fonts with Cyrillic support.')


def styles():
    return {
        'p': ParagraphStyle('Body', fontName='KIP', fontSize=9.2, leading=14.2, textColor=INK, spaceAfter=7),
        'h1': ParagraphStyle('Chapter', fontName='KIP-Bold', fontSize=20, leading=26, textColor=INK, spaceAfter=15, keepWithNext=True),
        'h2': ParagraphStyle('Section', fontName='KIP-Bold', fontSize=13.5, leading=18, textColor=TEAL, spaceBefore=13, spaceAfter=8, keepWithNext=True),
        'h3': ParagraphStyle('Subsection', fontName='KIP-Bold', fontSize=11, leading=16, textColor=INK, spaceBefore=9, spaceAfter=6, keepWithNext=True),
        'cell': ParagraphStyle('Cell', fontName='KIP', fontSize=7.7, leading=11.1, textColor=INK),
        'head': ParagraphStyle('HeadCell', fontName='KIP-Bold', fontSize=7.8, leading=11.1, textColor=colors.white),
        'code': ParagraphStyle('Formula', fontName='KIP', fontSize=8.7, leading=13.7, backColor=PALE, borderPadding=9, spaceBefore=5, spaceAfter=12, textColor=TEAL),
        'note': ParagraphStyle('Note', fontName='KIP', fontSize=8.8, leading=13.7, textColor=INK, backColor=PALE, borderPadding=8, spaceAfter=12),
        'caption': ParagraphStyle('Caption', fontName='KIP', fontSize=7.5, leading=11, textColor=MUTED, spaceAfter=10),
    }


def inline(value, origin):
    # All source strings are escaped first; only explicit local formatting is added.
    value = escape(value)
    def link(match):
        label, dest = match.groups()
        if dest.startswith(('https://', 'http://')):
            target = dest
        else:
            local = (origin.parent / unquote(dest.split('#')[0])).resolve().relative_to(ROOT)
            target = BASE_URL + quote(local.as_posix(), safe='/+')
        return f'<link href="{escape(target, quote=True)}" color="#007F78">{label}</link>'
    value = re.sub(r'\[([^\]]+)\]\(([^\s)]+)\)', link, value)
    value = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', value)
    value = re.sub(r'`([^`]+)`', r'<font color="#007F78">\1</font>', value)
    return value


def svg_image(path):
    with fitz.open(stream=path.read_bytes(), filetype='svg') as svg:
        with fitz.open('pdf', svg.convert_to_pdf()) as pdf:
            page = pdf[0]
            pix = page.get_pixmap(matrix=fitz.Matrix(1.7, 1.7), alpha=False)
            ratio = page.rect.height / page.rect.width
            return Image(BytesIO(pix.tobytes('png')), width=WIDTH, height=WIDTH * ratio)


def parse(file, st, skip_title=False):
    rows = file.read_text().splitlines()
    flow = []
    i = 0
    while i < len(rows):
        raw = rows[i].strip()
        if not raw:
            i += 1
            continue
        if raw.startswith('```'):
            language = raw[3:]
            code = []
            i += 1
            while i < len(rows) and not rows[i].strip().startswith('```'):
                code.append(rows[i])
                i += 1
            if language == 'mermaid':
                if file.name.startswith('00-'):
                    body = 'Измерительная цепочка: уровень → поплавок → цель → расстояние D → привязка к уровню → выход → ПЛК.'
                else:
                    body = 'Порядок поиска: питание → достоверность D → правильность локального L → выходной сигнал и масштаб ПЛК. Подробный алгоритм — в электронной версии.'
                flow.append(Paragraph(escape(body), st['note']))
            else:
                flow.append(Paragraph('<br/>'.join(escape(line) for line in code), st['code']))
            i += 1
            continue
        if raw.startswith('|'):
            table_rows = []
            while i < len(rows) and rows[i].strip().startswith('|'):
                cells = [x.strip() for x in rows[i].strip().strip('|').split('|')]
                if not all(re.fullmatch(r'[-: ]+', cell) for cell in cells):
                    table_rows.append(cells)
                i += 1
            n = len(table_rows[0])
            widths = [WIDTH / n] * n
            if n == 2:
                widths = [WIDTH * .32, WIDTH * .68]
            elif n == 3:
                widths = [WIDTH * .23, WIDTH * .35, WIDTH * .42]
            elif n == 4:
                widths = [WIDTH * .19, WIDTH * .31, WIDTH * .21, WIDTH * .29]
            data = [[Paragraph(inline(cell, file), st['head' if rownum == 0 else 'cell']) for cell in row] for rownum, row in enumerate(table_rows)]
            table = Table(data, colWidths=widths, repeatRows=1, hAlign='LEFT')
            table.setStyle(TableStyle([
                ('BACKGROUND', (0,0),(-1,0), INK),
                ('ROWBACKGROUNDS', (0,1),(-1,-1), [colors.white, PALE]),
                ('VALIGN', (0,0),(-1,-1), 'TOP'),
                ('LEFTPADDING', (0,0),(-1,-1), 7), ('RIGHTPADDING',(0,0),(-1,-1),7),
                ('TOPPADDING',(0,0),(-1,-1),7), ('BOTTOMPADDING',(0,0),(-1,-1),7),
                ('LINEBELOW',(0,0),(-1,0),.7,TEAL),
            ]))
            flow += [table, Spacer(1, 9)]
            continue
        image = re.fullmatch(r'!\[([^\]]*)\]\(([^)]+)\)', raw)
        if image:
            target = (file.parent / unquote(image.group(2))).resolve()
            flow.append(KeepTogether([svg_image(target), Paragraph(escape(image.group(1)), st['caption'])]))
            i += 1
            continue
        if raw.startswith('#'):
            level = len(raw) - len(raw.lstrip('#'))
            if not(skip_title and level == 1):
                flow.append(Paragraph(inline(raw[level:].strip(), file), st[f'h{min(level,3)}']))
            i += 1
            continue
        if raw.startswith('>'):
            note = []
            while i < len(rows) and rows[i].strip().startswith('>'):
                value = rows[i].strip().lstrip('> ').strip()
                if not value.startswith('[!'):
                    note.append(value)
                i += 1
            flow.append(Paragraph(inline(' '.join(note), file), st['note']))
            continue
        bullet = re.match(r'^(?:([-*])|([0-9]+)\.)\s+(.*)', raw)
        if bullet:
            marker = '•' if bullet.group(1) else bullet.group(2) + '.'
            value = bullet.group(3).replace('[ ]', '□').replace('[x]', '✓')
            flow.append(Paragraph(f'<b>{marker}</b> ' + inline(value, file), st['p']))
            i += 1
            continue
        # Navigation lines belong to GitHub, not the print text.
        if raw.startswith('[К ') or raw.startswith('[КИПиА]'):
            i += 1
            continue
        paragraph = [raw]
        i += 1
        while i < len(rows) and rows[i].strip() and not re.match(r'^(#|\||>|```|!\[|[-*] |\d+\. )', rows[i].strip()):
            paragraph.append(rows[i].strip())
            i += 1
        flow.append(Paragraph(inline(' '.join(paragraph), file), st['p']))
    return flow


class Book(SimpleDocTemplate):
    def afterFlowable(self, flowable):
        if isinstance(flowable, Paragraph) and flowable.style.name == 'Chapter':
            key = f'chapter-{self.page}-{id(flowable)}'
            self.canv.bookmarkPage(key)
            self.canv.addOutlineEntry(flowable.getPlainText(), key, level=0)


def footer(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor('#C8D5E2'))
    canvas.line(18*mm, 16*mm, A4[0]-18*mm, 16*mm)
    canvas.setFont('KIP', 7)
    canvas.setFillColor(MUTED)
    canvas.drawString(18*mm, 11*mm, 'КИПиА / PROSONIC · 1.0 · 15.10.2026')
    canvas.drawRightString(A4[0]-18*mm, 11*mm, str(doc.page))
    canvas.restoreState()


def build(name, title, files, short=False):
    st = styles()
    flow = [svg_image(ROOT/'.github/assets/cover.svg'), Spacer(1,22), Paragraph(title, st['h1'])]
    flow += [Paragraph('Каскад флотации ТОФ · поплавок / отражающая цель', st['h2'])]
    flow += [Paragraph('Общая техкарта и справочные материалы по официальным документам Endress+Hauser. Точная модель и конструкция поплавкового узла пока не установлены.', st['p'])]
    flow += [Paragraph('Версия 1.0 · 15 октября 2026<br/>Технические пределы привязаны к указанным редакциям. Механика поплавка и учебные расчёты отделены от данных производителя.', st['note'])]
    flow += [Paragraph('<link href="https://github.com/MaximValishevskiyNZ/KIPiA" color="#007F78">Электронная версия, схемы и шаблоны: github.com/MaximValishevskiyNZ/KIPiA</link>', st['p'])]
    for file in files:
        flow.append(PageBreak())
        flow += parse(file, st)
    if short:
        flow += [Spacer(1,12), Paragraph('Официальные документы и границы источников', st['h2'])]
        flow += [Paragraph('T1: BA00387F/00/EN/14.14 (FMU30). M1: BA00237F/00/EN/13.12 (Prosonic M HART). S1: BA00288F/00/EN/16.21 (FMU90 HART). A1: SO01117U60EN0123, с.14–15 (флотация, FDU91). Полный реестр со ссылками и контрольными суммами — в электронной версии.', st['p'])]
        source_url = BASE_URL + quote((DOCS/'источники.md').relative_to(ROOT).as_posix(), safe='/+')
        flow += [Paragraph(f'<link href="{source_url}" color="#007F78">Открыть реестр официальных источников</link>', st['p'])]
    doc = Book(str(OUT/name), pagesize=A4, leftMargin=18*mm, rightMargin=18*mm, topMargin=18*mm, bottomMargin=23*mm, title=title, author='КИПиА', subject='Prosonic: техкарта для каскада флотации с поплавком')
    doc.build(flow, onFirstPage=footer, onLaterPages=footer)
    print(name)


def main():
    fonts()
    OUT.mkdir(exist_ok=True)
    build('Prosonic-техкарта-флотация.pdf', 'Prosonic с поплавком · Техкарта', [DOCS/'00-техкарта-флотация.md'], short=True)
    files = [DOCS/n for n in ['00-техкарта-флотация.md','01-принцип-и-монтаж.md','02-fmu30.md','03-prosonic-m-hart.md','04-fmu90-hart.md','05-диагностика.md','06-примеры-и-приёмка.md','07-словарь.md','источники.md']]
    files.append(ROOT/'Шаблоны/Пусконаладка.md')
    build('Prosonic-понятное-руководство.pdf', 'Prosonic · Понятное руководство', files)


if __name__ == '__main__':
    main()
