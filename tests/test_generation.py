"""Génération complète : fichiers produits, contenus et clauses obligatoires."""
from datetime import date

import pytest
from docx import Document

from mge_docs import generation
from mge_docs.fiche import FicheInvalide, charger_fiche, valider

CLAUSES_LM = [
    "conseil et de pilotage financier",
    "ni la tenue de la comptabilité, ni l'établissement des comptes annuels",
    "Livrables",
    "Calendrier",
    "Honoraires HT",
    "TGC (6 %)",
    "payables à 15 jours",
    "période d'engagement ferme de 6 mois",
    "préavis de 1 mois",
    "Confidentialité",
    "limitée au montant des honoraires HT effectivement perçus au titre de la mission au cours des douze mois",
    "Obligations du Client",
]


def texte_docx(chemin):
    d = Document(chemin)
    t = [p.text for p in d.paragraphs]
    for tab in d.tables:
        for r in tab.rows:
            t += [c.text for c in r.cells]
    return "\n".join(t)


@pytest.fixture
def generer(tmp_path, config, catalogue, fiche_ok):
    def _g(**modif):
        fiche_ok.update(modif)
        f = valider(fiche_ok, catalogue)
        return generation.generer(f, config, sortie=tmp_path / "out", registre=tmp_path / "reg.json",
                                  date_document=date(2026, 11, 17))
    return _g


def test_quatre_fichiers_et_numero(generer):
    r = generer()
    assert r["numero"] == "MGE-PROP-2026-001"
    assert sorted(p.suffix for p in r["fichiers"]) == [".docx", ".docx", ".pdf", ".pdf"]
    assert all(p.stat().st_size > 1000 for p in r["fichiers"])
    assert generer()["numero"] == "MGE-PROP-2026-002"


def test_lettre_de_mission_clauses_obligatoires(generer):
    r = generer()
    lm = next(p for p in r["fichiers"] if "lettre" in p.name and p.suffix == ".docx")
    t = texte_docx(lm)
    for clause in CLAUSES_LM:
        assert clause in t, clause
    assert "MGE-PROP-2026-001" in t


def test_montants_dans_les_documents(generer):
    r = generer(duree=12)
    for p in (x for x in r["fichiers"] if x.suffix == ".docx"):
        t = texte_docx(p)
        for montant in ("250 000 F CFP", "15 000 F CFP", "265 000 F CFP",
                        "3 000 000 F CFP", "180 000 F CFP", "3 180 000 F CFP"):
            assert montant in t, (p.name, montant)
        assert "TVA" not in t


def test_taux_tgc_parametrable(tmp_path, config, catalogue, fiche_ok):
    f = valider(fiche_ok, catalogue)
    r = generation.generer(f, config, sortie=tmp_path, registre=tmp_path / "r.json", taux_tgc="11",
                           formats=["docx"], documents=("lettre-de-mission",))
    t = texte_docx(r["fichiers"][0])
    assert "TGC (11 %)" in t and "27 500 F CFP" in t and "277 500 F CFP" in t


def test_forfait_sans_engagement_mensuel(generer):
    r = generer(offre="diagnostic-flash-360", prix_ht=150_000, duree=3)
    lm = next(p for p in r["fichiers"] if "lettre" in p.name and p.suffix == ".docx")
    t = texte_docx(lm)
    assert "La mission prend fin à la remise des livrables" in t
    assert "159 000 F CFP" in t
    assert "ni la tenue de la comptabilité" in t


def test_pdf_contient_le_texte(generer):
    pypdf = pytest.importorskip("pypdf")
    r = generer()
    pdf = next(p for p in r["fichiers"] if "lettre" in p.name and p.suffix == ".pdf")
    t = " ".join(page.extract_text() for page in pypdf.PdfReader(pdf).pages)
    assert "MGE-PROP-2026-001" in t and "Confidentialité" in t


def test_erreur_de_modele_ne_consomme_pas_de_numero(tmp_path, config, catalogue, fiche_ok):
    (tmp_path / "tpl").mkdir()
    (tmp_path / "tpl" / "proposition.md.j2").write_text("{{ variable_inexistante }}")
    (tmp_path / "tpl" / "lettre_mission.md.j2").write_text("ok")
    f = valider(fiche_ok, catalogue)
    with pytest.raises(Exception):
        generation.generer(f, config, sortie=tmp_path, registre=tmp_path / "r.json", templates=tmp_path / "tpl")
    assert not (tmp_path / "r.json").exists()


def test_fiche_exemple_valide(catalogue):
    assert charger_fiche("exemples/client_fictif.yaml", catalogue).offre.code == "daf-pilotage"


def test_fiche_incomplete_refusee_en_cli(tmp_path, capsys):
    from mge_docs.cli import main
    fiche = tmp_path / "f.yaml"
    fiche.write_text("raison_sociale: X\n")
    assert main(["--registre", str(tmp_path / "r.json"), "generer", str(fiche), "--sortie", str(tmp_path)]) == 2
    assert "Champ obligatoire manquant : RIDET" in capsys.readouterr().err
    assert not (tmp_path / "r.json").exists()
