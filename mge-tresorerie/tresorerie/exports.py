"""Exports : PDF dirigeant (2 pages) et classeur XLSX détaillé."""
from __future__ import annotations

import io
from datetime import date
from pathlib import Path

from .attention import Point
from .categorisation import categoriser
from .delais import DelaiClient
from .prevision import BASE, PERTE, RETARD, SRC_CHARGES, SRC_CLIENTS, SRC_DIVERS, SRC_FOURN, Prevision
from .valeurs import xpf

BLEU_NUIT = "#0b1f3a"
COULEURS = {BASE: BLEU_NUIT, RETARD: "#c9a227", PERTE: "#b23b3b"}


def _milliers(x, _=None) -> str:
    return f"{int(x):,}".replace(",", " ")


def graphique(prev: dict[str, Prevision], largeur=9.0, hauteur=4.2):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.ticker import FuncFormatter

    fig, ax = plt.subplots(figsize=(largeur, hauteur), dpi=150)
    base = prev[BASE]
    x = [s.numero for s in base.semaines]
    for sc, pr in prev.items():
        y = [s.solde_fin for s in pr.semaines]
        ax.plot(x, y, marker="o", markersize=3.5, linewidth=2.2 if sc == BASE else 1.6,
                color=COULEURS[sc], label=pr.titre, linestyle="-" if sc == BASE else "--")
        alertes = [(s.numero, s.solde_fin) for s in pr.semaines if s.sous_seuil]
        if alertes:
            ax.scatter(*zip(*alertes), color="#d62828", zorder=5, s=22)
    ax.axhline(base.parametres.seuil, color="#d62828", linewidth=1, linestyle=":", label=f"Seuil ({xpf(base.parametres.seuil)})")
    ax.axhline(0, color="#999", linewidth=0.6)
    ax.set_xticks(x, [f"S{n}\n{s.debut:%d/%m}" for n, s in zip(x, base.semaines)], fontsize=7)
    ax.yaxis.set_major_formatter(FuncFormatter(_milliers))
    ax.tick_params(axis="y", labelsize=7)
    ax.set_ylabel("Solde fin de semaine (F CFP)", fontsize=8)
    ax.grid(axis="y", alpha=0.25)
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(fontsize=7, frameon=False, loc="best")
    fig.tight_layout()
    return fig


def png(prev, **kw) -> bytes:
    import matplotlib.pyplot as plt
    fig = graphique(prev, **kw)
    buf = io.BytesIO()
    fig.savefig(buf, format="png")
    plt.close(fig)
    return buf.getvalue()


# ------------------------------------------------------------------ PDF ----
def pdf_dirigeant(prev: dict[str, Prevision], points: list[Point], client: str, chemin: Path | str,
                  date_edition: date | None = None) -> Path:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import cm
    from reportlab.platypus import Image, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
    from xml.sax.saxutils import escape as e

    if len(points) != 5:
        raise ValueError("Le rapport dirigeant attend exactement 5 points d'attention.")
    date_edition = date_edition or date.today()
    base = prev[BASE]
    p = base.parametres
    bleu = colors.HexColor(BLEU_NUIT)
    ss = getSampleStyleSheet()
    h1 = ParagraphStyle("h1", parent=ss["Title"], fontSize=17, textColor=bleu, alignment=0, spaceAfter=2)
    sous = ParagraphStyle("s", parent=ss["Normal"], fontSize=9, textColor=colors.grey, spaceAfter=10)
    h2 = ParagraphStyle("h2", parent=ss["Heading2"], fontSize=12, textColor=bleu, spaceBefore=8, spaceAfter=6)
    corps = ParagraphStyle("c", parent=ss["Normal"], fontSize=9.5, leading=13)
    petit = ParagraphStyle("p", parent=ss["Normal"], fontSize=7.5, leading=9, textColor=colors.grey)
    largeur = A4[0] - 3.6 * cm

    cell_entete = ParagraphStyle("ce", parent=ss["Normal"], fontSize=8, leading=9.5, textColor=colors.white,
                                 fontName="Helvetica-Bold")
    cell = ParagraphStyle("cl", parent=ss["Normal"], fontSize=8.5, leading=10)

    def tableau(data, cols, entete=True, aligne_droite_depuis=1):
        data = [[Paragraph(e(str(v)), cell_entete if (entete and i == 0) else cell) if (i == 0 or j == 0) else v
                 for j, v in enumerate(ligne)] for i, ligne in enumerate(data)]
        t = Table(data, colWidths=cols)
        st = [("FONTSIZE", (0, 0), (-1, -1), 8.5), ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#d5dbe3")),
              ("ALIGN", (aligne_droite_depuis, 0), (-1, -1), "RIGHT"), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
              ("TOPPADDING", (0, 0), (-1, -1), 2.5), ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5)]
        if entete:
            st += [("BACKGROUND", (0, 0), (-1, 0), bleu), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                   ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold")]
        t.setStyle(TableStyle(st))
        return t

    # Page 1 ---------------------------------------------------------------
    el = [Paragraph(f"Trésorerie à {p.nb_semaines} semaines — {e(client)}", h1),
          Paragraph(f"Du {p.date_debut:%d/%m/%Y} au {p.date_fin:%d/%m/%Y} · édité le {date_edition:%d/%m/%Y} · "
                    f"MGE Conseil · montants en F CFP", sous)]
    lignes = [["Scénario", "Solde initial", f"Solde fin S{p.nb_semaines}", "Point bas", "Semaine du point bas", "Semaines sous le seuil"]]
    for pr in prev.values():
        m = pr.solde_min
        lignes.append([pr.titre, xpf(p.solde_initial), xpf(pr.semaines[-1].solde_fin), xpf(m.solde_fin),
                       f"S{m.numero} ({m.debut:%d/%m})", str(len(pr.alertes))])
    t = tableau(lignes, [largeur * w for w in (0.27, 0.15, 0.15, 0.15, 0.15, 0.13)])
    for i, pr in enumerate(prev.values(), 1):
        if pr.alertes:
            t.setStyle(TableStyle([("TEXTCOLOR", (3, i), (3, i), colors.HexColor("#b00020"))]))
    el += [t, Spacer(1, 10)]
    img = png(prev, largeur=9.0, hauteur=4.6)
    el += [Image(io.BytesIO(img), width=largeur, height=largeur * 4.6 / 9.0)]
    if base.alertes:
        a = base.alertes[0]
        el.append(Paragraph(f"<font color='#b00020'><b>Alerte :</b></font> dans le scénario de base, le solde passe sous le "
                            f"seuil de {xpf(p.seuil)} dès la semaine {a.numero} (du {a.debut:%d/%m}).", corps))
    el.append(Spacer(1, 6))
    el.append(Paragraph("Hypothèses : encaissements clients prévus à l'échéance décalée du retard moyen constaté pour chaque "
                        "client ; fournisseurs payés à l'échéance ; charges récurrentes selon leur calendrier ; dettes et "
                        f"créances échues ramenées en semaine 1 ; créances échues depuis plus de {p.seuil_douteux_jours} jours "
                        "exclues. Prévision établie à partir des données transmises par l'entreprise, non auditées.", petit))
    el.append(PageBreak())

    # Page 2 ---------------------------------------------------------------
    el.append(Paragraph("5 points d'attention", h1))
    el.append(Spacer(1, 4))
    pastille = {"alerte": "#b00020", "vigilance": "#a8861c", "info": BLEU_NUIT}
    for i, pt in enumerate(points, 1):
        el.append(Paragraph(f"<font color='{pastille[pt.niveau]}'><b>{i}. {e(pt.titre)}</b></font>", corps))
        el.append(Paragraph(e(pt.texte), corps))
        el.append(Spacer(1, 5))
    el.append(Paragraph("Détail hebdomadaire — scénario de base", h2))
    data = [["Sem.", "Du", "Solde début", "Encaissements", "Décaissements", "Solde fin"]]
    for s in base.semaines:
        data.append([f"S{s.numero}", f"{s.debut:%d/%m}", xpf(s.solde_debut), xpf(s.encaissements),
                     xpf(s.decaissements), xpf(s.solde_fin)])
    t = tableau(data, [largeur * w for w in (0.08, 0.1, 0.205, 0.205, 0.205, 0.205)], aligne_droite_depuis=2)
    for i, s in enumerate(base.semaines, 1):
        if s.sous_seuil:
            t.setStyle(TableStyle([("TEXTCOLOR", (5, i), (5, i), colors.HexColor("#b00020")),
                                   ("FONTNAME", (5, i), (5, i), "Helvetica-Bold")]))
    el.append(t)

    def pied(c, d):
        c.saveState()
        c.setFont("Helvetica", 7.5)
        c.setFillColor(colors.grey)
        c.drawString(1.8 * cm, 1.1 * cm, f"MGE Conseil · {client} · document confidentiel")
        c.drawRightString(A4[0] - 1.8 * cm, 1.1 * cm, f"Page {d.page}/2")
        c.restoreState()

    chemin = Path(chemin)
    chemin.parent.mkdir(parents=True, exist_ok=True)
    SimpleDocTemplate(str(chemin), pagesize=A4, leftMargin=1.8 * cm, rightMargin=1.8 * cm, topMargin=1.5 * cm,
                      bottomMargin=1.6 * cm, title=f"Trésorerie 13 semaines — {client}", author="MGE Conseil"
                      ).build(el, onFirstPage=pied, onLaterPages=pied)
    return chemin


# ----------------------------------------------------------------- XLSX ----
COLONNES_SOURCES = [("Encaissements clients", SRC_CLIENTS, 1), ("Autres encaissements", SRC_CHARGES, 1),
                    ("Fournisseurs", SRC_FOURN, -1), ("Charges récurrentes", SRC_CHARGES, -1),
                    ("Dépenses diverses", SRC_DIVERS, -1)]


def xlsx_detaille(prev: dict[str, Prevision], points: list[Point], client: str, chemin: Path | str,
                  banque=(), regles=(), delais: dict[str, DelaiClient] | None = None) -> Path:
    from openpyxl import Workbook
    from openpyxl.formatting.rule import CellIsRule
    from openpyxl.styles import Alignment, Font, PatternFill
    from openpyxl.utils import get_column_letter

    wb = Workbook()
    entete = PatternFill("solid", fgColor="0B1F3A")
    blanc = Font(bold=True, color="FFFFFF")
    rouge = PatternFill("solid", fgColor="F8D7DA")
    NB = '#,##0;[Red]-#,##0'

    def en_tete(ws, titres, ligne=1):
        for j, t in enumerate(titres, 1):
            c = ws.cell(ligne, j, t)
            c.fill, c.font = entete, blanc
            c.alignment = Alignment(wrap_text=True, vertical="center")
        ws.freeze_panes = ws.cell(ligne + 1, 1)

    def largeurs(ws, w):
        for j, x in enumerate(w, 1):
            ws.column_dimensions[get_column_letter(j)].width = x

    # Synthèse + 5 points
    ws = wb.active
    ws.title = "Synthèse"
    p = prev[BASE].parametres
    ws["A1"] = f"Trésorerie à {p.nb_semaines} semaines — {client}"
    ws["A1"].font = Font(bold=True, size=14, color="0B1F3A")
    ws["A2"] = f"Du {p.date_debut:%d/%m/%Y} au {p.date_fin:%d/%m/%Y} — montants en F CFP"
    en_tete(ws, ["Scénario", "Solde initial", "Solde fin", "Point bas", "Semaine du point bas", "Semaines sous le seuil"], 4)
    for i, pr in enumerate(prev.values(), 5):
        m = pr.solde_min
        for j, v in enumerate([pr.titre, p.solde_initial, pr.semaines[-1].solde_fin, m.solde_fin, m.numero, len(pr.alertes)], 1):
            ws.cell(i, j, v).number_format = NB
    ws.cell(9, 1, "Points d'attention").font = Font(bold=True, size=12, color="0B1F3A")
    for i, pt in enumerate(points, 10):
        ws.cell(i, 1, f"{i - 9}. {pt.titre}").font = Font(bold=True)
        ws.cell(i, 2, pt.texte).alignment = Alignment(wrap_text=True, vertical="top")
        ws.merge_cells(start_row=i, start_column=2, end_row=i, end_column=6)
        ws.row_dimensions[i].height = 48
    largeurs(ws, [34, 16, 16, 16, 16, 16])

    # Une feuille par scénario, avec formules de contrôle
    noms = {BASE: "Base", RETARD: "Retard clients", PERTE: "Perte 1er client"}
    for sc, pr in prev.items():
        ws = wb.create_sheet(noms[sc])
        ws["A1"] = pr.titre
        ws["A1"].font = Font(bold=True, size=12, color="0B1F3A")
        titres = ["Semaine", "Du", "Au", "Solde début"] + [c[0] for c in COLONNES_SOURCES] + \
                 ["Total encaissements", "Total décaissements", "Solde fin", "Contrôle (doit être 0)", "Sous le seuil"]
        en_tete(ws, titres, 3)
        for i, s in enumerate(pr.semaines, 4):
            fs = pr.flux_semaine(s.numero)
            par_col = [sum(abs(f.montant) for f in fs if f.source == src and (f.montant > 0) == (signe > 0))
                       for _, src, signe in COLONNES_SOURCES]
            ligne = [s.numero, s.debut, s.fin, s.solde_debut if i == 4 else f"=L{i - 1}", *par_col,
                     f"=E{i}+F{i}", f"=G{i}+H{i}+I{i}", f"=D{i}+J{i}-K{i}", None, "OUI" if s.sous_seuil else ""]
            for j, v in enumerate(ligne, 1):
                c = ws.cell(i, j, v)
                c.number_format = "DD/MM/YYYY" if j in (2, 3) else NB
            # Contrôle : solde fin calculé par Excel − solde fin calculé par l'application
            ws.cell(i, 13, f"=L{i}-{s.solde_fin}").number_format = NB
            if sum(par_col[:2]) != s.encaissements or sum(par_col[2:]) != s.decaissements:
                raise ArithmeticError(f"Ventilation incohérente en semaine {s.numero}")
        der = 3 + len(pr.semaines)
        ws.conditional_formatting.add(f"L4:L{der}", CellIsRule(operator="lessThan", formula=[str(p.seuil)], fill=rouge))
        ws.cell(der + 2, 1, f"Seuil d'alerte : {p.seuil}")
        largeurs(ws, [9, 11, 11] + [15] * 10)

    # Détail des flux
    ws = wb.create_sheet("Flux détaillés")
    en_tete(ws, ["Scénario", "Semaine", "Date prévue", "Date d'origine", "Reporté en S1", "Source", "Tiers / catégorie", "Libellé", "Montant"])
    r = 2
    for pr in prev.values():
        for f in sorted(pr.flux, key=lambda f: (f.date, f.source)):
            sem = (f.date - p.date_debut).days // 7 + 1
            for j, v in enumerate([pr.titre, sem, f.date, f.date_origine, "oui" if f.reporte else "", f.source,
                                   f.tiers, f.libelle, f.montant], 1):
                ws.cell(r, j, v).number_format = "DD/MM/YYYY" if j in (3, 4) else NB
            r += 1
    largeurs(ws, [30, 9, 12, 12, 10, 26, 24, 44, 14])

    # Exclus et hors horizon
    ws = wb.create_sheet("Exclus et hors période")
    en_tete(ws, ["Scénario", "Tiers", "Échéance / date", "Montant", "Motif"])
    r = 2
    for pr in prev.values():
        for f, motif in pr.exclus:
            for j, v in enumerate([pr.titre, f.tiers, f.echeance, f.montant_ttc, motif], 1):
                ws.cell(r, j, v).number_format = "DD/MM/YYYY" if j == 3 else NB
            r += 1
        for f in pr.hors_horizon:
            for j, v in enumerate([pr.titre, f.tiers, f.date, f.montant, "après la fin de la période"], 1):
                ws.cell(r, j, v).number_format = "DD/MM/YYYY" if j == 3 else NB
            r += 1
    largeurs(ws, [30, 26, 14, 14, 50])

    # Délais clients
    ws = wb.create_sheet("Délais clients")
    en_tete(ws, ["Client", "Factures soldées analysées", "Montant analysé", "Retard moyen pondéré (j)", "Retard max (j)", "Délai moyen depuis émission (j)"])
    for i, d in enumerate(sorted((delais or {}).values(), key=lambda d: -d.retard_moyen), 2):
        for j, v in enumerate([d.client, d.nb_factures, d.montant_total, d.retard_moyen, d.retard_max, d.delai_moyen_emission], 1):
            ws.cell(i, j, v).number_format = NB
    largeurs(ws, [30, 14, 16, 16, 12, 18])

    # Banque catégorisée
    ws = wb.create_sheet("Banque catégorisée")
    en_tete(ws, ["Date", "Libellé", "Montant", "Catégorie"])
    for i, l in enumerate(banque, 2):
        for j, v in enumerate([l.date, l.libelle, l.montant, categoriser(l.libelle, l.montant, list(regles))], 1):
            ws.cell(i, j, v).number_format = "DD/MM/YYYY" if j == 1 else NB
    ws.auto_filter.ref = f"A1:D{max(2, len(banque) + 1)}"
    largeurs(ws, [12, 50, 14, 26])

    # Paramètres
    ws = wb.create_sheet("Paramètres")
    for i, (k, v) in enumerate([("Date de départ (lundi)", p.date_debut), ("Solde initial", p.solde_initial),
                                ("Seuil d'alerte", p.seuil), ("Nombre de semaines", p.nb_semaines),
                                ("Retard du scénario (jours)", p.retard_scenario_jours),
                                ("Créances exclues au-delà de (jours échus)", p.seuil_douteux_jours),
                                ("Catégories extrapolées", ", ".join(p.categories_divers) or "aucune")], 1):
        ws.cell(i, 1, k).font = Font(bold=True)
        ws.cell(i, 2, v).number_format = "DD/MM/YYYY" if i == 1 else NB
    largeurs(ws, [40, 30])

    chemin = Path(chemin)
    chemin.parent.mkdir(parents=True, exist_ok=True)
    wb.save(chemin)
    return chemin
