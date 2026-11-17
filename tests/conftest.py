import sys
from datetime import date
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE))

from tresorerie import imports as im  # noqa: E402
from tresorerie.categorisation import REGLES_DEFAUT, charger_regles  # noqa: E402
from tresorerie.delais import delais_clients  # noqa: E402
from tresorerie.prevision import Parametres, prevoir  # noqa: E402

DEMO = RACINE / "exemples" / "demo"


@pytest.fixture(scope="session")
def demo():
    d = {"banque": im.lire_banque(DEMO / "banque.csv"), "clients": im.lire_factures(DEMO / "factures_clients.csv"),
         "fournisseurs": im.lire_factures(DEMO / "factures_fournisseurs.csv"), "charges": im.lire_charges(DEMO / "charges.csv"),
         "regles": charger_regles(REGLES_DEFAUT)}
    d["delais"] = delais_clients(d["clients"])
    d["params"] = Parametres(date(2026, 11, 23), 9_500_000, 2_000_000,
                             categories_divers=("Carburant", "Frais bancaires", "Énergie et eau"))
    d["prev"] = prevoir(d["clients"], d["fournisseurs"], d["charges"], d["delais"], d["params"], d["banque"], d["regles"])
    return d
