from datetime import date, timedelta

import pytest

from tresorerie.attention import points_attention
from tresorerie.categorisation import NON_CATEGORISE, REGLES_DEFAUT, charger_regles, categoriser
from tresorerie.delais import delais_clients, retard_global
from tresorerie.imports import Charge, Facture, LigneBanque
from tresorerie.prevision import (PERTE, RETARD, SRC_DIVERS, Parametres, construire, moyenne_divers, occurrences,
                                  premier_client, prevoir)

LUNDI = date(2027, 1, 4)


# --- Catégorisation ---------------------------------------------------------
def test_regles_par_defaut():
    r = charger_regles(REGLES_DEFAUT)
    assert categoriser("PRLV CAFAT COTISATIONS", -1, r) == "CAFAT"
    assert categoriser("Vir Salaires décembre", -1, r) == "Salaires"
    assert categoriser("VIR HOTEL FICTIF", 1000, r) == "Encaissements clients"
    assert categoriser("VIR HOTEL FICTIF", -1000, r) == "Fournisseurs"
    assert categoriser("Achat inconnu", -1, r) == NON_CATEGORISE
    assert categoriser("OPTION GARANTIE", -1, r) != "Télécom"       # motif « opt » limité au mot entier


def test_premiere_regle_et_accents_et_regex():
    r = charger_regles([{"motif": "énercal", "categorie": "Énergie"}, {"motif": "re:^cb\\s", "categorie": "Carte"},
                        {"motif": "enercal", "categorie": "Jamais"}])
    assert categoriser("PRLV ENERCAL", -1, r) == "Énergie"
    assert categoriser("CB STATION", -1, r) == "Carte"
    assert categoriser("ACHAT CB X", -1, r) == NON_CATEGORISE


@pytest.mark.parametrize("regle", [{"motif": "", "categorie": "X"}, {"motif": "x", "categorie": ""},
                                   {"motif": "x", "categorie": "X", "sens": "haut"}, {"motif": "re:(", "categorie": "X"}])
def test_regle_invalide_refusee(regle):
    with pytest.raises(ValueError):
        charger_regles([regle])


# --- Délais clients ---------------------------------------------------------
def test_retard_moyen_pondere():
    f = [Facture("A", 100_000, LUNDI, date_paiement=LUNDI + timedelta(days=10)),
         Facture("A", 300_000, LUNDI, date_paiement=LUNDI + timedelta(days=30)),
         Facture("B", 100_000, LUNDI, date_paiement=LUNDI - timedelta(days=2)),
         Facture("C", 999, LUNDI)]                                   # ouverte : ignorée
    d = delais_clients(f)
    assert d["A"].retard_moyen == 25          # (10×100 000 + 30×300 000) / 400 000
    assert d["A"].retard_max == 30 and d["A"].nb_factures == 2
    assert d["B"].retard_moyen == -2
    assert "C" not in d
    assert retard_global(d) == 20             # (25×400 000 − 2×100 000) / 500 000 = 19,6 -> 20


# --- Prévision --------------------------------------------------------------
def test_retard_client_applique_et_client_sans_historique():
    hist = [Facture("A", 100, LUNDI - timedelta(days=60), date_paiement=LUNDI - timedelta(days=46))]  # 14 j
    ouvertes = [Facture("A", 1_000, LUNDI + timedelta(days=1)), Facture("Z", 2_000, LUNDI + timedelta(days=1))]
    pr = prevoir(hist + ouvertes, [], [], delais_clients(hist), Parametres(LUNDI, 0))["base"]
    dates = {f.tiers: f.date for f in pr.flux}
    assert dates["A"] == LUNDI + timedelta(days=15)
    assert dates["Z"] == LUNDI + timedelta(days=15)     # sans historique : retard moyen global


def test_echus_reportes_en_semaine_1_et_douteux_exclus():
    clients = [Facture("A", 1_000, LUNDI - timedelta(days=20)), Facture("B", 5_000, LUNDI - timedelta(days=91))]
    fourn = [Facture("F", 700, LUNDI - timedelta(days=200))]
    pr = prevoir(clients, fourn, [], {}, Parametres(LUNDI, 0))["base"]
    assert pr.semaines[0].encaissements == 1_000 and pr.semaines[0].decaissements == 700
    assert all(f.reporte for f in pr.flux)
    assert [f.tiers for f, _ in pr.exclus] == ["B"]


def test_scenarios():
    clients = [Facture("Gros", 900, LUNDI + timedelta(days=2)), Facture("Petit", 100, LUNDI + timedelta(days=2)),
               Facture("Gros", 50, LUNDI - timedelta(days=100), date_paiement=LUNDI - timedelta(days=100))]
    prev = prevoir(clients, [], [], {}, Parametres(LUNDI, 0, retard_scenario_jours=30))
    assert premier_client(clients) == "Gros"
    assert prev["base"].semaines[0].encaissements == 1_000
    assert prev[RETARD].semaines[0].encaissements == 0
    assert prev[RETARD].semaines[4].encaissements == 1_000          # +30 jours -> semaine 5
    assert sum(s.encaissements for s in prev[PERTE].semaines) == 100
    assert "Gros" in prev[PERTE].titre


def test_hors_horizon():
    pr = prevoir([], [Facture("F", 10, LUNDI + timedelta(weeks=13))], [], {}, Parametres(LUNDI, 0))["base"]
    assert not pr.flux and len(pr.hors_horizon) == 1


def test_alerte_strictement_sous_le_seuil():
    p = Parametres(LUNDI, 1_000, seuil=500)
    sem, _, _ = construire([], p)
    assert not any(s.sous_seuil for s in sem)
    pr = prevoir([], [Facture("F", 500, LUNDI + timedelta(days=8))], [], {}, p)["base"]
    assert pr.semaines[1].solde_fin == 500 and not pr.semaines[1].sous_seuil
    pr = prevoir([], [Facture("F", 501, LUNDI + timedelta(days=8))], [], {}, p)["base"]
    assert [s.numero for s in pr.alertes] == list(range(2, 14))


def test_occurrences_charges():
    fin = LUNDI + timedelta(weeks=13, days=-1)
    m = Charge("Loyer", "Loyers", 1, "mensuelle", date(2027, 1, 31))
    assert occurrences(m, LUNDI, fin) == [date(2027, 1, 31), date(2027, 2, 28), date(2027, 3, 31)]
    h = Charge("V", "V", 1, "hebdomadaire", LUNDI)
    assert len(occurrences(h, LUNDI, fin)) == 13
    assert occurrences(Charge("P", "P", 1, "ponctuelle", LUNDI + timedelta(days=3)), LUNDI, fin) == [LUNDI + timedelta(days=3)]
    borne = Charge("Prêt", "E", 1, "mensuelle", date(2027, 1, 10), date_fin=date(2027, 2, 10))
    assert occurrences(borne, LUNDI, fin) == [date(2027, 1, 10), date(2027, 2, 10)]
    passe = Charge("T", "TGC", 1, "trimestrielle", date(2026, 11, 30))
    assert occurrences(passe, LUNDI, fin) == [date(2027, 2, 28)]


def test_moyenne_divers():
    banque = [LigneBanque(LUNDI - timedelta(weeks=k, days=-2), "CB STATION", -10_000) for k in range(1, 5)]
    banque.sort(key=lambda l: l.date)
    regles = charger_regles(REGLES_DEFAUT)
    p = Parametres(LUNDI, 0, categories_divers=("Carburant",), semaines_historique=4)
    assert moyenne_divers(banque, regles, p) == 10_000
    pr = prevoir([], [], [], {}, p, banque, regles)["base"]
    assert sum(1 for f in pr.flux if f.source == SRC_DIVERS) == 13
    assert pr.semaines[-1].solde_fin == -130_000


# --- Points d'attention -----------------------------------------------------
def test_toujours_cinq_points(demo):
    assert len(points_attention(demo["prev"], demo["clients"], demo["delais"])) == 5
    vide = prevoir([], [], [], {}, Parametres(LUNDI, 0))
    pts = points_attention(vide, [], {})
    assert len(pts) == 5 and "Aucune facture client" in pts[2].texte
