"""Test central : pour chaque semaine, la somme des flux égale la variation du solde."""
import random
from datetime import date, timedelta

import pytest

from tresorerie.delais import delais_clients
from tresorerie.imports import Charge, Facture
from tresorerie.prevision import Parametres, prevoir


def verifier(prev):
    for pr in prev.values():
        p = pr.parametres
        assert pr.semaines[0].solde_debut == p.solde_initial
        assert len(pr.semaines) == p.nb_semaines
        for i, s in enumerate(pr.semaines):
            flux = pr.flux_semaine(s.numero)
            assert sum(f.montant for f in flux) == s.solde_fin - s.solde_debut, (pr.titre, s.numero)
            assert s.encaissements - s.decaissements == s.variation
            assert s.encaissements == sum(f.montant for f in flux if f.montant > 0)
            assert s.decaissements == -sum(f.montant for f in flux if f.montant < 0)
            assert s.encaissements >= 0 and s.decaissements >= 0
            if i:
                assert s.solde_debut == pr.semaines[i - 1].solde_fin
            assert s.fin - s.debut == timedelta(days=6) and s.debut.weekday() == 0
        # Chaque flux de l'horizon est compté dans une et une seule semaine
        assert sum(len(pr.flux_semaine(s.numero)) for s in pr.semaines) == len(pr.flux)
        assert pr.semaines[-1].solde_fin == p.solde_initial + sum(f.montant for f in pr.flux)
        assert all(f.date > p.date_fin for f in pr.hors_horizon)


def test_conservation_donnees_demo(demo):
    verifier(demo["prev"])


def test_valeurs_demo_recalculees_a_la_main(demo):
    """Semaine 1 du scénario de base, recalculée indépendamment à partir des fichiers."""
    s1 = demo["prev"]["base"].semaines[0]
    p = demo["params"]
    fin_s1 = p.date_debut + timedelta(days=6)
    fournisseurs = sum(f.montant_ttc for f in demo["fournisseurs"] if f.echeance <= fin_s1)   # échues -> S1
    assert fournisseurs == 1_350_000
    divers = s1.decaissements - fournisseurs
    assert divers == 47_715            # moyenne hebdo des catégories extrapolées
    assert s1.solde_fin == 9_500_000 - 1_397_715 == 8_102_285


@pytest.mark.parametrize("graine", range(60))
def test_conservation_donnees_aleatoires(graine):
    rnd = random.Random(graine)
    debut = date(2027, 1, 4) + timedelta(days=rnd.randrange(0, 300))
    clients = [f"C{i}" for i in range(rnd.randint(0, 6))]
    factures = []
    for _ in range(rnd.randint(0, 60)):
        if not clients:
            break
        ech = debut + timedelta(days=rnd.randint(-200, 150))
        paye = ech + timedelta(days=rnd.randint(-10, 90)) if rnd.random() < 0.5 else None
        factures.append(Facture(rnd.choice(clients), rnd.randint(1, 5_000_000), ech, date_paiement=paye))
    fournisseurs = [Facture(f"F{rnd.randint(1, 4)}", rnd.randint(1, 3_000_000), debut + timedelta(days=rnd.randint(-60, 120)))
                    for _ in range(rnd.randint(0, 30))]
    freqs = ["hebdomadaire", "mensuelle", "trimestrielle", "semestrielle", "annuelle", "ponctuelle"]
    charges = [Charge(f"Ch{i}", f"Cat{i}", rnd.randint(1, 4_000_000), rnd.choice(freqs),
                      debut + timedelta(days=rnd.randint(-40, 100)),
                      debut + timedelta(days=rnd.randint(0, 120)) if rnd.random() < 0.3 else None,
                      rnd.choice(["decaissement", "encaissement"])) for i in range(rnd.randint(0, 10))]
    p = Parametres(debut, rnd.randint(-5_000_000, 20_000_000), rnd.randint(-1_000_000, 5_000_000),
                   nb_semaines=rnd.choice([13, 13, 4, 26]), retard_scenario_jours=rnd.choice([30, 15, 60]))
    verifier(prevoir(factures, fournisseurs, charges, delais_clients(factures), p))
