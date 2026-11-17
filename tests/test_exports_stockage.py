from openpyxl import load_workbook
import pytest
from pypdf import PdfReader

from tresorerie import stockage
from tresorerie.attention import points_attention
from tresorerie.exports import pdf_dirigeant, xlsx_detaille
from tresorerie.imports import ErreurImport

from conftest import DEMO


def test_pdf_deux_pages(demo, tmp_path):
    pts = points_attention(demo["prev"], demo["clients"], demo["delais"])
    f = pdf_dirigeant(demo["prev"], pts, "Client Fictif", tmp_path / "r.pdf")
    lecteur = PdfReader(f)
    assert len(lecteur.pages) == 2
    t2 = lecteur.pages[1].extract_text()
    assert "5 points d'attention" in t2 and all(f"{i}. " in t2 for i in range(1, 6))


def test_pdf_refuse_sans_5_points(demo, tmp_path):
    with pytest.raises(ValueError):
        pdf_dirigeant(demo["prev"], [], "X", tmp_path / "r.pdf")


def test_xlsx_coherent(demo, tmp_path):
    pts = points_attention(demo["prev"], demo["clients"], demo["delais"])
    f = xlsx_detaille(demo["prev"], pts, "Client Fictif", tmp_path / "d.xlsx", demo["banque"], demo["regles"], demo["delais"])
    wb = load_workbook(f)
    assert {"Synthèse", "Base", "Retard clients", "Perte 1er client", "Flux détaillés", "Délais clients",
            "Banque catégorisée", "Paramètres"} <= set(wb.sheetnames)
    ws = wb["Base"]
    for i, s in enumerate(demo["prev"]["base"].semaines, 4):
        enc = ws.cell(i, 5).value + ws.cell(i, 6).value
        dec = sum(ws.cell(i, j).value for j in (7, 8, 9))
        assert (enc, dec) == (s.encaissements, s.decaissements)
        assert ws.cell(i, 12).value == f"=D{i}+J{i}-K{i}"
    flux = wb["Flux détaillés"]
    total_base = sum(r[8] for r in flux.iter_rows(min_row=2, values_only=True) if r[0] == "Base")
    assert total_base == demo["prev"]["base"].semaines[-1].solde_fin - demo["params"].solde_initial


def test_dossier_client(tmp_path, monkeypatch):
    monkeypatch.setenv("TRESO_DATA_DIR", str(tmp_path))
    nom = stockage.creer_client("Société Fictive SARL")
    assert nom == "societe-fictive-sarl" and stockage.lister_clients() == [nom]
    assert stockage.enregistrer_csv(nom, "banque", (DEMO / "banque.csv").read_bytes()) > 10
    with pytest.raises(ErreurImport):
        stockage.enregistrer_csv(nom, "clients", b"client;montant\nA;1\n")
    assert not (tmp_path / nom / "factures_clients.csv").exists()     # fichier invalide non enregistré
    data = stockage.charger(nom)
    assert data["banque"] and data["clients"] == [] and data["regles"]


def test_nom_client_sans_echappement(tmp_path, monkeypatch):
    monkeypatch.setenv("TRESO_DATA_DIR", str(tmp_path))
    assert stockage.creer_client("../../etc") == "etc"
    with pytest.raises(ValueError):
        stockage.creer_client("../..")


def test_parametres_date_texte_ou_date(tmp_path, monkeypatch):
    from datetime import date
    p = stockage.parametres_depuis({"date_debut": "2026-11-25", "solde_initial": "100"}, date(2026, 1, 1))
    assert p.date_debut == date(2026, 11, 23) and p.solde_initial == 100
    assert stockage.parametres_depuis({"date_debut": "25/11/2026"}, date(2026, 1, 1)).date_debut == date(2026, 11, 23)
    assert stockage.parametres_depuis({}, date(2026, 1, 5)).date_debut == date(2026, 1, 5)
