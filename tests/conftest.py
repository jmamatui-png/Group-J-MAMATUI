import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from mge_docs.catalogue import charger_catalogue, charger_config  # noqa: E402


@pytest.fixture
def catalogue():
    return charger_catalogue()


@pytest.fixture
def config():
    return charger_config()


@pytest.fixture
def fiche_ok():
    return {
        "raison_sociale": "Société Fictive SARL", "ridet": "1234567.001", "dirigeant": "Jean Exemple",
        "secteur": "Commerce", "chiffre_affaires": 50_000_000, "enjeux": ["Trésorerie"],
        "offre": "daf-pilotage", "prix_ht": 250_000, "duree": 6, "date_debut": "2027-02-01",
    }
