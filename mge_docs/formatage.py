"""Mise en forme française : montants XPF, dates, taux."""
from __future__ import annotations

from datetime import date
from decimal import Decimal

MOIS = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet",
        "août", "septembre", "octobre", "novembre", "décembre"]
NBSP = " "  # espace insécable (compatible PDF et Word)
A_COMPLETER = "[À compléter]"


def xpf(montant: int) -> str:
    """150000 -> '150 000 F CFP'."""
    signe = "-" if montant < 0 else ""
    chiffres = f"{abs(int(montant)):,}".replace(",", NBSP)
    return f"{signe}{chiffres}{NBSP}F{NBSP}CFP"


def date_fr(d: date) -> str:
    return f"{d.day}{'er' if d.day == 1 else ''} {MOIS[d.month - 1]} {d.year}"


def pct(taux: Decimal) -> str:
    """Decimal('11') -> '11 %', Decimal('5.5') -> '5,5 %'."""
    t = format(taux.normalize(), "f")
    return f"{t.replace('.', ',')}{NBSP}%"


def ou_a_completer(valeur) -> str:
    return str(valeur) if valeur not in (None, "") else A_COMPLETER


def ajouter_mois(d: date, mois: int) -> date:
    """Ajoute des mois en ramenant au dernier jour du mois si nécessaire (31/01 + 1 -> 28 ou 29/02)."""
    import calendar
    m = d.month - 1 + mois
    annee, mois_ = d.year + m // 12, m % 12 + 1
    return date(annee, mois_, min(d.day, calendar.monthrange(annee, mois_)[1]))
