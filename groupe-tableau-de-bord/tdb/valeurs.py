"""Lecture des montants (F CFP entiers) et des dates au format français."""
from __future__ import annotations

import calendar
import re
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

ESPACES = re.compile(r"[\s  ']")


def montant(valeur) -> int:
    """'-1 234 567', '12 500,00', '1.234.567', '1234567.4' -> entier XPF (arrondi au franc)."""
    if isinstance(valeur, bool):
        raise ValueError(f"montant invalide : {valeur!r}")
    if isinstance(valeur, int):
        return valeur
    s = ESPACES.sub("", str(valeur)).upper().replace("XPF", "").replace("CFP", "").replace("F", "")
    if not s:
        raise ValueError("montant vide")
    neg = s.startswith("(") and s.endswith(")")
    s = s.strip("()")
    if "," in s and "." in s:          # 1.234.567,50 ou 1,234,567.50
        s = s.replace(".", "").replace(",", ".") if s.rfind(",") > s.rfind(".") else s.replace(",", "")
    elif "," in s:
        s = s.replace(",", ".")
    elif s.count(".") > 1:              # 1.234.567
        s = s.replace(".", "")
    try:
        d = Decimal(s)
    except InvalidOperation:
        raise ValueError(f"montant invalide : {valeur!r}")
    if not d.is_finite():
        raise ValueError(f"montant invalide : {valeur!r}")
    r = int(d.quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    return -r if neg else r


def date_fr(valeur) -> date:
    """'31/01/2027', '31-01-2027', '31/01/27', '2027-01-31' -> date."""
    if isinstance(valeur, datetime):
        return valeur.date()
    if isinstance(valeur, date):
        return valeur
    s = str(valeur).strip()
    for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%d.%m.%Y", "%Y-%m-%d", "%d/%m/%y"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            pass
    raise ValueError(f"date invalide : {valeur!r} (attendu JJ/MM/AAAA)")


def lundi(d: date) -> date:
    return d - timedelta(days=d.weekday())


def ajouter_mois(d: date, mois: int) -> date:
    m = d.month - 1 + mois
    a, m = d.year + m // 12, m % 12 + 1
    return date(a, m, min(d.day, calendar.monthrange(a, m)[1]))


def xpf(n: int) -> str:
    return f"{n:,}".replace(",", " ") + " F"
