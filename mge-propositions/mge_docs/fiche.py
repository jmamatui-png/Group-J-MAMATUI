"""Lecture et validation d'une fiche client."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

import yaml

from .catalogue import Offre

CHAMPS_OBLIGATOIRES = {
    "raison_sociale": "raison sociale",
    "ridet": "RIDET",
    "dirigeant": "dirigeant",
    "secteur": "secteur d'activité",
    "chiffre_affaires": "chiffre d'affaires",
    "enjeux": "enjeux",
    "offre": "offre choisie",
    "prix_ht": "prix HT",
    "duree": "durée",
    "date_debut": "date de début",
}
# RIDET : n° RID à 7 chiffres, éventuellement suivi du n° d'établissement à 3 chiffres.
RIDET_RE = re.compile(r"^\d{7}(?:[.\s-]?\d{3})?$")


class FicheInvalide(ValueError):
    def __init__(self, erreurs: list[str]):
        self.erreurs = erreurs
        super().__init__("Fiche client invalide :\n- " + "\n- ".join(erreurs))


@dataclass
class Fiche:
    raison_sociale: str
    ridet: str
    dirigeant: str
    secteur: str
    chiffre_affaires: int
    enjeux: list[str]
    offre: Offre
    prix_ht: int
    duree: int
    date_debut: date
    qualite_dirigeant: str = ""
    adresse: str = ""
    avertissements: list[str] = field(default_factory=list)


def _vide(v) -> bool:
    return v is None or (isinstance(v, str) and not v.strip()) or (isinstance(v, (list, dict)) and not v)


def _entier(v):
    if isinstance(v, bool):
        return None
    if isinstance(v, int):
        return v
    if isinstance(v, str) and re.fullmatch(r"\d[\d\s  ]*", v.strip()):
        return int(re.sub(r"\D", "", v))
    return None


def valider(donnees: dict, catalogue: dict[str, Offre], engagement_mois: int = 6) -> Fiche:
    """Valide une fiche. Lève FicheInvalide avec la liste complète des erreurs."""
    if not isinstance(donnees, dict):
        raise FicheInvalide(["La fiche doit être un dictionnaire YAML (clé: valeur)."])
    erreurs: list[str] = []
    avert: list[str] = []

    manquants = [lib for cle, lib in CHAMPS_OBLIGATOIRES.items() if _vide(donnees.get(cle))]
    erreurs += [f"Champ obligatoire manquant : {m}" for m in manquants]

    ridet = str(donnees.get("ridet") or "").strip()
    if ridet and not RIDET_RE.match(ridet):
        erreurs.append(f"RIDET invalide : {ridet!r} (attendu : 7 chiffres, ex. 1234567 ou 1234567.001)")

    ca = donnees.get("chiffre_affaires")
    ca_i = _entier(ca) if not _vide(ca) else None
    if not _vide(ca) and (ca_i is None or ca_i < 0):
        erreurs.append("Chiffre d'affaires invalide : entier positif en F CFP attendu.")

    enjeux = donnees.get("enjeux")
    if isinstance(enjeux, str):
        enjeux = [e.strip(" -•") for e in enjeux.splitlines() if e.strip(" -•")]
    if not _vide(enjeux) and not (isinstance(enjeux, list) and all(isinstance(e, str) and e.strip() for e in enjeux)):
        erreurs.append("Enjeux invalides : liste de textes attendue.")

    offre = None
    code = donnees.get("offre")
    if not _vide(code):
        offre = catalogue.get(str(code).strip())
        if offre is None:
            # Accepte aussi le nom affiché (« DAF Pilotage »).
            offre = next((o for o in catalogue.values() if o.nom.lower() == str(code).strip().lower()), None)
        if offre is None:
            erreurs.append(f"Offre inconnue : {code!r}. Offres disponibles : {', '.join(catalogue)}")

    prix = donnees.get("prix_ht")
    prix_i = _entier(prix) if not _vide(prix) else None
    if not _vide(prix) and (prix_i is None or prix_i <= 0):
        erreurs.append("Prix HT invalide : entier strictement positif en F CFP attendu.")
    elif prix_i and offre:
        if offre.a_fourchette:
            if not offre.prix_ht_min <= prix_i <= offre.prix_ht_max:
                erreurs.append(f"Prix HT {prix_i} hors fourchette de l'offre {offre.nom} "
                               f"({offre.prix_ht_min} à {offre.prix_ht_max}).")
        elif prix_i != offre.prix_ht:
            avert.append(f"Prix HT {prix_i} différent du tarif catalogue ({offre.prix_ht}) pour {offre.nom}.")

    duree = donnees.get("duree")
    duree_i = _entier(duree) if not _vide(duree) else None
    if not _vide(duree) and (duree_i is None or duree_i < 1):
        erreurs.append("Durée invalide : entier ≥ 1 attendu (mois pour une offre mensuelle, semaines pour un forfait).")
    elif duree_i and offre and offre.mensuelle and duree_i < engagement_mois:
        erreurs.append(f"Durée de {duree_i} mois inférieure à l'engagement minimal de {engagement_mois} mois.")

    d = donnees.get("date_debut")
    if isinstance(d, str) and d.strip():
        try:
            d = date.fromisoformat(d.strip())
        except ValueError:
            erreurs.append(f"Date de début invalide : {d!r} (format attendu AAAA-MM-JJ).")
            d = None
    elif not _vide(d) and not isinstance(d, date):
        erreurs.append("Date de début invalide (format attendu AAAA-MM-JJ).")
        d = None

    if erreurs:
        raise FicheInvalide(erreurs)

    return Fiche(
        raison_sociale=str(donnees["raison_sociale"]).strip(), ridet=ridet,
        dirigeant=str(donnees["dirigeant"]).strip(), secteur=str(donnees["secteur"]).strip(),
        chiffre_affaires=ca_i, enjeux=[e.strip() for e in enjeux], offre=offre, prix_ht=prix_i,
        duree=duree_i, date_debut=d,
        qualite_dirigeant=str(donnees.get("qualite_dirigeant") or "").strip(),
        adresse=str(donnees.get("adresse") or "").strip(), avertissements=avert,
    )


def charger_fiche(chemin: Path | str, catalogue: dict[str, Offre], engagement_mois: int = 6) -> Fiche:
    try:
        donnees = yaml.safe_load(Path(chemin).read_text(encoding="utf-8"))
    except yaml.YAMLError as e:
        raise FicheInvalide([f"YAML illisible : {e}"])
    return valider(donnees, catalogue, engagement_mois)
