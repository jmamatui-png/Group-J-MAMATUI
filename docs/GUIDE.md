# Guide d'installation et d'utilisation de Dolibarr — Groupe J Mamatui

Ce guide s'adresse à une personne qui n'est pas informaticienne. Suivez les étapes dans l'ordre. Les commandes sont à **copier-coller** dans un terminal, une par une.

> **Avant de commencer.** Rien n'est installé tant que vous ne lancez pas vous-même les commandes. Sur un serveur loué (VPS), faites-vous accompagner la première fois si possible.

---

## 0. Ce que vous allez obtenir

- **3 Dolibarr séparés**, un par société : Terrawaves Logistics, MGE Conseil et GROUP J MAMATUI. Chacun a sa propre base de données, ses propres documents et sa propre numérotation de factures.
- **Une adresse sécurisée (HTTPS) par société** :
  - Sur un ordinateur : `https://terrawaves.localhost`, `https://mge.localhost`, `https://holding.localhost`.
  - Sur un serveur : `https://terrawaves.votre-domaine.nc`, etc.
- Une **sauvegarde chiffrée chaque nuit**, copiée hors du serveur.

**Pourquoi 3 Dolibarr et pas un seul « multi-société » ?** Dolibarr ne gère pas plusieurs sociétés d'origine. Il faut acheter un module complémentaire (« Multicompany », vendu sur DoliStore) et le maintenir à chaque mise à jour. Trois installations séparées sont gratuites, plus simples et mieux cloisonnées. Le tableau de bord du groupe fait ensuite la consolidation. Seul inconvénient : un utilisateur qui travaille pour deux sociétés a deux comptes.

---

## 1. Choisir où installer

| | Ordinateur (local) | Serveur loué (VPS) |
|---|---|---|
| Accès | Uniquement depuis cet ordinateur | Depuis partout, via Internet |
| Coût | Gratuit | Abonnement mensuel du serveur + nom de domaine |
| Prérequis | Docker Desktop, 8 Go de RAM | Serveur Ubuntu 24.04, **4 Go de RAM**, 2 processeurs, 40 Go de disque, un nom de domaine |
| Risque principal | Perte ou vol de l'ordinateur → la sauvegarde distante est indispensable | Exposition sur Internet → mots de passe forts, mises à jour |

Pour un essai, commencez sur votre ordinateur.

---

## 2. Installer Docker

**Ordinateur Windows ou Mac** : installez **Docker Desktop** depuis le site officiel de Docker, puis redémarrez. Sous Windows, ouvrez ensuite le terminal « Ubuntu » (WSL) proposé par Docker Desktop. Les scripts fournis fonctionnent sous Linux, macOS et WSL.

**Serveur Ubuntu** : connectez-vous en SSH, puis :

```bash
sudo apt update && sudo apt upgrade -y
```

```bash
sudo apt install -y docker.io docker-compose-v2 gpg openssl ufw unattended-upgrades
```

```bash
sudo usermod -aG docker $USER
```

Déconnectez-vous puis reconnectez-vous. Ensuite, n'ouvrez que les ports nécessaires (SSH, HTTP pour la redirection, HTTPS) :

```bash
sudo ufw allow OpenSSH && sudo ufw allow 80/tcp && sudo ufw allow 443/tcp && sudo ufw enable
```

> **Sécurité serveur** : connectez-vous en SSH par **clé**, pas par mot de passe. Votre hébergeur l'explique dans sa documentation. Les mises à jour de sécurité automatiques sont activées par le paquet `unattended-upgrades`.

**Nom de domaine (VPS uniquement)** : chez votre fournisseur de nom de domaine, créez 3 enregistrements **A** pointant vers l'adresse IP du serveur : `terrawaves`, `mge` et `holding`. Attendez qu'ils soient actifs (de quelques minutes à quelques heures).

---

## 3. Installer Dolibarr

1. Copiez le dossier `groupe-dolibarr` sur l'ordinateur ou le serveur, puis placez-vous dedans :

   ```bash
   cd groupe-dolibarr
   ```

2. Créez la configuration et les mots de passe. Le script pose deux questions : ordinateur ou serveur, et, pour un serveur, le domaine et l'e-mail.

   ```bash
   scripts/initialiser.sh
   ```

3. **Recopiez immédiatement dans votre gestionnaire de mots de passe** (Bitwarden, 1Password, KeePass…) les deux valeurs affichées par cette commande :

   ```bash
   grep -E 'DOLI_ADMIN_PASSWORD|SAUVEGARDE_PHRASE' .env
   ```

   Sans la **phrase de sauvegarde**, aucune sauvegarde ne pourra être relue.

4. Démarrez :

   ```bash
   docker compose up -d
   ```

   La première fois, comptez **5 à 10 minutes** : les 3 bases sont créées et configurées. Pour suivre l'avancement :

   ```bash
   docker compose logs -f terrawaves
   ```

   Quand vous voyez « `[securite] Mot de passe admin re-haché` », c'est prêt. Appuyez sur `Ctrl+C` pour quitter l'affichage, sans arrêter Dolibarr.

5. Ouvrez `https://terrawaves.localhost` (ou `https://terrawaves.votre-domaine.nc`).

   **Sur un ordinateur**, le navigateur affiche un avertissement de certificat. C'est normal : le certificat est créé sur votre machine. Pour ne plus le voir, installez comme « autorité de confiance » le fichier `donnees/caddy/data/caddy/pki/authorities/local/root.crt`. Sinon, cliquez sur « Continuer ». **Sur un serveur**, le certificat est valide automatiquement.

---

## 4. Première connexion et sécurité

1. Connectez-vous avec l'identifiant `admin` et le mot de passe noté à l'étape 3. Recopiez le code de sécurité (captcha) affiché sur la page.
2. **Créez un utilisateur nominatif** pour chaque personne : *Accueil › Utilisateurs & Groupes › Nouvel utilisateur*. N'utilisez pas le compte `admin` au quotidien.
3. Faites la même chose sur les 3 sociétés : ce sont 3 installations distinctes.
4. Mots de passe : au moins 14 caractères, différents pour chaque personne, rangés dans un gestionnaire de mots de passe.

---

## 5. Configurer les 3 sociétés

À faire **dans chacun des 3 Dolibarr**.

### 5.1 Identité de la société

*Accueil › Configuration › Société/Organisation* :
- raison sociale, adresse, code postal, ville (Nouméa) ;
- téléphone, e-mail, logo ;
- forme juridique, capital ;
- dans « Identifiants professionnels », le **RIDET** et le numéro RCS.

Le pays (Nouvelle-Calédonie) et l'option « Assujetti à la TGC » sont déjà réglés.

### 5.2 Devise et arrondis — déjà faits, à contrôler

- *Accueil › Configuration › Société/Organisation*, champ « Devise principale » : **XPF (Franc CFP)**.
- *Accueil › Configuration › Limites et précision* : 0 décimale sur les prix unitaires et sur les totaux.

### 5.3 Taux de TGC — à faire vérifier

*Accueil › Configuration › Dictionnaires › Taux de TVA* (le dictionnaire garde son nom d'origine) : les taux de Nouvelle-Calédonie sont actifs (0, 3, 6, 11 et 22 %), avec la mention « (à vérifier) ».

Le taux de **6 %** est proposé par défaut : c'est celui des **prestations de service**, validé le 17/11/2026. Les autres taux restent disponibles pour les cas particuliers.

> ⚠ Si une société vend aussi des **biens** (cartons, emballages, fournitures refacturées…), le taux n'est pas forcément 6 % : faites-le confirmer par votre expert-comptable et choisissez le taux ligne par ligne.

Les écrans et les PDF affichent « TGC » au lieu de « TVA » pour les libellés principaux. Si un « TVA » subsiste quelque part, corrigez-le dans *Accueil › Configuration › Traduction*.

### 5.4 Compte bancaire

*Banques | Caisses › Nouveau compte financier* : nom (ex. « BCI courant »), banque, IBAN/RIB, devise XPF, et **solde initial** à la date de démarrage. Créez aussi une « Caisse » si vous encaissez en espèces.

### 5.5 Modules

Les modules Tiers, Propositions commerciales, Factures, Projets, Banques et caisses, Exports et Imports sont activés. Pour en ajouter : *Accueil › Configuration › Modules/Applications*.

---

## 6. Sauvegardes automatiques

### 6.1 Programmer la sauvegarde de chaque nuit (2 h 30)

```bash
scripts/installer-sauvegarde-auto.sh
```

Chaque nuit, le script :
- sauvegarde les 3 bases et tous les documents (PDF, pièces jointes) ;
- **chiffre** l'archive (AES-256) avec la phrase de sauvegarde ;
- vérifie que l'archive se relit ;
- la copie hors du serveur ;
- garde 14 jours d'archives sur place et 60 jours à distance (réglable dans `.env`).

Pour lancer une sauvegarde tout de suite :

```bash
scripts/sauvegarde.sh
```

### 6.2 Copie hors du serveur (obligatoire)

Une sauvegarde qui reste sur le même serveur ne protège ni contre une panne, ni contre un piratage, ni contre une erreur de l'hébergeur. Choisissez un espace de stockage **chez un autre fournisseur** que votre serveur : stockage objet type S3, Backblaze B2, un autre serveur en SFTP, un NAS…

Configurez-le une fois, avec l'assistant rclone, en répondant à ses questions. Nommez la destination **`distant`**.

```bash
docker run --rm -it -v "$PWD/rclone:/config/rclone" rclone/rclone:1.71 config
```

Puis indiquez la destination dans `.env`, à la ligne `RCLONE_DESTINATION`. Exemple : `RCLONE_DESTINATION=distant:dolibarr-sauvegardes`. Testez ensuite :

```bash
scripts/sauvegarde.sh
```

La dernière ligne doit indiquer « Copie distante vérifiée ».

> Les archives sont chiffrées avant de partir : le fournisseur de stockage ne peut pas lire vos données. En revanche, **sans la phrase de sauvegarde, vous non plus**.

### 6.3 Vérifier chaque mois

- Consultez le journal :

  ```bash
  tail -20 sauvegardes/sauvegarde.log
  ```

- Une fois par trimestre, faites un **essai de restauration** sur un ordinateur de test (étape 9).

---

## 7. Votre première facture

1. **Créer le client** : *Tiers › Nouveau tiers*. Indiquez le nom, le type « Client » et l'adresse, plus le RIDET s'il s'agit d'une entreprise. Enregistrez.
2. **(Facultatif) Proposition commerciale** : *Commercial › Nouvelle proposition*. Choisissez le client, ajoutez les lignes, puis **Valider** et **Générer** le PDF. Une fois la proposition acceptée, utilisez « Créer facture ».
3. **Nouvelle facture** : *Facturation | Paiement › Nouvelle facture*.
   - Choisissez le client, la date et les conditions de règlement (ex. « 30 jours »).
   - Ajoutez une ligne : description, **taux de TGC**, prix unitaire HT en F CFP (sans décimales), quantité.
   - Vérifiez les totaux HT, TGC et TTC.
4. Cliquez sur **Valider** : la facture reçoit son numéro définitif et ne peut plus être modifiée. Une erreur se corrige ensuite par un **avoir**, jamais par une suppression.
5. **Générer** le PDF, puis **Envoyer par e-mail**. Il faut avoir configuré l'envoi d'e-mails dans *Configuration › E-mails*.
6. À réception du paiement : ouvrez la facture, puis **Saisir règlement**. Indiquez la date, le mode, le compte bancaire et le montant. La facture passe à « Payée » et l'écriture apparaît dans le compte bancaire.

---

## 8. Exports

### 8.1 Export pour l'expert-comptable

*Outils › Exports › Nouvel export* :
1. Choisissez **« Factures clients et lignes de factures »**.
2. Cochez les champs utiles (ou « Tout sélectionner »). Filtrez sur la période, par exemple les dates de facturation du mois.
3. Choisissez le format **CSV** (ou Excel), puis **Générer**, puis téléchargez.

Faites de même avec **« Factures clients et règlements »** et **« Écritures bancaires et relevés »**. Joignez les PDF des factures si votre expert-comptable le demande.

Enregistrez chaque sélection comme **« profil d'export »** : la fois suivante, il suffira de changer les dates.

> Pour un export directement intégrable dans un logiciel comptable (journal, format FEC), il faut activer et paramétrer le module « Comptabilité » (plan comptable, comptes de vente et de TGC). **Faites ce paramétrage avec votre expert-comptable**, car le plan comptable calédonien doit être chargé et vérifié.

### 8.2 Export pour le tableau de bord du groupe

Les mêmes 3 exports, au format CSV et **sans filtre de date** (tout l'historique), sont à déposer pour chaque société dans le dossier du tableau de bord :
- `donnees/terrawaves/factures.csv`, `paiements.csv`, `banque.csv` ;
- idem pour `mge/` et `holding/`.

Voir le README du tableau de bord.

---

## 9. Restaurer une sauvegarde

À utiliser après une erreur grave, une panne ou un changement de serveur.

1. Listez les archives disponibles sur place :

   ```bash
   ls sauvegardes/
   ```

2. Si le serveur est perdu, réinstallez d'abord (étapes 2 et 3) **avec le même fichier `.env`** (ou au moins la même `SAUVEGARDE_PHRASE`), puis rapatriez l'archive. La première commande liste les archives distantes ; la seconde télécharge celle que vous indiquez.

   ```bash
   scripts/recuperer-distante.sh
   ```

   ```bash
   scripts/recuperer-distante.sh dolibarr_2026-11-17_0230.tar.gz.gpg
   ```

3. Restaurez une société (`terrawaves`, `mge` ou `holding`) ou `toutes` :

   ```bash
   scripts/restauration.sh sauvegardes/dolibarr_2026-11-17_0230.tar.gz.gpg terrawaves
   ```

   Tapez `RESTAURER` pour confirmer. Les données de la société sont remplacées par celles de la sauvegarde. Les autres sociétés ne sont pas touchées. Les anciens documents sont conservés dans `donnees/documents/<société>.avant-restauration`.

---

## 10. Mises à jour de Dolibarr

1. Faites une sauvegarde :

   ```bash
   scripts/sauvegarde.sh
   ```

2. Dans `docker-compose.yml`, changez le numéro de version de l'image (ex. `dolibarr/dolibarr:22.0.5` → `22.0.6`). Ne sautez jamais de version majeure : passez de 22 à 23, puis de 23 à 24.
3. Téléchargez la nouvelle version et redémarrez. La base est migrée automatiquement.

   ```bash
   docker compose pull && docker compose up -d
   ```

4. Vérifiez que les 3 sociétés s'ouvrent et que la dernière facture est bien là.

Suivez les annonces de sécurité de Dolibarr et appliquez les versions correctives (le dernier chiffre) dans le mois.

---

## 11. Liste de contrôle sécurité

- [ ] HTTPS partout : le HTTP est redirigé automatiquement, le dossier `/install` est bloqué.
- [ ] Mot de passe `admin` de 24 caractères minimum, conservé dans un gestionnaire, et utilisateurs nominatifs pour le quotidien.
- [ ] La base de données n'est jamais exposée : seul le proxy HTTPS écoute (ports 80 et 443). En mode ordinateur, uniquement sur la machine elle-même.
- [ ] Fichier `.env` lisible par vous seul (créé ainsi par le script), jamais envoyé par e-mail ni mis dans Git.
- [ ] Sauvegarde nocturne chiffrée, copie hors serveur vérifiée, essai de restauration trimestriel.
- [ ] Serveur : connexion SSH par clé, pare-feu actif, mises à jour automatiques.
- [ ] Captcha actif sur la page de connexion.

---

## 12. En cas de problème

| Symptôme | Que faire |
|---|---|
| La page ne s'ouvre pas | Vérifiez que tous les services sont « running » avec `docker compose ps`. Sinon, redémarrez avec `docker compose up -d`. |
| Erreur de certificat sur un serveur | Les enregistrements DNS pointent-ils vers le serveur ? Les ports 80 et 443 sont-ils ouverts ? Consultez `docker compose logs caddy`. |
| Mot de passe admin perdu | Il est dans `.env` (`DOLI_ADMIN_PASSWORD`) **seulement s'il n'a pas été changé** depuis. Sinon, il se réinitialise en ligne de commande : demandez de l'aide. |
| La sauvegarde échoue | Consultez `tail -50 sauvegardes/sauvegarde.log`. Le message indique l'étape en cause. |
| Disque plein | Supprimez de vieilles archives dans `sauvegardes/`, après avoir vérifié qu'elles sont bien sur la copie distante. |
