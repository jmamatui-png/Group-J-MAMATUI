"""Import et contrôle des fichiers CSV (séparateur ; ou , détecté, encodage UTF-8 ou Windows-1252)."""
from __future__ import annotations

import csv
import io
import unicodedata
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from .valeurs import date_fr, montant


class ErreurImport(ValueError):
    def __init__(self, fichier: str, erreurs: list[str]):
        self.fichier, self.erreurs = fichier, erreurs
        super().__init__(f"{fichier} : " + " ; ".join(erreurs[:10]) + (" …" if len(erreurs) > 10 else ""))


FREQUENCES = {"hebdomadaire": 0, "mensuelle": 1, "trimestrielle": 3, "semestrielle": 6, "annuelle": 12, "ponctuelle": None}


@dataclass(frozen=True)
class LigneBanque:
    date: date
    libelle: str
    montant: int            # + crédit, − débit
    solde: int | None = None


@dataclass(frozen=True)
class Facture:
    tiers: str
    montant_ttc: int        # toujours positif
    echeance: date
    numero: str = ""
    date_emission: date | None = None
    date_paiement: date | None = None   # renseignée = facture soldée (historique)

    @property
    def ouverte(self) -> bool:
        return self.date_paiement is None


@dataclass(frozen=True)
class Charge:
    libelle: str
    categorie: str
    montant: int            # positif
    frequence: str
    prochaine_echeance: date
    date_fin: date | None = None
    sens: str = "decaissement"   # ou "encaissement"


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower().strip()
    return s.replace(" ", "_").replace("-", "_")


ALIAS = {
    "date_operation": "date", "date_valeur": "date", "libelle_operation": "libelle", "intitule": "libelle",
    "client": "tiers", "fournisseur": "tiers", "montant_ttc": "montant", "date_echeance": "echeance",
    "numero_facture": "numero", "n_facture": "numero", "date_facture": "date_emission",
    "date_reglement": "date_paiement", "paye_le": "date_paiement",
}


def lire_lignes(source, nom: str) -> list[dict]:
    """Lit un CSV (chemin, octets ou texte) et renvoie des dictionnaires aux clés normalisées."""
    if isinstance(source, (str, Path)) and Path(source).exists():
        brut = Path(source).read_bytes()
    elif isinstance(source, bytes):
        brut = source
    else:
        brut = str(source).encode()
    try:
        texte = brut.decode("utf-8-sig")
    except UnicodeDecodeError:
        texte = brut.decode("cp1252")
    if not texte.strip():
        raise ErreurImport(nom, ["fichier vide"])
    entete = texte.splitlines()[0]
    sep = ";" if entete.count(";") >= entete.count(",") else ","
    lecteur = csv.DictReader(io.StringIO(texte), delimiter=sep)
    lecteur.fieldnames = [ALIAS.get(_norm(c), _norm(c)) for c in lecteur.fieldnames or []]
    return [{k: (v or "").strip() for k, v in ligne.items() if k} for ligne in lecteur
            if any((v or "").strip() for v in ligne.values() if isinstance(v, str))]


def _exiger(lignes, colonnes, nom):
    if not lignes:
        return
    manquantes = [c for c in colonnes if c not in lignes[0]]
    if manquantes:
        raise ErreurImport(nom, [f"colonne(s) manquante(s) : {', '.join(manquantes)}"])


def _boucle(lignes, nom, fabrique):
    resultat, erreurs = [], []
    for i, l in enumerate(lignes, start=2):    # ligne 1 = en-tête
        try:
            resultat.append(fabrique(l))
        except (ValueError, KeyError) as e:
            erreurs.append(f"ligne {i} : {e}")
    if erreurs:
        raise ErreurImport(nom, erreurs)
    return resultat


def lire_banque(source, nom="relevé bancaire") -> list[LigneBanque]:
    lignes = lire_lignes(source, nom)
    deux_colonnes = bool(lignes) and "montant" not in lignes[0] and {"debit", "credit"} <= set(lignes[0])
    _exiger(lignes, ["date", "libelle"] + ([] if deux_colonnes else ["montant"]), nom)

    def f(l):
        if deux_colonnes:   # export bancaire en colonnes Débit / Crédit
            m = (montant(l["credit"]) if l["credit"] else 0) - (abs(montant(l["debit"])) if l["debit"] else 0)
        else:
            m = montant(l["montant"])
        return LigneBanque(date_fr(l["date"]), l["libelle"], m,
                           montant(l["solde"]) if l.get("solde") else None)
    return sorted(_boucle(lignes, nom, f), key=lambda x: x.date)


def lire_factures(source, nom="factures") -> list[Facture]:
    lignes = lire_lignes(source, nom)
    _exiger(lignes, ["tiers", "montant", "echeance"], nom)

    def f(l):
        m = montant(l["montant"])
        if m <= 0:
            raise ValueError("le montant TTC doit être positif (saisir les avoirs à part)")
        if not l["tiers"]:
            raise ValueError("nom du tiers vide")
        return Facture(l["tiers"], m, date_fr(l["echeance"]), l.get("numero", ""),
                       date_fr(l["date_emission"]) if l.get("date_emission") else None,
                       date_fr(l["date_paiement"]) if l.get("date_paiement") else None)
    return _boucle(lignes, nom, f)


def lire_charges(source, nom="charges récurrentes") -> list[Charge]:
    lignes = lire_lignes(source, nom)
    _exiger(lignes, ["libelle", "montant", "frequence", "prochaine_echeance"], nom)

    def f(l):
        freq = _norm(l["frequence"]).replace("_", "")
        freq = {"mensuel": "mensuelle", "trimestriel": "trimestrielle", "annuel": "annuelle",
                "semestriel": "semestrielle", "unique": "ponctuelle"}.get(freq, freq)
        if freq not in FREQUENCES:
            raise ValueError(f"fréquence inconnue {l['frequence']!r} ({', '.join(FREQUENCES)})")
        m = montant(l["montant"])
        if m <= 0:
            raise ValueError("montant positif attendu (le sens est donné par la colonne « sens »)")
        sens = _norm(l.get("sens") or "decaissement")
        if sens not in ("decaissement", "encaissement"):
            raise ValueError("sens : « décaissement » ou « encaissement »")
        return Charge(l["libelle"], l.get("categorie") or l["libelle"], m, freq, date_fr(l["prochaine_echeance"]),
                      date_fr(l["date_fin"]) if l.get("date_fin") else None, sens)
    return _boucle(lignes, nom, f)
