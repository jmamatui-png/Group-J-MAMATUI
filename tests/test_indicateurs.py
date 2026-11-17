from datetime import date

import pytest

from tdb.donnees import Facture, Mouvement, Paiement, Saisie
from tdb.indicateurs import GROUPE, Donnees, fin_de_mois, liste_mois, lundi_chiffres, lundi_mouvements

ENTITES = {"terrawaves": {"nom": "Terrawaves Logistics", "noms_tiers": ["Terrawaves"]},
           "mge": {"nom": "MGE Conseil", "noms_tiers": ["MGE"]},
           "holding": {"nom": "GROUP J MAMATUI", "noms_tiers": []}}


def F(entite, ref, tiers, d, ht, ech=None, ttc=None):
    return Facture(entite, ref, tiers, d, ech or d, ht, ttc if ttc is not None else round(ht * 1.11))


def jeu(saisie=None, factures=None, paiements=(), banque=(), soldes=None):
    factures = factures if factures is not None else [
        F("terrawaves", "TW1", "Client A", date(2026, 10, 5), 1_000_000),
        F("terrawaves", "TW2", "Client B", date(2026, 10, 20), 250_000),
        F("mge", "MG1", "Terrawaves Logistics", date(2026, 10, 1), 150_000),   # intragroupe
        F("mge", "MG2", "PME X", date(2026, 10, 15), 300_000),
        F("holding", "HD1", "terrawaves", date(2026, 10, 3), 100_000),          # intragroupe (casse / accents ignorés)
    ]
    return Donnees(factures, list(paiements), list(banque), saisie or Saisie(), ENTITES, soldes or {}, 30)


def test_outils_dates():
    assert fin_de_mois("2026-02") == date(2026, 2, 28) and fin_de_mois("2028-02") == date(2028, 2, 29)
    assert liste_mois("2025-11", "2026-02") == ["2025-11", "2025-12", "2026-01", "2026-02"]


def test_ca_par_entite_et_consolide_sans_intragroupe():
    d = jeu()
    assert d.ca_ht_mois("terrawaves", "2026-10") == 1_250_000
    assert d.ca_ht_mois("mge", "2026-10") == 450_000
    assert d.ca_ht_mois("holding", "2026-10") == 100_000
    assert d.ca_intragroupe_mois("2026-10") == 250_000
    assert d.ca_ht_mois(GROUPE, "2026-10") == 1_250_000 + 450_000 + 100_000 - 250_000 == 1_550_000


def test_facture_a_soi_meme_pas_intragroupe():
    d = jeu(factures=[F("terrawaves", "X", "Terrawaves", date(2026, 10, 1), 10)])
    assert not d.est_intragroupe(d.factures[0])


def test_marge_charges_resultat_et_reconciliation_intragroupe():
    s = Saisie({("2026-10", "terrawaves"): {"couts_directs": 100_000, "sous_traitance": 200_000, "carburant": 50_000,
                                            "charges_fixes": 600_000, "charges_fixes_intragroupe": 250_000},
                ("2026-10", "mge"): {"couts_directs": 0, "charges_fixes": 200_000},
                ("2026-10", "holding"): {"couts_directs": 0, "charges_fixes": 10_000}})
    d = jeu(saisie=s)
    tw = d.indicateurs_mois("terrawaves", "2026-10")
    assert tw["marge"] == 1_250_000 - 350_000 == 900_000
    assert tw["resultat"] == 900_000 - 600_000 == 300_000
    g = d.indicateurs_mois(GROUPE, "2026-10")
    resultat_somme = sum(d.indicateurs_mois(e, "2026-10")["resultat"] for e in ENTITES)
    # L'intragroupe est bien éliminé des deux côtés : le résultat consolidé = somme des résultats.
    assert g["ecart_intragroupe"] == 0
    assert g["resultat"] == resultat_somme == 300_000 + 250_000 + 90_000
    assert g["charges_fixes"] == 810_000 - 250_000
    assert g["ca_ht"] - g["marge"] == 350_000   # seuls les coûts directs externes restent


def test_ecart_intragroupe_signale():
    s = Saisie({(m, e): {"couts_directs": 0, "charges_fixes": 0} for m in ["2026-10"] for e in ENTITES})
    assert jeu(saisie=s).indicateurs_mois(GROUPE, "2026-10")["ecart_intragroupe"] == 250_000


def test_saisie_manquante_donne_none_et_non_zero():
    i = jeu().indicateurs_mois("terrawaves", "2026-10")
    assert i["marge"] is None and i["charges_fixes"] is None and i["resultat"] is None
    assert jeu().indicateurs_mois(GROUPE, "2026-10")["marge"] is None


def test_tresorerie_soldes_initiaux_et_dates():
    banque = [Mouvement("terrawaves", "C1", date(2026, 10, 1), 500), Mouvement("terrawaves", "C1", date(2026, 10, 31), -200),
              Mouvement("terrawaves", "C1", date(2026, 11, 1), 1_000), Mouvement("mge", "C2", date(2026, 9, 1), 50)]
    d = jeu(banque=banque, soldes={"terrawaves": {"C1": 10_000}, "mge": {"C2": 1}})
    assert d.tresorerie("terrawaves", date(2026, 10, 31)) == 10_300
    assert d.tresorerie("terrawaves", date(2026, 9, 30)) == 10_000
    assert d.tresorerie(GROUPE, date(2026, 10, 31)) == 10_300 + 51


def test_creances_plus_30_jours_paiements_partiels():
    f = F("terrawaves", "T", "Client A", date(2026, 8, 1), 100_000, ech=date(2026, 8, 31), ttc=111_000)
    p = [Paiement("terrawaves", "T", date(2026, 10, 10), 40_000), Paiement("terrawaves", "T", date(2026, 11, 5), 71_000)]
    d = jeu(factures=[f], paiements=p)
    assert d.creances_plus_30("terrawaves", date(2026, 9, 30)) == 0           # échue depuis 30 j : pas plus de 30
    assert d.creances_plus_30("terrawaves", date(2026, 10, 1)) == 111_000     # 31 jours
    assert d.creances_plus_30("terrawaves", date(2026, 10, 31)) == 71_000     # après acompte
    assert d.creances_plus_30("terrawaves", date(2026, 11, 30)) == 0          # soldée


def test_creances_groupe_hors_intragroupe_et_avoirs_ignores():
    fs = [F("mge", "M", "Terrawaves", date(2026, 1, 1), 10_000), F("mge", "A", "PME", date(2026, 1, 1), -5_000),
          F("mge", "E", "PME", date(2026, 1, 1), 20_000)]
    d = jeu(factures=fs)
    assert d.creances_plus_30("mge", date(2026, 6, 1)) == round(10_000 * 1.11) + round(20_000 * 1.11)
    assert d.creances_plus_30(GROUPE, date(2026, 6, 1)) == round(20_000 * 1.11)


def test_terrawaves_concentration_et_ratios():
    s = Saisie({("2026-10", "terrawaves"): {"heures_vendues": 600, "fourgons": 4, "carburant": 420_000, "km": 6_000,
                                            "sous_traitance": 250_000}})
    t = jeu(saisie=s).terrawaves_mois("2026-10", 0.75)
    assert t["premier_client"] == "Client A" and t["part_premier_client"] == pytest.approx(0.8)
    assert t["alerte_concentration"] is True
    assert t["heures_par_fourgon"] == 150 and t["carburant_par_km"] == 70
    assert t["sous_traitance_pct_ca"] == pytest.approx(0.2)
    assert jeu(saisie=s).terrawaves_mois("2026-10", 0.8)["alerte_concentration"] is False   # strictement au-dessus


def test_terrawaves_division_par_zero():
    s = Saisie({("2026-10", "terrawaves"): {"heures_vendues": 600, "fourgons": 0, "carburant": 1}})
    t = jeu(saisie=s).terrawaves_mois("2026-10", 0.75)
    assert t["heures_par_fourgon"] is None and t["carburant_par_km"] is None


def test_mge():
    s = Saisie({("2026-10", "mge"): {"mrr_signe": 450_000, "jours_factures": 7, "contacts": 10, "rendez_vous": 4, "diagnostics": 1}})
    m = jeu(saisie=s).mge_mois("2026-10", 10)
    assert m["taux_occupation"] == 0.7 and m["jours_disponibles"] == 10
    assert m["conversion_rdv"] == 0.4 and m["conversion_diagnostic"] == 0.25
    s.valeurs[("2026-10", "mge")]["jours_disponibles"] = 8
    assert jeu(saisie=s).mge_mois("2026-10", 10)["taux_occupation"] == 7 / 8


def test_personnel_provision():
    s = Saisie({("2026-11", "personnel"): {"prelevement_dirigeant": 333_333},
                ("2026-12", "personnel"): {"prelevement_dirigeant": 400_000},
                ("2027-01", "personnel"): {"prelevement_dirigeant": 100_000}})
    r = jeu(saisie=s).personnel(["2026-11", "2026-12", "2027-01"], 0.25)
    assert [x["provision"] for x in r] == [83_333, 100_000, 25_000]     # 83 333,25 -> 83 333
    assert r[1]["cumul_preleve"] == 733_333 and r[1]["cumul_provision"] == 183_333
    assert r[2]["cumul_preleve"] == 100_000                              # remise à zéro en janvier
    sans_taux = jeu(saisie=s).personnel(["2026-11"], None)
    assert sans_taux[0]["provision"] is None and sans_taux[0]["cumul_provision"] is None


def test_lundi():
    fs = [F("terrawaves", "A", "Client A", date(2026, 11, 10), 900_000, ech=date(2026, 11, 10)),
          F("terrawaves", "B", "Client B", date(2026, 11, 3), 100_000),
          F("terrawaves", "V", "Client C", date(2026, 9, 1), 50_000, ech=date(2026, 10, 10)),
          F("mge", "I", "Terrawaves", date(2026, 11, 12), 999_999)]                 # intragroupe : ignorée
    p = [Paiement("terrawaves", "B", date(2026, 11, 12), round(100_000 * 1.11))]
    b = [Mouvement("terrawaves", "C", date(2026, 11, 12), round(100_000 * 1.11))]
    d = jeu(factures=fs, paiements=p, banque=b, soldes={"terrawaves": {"C": 1_000_000}})
    ch = {c.cle: c for c in lundi_chiffres(d, date(2026, 11, 16), 0.75)}     # semaine du 9 au 15/11
    assert ch["tresorerie"].valeur == 1_111_000 and ch["tresorerie"].precedent == 1_000_000
    assert ch["tresorerie"].variation == 111_000
    assert ch["creances"].valeur == round(50_000 * 1.11) and ch["creances"].precedent == 0   # dépasse 30 j le 10/11
    assert ch["ca30"].valeur == 1_000_000 and ch["ca30"].precedent == 100_000
    assert ch["enc7"].valeur == 111_000 and ch["enc7"].precedent == 0
    assert ch["part"].valeur == pytest.approx(900_000 / 1_050_000) and ch["part"].alerte and ch["part"].detail == "Client A"
    mv = lundi_mouvements(d, date(2026, 11, 16))
    assert mv["periode"] == (date(2026, 11, 9), date(2026, 11, 15))
    assert [f.ref for f, _ in mv["nouvelles_creances_30"]] == ["V"]
    assert [f.ref for f in mv["factures"]] == ["A"]
    assert [p.ref_facture for p in mv["paiements"]] == ["B"]
