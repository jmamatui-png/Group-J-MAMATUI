from datetime import date

import pytest
import yaml

from tdb.donnees import ErreurDonnees, lire_banque, lire_factures, lire_paiements, lire_saisie
from conftest import RACINE

COL = yaml.safe_load((RACINE / "config.yaml").read_text())["colonnes"]

EXPORT_FACTURES = ("Raison sociale;Réf. facture;Type;Date facturation;Date échéance;Total HT;Total TTC;Statut facture;Réf. produit\n"
                   "Client A;FA1;0;05/10/2026;04/11/2026;100000.00;111000.00;1;P1\n"
                   "Client A;FA1;0;05/10/2026;04/11/2026;100000.00;111000.00;1;P2\n"      # 2e ligne de la même facture
                   "Client B;AV1;2;06/10/2026;06/10/2026;-10000.00;-11100.00;2;\n"
                   "Client B;PROV1;0;07/10/2026;;5000;5550;0;\n"                           # brouillon
                   "Client B;AB1;0;07/10/2026;;5000;5550;3;\n")                            # abandonnée


def test_export_factures_dolibarr():
    f = lire_factures(EXPORT_FACTURES.encode(), "terrawaves", COL["factures"])
    assert [x.ref for x in f] == ["FA1", "AV1"]
    assert f[0].ht == 100_000 and f[0].echeance == date(2026, 11, 4)
    assert f[1].ht == -10_000 and f[1].ttc == -11_100


def test_export_factures_libelles_de_statut_et_avoir_positif():
    t = ("Raison sociale,Réf. facture,Type,Date facturation,Total HT,Total TTC,Statut facture\n"
         "A,X1,Avoir,2026-10-01,\"1 000,00\",\"1 110,00\",Payée\nA,X2,Standard,2026-10-01,10,11,Brouillon\n")
    f = lire_factures(t.encode("cp1252"), "mge", COL["factures"])
    assert len(f) == 1 and f[0].ht == -1_000 and f[0].echeance == date(2026, 10, 1)


def test_colonne_manquante_message_clair():
    with pytest.raises(ErreurDonnees, match="Total HT|ht"):
        lire_factures(b"Raison sociale;Ref. facture;Date facturation\nA;1;01/01/2026\n", "mge", COL["factures"])


def test_export_paiements_ignore_factures_sans_reglement():
    t = ("Réf. facture;Date paiement;Montant paiement;Montant paiement affecté à la facture\n"
         "FA1;12/11/2026;500000;111000\nFA2;;;\n")
    p = lire_paiements(t.encode(), "terrawaves", COL["paiements"])
    assert len(p) == 1 and p[0].montant == 111_000      # montant affecté, pas le règlement global


def test_export_banque_debit_credit():
    t = "Ref compte financier;Date opération;Libellé;Débit;Crédit\nCPT;01/11/2026;Loyer;300000;\nCPT;02/11/2026;Client;;111000\n"
    b = lire_banque(t.encode(), "terrawaves", COL["banque"])
    assert [m.montant for m in b] == [-300_000, 111_000] and b[0].compte == "CPT"


def test_erreurs_ligne():
    with pytest.raises(ErreurDonnees, match="ligne 2"):
        lire_banque("Ref compte financier;Date opération;Débit;Crédit\nC;32/13/2026;1;\n".encode(), "mge", COL["banque"])


def test_saisie(tmp_path):
    p = tmp_path / "s.csv"
    p.write_text("mois;entite;charges_fixes;heures_vendues\n2026-10;Terrawaves;1 000 000;600\n2026-10;personnel;;\n", encoding="utf-8")
    s = lire_saisie(p)
    assert s.get("2026-10", "terrawaves", "charges_fixes") == 1_000_000
    assert s.get("2026-10", "terrawaves", "km") is None
    assert lire_saisie(tmp_path / "absent.csv").valeurs == {}


@pytest.mark.parametrize("ligne, motif", [("2026-13;mge;1", "mois"), ("2026-10;inconnue;1", "entité"),
                                          ("2026-10;mge;abc", "nombre"), ("2026-10;mge;-5", "négatif")])
def test_saisie_invalide(tmp_path, ligne, motif):
    p = tmp_path / "s.csv"
    p.write_text(f"mois;entite;charges_fixes\n{ligne}\n", encoding="utf-8")
    with pytest.raises(ErreurDonnees, match=motif):
        lire_saisie(p)


def test_saisie_doublon(tmp_path):
    p = tmp_path / "s.csv"
    p.write_text("mois;entite;charges_fixes\n2026-10;mge;1\n2026-10;mge;2\n", encoding="utf-8")
    with pytest.raises(ErreurDonnees, match="doublon"):
        lire_saisie(p)


def test_demo_lisible():
    for e in ["terrawaves", "mge", "holding"]:
        assert lire_factures(RACINE / f"exemples/demo/{e}/factures.csv", e, COL["factures"])
        assert lire_banque(RACINE / f"exemples/demo/{e}/banque.csv", e, COL["banque"])
    assert lire_saisie(RACINE / "exemples/demo/saisie_mensuelle.csv").valeurs
