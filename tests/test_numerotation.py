import json
from concurrent.futures import ThreadPoolExecutor

import pytest

from mge_docs.numerotation import FORMAT_RE, attribuer_numero, formater, prochain_numero


def test_format():
    assert formater(2026, 1) == "MGE-PROP-2026-001"
    assert formater(2026, 42) == "MGE-PROP-2026-042"
    assert formater(2026, 1000) == "MGE-PROP-2026-1000"
    assert FORMAT_RE.match(formater(2026, 7))
    with pytest.raises(ValueError):
        formater(2026, 0)


def test_sequence_et_apercu(tmp_path):
    reg = tmp_path / "registre.json"
    assert prochain_numero(reg, 2026) == "MGE-PROP-2026-001"
    assert attribuer_numero(reg, 2026) == "MGE-PROP-2026-001"
    assert attribuer_numero(reg, 2026) == "MGE-PROP-2026-002"
    # L'aperçu ne consomme pas de numéro.
    assert prochain_numero(reg, 2026) == "MGE-PROP-2026-003"
    assert prochain_numero(reg, 2026) == "MGE-PROP-2026-003"


def test_remise_a_zero_annuelle(tmp_path):
    reg = tmp_path / "registre.json"
    attribuer_numero(reg, 2026)
    attribuer_numero(reg, 2026)
    assert attribuer_numero(reg, 2027) == "MGE-PROP-2027-001"
    assert attribuer_numero(reg, 2026) == "MGE-PROP-2026-003"


def test_historique(tmp_path):
    reg = tmp_path / "registre.json"
    attribuer_numero(reg, 2026, client="Fictive", offre="DAF Pilotage")
    h = json.loads(reg.read_text())["historique"]
    assert h[0]["numero"] == "MGE-PROP-2026-001" and h[0]["client"] == "Fictive"


def test_pas_de_doublon_en_parallele(tmp_path):
    reg = tmp_path / "registre.json"
    with ThreadPoolExecutor(8) as ex:
        numeros = list(ex.map(lambda _: attribuer_numero(reg, 2026), range(40)))
    assert len(set(numeros)) == 40
    assert sorted(numeros) == [formater(2026, i) for i in range(1, 41)]
