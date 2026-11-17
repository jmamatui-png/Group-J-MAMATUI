"""Lecture des exports Dolibarr et de la saisie mensuelle."""
from __future__ import annotations

import csv
import io
import unicodedata
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

from .valeurs import date_fr, montant

STATUTS_EXCLUS = {"0", "brouillon", "draft", "3", "abandonnee", "abandonne", "abandoned"}
TYPES_AVOIR = {"2", "avoir", "facture avoir", "credit note"}


class ErreurDonnees(ValueError):
    pass


def norm(s: str) -> str:
    return unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().lower().strip()


@dataclass(frozen=True)
class Facture:
    entite: str
    ref: str
    tiers: str
    date: date
    echeance: date
    ht: int      # négatif pour un avoir
    ttc: int


@dataclass(frozen=True)
class Paiement:
    entite: str
    ref_facture: str
    date: date
    montant: int


@dataclass(frozen=True)
class Mouvement:
    entite: str
    compte: str
    date: date
    montant: int   # + crédit, − débit


def _lire_csv(source) -> list[dict]:
    brut = Path(source).read_bytes() if isinstance(source, (str, Path)) else source
    try:
        texte = brut.decode("utf-8-sig")
    except UnicodeDecodeError:
        texte = brut.decode("cp1252")
    lignes = texte.splitlines()
    if not lignes:
        return []
    sep = max([";", ",", "\t"], key=lignes[0].count)
    return list(csv.DictReader(io.StringIO(texte), delimiter=sep))


def _colonnes(lignes: list[dict], alias: dict[str, list[str]], obligatoires: list[str], nom: str) -> dict[str, str]:
    if not lignes:
        return {}
    dispo = {norm(c): c for c in lignes[0] if c}
    trouve = {}
    for champ, noms in alias.items():
        for n in noms:
            if norm(n) in dispo:
                trouve[champ] = dispo[norm(n)]
                break
    manquants = [c for c in obligatoires if c not in trouve]
    if manquants:
        raise ErreurDonnees(f"{nom} : colonne(s) introuvable(s) pour {', '.join(manquants)}. "
                            f"Colonnes du fichier : {', '.join(lignes[0])}. Complétez « colonnes » dans config.yaml.")
    return trouve


def _iter(lignes, nom, fabrique):
    res, err = [], []
    for i, l in enumerate(lignes, 2):
        try:
            r = fabrique(l)
            if r is not None:
                res.append(r)
        except (ValueError, KeyError) as e:
            err.append(f"ligne {i} : {e}")
    if err:
        raise ErreurDonnees(f"{nom} : " + " ; ".join(err[:8]) + (" …" if len(err) > 8 else ""))
    return res


def lire_factures(source, entite: str, alias: dict, nom="factures") -> list[Facture]:
    lignes = _lire_csv(source)
    c = _colonnes(lignes, alias, ["ref", "tiers", "date", "ht", "ttc"], nom)

    def f(l):
        if "statut" in c and norm(l[c["statut"]]) in STATUTS_EXCLUS:
            return None   # brouillons et factures abandonnées : hors CA
        ht, ttc = montant(l[c["ht"]]), montant(l[c["ttc"]])
        if "type" in c and norm(l[c["type"]]) in TYPES_AVOIR:
            ht, ttc = -abs(ht), -abs(ttc)
        d = date_fr(l[c["date"]].split(" ")[0])
        ech = date_fr(l[c["echeance"]].split(" ")[0]) if c.get("echeance") and l[c["echeance"]].strip() else d
        return Facture(entite, l[c["ref"]].strip(), l[c["tiers"]].strip(), d, ech, ht, ttc)

    factures = _iter(lignes, nom, f)
    # Un export « factures + lignes » répète la facture sur chaque ligne : on dédoublonne par référence.
    uniques = {}
    for fa in factures:
        uniques.setdefault(fa.ref, fa)
    return list(uniques.values())


def lire_paiements(source, entite: str, alias: dict, nom="paiements") -> list[Paiement]:
    lignes = _lire_csv(source)
    c = _colonnes(lignes, alias, ["ref_facture", "date", "montant"], nom)

    def f(l):
        if not l[c["date"]].strip():   # export « factures et règlements » : facture sans règlement
            return None
        return Paiement(entite, l[c["ref_facture"]].strip(), date_fr(l[c["date"]].split(" ")[0]), montant(l[c["montant"]]))
    return _iter(lignes, nom, f)


def lire_banque(source, entite: str, alias: dict, nom="banque") -> list[Mouvement]:
    lignes = _lire_csv(source)
    c = _colonnes(lignes, alias, ["date"], nom)
    if lignes and "montant" not in c and not {"debit", "credit"} <= set(c):
        raise ErreurDonnees(f"{nom} : colonne « Montant » ou colonnes « Débit » et « Crédit » introuvables. "
                            f"Colonnes du fichier : {', '.join(lignes[0])}.")

    def f(l):
        if "montant" in c:
            m = montant(l[c["montant"]])
        else:
            m = (montant(l[c["credit"]]) if l[c["credit"]].strip() else 0) - (abs(montant(l[c["debit"]])) if l[c["debit"]].strip() else 0)
        return Mouvement(entite, l[c["compte"]].strip() if "compte" in c else "principal", date_fr(l[c["date"]].split(" ")[0]), m)
    return _iter(lignes, nom, f)


# ------------------------------------------------------------ Saisie mensuelle ----
CHAMPS_SAISIE = {
    # champ : (libellé, entités concernées)
    "charges_fixes": ("Charges fixes HT", "toutes"),
    "charges_fixes_intragroupe": ("dont facturées par une autre entité du groupe", "toutes"),
    "couts_directs": ("Coûts directs / achats HT (hors sous-traitance et carburant)", "toutes"),
    "couts_directs_intragroupe": ("dont facturés par une autre entité du groupe", "toutes"),
    "sous_traitance": ("Sous-traitance HT", "terrawaves"),
    "carburant": ("Carburant HT", "terrawaves"),
    "km": ("Kilomètres parcourus", "terrawaves"),
    "heures_vendues": ("Heures vendues", "terrawaves"),
    "fourgons": ("Nombre de fourgons", "terrawaves"),
    "mrr_signe": ("Revenu mensuel récurrent signé HT", "mge"),
    "jours_factures": ("Jours facturés", "mge"),
    "jours_disponibles": ("Jours disponibles", "mge"),
    "contacts": ("Contacts (pipeline)", "mge"),
    "rendez_vous": ("Rendez-vous (pipeline)", "mge"),
    "diagnostics": ("Diagnostics vendus (pipeline)", "mge"),
    "prelevement_dirigeant": ("Montant prélevé par le dirigeant", "personnel"),
}
ENTITES_SAISIE = ["terrawaves", "mge", "holding", "personnel"]


@dataclass
class Saisie:
    valeurs: dict[tuple[str, str], dict[str, int]] = field(default_factory=dict)   # (mois AAAA-MM, entité) -> champs

    def get(self, mois: str, entite: str, champ: str) -> int | None:
        return self.valeurs.get((mois, entite), {}).get(champ)


def lire_saisie(source) -> Saisie:
    if isinstance(source, (str, Path)) and not Path(source).exists():
        return Saisie()
    lignes = _lire_csv(source)
    s, err = Saisie(), []
    for i, l in enumerate(lignes, 2):
        mois, ent = (l.get("mois") or "").strip(), norm(l.get("entite") or "")
        if not mois and not ent:
            continue
        if len(mois) != 7 or mois[4] != "-" or not (mois[:4] + mois[5:]).isdigit() or not 1 <= int(mois[5:]) <= 12:
            err.append(f"ligne {i} : mois {mois!r} invalide (format AAAA-MM)")
            continue
        if ent not in ENTITES_SAISIE:
            err.append(f"ligne {i} : entité {ent!r} inconnue ({', '.join(ENTITES_SAISIE)})")
            continue
        if (mois, ent) in s.valeurs:
            err.append(f"ligne {i} : doublon {mois} / {ent}")
            continue
        champs = {}
        for k in CHAMPS_SAISIE:
            v = (l.get(k) or "").strip()
            if v:
                try:
                    champs[k] = montant(v)
                except ValueError:
                    err.append(f"ligne {i} : {k} = {v!r} n'est pas un nombre")
                    continue
                if champs[k] < 0:
                    err.append(f"ligne {i} : {k} négatif")
        s.valeurs[(mois, ent)] = champs
    if err:
        raise ErreurDonnees("saisie mensuelle : " + " ; ".join(err[:8]))
    return s


def ecrire_saisie(saisie_lignes: list[dict], chemin: Path) -> None:
    colonnes = ["mois", "entite", *CHAMPS_SAISIE]
    with open(chemin, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=colonnes, delimiter=";", extrasaction="ignore")
        w.writeheader()
        for l in saisie_lignes:
            w.writerow({k: ("" if l.get(k) in (None, "") else l[k]) for k in colonnes})
