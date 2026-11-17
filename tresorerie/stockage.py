"""Un dossier local par client. Aucune donnée n'est envoyée à l'extérieur."""
from __future__ import annotations

import os
import re
import unicodedata
from dataclasses import asdict
from datetime import date
from pathlib import Path

import yaml

from . import imports
from .categorisation import REGLES_DEFAUT, charger_regles
from .prevision import Parametres
from .valeurs import date_fr

RACINE_DEFAUT = Path(__file__).resolve().parent.parent / "donnees_clients"
FICHIERS = {
    "banque": ("banque.csv", imports.lire_banque),
    "clients": ("factures_clients.csv", imports.lire_factures),
    "fournisseurs": ("factures_fournisseurs.csv", imports.lire_factures),
    "charges": ("charges.csv", imports.lire_charges),
}


def racine() -> Path:
    return Path(os.environ.get("TRESO_DATA_DIR", RACINE_DEFAUT))


def slug(nom: str) -> str:
    s = unicodedata.normalize("NFKD", nom).encode("ascii", "ignore").decode()
    s = re.sub(r"[^A-Za-z0-9]+", "-", s).strip("-").lower()
    if not s:
        raise ValueError("nom de client invalide")
    return s[:60]


def lister_clients() -> list[str]:
    r = racine()
    return sorted(d.name for d in r.iterdir() if d.is_dir()) if r.exists() else []


def dossier(client: str) -> Path:
    d = racine() / slug(client)
    if racine().resolve() not in d.resolve().parents:
        raise ValueError("chemin client invalide")
    return d


def creer_client(nom: str) -> str:
    d = dossier(nom)
    (d / "exports").mkdir(parents=True, exist_ok=True)
    if not (d / "regles.yaml").exists():
        sauver_regles(d.name, REGLES_DEFAUT)
    return d.name


def enregistrer_csv(client: str, type_: str, contenu: bytes) -> int:
    """Contrôle le fichier puis l'enregistre. Renvoie le nombre de lignes. Lève ErreurImport sinon."""
    nom, lecteur = FICHIERS[type_]
    lignes = lecteur(contenu, nom)
    (dossier(client) / nom).write_bytes(contenu)
    return len(lignes)


def charger(client: str) -> dict:
    d = dossier(client)
    data = {}
    for type_, (nom, lecteur) in FICHIERS.items():
        data[type_] = lecteur(d / nom, nom) if (d / nom).exists() else []
    data["regles_brutes"] = yaml.safe_load((d / "regles.yaml").read_text(encoding="utf-8")) if (d / "regles.yaml").exists() else REGLES_DEFAUT
    data["regles"] = charger_regles(data["regles_brutes"])
    return data


def sauver_regles(client: str, regles: list[dict]) -> None:
    charger_regles(regles)  # validation
    (dossier(client) / "regles.yaml").write_text(
        yaml.safe_dump(regles, allow_unicode=True, sort_keys=False), encoding="utf-8")


def charger_parametres(client: str) -> dict:
    f = dossier(client) / "parametres.yaml"
    return yaml.safe_load(f.read_text(encoding="utf-8")) or {} if f.exists() else {}


def sauver_parametres(client: str, p: Parametres) -> None:
    d = asdict(p)
    d["categories_divers"] = list(p.categories_divers)
    (dossier(client) / "parametres.yaml").write_text(yaml.safe_dump(d, allow_unicode=True, sort_keys=False), encoding="utf-8")


def parametres_depuis(d: dict, defaut_debut: date) -> Parametres:
    return Parametres(
        date_debut=date_fr(d["date_debut"]) if d.get("date_debut") else defaut_debut, solde_initial=int(d.get("solde_initial") or 0),
        seuil=int(d.get("seuil") or 0), nb_semaines=int(d.get("nb_semaines") or 13),
        retard_scenario_jours=int(d.get("retard_scenario_jours") or 30),
        seuil_douteux_jours=int(d.get("seuil_douteux_jours") or 90),
        categories_divers=tuple(d.get("categories_divers") or ()),
        semaines_historique=int(d.get("semaines_historique") or 13))
