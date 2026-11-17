"""Lecture du catalogue des offres et de la configuration du cabinet."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml

RACINE = Path(__file__).resolve().parent.parent
CATALOGUE_DEFAUT = RACINE / "config" / "offres.yaml"
CONFIG_DEFAUT = RACINE / "config" / "mge.yaml"


@dataclass(frozen=True)
class Offre:
    code: str
    nom: str
    type: str                      # "mensuel" | "forfait"
    description: str
    livrables: list[str] = field(default_factory=list)
    prix_ht: int | None = None     # prix fixe
    prix_ht_min: int | None = None # fourchette
    prix_ht_max: int | None = None
    jours_min: int | None = None
    jours_max: int | None = None

    @property
    def mensuelle(self) -> bool:
        return self.type == "mensuel"

    @property
    def a_fourchette(self) -> bool:
        return self.prix_ht is None

    @property
    def rythme(self) -> str:
        if self.jours_min is None:
            return ""
        j = str(self.jours_min) if self.jours_min == self.jours_max else f"{self.jours_min} à {self.jours_max}"
        return f"{j} jour{'s' if (self.jours_max or 0) > 1 else ''} d'intervention par mois"


def charger_catalogue(chemin: Path | str = CATALOGUE_DEFAUT) -> dict[str, Offre]:
    donnees = yaml.safe_load(Path(chemin).read_text(encoding="utf-8")) or {}
    offres: dict[str, Offre] = {}
    for code, o in donnees.items():
        if o.get("type") not in ("mensuel", "forfait"):
            raise ValueError(f"Offre {code} : type doit être « mensuel » ou « forfait ».")
        offre = Offre(code=code, nom=o["nom"], type=o["type"], description=o.get("description", ""),
                      livrables=list(o.get("livrables", [])), prix_ht=o.get("prix_ht"),
                      prix_ht_min=o.get("prix_ht_min"), prix_ht_max=o.get("prix_ht_max"),
                      jours_min=o.get("jours_min"), jours_max=o.get("jours_max"))
        if offre.a_fourchette and not (offre.prix_ht_min and offre.prix_ht_max
                                       and offre.prix_ht_min <= offre.prix_ht_max):
            raise ValueError(f"Offre {code} : indiquer prix_ht, ou prix_ht_min ≤ prix_ht_max.")
        offres[code] = offre
    return offres


def charger_config(chemin: Path | str = CONFIG_DEFAUT) -> dict:
    return yaml.safe_load(Path(chemin).read_text(encoding="utf-8"))
