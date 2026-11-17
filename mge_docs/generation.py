"""Assemblage : fiche validée + configuration -> proposition et lettre de mission."""
from __future__ import annotations

import re
import unicodedata
from dataclasses import asdict
from datetime import date, timedelta
from pathlib import Path

from . import numerotation, rendu
from .calculs import Montants, calculer
from .fiche import Fiche
from .formatage import ajouter_mois

RACINE = Path(__file__).resolve().parent.parent
REGISTRE_DEFAUT = RACINE / "data" / "registre.json"
SORTIE_DEFAUT = RACINE / "sortie"
DOCUMENTS = {"proposition": "proposition.md.j2", "lettre-de-mission": "lettre_mission.md.j2"}
FORMATS = ("docx", "pdf")


def slug(texte: str) -> str:
    t = unicodedata.normalize("NFKD", texte).encode("ascii", "ignore").decode()
    return re.sub(r"[^A-Za-z0-9]+", "-", t).strip("-")[:50] or "client"


def date_fin(fiche: Fiche) -> date:
    if fiche.offre.mensuelle:
        return ajouter_mois(fiche.date_debut, fiche.duree) - timedelta(days=1)
    return fiche.date_debut + timedelta(weeks=fiche.duree)


def montants(fiche: Fiche, taux_tgc) -> Montants:
    return calculer(fiche.prix_ht, taux_tgc, fiche.duree if fiche.offre.mensuelle else 1)


def contexte(fiche: Fiche, config: dict, numero: str, taux_tgc=None, date_document: date | None = None) -> dict:
    conditions = dict(config["conditions"])
    taux = taux_tgc if taux_tgc is not None else conditions["taux_tgc"]
    client = {k: v for k, v in asdict(fiche).items() if k not in ("offre", "avertissements")}
    return {
        "client": client,
        "offre": fiche.offre,
        "mission": {"date_debut": fiche.date_debut, "duree": fiche.duree, "date_fin": date_fin(fiche)},
        "montants": montants(fiche, taux),
        "cabinet": config["cabinet"],
        "conditions": conditions,
        "numero": numero,
        "date_document": date_document or date.today(),
    }


def generer(fiche: Fiche, config: dict, *, formats=FORMATS, sortie: Path | str = SORTIE_DEFAUT,
            registre: Path | str = REGISTRE_DEFAUT, templates: Path | str = rendu.TEMPLATES_DEFAUT,
            taux_tgc=None, date_document: date | None = None, documents=tuple(DOCUMENTS)) -> dict:
    """Génère les documents. Renvoie {'numero': ..., 'fichiers': [Path, ...]}."""
    formats = tuple(formats)
    if not formats or any(f not in FORMATS for f in formats):
        raise ValueError(f"Formats acceptés : {', '.join(FORMATS)}")
    date_document = date_document or date.today()

    # 1. Rendu d'essai avec un numéro fictif : une erreur de modèle ou de calcul
    #    ne consomme pas de numéro dans le registre.
    for doc in documents:
        rendu.rendre_texte(DOCUMENTS[doc], contexte(fiche, config, "MGE-PROP-0000-000", taux_tgc, date_document), templates)

    # 2. Attribution définitive du numéro.
    numero = numerotation.attribuer_numero(registre, date_document.year, client=fiche.raison_sociale,
                                           offre=fiche.offre.nom, prix_ht=fiche.prix_ht)
    ctx = contexte(fiche, config, numero, taux_tgc, date_document)

    fichiers = []
    for doc in documents:
        blocs = rendu.analyser(rendu.rendre_texte(DOCUMENTS[doc], ctx, templates))
        base = Path(sortie) / f"{numero}_{doc}_{slug(fiche.raison_sociale)}"
        if "docx" in formats:
            fichiers.append(rendu.vers_docx(blocs, base.with_suffix(".docx"), numero))
        if "pdf" in formats:
            fichiers.append(rendu.vers_pdf(blocs, base.with_suffix(".pdf"), numero))
    return {"numero": numero, "fichiers": fichiers, "montants": ctx["montants"]}


def champs_cabinet_manquants(config: dict) -> list[str]:
    manquants = [f"cabinet.{k}" for k, v in config["cabinet"].items() if v in (None, "")]
    manquants += [f"conditions.{k}" for k, v in config["conditions"].items() if v in (None, "")]
    return manquants
