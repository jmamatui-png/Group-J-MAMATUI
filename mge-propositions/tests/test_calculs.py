from decimal import Decimal

import pytest

from mge_docs.calculs import arrondi_xpf, calculer
from mge_docs.formatage import ajouter_mois, pct, xpf
from datetime import date


@pytest.mark.parametrize("ht, taux, tgc, ttc", [
    (150_000, "11", 16_500, 166_500),      # Diagnostic / DAF Essentiel
    (250_000, "11", 27_500, 277_500),      # DAF Pilotage
    (400_000, "11", 44_000, 444_000),      # DAF Croissance
    (500_000, "11", 55_000, 555_000),      # Dossier de financement, haut de fourchette
    (150_000, "6", 9_000, 159_000),
    (150_000, "22", 33_000, 183_000),
    (150_000, "0", 0, 150_000),
    (150_000, "5,5", 8_250, 158_250),      # virgule décimale acceptée
])
def test_ht_tgc_ttc(ht, taux, tgc, ttc):
    m = calculer(ht, taux)
    assert (m.ht, m.tgc, m.ttc) == (ht, tgc, ttc)
    assert m.ht + m.tgc == m.ttc


def test_arrondi_au_franc_demi_superieur():
    assert arrondi_xpf(Decimal("0.5")) == 1
    assert arrondi_xpf(Decimal("1.49")) == 1
    # 123 455 × 11 % = 13 580,05 -> 13 580
    assert calculer(123_455, "11").tgc == 13_580
    # 123 450 × 11 % = 13 579,5 -> 13 580 (demi-franc arrondi au supérieur)
    assert calculer(123_450, "11").tgc == 13_580


def test_totaux_mensuels_egaux_a_la_somme_des_factures():
    m = calculer(250_000, "11", 12)
    assert (m.total_ht, m.total_tgc, m.total_ttc) == (3_000_000, 330_000, 3_330_000)
    # Avec arrondi : 123 455 × 11 % = 13 580,05 -> 13 580 par mois, × 7 mois.
    m = calculer(123_455, "11", 7)
    assert m.total_tgc == 13_580 * 7 == 95_060
    assert m.total_ttc == m.total_ht + m.total_tgc == 864_185 + 95_060


@pytest.mark.parametrize("prix", [0, -1, 1.5, "150000", True, None])
def test_prix_invalide_refuse(prix):
    with pytest.raises(ValueError):
        calculer(prix, "11")


@pytest.mark.parametrize("taux", ["-1", "101", "abc", "", "NaN"])
def test_taux_invalide_refuse(taux):
    with pytest.raises(ValueError):
        calculer(150_000, taux)


def test_periodes_invalides():
    with pytest.raises(ValueError):
        calculer(150_000, "11", 0)


def test_formatage():
    assert xpf(1_234_567) == "1 234 567 F CFP"
    assert xpf(0) == "0 F CFP"
    assert pct(Decimal("11")) == "11 %"
    assert pct(Decimal("5.5")) == "5,5 %"
    assert ajouter_mois(date(2027, 1, 31), 1) == date(2027, 2, 28)
    assert ajouter_mois(date(2027, 11, 15), 3) == date(2028, 2, 15)
