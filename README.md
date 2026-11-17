# MGE Conseil — Propositions commerciales et lettres de mission

À partir d'une fiche client YAML, l'outil génère une **proposition commerciale** et une **lettre de mission** en DOCX et en PDF. Le numéro (`MGE-PROP-AAAA-NNN`) est attribué automatiquement. On l'utilise en ligne de commande ou via une petite interface Streamlit.

## Installation

Il faut Python 3.11 ou plus récent.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Ensuite, **compléter `config/mge.yaml`** : dénomination, RIDET, adresse, signataire, pénalités de retard. Tant que ces champs sont vides, les documents affichent « [À compléter] » et l'outil le signale à chaque génération.

## Utilisation

### Ligne de commande

```bash
python -m mge_docs offres                                    # catalogue
python -m mge_docs verifier exemples/client_fictif.yaml      # contrôle + montants, ne génère rien
python -m mge_docs generer exemples/client_fictif.yaml       # DOCX + PDF dans sortie/
python -m mge_docs generer fiche.yaml --format pdf --document lettre-de-mission --taux-tgc 11
```

Code de sortie : `0` OK, `2` fiche invalide (toutes les erreurs sont listées), `1` autre erreur.

### Interface

```bash
streamlit run app_streamlit.py
```

On peut charger une fiche YAML ou saisir les informations directement. Les montants s'affichent en direct ; la génération propose ensuite les fichiers au téléchargement.

### Fiche client

Exemple : `exemples/client_fictif.yaml`. Les champs obligatoires sont `raison_sociale`, `ridet`, `dirigeant`, `secteur`, `chiffre_affaires`, `enjeux`, `offre`, `prix_ht`, `duree` et `date_debut` (format AAAA-MM-JJ). Les champs `qualite_dirigeant` et `adresse` sont facultatifs.

Mettez les fiches réelles dans `clients/`. Ce dossier est exclu de Git.

### Personnaliser

- **Offres et prix** : `config/offres.yaml`.
- **Taux de TGC, délai de paiement, engagement, préavis, confidentialité, modalités de facturation** : `config/mge.yaml`.
- **Textes** : `templates/*.md.j2` (Jinja2 + Markdown simplifié, voir `templates/LISEZMOI.md`).

## Règles de calcul

- Montants en F CFP entiers. TGC = HT × taux, **arrondie au franc** (un demi-franc est arrondi au franc supérieur). TTC = HT + TGC.
- **Offre mensuelle** : la TGC est calculée sur la facture d'un mois, puis multipliée par le nombre de mois. Le total correspond ainsi exactement à la somme des factures.
- **Fourchette** (Dossier de financement) : un prix hors de 250 000 – 500 000 F HT est refusé.
- **Prix fixe** : un prix différent du catalogue est accepté, avec un avertissement (cas d'une remise).
- **Offre mensuelle** : une durée inférieure à l'engagement de 6 mois est refusée.

## Numérotation

Le registre `data/registre.json` conserve le dernier numéro de chaque année et l'historique (date, client, offre, prix). La numérotation repart à 001 au 1er janvier. Un verrou de fichier empêche les doublons. Le modèle est d'abord rendu « à blanc », puis le numéro est attribué : une erreur de fiche ou de modèle ne consomme donc pas de numéro.

## Tests

```bash
python -m pytest -q
```

Les 94 tests couvrent :
- les calculs HT/TGC/TTC (tarifs du catalogue, arrondis, totaux sur plusieurs mois, valeurs invalides) ;
- la numérotation (format, séquence, remise à zéro annuelle, absence de doublon avec 40 générations en parallèle) ;
- le refus de chaque champ obligatoire manquant ;
- les valeurs invalides ;
- la génération de bout en bout, avec la présence des clauses obligatoires et des montants dans les documents.

## Sauvegarde

- **À sauvegarder impérativement :** `data/registre.json`. Le perdre ferait repartir la numérotation à 001 et créerait des doublons. Copiez-le avec `sortie/` sur un stockage sauvegardé (Drive, NAS), au moins une fois par semaine.
- `data/`, `sortie/` et `clients/` contiennent des données clients : ils sont **exclus de Git** et ne doivent pas être poussés dans un dépôt.
- Le code, la configuration et les modèles se versionnent dans Git.

## Hypothèses retenues — à valider

1. **TGC à 6 %** (prestations de service), validé le 17/11/2026. Taux modifiable dans `config/mge.yaml` ou avec `--taux-tgc`.
2. **Durée** : en **mois** pour les offres mensuelles, en **semaines** (délai de remise) pour les forfaits.
3. **Engagement de 6 mois et préavis d'1 mois** : appliqués aux **offres mensuelles uniquement**. Pour un forfait, la mission se termine à la remise des livrables.
4. **Facturation** : mensuelle en début de mois pour les offres mensuelles ; **50 % à la signature et 50 % à la livraison** pour les forfaits (modifiable dans `config/mge.yaml`).
5. **Confidentialité** : pendant la mission, puis **3 ans** après.
6. **RIDET** : 7 chiffres, éventuellement suivis du numéro d'établissement à 3 chiffres (`1234567.001`).
7. Clauses ajoutées par prudence : obligation de moyens, suspension des travaux après une mise en demeure restée sans effet pendant 8 jours, frais hors Grand Nouméa refacturés après accord, juridictions de Nouméa.

## Points de vigilance juridiques

- **Plafond de responsabilité** : il est rédigé « sauf faute lourde ou dolosive », car un plafond qui couvrirait ces cas serait inopérant. Faites relire le modèle par un avocat calédonien avant le premier envoi.
- **Pénalités de retard** : le champ est laissé vide volontairement. Le taux et l'éventuelle indemnité forfaitaire applicables en Nouvelle-Calédonie sont à faire valider.
- **Dossier de financement** : la lettre précise que le Cabinet n'accorde pas de financement et ne garantit pas son obtention. Si MGE est un jour rémunéré par un établissement prêteur, le statut d'intermédiaire en opérations de banque (IOBSP) devra être vérifié.
- **Périmètre** : l'exclusion de la tenue comptable et des comptes annuels est imposée par le modèle et vérifiée par les tests. Ne pas la supprimer.
