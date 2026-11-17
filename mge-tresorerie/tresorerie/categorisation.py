"""Catégorisation des lignes bancaires par règles modifiables (fichier regles.yaml du client).

Une règle = un motif (texte contenu dans le libellé, sans tenir compte des majuscules ni
des accents, ou expression régulière préfixée par « re: »), un sens facultatif
(credit / debit) et une catégorie. La première règle qui correspond s'applique.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

NON_CATEGORISE = "Non catégorisé"

REGLES_DEFAUT = [
    {"motif": "salaire", "categorie": "Salaires", "sens": "debit"},
    {"motif": "paie", "categorie": "Salaires", "sens": "debit"},
    {"motif": "cafat", "categorie": "CAFAT", "sens": "debit"},
    {"motif": "ruamm", "categorie": "CAFAT", "sens": "debit"},
    {"motif": "tgc", "categorie": "TGC", "sens": "debit"},
    {"motif": "dsf", "categorie": "Impôts et taxes", "sens": "debit"},
    {"motif": "loyer", "categorie": "Loyers", "sens": "debit"},
    {"motif": "echeance pret", "categorie": "Emprunts", "sens": "debit"},
    {"motif": "re:\\bpret\\b", "categorie": "Emprunts", "sens": "debit"},
    {"motif": "enercal", "categorie": "Énergie et eau", "sens": "debit"},
    {"motif": "re:\\beec\\b", "categorie": "Énergie et eau", "sens": "debit"},
    {"motif": "calédonienne des eaux", "categorie": "Énergie et eau", "sens": "debit"},
    {"motif": "re:\\bopt\\b", "categorie": "Télécom", "sens": "debit"},
    {"motif": "frais", "categorie": "Frais bancaires", "sens": "debit"},
    {"motif": "commission", "categorie": "Frais bancaires", "sens": "debit"},
    {"motif": "cotisation carte", "categorie": "Frais bancaires", "sens": "debit"},
    {"motif": "carburant", "categorie": "Carburant", "sens": "debit"},
    {"motif": "station", "categorie": "Carburant", "sens": "debit"},
    {"motif": "vir", "categorie": "Encaissements clients", "sens": "credit"},
    {"motif": "remise cheque", "categorie": "Encaissements clients", "sens": "credit"},
    {"motif": "tpe", "categorie": "Encaissements clients", "sens": "credit"},
    {"motif": "prlv", "categorie": "Fournisseurs", "sens": "debit"},
    {"motif": "vir", "categorie": "Fournisseurs", "sens": "debit"},
]


def normaliser(s: str) -> str:
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()


@dataclass(frozen=True)
class Regle:
    motif: str
    categorie: str
    sens: str | None = None   # "credit", "debit" ou None

    def correspond(self, libelle: str, montant: int) -> bool:
        if self.sens == "credit" and montant <= 0 or self.sens == "debit" and montant >= 0:
            return False
        if self.motif.startswith("re:"):
            return re.search(self.motif[3:], normaliser(libelle)) is not None
        return normaliser(self.motif) in normaliser(libelle)


def charger_regles(donnees: list[dict]) -> list[Regle]:
    regles, erreurs = [], []
    for i, d in enumerate(donnees or [], 1):
        try:
            sens = d.get("sens") or None
            if sens not in (None, "credit", "debit"):
                raise ValueError("sens doit être credit, debit ou vide")
            if not d.get("motif") or not d.get("categorie"):
                raise ValueError("motif et categorie obligatoires")
            r = Regle(str(d["motif"]), str(d["categorie"]), sens)
            if r.motif.startswith("re:"):
                re.compile(r.motif[3:])
            regles.append(r)
        except (ValueError, re.error, AttributeError) as e:
            erreurs.append(f"règle {i} : {e}")
    if erreurs:
        raise ValueError(" ; ".join(erreurs))
    return regles


def categoriser(libelle: str, montant: int, regles: list[Regle]) -> str:
    return next((r.categorie for r in regles if r.correspond(libelle, montant)), NON_CATEGORISE)
