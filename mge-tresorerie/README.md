# Trésorerie à 13 semaines — MGE Conseil

Application Streamlit de prévision de trésorerie hebdomadaire pour les PME clientes. Chaque client a son propre dossier. **Les données restent sur le poste** : serveur limité à `localhost`, télémétrie Streamlit désactivée, aucun service externe.

## Installation

Il faut Python 3.11 ou plus récent.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Utilisation

```bash
streamlit run app.py          # ouvre http://localhost:8501
```

1. **Dossier client** (barre latérale) : créer ou choisir un client.
2. **Données** : importer les 4 CSV (séparateur `;` ou `,`, dates JJ/MM/AAAA, montants en F CFP). Un fichier invalide est refusé avec le numéro des lignes en erreur, et le fichier précédent est conservé.
3. **Catégorisation** : modifier les règles. La première règle qui correspond l'emporte. Les lignes non catégorisées sont listées à part.
4. **Paramètres** : lundi de départ, solde au départ, seuil d'alerte, retard du scénario, seuil des créances douteuses, catégories bancaires à extrapoler.
5. **Prévision** : alertes, graphique des 3 scénarios, tableau hebdomadaire, détail des flux, délais clients, 5 points d'attention.
6. **Exports** : PDF dirigeant (2 pages) et XLSX détaillé, enregistrés dans `donnees_clients/<client>/exports/`.

### Données de démonstration (fictives)

```bash
python exemples/generer_demo.py        # régénère exemples/demo/*.csv
```

Importez ensuite les 4 fichiers de `exemples/demo/` dans un client de test. Paramètres utilisés pour la démonstration : départ le 23/11/2026, solde de 9 500 000 F, seuil de 2 000 000 F.

### Formats CSV

| Fichier | Colonnes obligatoires | Facultatives |
|---|---|---|
| Relevé bancaire | `date ; libelle ; montant` (signé) — ou `debit ; credit` | `solde` |
| Factures clients | `client ; montant_ttc ; echeance` | `numero ; date_emission ; date_paiement` |
| Factures fournisseurs | `fournisseur ; montant_ttc ; echeance` | `numero` |
| Charges récurrentes | `libelle ; montant ; frequence ; prochaine_echeance` | `categorie ; date_fin ; sens` |

- Fréquences : hebdomadaire, mensuelle, trimestrielle, semestrielle, annuelle, ponctuelle.
- `sens` : décaissement (par défaut) ou encaissement.

## Méthode de calcul

- **Semaines** : du lundi au dimanche ; S1 commence le lundi de départ. Montants en F CFP entiers.
- **Solde fin = solde début + encaissements − décaissements.** Le solde début de chaque semaine est le solde fin de la précédente.
- **Encaissements clients** : date d'échéance + retard moyen réel du client.
  - Le retard est pondéré par les montants et calculé sur les factures qui ont une `date_paiement`.
  - Un client sans historique reçoit le retard moyen global.
- **Fournisseurs** : payés à l'échéance.
- **Charges** : selon leur calendrier. Le 31 du mois devient le 28 ou le 29 en février.
- **Échus au départ** : créances et dettes échues sont ramenées en S1. Les créances échues depuis plus de 90 jours (paramétrable) sont **exclues** par prudence.
- **Dépenses diverses** (facultatif) : moyenne hebdomadaire, sur l'historique bancaire, des catégories choisies.
- **Scénarios** :
  - Base.
  - Retard : tous les encaissements clients décalés de +30 jours.
  - Perte du 1er client : ses factures ouvertes ne sont pas encaissées.
- **Alerte** : solde fin **strictement inférieur** au seuil.

## Tests

```bash
python -m pytest -q
```

Les 109 tests couvrent :
- **Le test central** : pour chaque semaine et chaque scénario, la somme des flux égale la variation du solde. On vérifie aussi encaissements − décaissements = variation, le chaînage des soldes, et que chaque flux est compté une seule fois. Ces contrôles tournent sur les données de démonstration et sur 60 jeux de données aléatoires (factures échues ou futures, toutes les fréquences, soldes négatifs).
- La semaine 1 de la démonstration, recalculée à la main.
- La lecture des montants et des dates, et les erreurs d'import.
- Les règles de catégorisation et les délais pondérés.
- Les scénarios, les reports, les exclusions et l'alerte.
- Le PDF (exactement 2 pages, 5 points d'attention) et la cohérence du XLSX.
- Le dossier client, y compris l'impossibilité de sortir du dossier de données.

Dans le XLSX, chaque feuille de scénario contient une colonne **« Contrôle (doit être 0) »** : la différence entre le solde recalculé par Excel et celui calculé par l'application.

## Sauvegarde

- Tout est dans `donnees_clients/` (un sous-dossier par client : CSV, `regles.yaml`, `parametres.yaml`, `exports/`). **Sauvegardez ce dossier** sur un support chiffré ou un stockage d'entreprise, au moins une fois par semaine.
- Pour changer son emplacement : `export TRESO_DATA_DIR=/chemin/vers/dossier` avant de lancer l'application.
- `donnees_clients/` est exclu de Git : ne jamais le pousser dans un dépôt.

## Hypothèses retenues — à valider

1. **Délais réels** : il faut un historique de factures soldées avec leur `date_paiement`, dans le fichier des factures clients. Le relevé bancaire seul ne suffit pas, car il ne dit pas quelle facture a été payée.
2. **Ventes futures** : une prévision fondée sur les seules factures déjà émises s'effondre après 5 à 6 semaines. Les ventes prévues mais pas encore facturées se saisissent dans `charges.csv` avec `sens = encaissement`. C'est une estimation du dirigeant : elle doit être justifiée.
3. **1er client** : le client au plus gros montant TTC facturé (factures ouvertes + soldées).
4. **Solde de départ** : saisi à la main. Il doit correspondre au solde réel du lundi matin, tous comptes bancaires confondus.
5. **TGC** : saisie comme charge récurrente (montant net à reverser). Elle n'est pas recalculée à partir des factures.

## Limites et risques

- La prévision n'est **pas un document audité**. Elle vaut ce que valent les données saisies. Le PDF le rappelle.
- **Double comptage** : une catégorie bancaire extrapolée (ex. Énergie) ne doit pas figurer aussi dans les charges récurrentes.
- Les **avoirs** et les acomptes ne sont pas gérés (montants négatifs refusés) : à déduire des factures avant l'import.
- **Un seul solde** : les placements, découverts autorisés et lignes de crédit court terme ne sont pas modélisés. Le seuil d'alerte peut tenir compte du découvert autorisé.
- Les données importées sont celles du client : prévoir une clause de confidentialité et la durée de conservation dans la lettre de mission.
