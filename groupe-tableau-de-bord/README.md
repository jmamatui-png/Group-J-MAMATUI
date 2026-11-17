# Tableau de bord du groupe — Terrawaves, MGE, holding

Application Streamlit locale qui consolide les 3 sociétés à partir des **exports CSV de Dolibarr** et d'une **saisie mensuelle**. Elle n'utilise ni base de données ni service externe ; elle n'est accessible que depuis le poste.

## Installation

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Utilisation

```bash
streamlit run app.py
```

L'application s'ouvre sur http://localhost:8501.

Pour essayer avec les **données fictives** :

```bash
python exemples/generer_demo.py
```

```bash
TDB_DONNEES=exemples/demo streamlit run app.py
```

### 1. Déposer les exports Dolibarr

Dans chacun des 3 Dolibarr, aller dans *Outils › Exports* et exporter en CSV, sans filtre de date :

| Fichier à déposer | Export Dolibarr |
|---|---|
| `donnees/<entité>/factures.csv` | Factures clients et lignes de factures |
| `donnees/<entité>/paiements.csv` | Factures clients et règlements |
| `donnees/<entité>/banque.csv` | Écritures bancaires et relevés |

`<entité>` vaut `terrawaves`, `mge` ou `holding`. Les intitulés de colonnes ont été relevés sur Dolibarr 22 en français ; ils sont listés dans `config.yaml`, rubrique `colonnes`. Si un import échoue, le message indique les colonnes trouvées : ajoutez l'intitulé exact dans `config.yaml`.

### 2. Saisie mensuelle

Page **Saisie mensuelle** (ou fichier `donnees/saisie_mensuelle.csv`) : une ligne par mois et par entité (`terrawaves`, `mge`, `holding`, `personnel`) pour ce que Dolibarr ne contient pas :
- **Toutes les entités** : charges fixes, coûts directs, et la part de ces deux montants facturée par une autre entité du groupe (`*_intragroupe`).
- **Terrawaves** : sous-traitance, carburant, km, heures vendues, nombre de fourgons.
- **MGE** : revenu mensuel récurrent signé, jours facturés et disponibles, contacts, rendez-vous, diagnostics.
- **Personnel** : montant prélevé par le dirigeant.

Une saisie invalide (mois mal écrit, doublon, nombre négatif) est refusée et le fichier précédent est conservé.

### 3. Paramètres (`config.yaml`)

- `soldes_initiaux` : solde de chaque compte bancaire avant la première écriture exportée. **Sans eux, la trésorerie est fausse.**
- `noms_tiers` : les noms sous lesquels chaque société apparaît comme client des autres, pour éliminer l'intragroupe.
- `seuil_part_premier_client` (0,75), `jours_retard_creances` (30), `jours_disponibles_mge` (10).
- `taux_provision_fiscale` : **à fixer avec l'expert-comptable** (voir plus bas).

Pour des réglages personnels sans modifier le modèle, créez `config.local.yaml` : il est prioritaire et exclu de Git.

## Pages

- **Lundi** : les 5 chiffres au dimanche soir, comparés au dimanche précédent.
  1. Trésorerie du groupe.
  2. Créances échues depuis plus de 30 jours.
  3. CA HT des 30 derniers jours.
  4. Encaissements de la semaine.
  5. Part du 1er client de Terrawaves sur 90 jours (alerte au-dessus de 75 %).

  La page liste aussi ce qui a bougé : nouvelles créances à plus de 30 jours, plus grosses factures, plus gros encaissements.
- **Indicateurs mensuels** : CA HT, marge, charges fixes, résultat estimé, trésorerie et créances à plus de 30 jours en fin de mois, par entité et consolidés.
- **Terrawaves** : part du 1er client avec alerte, heures vendues par fourgon, carburant au km, sous-traitance (montant et part du CA).
- **MGE** : revenu récurrent signé, jours facturés sur jours disponibles, pipeline et taux de conversion.
- **Personnel** : prélèvements, provision fiscale recommandée, cumuls annuels.

## Règles de calcul

- **CA HT** : factures validées, payées ou non, à leur date de facturation. Les brouillons et factures abandonnées sont exclus. Les avoirs sont comptés en négatif. Une facture répétée sur plusieurs lignes d'export n'est comptée qu'une fois.
- **Marge** = CA HT − coûts directs (y compris sous-traitance et carburant pour Terrawaves). **Résultat estimé** = marge − charges fixes.
- **Consolidation** : la facturation entre sociétés du groupe est retirée du CA et des créances consolidés. Les charges `*_intragroupe` saisies sont retirées des coûts. Si les deux montants ne concordent pas, un **écart intragroupe** est signalé.
- **Trésorerie** = soldes initiaux + écritures bancaires jusqu'à la date.
- **Créances à plus de 30 jours** : reste dû TTC (montant TTC − règlements reçus à la date) des factures échues depuis **plus** de 30 jours. Les créances intragroupe sont exclues du consolidé.
- **Provision fiscale** = prélèvement × taux, arrondie au franc, cumulée par année civile.
- Un indicateur dont la saisie manque affiche « à saisir », jamais 0.

## Tests

```bash
python -m pytest -q
```

Les 27 tests couvrent :
- la lecture des exports Dolibarr réels : lignes répétées, avoirs, brouillons, colonnes Débit/Crédit, montant affecté à la facture ;
- l'élimination de l'intragroupe (le résultat consolidé égale la somme des résultats quand l'intragroupe est saisi des deux côtés) ;
- les créances avec règlements partiels et la limite des 30 jours ;
- la trésorerie, les ratios (y compris la division par zéro), la provision et les 5 chiffres du lundi.

## Sauvegarde

Les données sont dans `donnees/` (exports et saisie mensuelle), exclu de Git. Seule la **saisie mensuelle** n'existe nulle part ailleurs : sauvegardez `donnees/saisie_mensuelle.csv` avec vos documents de gestion, par exemple dans le même espace chiffré que les sauvegardes Dolibarr. Les exports, eux, se régénèrent depuis Dolibarr.

## Limites et points de vigilance

- **Provision fiscale** : un taux unique est une approximation. L'impôt calédonien sur le revenu est progressif et des cotisations s'ajoutent selon le statut du dirigeant. Ce taux est une décision à prendre avec l'expert-comptable ; tant qu'il n'est pas fixé, la page l'indique.
- **Prélèvements du dirigeant** : selon leur nature (rémunération, dividendes, compte courant), le traitement fiscal diffère, et la page ne les distingue pas.
- **Marge** : elle dépend de la saisie des coûts directs. Dolibarr n'en exporte pas ici, les factures fournisseurs n'étant pas importées.
- **Encaissements « Lundi »** : ils sont fondés sur les règlements saisis dans Dolibarr. Un encaissement non rapproché d'une facture n'y figure pas.
