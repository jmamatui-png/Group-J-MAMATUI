"""Génère des exports Dolibarr et une saisie mensuelle FICTIFS dans exemples/demo/.

Format identique aux exports Dolibarr 22 en français (séparateur « ; »).
Usage : python exemples/generer_demo.py [AAAA-MM-JJ]   (date de fin, par défaut aujourd'hui)
"""
import csv
import random
import sys
from datetime import date, timedelta
from pathlib import Path

SORTIE = Path(__file__).parent / "demo"
FIN = date.fromisoformat(sys.argv[1]) if len(sys.argv) > 1 else date.today()
DEBUT = date(FIN.year - 1, FIN.month, 1)
rnd = random.Random(7)
TGC = 0.11  # taux fictif appliqué à la démo


def ecrire(chemin, entetes, lignes):
    chemin.parent.mkdir(parents=True, exist_ok=True)
    with open(chemin, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(entetes)
        w.writerows(lignes)


def fr(d):
    return d.strftime("%d/%m/%Y")


def jours():
    d = DEBUT
    while d <= FIN:
        yield d
        d += timedelta(days=1)


def generer(entite, prefixe, clients, frequence, montants, delais, solde_depart=0, charges=()):
    factures, paiements, banque = [], [], []
    n = 0
    for d in jours():
        if d.weekday() < 5 and rnd.random() < frequence:
            client = rnd.choices(list(clients), weights=list(clients.values()))[0]
            ht = rnd.randrange(*montants, 1000)
            ttc = round(ht * (1 + TGC))
            n += 1
            ref = f"{prefixe}{d:%y%m}-{n:04d}"
            ech = d + timedelta(days=30)
            factures.append([client, ref, "0", fr(d), fr(ech), ht, ttc])
            paye = ech + timedelta(days=max(-5, int(rnd.gauss(delais.get(client, 10), 8))))
            if paye <= FIN and rnd.random() > 0.04:
                paiements.append([ref, fr(paye), ttc])
                banque.append(["CPT-PRINCIPAL", fr(paye), f"Règlement {ref} {client}", "", ttc])
    # Facturation intragroupe mensuelle et charges
    for d in jours():
        for jour, libelle, montant, client in charges:
            if d.day == jour:
                if client:   # facture intragroupe émise par cette entité
                    n += 1
                    ref = f"{prefixe}{d:%y%m}-{n:04d}"
                    ttc = round(montant * (1 + TGC))
                    factures.append([client, ref, "0", fr(d), fr(d + timedelta(days=15)), montant, ttc])
                    if d + timedelta(days=15) <= FIN:
                        paiements.append([ref, fr(d + timedelta(days=15)), ttc])
                        banque.append(["CPT-PRINCIPAL", fr(d + timedelta(days=15)), f"Règlement {ref}", "", ttc])
                else:
                    banque.append(["CPT-PRINCIPAL", fr(d), libelle, montant, ""])
    # Un brouillon et un avoir, pour vérifier qu'ils sont bien traités
    factures.append([list(clients)[0], f"{prefixe}PROV-1", "0", fr(FIN), fr(FIN), 999_999, 1_109_999, "0"])
    if entite != "holding":
        factures.append([list(clients)[0], f"{prefixe}AV-0001", "2", fr(FIN - timedelta(days=20)), fr(FIN - timedelta(days=20)), -50_000, -55_500])
    base = SORTIE / entite
    ecrire(base / "factures.csv", ["Raison sociale", "Réf. facture", "Type", "Date facturation", "Date échéance",
                                   "Total HT", "Total TTC", "Statut facture"],
           [l if len(l) == 8 else l + ["1"] for l in factures])
    ecrire(base / "paiements.csv", ["Réf. facture", "Date paiement", "Montant paiement affecté à la facture"], paiements)
    banque.sort(key=lambda l: (l[1][6:], l[1][3:5], l[1][:2]))
    ecrire(base / "banque.csv", ["Ref compte financier", "Date opération", "Libellé", "Débit", "Crédit"], banque)
    return solde_depart


def main():
    soldes = {
        "terrawaves": generer("terrawaves", "TW", {"Client Logistique Alpha (fictif)": 70, "Client Beta (fictif)": 15,
                                                    "Particuliers divers": 15}, 0.9, (80_000, 480_000),
                              {"Client Logistique Alpha (fictif)": 25},
                              charges=[(28, "Salaires", 2_400_000, None), (15, "CAFAT", 780_000, None),
                                       (5, "Loyer dépôt", 300_000, None), (10, "Carburant", 420_000, None),
                                       (20, "Sous-traitant transport", 350_000, None)]),
        "mge": generer("mge", "MG", {"PME Exemple 1 (fictif)": 40, "PME Exemple 2 (fictif)": 30, "PME Exemple 3 (fictif)": 30},
                       0.08, (150_000, 400_000), {"PME Exemple 2 (fictif)": 20},
                       charges=[(1, "Mission DAF", 150_000, "Terrawaves Logistics"), (12, "Loyer bureau", 90_000, None),
                                (25, "Rémunération gérance", 450_000, None)]),
        "holding": generer("holding", "HD", {"Terrawaves Logistics": 100}, 0.0, (1000, 2000), {},
                           charges=[(3, "Frais de holding", 100_000, "Terrawaves Logistics"), (18, "Frais bancaires", 3_500, None)]),
    }
    # Saisie mensuelle
    lignes = []
    d = DEBUT
    while d <= FIN:
        m = f"{d:%Y-%m}"
        lignes += [
            {"mois": m, "entite": "terrawaves", "charges_fixes": 3_480_000 + 250_000, "charges_fixes_intragroupe": 250_000,
             "couts_directs": rnd.randrange(150_000, 300_000, 1000), "sous_traitance": 350_000,
             "carburant": 420_000, "km": rnd.randrange(5_500, 7_500, 10), "heures_vendues": rnd.randrange(520, 700),
             "fourgons": 4},
            {"mois": m, "entite": "mge", "charges_fixes": 540_000, "couts_directs": 0, "mrr_signe": rnd.choice([300_000, 450_000, 600_000]),
             "jours_factures": rnd.randint(4, 9), "jours_disponibles": 10, "contacts": rnd.randint(6, 15),
             "rendez_vous": rnd.randint(2, 6), "diagnostics": rnd.randint(0, 2)},
            {"mois": m, "entite": "holding", "charges_fixes": 3_500, "couts_directs": 0},
            {"mois": m, "entite": "personnel", "prelevement_dirigeant": rnd.choice([300_000, 400_000, 450_000])},
        ]
        d = date(d.year + (d.month == 12), d.month % 12 + 1, 1)
    from_cols = ["mois", "entite", "charges_fixes", "charges_fixes_intragroupe", "couts_directs", "couts_directs_intragroupe",
                 "sous_traitance", "carburant", "km", "heures_vendues", "fourgons", "mrr_signe", "jours_factures",
                 "jours_disponibles", "contacts", "rendez_vous", "diagnostics", "prelevement_dirigeant"]
    with open(SORTIE / "saisie_mensuelle.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=from_cols, delimiter=";")
        w.writeheader()
        w.writerows(lignes)
    print(f"Données fictives écrites dans {SORTIE} (du {DEBUT} au {FIN})")


if __name__ == "__main__":
    main()
