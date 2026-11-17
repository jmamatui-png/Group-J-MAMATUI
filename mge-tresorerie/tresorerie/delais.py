"""Délai de paiement réel par client, calculé sur les factures soldées (avec date de paiement)."""
from __future__ import annotations

from dataclasses import dataclass

from .imports import Facture


@dataclass(frozen=True)
class DelaiClient:
    client: str
    nb_factures: int
    montant_total: int
    retard_moyen: int          # jours après échéance, moyenne pondérée par le montant (négatif = paie en avance)
    retard_max: int
    delai_moyen_emission: int | None   # jours entre émission et paiement, si dates d'émission connues


def _arrondi(x: float) -> int:
    return int(x + 0.5) if x >= 0 else -int(-x + 0.5)


def delais_clients(factures: list[Facture]) -> dict[str, DelaiClient]:
    par_client: dict[str, list[Facture]] = {}
    for f in factures:
        if f.date_paiement:
            par_client.setdefault(f.tiers, []).append(f)
    res = {}
    for client, fs in par_client.items():
        total = sum(f.montant_ttc for f in fs)
        retards = [(f.date_paiement - f.echeance).days for f in fs]
        pond = sum(r * f.montant_ttc for r, f in zip(retards, fs)) / total
        avec_em = [f for f in fs if f.date_emission]
        dem = (_arrondi(sum((f.date_paiement - f.date_emission).days * f.montant_ttc for f in avec_em)
                        / sum(f.montant_ttc for f in avec_em)) if avec_em else None)
        res[client] = DelaiClient(client, len(fs), total, _arrondi(pond), max(retards), dem)
    return res


def retard_global(delais: dict[str, DelaiClient]) -> int:
    """Retard moyen pondéré tous clients confondus : appliqué aux clients sans historique."""
    total = sum(d.montant_total for d in delais.values())
    if not total:
        return 0
    return _arrondi(sum(d.retard_moyen * d.montant_total for d in delais.values()) / total)
