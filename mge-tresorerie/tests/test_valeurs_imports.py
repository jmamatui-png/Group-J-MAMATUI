from datetime import date

import pytest

from tresorerie.imports import ErreurImport, lire_banque, lire_charges, lire_factures
from tresorerie.valeurs import ajouter_mois, date_fr, lundi, montant


@pytest.mark.parametrize("texte, attendu", [
    ("1 234 567", 1_234_567), ("-12 500", -12_500), ("12 500,00", 12_500), ("1.234.567", 1_234_567),
    ("1.234.567,50", 1_234_568), ("1,234,567.49", 1_234_567), ("150000 XPF", 150_000), ("150 000 F CFP", 150_000),
    ("(5 000)", -5_000), ("0,5", 1), ("-0,5", -1), ("1 000", 1_000), (42, 42),
])
def test_montant(texte, attendu):
    assert montant(texte) == attendu


@pytest.mark.parametrize("texte", ["", "abc", "1,2,3x", True])
def test_montant_invalide(texte):
    with pytest.raises(ValueError):
        montant(texte)


def test_dates():
    assert date_fr("31/01/2027") == date(2027, 1, 31) == date_fr("2027-01-31") == date_fr("31-01-2027")
    with pytest.raises(ValueError):
        date_fr("31/02/2027")
    assert lundi(date(2026, 11, 22)) == date(2026, 11, 16)
    assert ajouter_mois(date(2027, 1, 31), 1) == date(2027, 2, 28)
    assert ajouter_mois(date(2027, 12, 31), 2) == date(2028, 2, 29)


def test_banque_point_virgule_et_tri():
    b = lire_banque("Date;Libellé;Montant\n05/01/2027;VIR X;1 000\n03/01/2027;PRLV Y;-500,00\n".encode("cp1252"))
    assert [(l.date.day, l.montant) for l in b] == [(3, -500), (5, 1000)]


def test_banque_colonnes_debit_credit():
    b = lire_banque(b"date,libelle,debit,credit\n03/01/2027,PRLV,500,\n04/01/2027,VIR,,1200\n")
    assert [l.montant for l in b] == [-500, 1200]


def test_erreurs_avec_numero_de_ligne():
    with pytest.raises(ErreurImport) as e:
        lire_banque(b"date;libelle;montant\n03/01/2027;A;10\n99/99/2027;B;10\n03/01/2027;C;abc\n")
    assert e.value.erreurs[0].startswith("ligne 3") and e.value.erreurs[1].startswith("ligne 4")


def test_colonne_manquante():
    with pytest.raises(ErreurImport, match="colonne"):
        lire_factures(b"client;montant_ttc\nA;100\n")


def test_facture_montant_negatif_refuse():
    with pytest.raises(ErreurImport, match="positif"):
        lire_factures(b"client;montant_ttc;echeance\nA;-100;01/02/2027\n")


def test_factures_alias_et_historique():
    f = lire_factures(b"Client;Montant TTC;Date echeance;Date paiement\nA;100;01/02/2027;15/02/2027\nB;50;01/03/2027;\n")
    assert f[0].tiers == "A" and not f[0].ouverte and f[1].ouverte


def test_charges():
    c = lire_charges("libelle;montant;frequence;prochaine_echeance;sens\nLoyer;450 000;Mensuel;05/01/2027;\n"
                     "Vente;100;hebdomadaire;04/01/2027;Encaissement\n".encode())
    assert c[0].frequence == "mensuelle" and c[0].sens == "decaissement" and c[1].sens == "encaissement"
    with pytest.raises(ErreurImport, match="fréquence"):
        lire_charges(b"libelle;montant;frequence;prochaine_echeance\nX;1;bimensuelle;05/01/2027\n")


def test_fichier_vide():
    with pytest.raises(ErreurImport, match="vide"):
        lire_banque(b"")
