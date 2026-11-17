import pytest

from mge_docs.fiche import CHAMPS_OBLIGATOIRES, FicheInvalide, valider


def test_fiche_valide(fiche_ok, catalogue):
    f = valider(fiche_ok, catalogue)
    assert f.offre.nom == "DAF Pilotage" and f.prix_ht == 250_000 and not f.avertissements


@pytest.mark.parametrize("champ", list(CHAMPS_OBLIGATOIRES))
@pytest.mark.parametrize("valeur", [None, "", "   ", []])
def test_champ_obligatoire_manquant_refuse(fiche_ok, catalogue, champ, valeur):
    fiche_ok[champ] = valeur
    with pytest.raises(FicheInvalide) as e:
        valider(fiche_ok, catalogue)
    assert any(CHAMPS_OBLIGATOIRES[champ] in err for err in e.value.erreurs)


def test_champ_absent_refuse(fiche_ok, catalogue):
    del fiche_ok["ridet"]
    with pytest.raises(FicheInvalide, match="RIDET"):
        valider(fiche_ok, catalogue)


def test_toutes_les_erreurs_listees(catalogue):
    with pytest.raises(FicheInvalide) as e:
        valider({}, catalogue)
    assert len(e.value.erreurs) == len(CHAMPS_OBLIGATOIRES)


@pytest.mark.parametrize("modif, motif", [
    ({"ridet": "12345"}, "RIDET invalide"),
    ({"offre": "inconnue"}, "Offre inconnue"),
    ({"prix_ht": -5}, "Prix HT invalide"),
    ({"prix_ht": "abc"}, "Prix HT invalide"),
    ({"chiffre_affaires": "beaucoup"}, "Chiffre d'affaires invalide"),
    ({"duree": 5}, "engagement minimal de 6 mois"),
    ({"duree": 0}, "Durée invalide"),
    ({"date_debut": "01/02/2027"}, "Date de début invalide"),
    ({"offre": "dossier-de-financement", "prix_ht": 200_000}, "hors fourchette"),
    ({"offre": "dossier-de-financement", "prix_ht": 500_001}, "hors fourchette"),
])
def test_valeurs_invalides_refusees(fiche_ok, catalogue, modif, motif):
    fiche_ok.update(modif)
    with pytest.raises(FicheInvalide, match=motif):
        valider(fiche_ok, catalogue)


def test_fourchette_bornes_acceptees(fiche_ok, catalogue):
    for prix in (250_000, 375_000, 500_000):
        fiche_ok.update(offre="dossier-de-financement", prix_ht=prix, duree=4)
        assert valider(fiche_ok, catalogue).prix_ht == prix


def test_forfait_duree_courte_acceptee(fiche_ok, catalogue):
    fiche_ok.update(offre="diagnostic-flash-360", prix_ht=150_000, duree=2)
    assert valider(fiche_ok, catalogue).duree == 2


def test_prix_different_du_catalogue_avertit(fiche_ok, catalogue):
    fiche_ok["prix_ht"] = 230_000
    assert "différent du tarif catalogue" in valider(fiche_ok, catalogue).avertissements[0]


def test_offre_par_nom_et_montants_texte(fiche_ok, catalogue):
    fiche_ok.update(offre="DAF Pilotage", prix_ht="250 000", chiffre_affaires="50 000 000")
    f = valider(fiche_ok, catalogue)
    assert f.prix_ht == 250_000 and f.chiffre_affaires == 50_000_000
