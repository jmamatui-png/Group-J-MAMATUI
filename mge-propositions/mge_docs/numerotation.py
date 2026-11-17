"""Numérotation automatique MGE-PROP-AAAA-NNN, remise à zéro chaque année.

Le registre (JSON) garde le dernier numéro de chaque année et l'historique des
numéros attribués. Un verrou de fichier empêche deux générations simultanées
d'obtenir le même numéro.
"""
from __future__ import annotations

import fcntl
import json
import os
import re
from contextlib import contextmanager
from datetime import date, datetime
from pathlib import Path

PREFIXE = "MGE-PROP"
FORMAT_RE = re.compile(r"^MGE-PROP-(\d{4})-(\d{3,})$")


def formater(annee: int, rang: int) -> str:
    if rang < 1:
        raise ValueError("Le rang doit être ≥ 1.")
    return f"{PREFIXE}-{annee:04d}-{rang:03d}"


@contextmanager
def _verrou(registre: Path):
    registre.parent.mkdir(parents=True, exist_ok=True)
    with open(registre.with_suffix(".lock"), "w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(lock, fcntl.LOCK_UN)


def _lire(registre: Path) -> dict:
    if not registre.exists():
        return {"compteurs": {}, "historique": []}
    return json.loads(registre.read_text(encoding="utf-8"))


def _ecrire(registre: Path, donnees: dict) -> None:
    tmp = registre.with_suffix(".tmp")
    tmp.write_text(json.dumps(donnees, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, registre)  # écriture atomique


def prochain_numero(registre: Path | str, annee: int | None = None) -> str:
    """Aperçu du prochain numéro, sans le réserver."""
    annee = annee or date.today().year
    return formater(annee, _lire(Path(registre))["compteurs"].get(str(annee), 0) + 1)


def attribuer_numero(registre: Path | str, annee: int | None = None, **infos) -> str:
    """Réserve et renvoie le prochain numéro de l'année."""
    registre = Path(registre)
    annee = annee or date.today().year
    with _verrou(registre):
        d = _lire(registre)
        rang = d["compteurs"].get(str(annee), 0) + 1
        d["compteurs"][str(annee)] = rang
        numero = formater(annee, rang)
        d["historique"].append({"numero": numero, "horodatage": datetime.now().isoformat(timespec="seconds"), **infos})
        _ecrire(registre, d)
    return numero
