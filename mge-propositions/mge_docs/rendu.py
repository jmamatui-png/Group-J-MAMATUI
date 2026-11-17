"""Rendu des modèles (Jinja2 + Markdown simplifié) en DOCX et PDF."""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined

from . import formatage

TEMPLATES_DEFAUT = Path(__file__).resolve().parent.parent / "templates"
SAUT_DE_PAGE = "[[saut-de-page]]"
BLEU_NUIT = (0x0B, 0x1F, 0x3A)


# ---------------------------------------------------------------- Jinja ----
def environnement(dossier: Path | str = TEMPLATES_DEFAUT) -> Environment:
    env = Environment(loader=FileSystemLoader(str(dossier)), undefined=StrictUndefined,
                      trim_blocks=True, lstrip_blocks=True, keep_trailing_newline=True)
    env.filters.update(xpf=formatage.xpf, date_fr=formatage.date_fr, pct=formatage.pct,
                       ac=formatage.ou_a_completer,
                       initiale_min=lambda s: s[:1].lower() + s[1:] if s else s)
    return env


def rendre_texte(modele: str, contexte: dict, dossier: Path | str = TEMPLATES_DEFAUT) -> str:
    return environnement(dossier).get_template(modele).render(**contexte)


# ------------------------------------------------- Markdown simplifié ----
@dataclass
class Bloc:
    type: str              # h1 h2 h3 p ul table saut
    contenu: object = None


def analyser(texte: str) -> list[Bloc]:
    blocs: list[Bloc] = []
    para: list[str] = []

    def fin_para():
        if para:
            blocs.append(Bloc("p", " ".join(para)))
            para.clear()

    for brut in texte.splitlines():
        ligne = brut.strip()
        if not ligne:
            fin_para()
            continue
        if ligne == SAUT_DE_PAGE:
            fin_para(); blocs.append(Bloc("saut"))
        elif m := re.match(r"^(#{1,3})\s+(.*)$", ligne):
            fin_para(); blocs.append(Bloc(f"h{len(m.group(1))}", m.group(2)))
        elif ligne.startswith("- "):
            fin_para()
            if blocs and blocs[-1].type == "ul":
                blocs[-1].contenu.append(ligne[2:])
            else:
                blocs.append(Bloc("ul", [ligne[2:]]))
        elif ligne.startswith("|") and ligne.endswith("|"):
            fin_para()
            cellules = [c.strip() for c in ligne[1:-1].split("|")]
            if all(re.fullmatch(r":?-{3,}:?", c) for c in cellules):
                continue  # ligne de séparation
            if blocs and blocs[-1].type == "table":
                blocs[-1].contenu.append(cellules)
            else:
                blocs.append(Bloc("table", [cellules]))
        else:
            para.append(ligne)
    fin_para()
    return blocs


def segments(texte: str) -> list[tuple[str, bool]]:
    """Découpe '**gras** normal' en [(texte, gras), ...]."""
    parties = re.split(r"(\*\*.+?\*\*)", texte)
    return [(p[2:-2], True) if p.startswith("**") and p.endswith("**") else (p, False) for p in parties if p]


# ---------------------------------------------------------------- DOCX ----
def vers_docx(blocs: list[Bloc], chemin: Path, reference: str) -> Path:
    from docx import Document
    from docx.enum.text import WD_BREAK
    from docx.shared import Pt, RGBColor, Cm

    doc = Document()
    for s in doc.sections:
        s.left_margin = s.right_margin = Cm(2.2)
        s.top_margin = s.bottom_margin = Cm(2)
        pied = s.footer.paragraphs[0]
        pied.text = f"MGE Conseil · {reference}"
        pied.runs[0].font.size = Pt(8)
    normal = doc.styles["Normal"]
    normal.font.name = "Calibri"
    normal.font.size = Pt(10.5)
    for nom in ("Title", "Heading 1", "Heading 2", "Heading 3"):
        doc.styles[nom].font.color.rgb = RGBColor(*BLEU_NUIT)

    def remplir(par, texte):
        for t, gras in segments(texte):
            par.add_run(t).bold = gras

    for b in blocs:
        if b.type == "h1":
            doc.add_heading(b.contenu, level=0)
        elif b.type in ("h2", "h3"):
            doc.add_heading(b.contenu, level=int(b.type[1]) - 1)
        elif b.type == "p":
            remplir(doc.add_paragraph(), b.contenu)
        elif b.type == "ul":
            for item in b.contenu:
                remplir(doc.add_paragraph(style="List Bullet"), item)
        elif b.type == "table":
            ncol = max(len(r) for r in b.contenu)
            t = doc.add_table(rows=0, cols=ncol)
            t.style = "Table Grid"
            for i, ligne in enumerate(b.contenu):
                cells = t.add_row().cells
                for j in range(ncol):
                    p = cells[j].paragraphs[0]
                    remplir(p, ligne[j] if j < len(ligne) else "")
                    if i == 0:
                        for r in p.runs:
                            r.bold = True
            doc.add_paragraph()
        elif b.type == "saut":
            doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)
    chemin.parent.mkdir(parents=True, exist_ok=True)
    doc.save(chemin)
    return chemin


# ----------------------------------------------------------------- PDF ----
def vers_pdf(blocs: list[Bloc], chemin: Path, reference: str) -> Path:
    from xml.sax.saxutils import escape
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_JUSTIFY
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import cm
    from reportlab.platypus import (KeepTogether, ListFlowable, ListItem, PageBreak, Paragraph,
                                    SimpleDocTemplate, Spacer, Table, TableStyle)

    bleu = colors.Color(*(c / 255 for c in BLEU_NUIT))
    ss = getSampleStyleSheet()
    st = {
        "h1": ParagraphStyle("h1", parent=ss["Title"], textColor=bleu, fontSize=20, spaceAfter=10, alignment=0),
        "h2": ParagraphStyle("h2", parent=ss["Heading2"], textColor=bleu, fontSize=13, spaceBefore=12, spaceAfter=6, keepWithNext=1),
        "h3": ParagraphStyle("h3", parent=ss["Heading3"], textColor=bleu, fontSize=11, keepWithNext=1),
        "p": ParagraphStyle("p", parent=ss["BodyText"], fontSize=10, leading=14, alignment=TA_JUSTIFY, spaceAfter=6),
        "cell": ParagraphStyle("cell", parent=ss["BodyText"], fontSize=9.5, leading=12),
    }

    def html(texte):
        return "".join(f"<b>{escape(t)}</b>" if g else escape(t) for t, g in segments(texte))

    elements = []
    largeur = A4[0] - 4.4 * cm
    for b in blocs:
        if b.type in ("h1", "h2", "h3"):
            elements.append(Paragraph(html(b.contenu), st[b.type]))
        elif b.type == "p":
            elements.append(Paragraph(html(b.contenu), st["p"]))
        elif b.type == "ul":
            elements.append(ListFlowable([ListItem(Paragraph(html(i), st["p"]), leftIndent=12) for i in b.contenu],
                                         bulletType="bullet", start="•", leftIndent=12))
        elif b.type == "table":
            ncol = max(len(r) for r in b.contenu)
            data = [[Paragraph(html(r[j] if j < len(r) else ""), st["cell"]) for j in range(ncol)] for r in b.contenu]
            t = Table(data, colWidths=[largeur / ncol] * ncol, repeatRows=1)
            t.setStyle(TableStyle([
                ("GRID", (0, 0), (-1, -1), 0.5, colors.Color(0.8, 0.83, 0.88)),
                ("BACKGROUND", (0, 0), (-1, 0), colors.Color(0.93, 0.95, 0.97)),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]))
            elements += [KeepTogether(t), Spacer(1, 8)]
        elif b.type == "saut":
            elements.append(PageBreak())

    # Un titre reste toujours sur la même page que l'élément qui le suit.
    groupes, i = [], 0
    while i < len(elements):
        e = elements[i]
        if getattr(e, "style", None) in (st["h2"], st["h3"]) and i + 1 < len(elements):
            suivant = elements[i + 1]
            contenu = suivant._content if isinstance(suivant, KeepTogether) else [suivant]
            groupes.append(KeepTogether([e, *contenu]))
            i += 2
        else:
            groupes.append(e)
            i += 1
    elements = groupes

    def pied(canvas, doc_):
        canvas.saveState()
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.grey)
        canvas.drawString(2.2 * cm, 1.2 * cm, f"MGE Conseil · {reference}")
        canvas.drawRightString(A4[0] - 2.2 * cm, 1.2 * cm, f"Page {doc_.page}")
        canvas.restoreState()

    chemin.parent.mkdir(parents=True, exist_ok=True)
    SimpleDocTemplate(str(chemin), pagesize=A4, leftMargin=2.2 * cm, rightMargin=2.2 * cm,
                      topMargin=2 * cm, bottomMargin=2 * cm, title=reference,
                      author="MGE Conseil").build(elements, onFirstPage=pied, onLaterPages=pied)
    return chemin
