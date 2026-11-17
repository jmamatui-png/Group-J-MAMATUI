"""Calculs HT / TGC / TTC en F CFP (XPF, sans décimales)."""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation


def arrondi_xpf(montant: Decimal) -> int:
    """Arrondi au franc le plus proche, demi-franc arrondi au supérieur."""
    return int(montant.quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def taux_valide(taux) -> Decimal:
    """Convertit un taux de TGC en Decimal (en %) et le contrôle (0 à 100)."""
    try:
        t = Decimal(str(taux).replace(",", ".").strip())
    except (InvalidOperation, AttributeError):
        raise ValueError(f"Taux de TGC invalide : {taux!r}")
    if not t.is_finite() or t < 0 or t > 100:
        raise ValueError(f"Taux de TGC hors limites (0 à 100 %) : {taux!r}")
    return t


@dataclass(frozen=True)
class Montants:
    taux_tgc: Decimal       # en %
    nb_periodes: int        # nombre de mois (offre mensuelle) ou 1 (forfait)
    ht: int                 # par période
    tgc: int                # par période
    ttc: int                # par période
    total_ht: int
    total_tgc: int
    total_ttc: int


def calculer(prix_ht: int, taux_tgc, nb_periodes: int = 1) -> Montants:
    """Calcule HT, TGC et TTC par période et au total.

    La TGC est calculée et arrondie sur le montant d'une période (une facture),
    puis multipliée par le nombre de périodes : le total correspond ainsi
    exactement à la somme des factures émises.
    """
    if isinstance(prix_ht, bool) or not isinstance(prix_ht, int):
        raise ValueError("Le prix HT doit être un nombre entier de F CFP.")
    if prix_ht <= 0:
        raise ValueError("Le prix HT doit être strictement positif.")
    if isinstance(nb_periodes, bool) or not isinstance(nb_periodes, int) or nb_periodes < 1:
        raise ValueError("Le nombre de périodes doit être un entier ≥ 1.")
    taux = taux_valide(taux_tgc)
    tgc = arrondi_xpf(Decimal(prix_ht) * taux / Decimal(100))
    ttc = prix_ht + tgc
    m = Montants(taux, nb_periodes, prix_ht, tgc, ttc,
                 prix_ht * nb_periodes, tgc * nb_periodes, ttc * nb_periodes)
    # Contrôle de cohérence systématique.
    if m.ht + m.tgc != m.ttc or m.total_ht + m.total_tgc != m.total_ttc:
        raise ArithmeticError("Incohérence HT + TGC ≠ TTC")
    return m
