"""Génère un jeu de données FICTIF (entreprise, clients et montants inventés) dans exemples/demo/.

Usage : python exemples/generer_demo.py
"""
import csv
import random
from datetime import date, timedelta
from pathlib import Path

SORTIE = Path(__file__).parent / "demo"
DEPART = date(2026, 11, 23)          # lundi de départ de la prévision
rnd = random.Random(42)

CLIENTS = {  # nom fictif : (retard moyen réel en jours, poids)
    "Commune Exemple": (45, 0.35),
    "Hôtel Lagon Fictif": (12, 0.25),
    "SARL Démo Bâtiment": (25, 0.2),
    "Résidence Témoin": (3, 0.12),
    "Particuliers divers": (0, 0.08),
}


def ecrire(nom, entetes, lignes):
    SORTIE.mkdir(parents=True, exist_ok=True)
    with open(SORTIE / nom, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(entetes)
        w.writerows(lignes)


def fr(d):
    return d.strftime("%d/%m/%Y")


def main():
    factures, banque = [], []
    n = 1
    # Historique : factures émises sur 6 mois, payées avec le retard propre à chaque client
    d = DEPART - timedelta(days=200)
    while d < DEPART:
        for client, (retard, poids) in CLIENTS.items():
            if rnd.random() < poids:
                montant = rnd.randrange(200_000, 2_500_000, 1_000)
                emission = d
                echeance = emission + timedelta(days=30)
                paiement = echeance + timedelta(days=max(0, int(rnd.gauss(retard, 5))))
                num = f"F{n:04d}"
                n += 1
                if paiement < DEPART:
                    factures.append([client, num, fr(emission), fr(echeance), montant, fr(paiement)])
                    banque.append([fr(paiement), f"VIR {client.upper()} {num}", montant])
                else:
                    factures.append([client, num, fr(emission), fr(echeance), montant, ""])
        d += timedelta(days=7)
    # Une vieille créance douteuse
    factures.append(["SARL Démo Bâtiment", "F0007B", fr(DEPART - timedelta(days=160)), fr(DEPART - timedelta(days=130)), 850_000, ""])

    fournisseurs = [
        ["Négoce Bois Fictif", "BF-311", fr(DEPART - timedelta(days=5)), 1_350_000],
        ["Négoce Bois Fictif", "BF-322", fr(DEPART + timedelta(days=17)), 2_100_000],
        ["Quincaillerie Démo", "Q-88", fr(DEPART + timedelta(days=9)), 420_000],
        ["Transport Exemple", "T-12", fr(DEPART + timedelta(days=24)), 260_000],
        ["Négoce Bois Fictif", "BF-340", fr(DEPART + timedelta(days=45)), 1_800_000],
        ["Location Engins Démo", "LE-5", fr(DEPART + timedelta(days=60)), 690_000],
    ]

    charges = [
        ["Salaires", "Salaires", 3_200_000, "mensuelle", fr(date(2026, 11, 30)), "", "décaissement"],
        ["Cotisations CAFAT", "CAFAT", 1_150_000, "mensuelle", fr(date(2026, 12, 15)), "", "décaissement"],
        ["Loyer atelier", "Loyers", 450_000, "mensuelle", fr(date(2026, 12, 5)), "", "décaissement"],
        ["Échéance prêt camion", "Emprunts", 185_000, "mensuelle", fr(date(2026, 12, 10)), fr(date(2027, 6, 10)), "décaissement"],
        ["Déclaration TGC", "TGC", 980_000, "trimestrielle", fr(date(2027, 1, 31)), "", "décaissement"],
        ["Prime de fin d'année", "Salaires", 1_600_000, "ponctuelle", fr(date(2026, 12, 18)), "", "décaissement"],
        ["Ventes prévues non encore facturées (estimation)", "Ventes futures", 1_250_000, "hebdomadaire",
         fr(DEPART + timedelta(days=38)), "", "encaissement"],
        ["Sous-location parking", "Autres produits", 60_000, "mensuelle", fr(date(2026, 12, 1)), "", "encaissement"],
    ]

    # Charges passées dans la banque (pour la catégorisation et la moyenne des dépenses diverses)
    m = DEPART - timedelta(days=200)
    while m < DEPART:
        if m.day == 30 or (m.month == 2 and m.day == 28):
            banque.append([fr(m), "VIR SALAIRES PERSONNEL", -3_200_000])
        if m.day == 15:
            banque.append([fr(m), "PRLV CAFAT COTISATIONS", -1_150_000])
        if m.day == 5:
            banque.append([fr(m), "PRLV LOYER ATELIER", -450_000])
            banque.append([fr(m), "PRLV ENERCAL", -rnd.randrange(60_000, 95_000, 100)])
        if m.day == 10:
            banque.append([fr(m), "ECHEANCE PRET 00123", -185_000])
        if m.weekday() == 2:
            banque.append([fr(m), "CB STATION SERVICE", -rnd.randrange(15_000, 40_000, 100)])
        if m.day == 1:
            banque.append([fr(m), "FRAIS TENUE DE COMPTE", -4_500])
        if m.day == 20 and rnd.random() < 0.6:
            banque.append([fr(m), "VIR NEGOCE BOIS FICTIF", -rnd.randrange(800_000, 2_000_000, 1000)])
        m += timedelta(days=1)

    banque.sort(key=lambda l: (l[0][6:], l[0][3:5], l[0][:2]))
    ecrire("banque.csv", ["date", "libelle", "montant"], banque)
    ecrire("factures_clients.csv", ["client", "numero", "date_emission", "echeance", "montant_ttc", "date_paiement"], factures)
    ecrire("factures_fournisseurs.csv", ["fournisseur", "numero", "echeance", "montant_ttc"], fournisseurs)
    ecrire("charges.csv", ["libelle", "categorie", "montant", "frequence", "prochaine_echeance", "date_fin", "sens"], charges)
    print(f"Données fictives écrites dans {SORTIE}")


if __name__ == "__main__":
    main()
