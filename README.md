# Dolibarr du groupe — installation Docker

Trois Dolibarr séparés (Terrawaves Logistics, MGE Conseil, GROUP J MAMATUI) avec MariaDB et un reverse proxy Caddy en **HTTPS obligatoire**. La sauvegarde est chiffrée chaque nuit et copiée hors du serveur.

👉 **Guide pas à pas pour un non-informaticien : [docs/GUIDE.md](docs/GUIDE.md)** (installation, création des 3 sociétés, première facture, export comptable, sauvegarde et restauration).

## Démarrage rapide

```bash
scripts/initialiser.sh
```

```bash
docker compose up -d
```

## Contenu

| Élément | Rôle |
|---|---|
| `docker-compose.yml` | MariaDB 11.4, 3 × Dolibarr 22.0.5, Caddy 2.10. Seul Caddy publie des ports (80 → redirection HTTPS, 443). |
| `caddy/Caddyfile` | Un sous-domaine par société, en-têtes de sécurité (HSTS…), `/install` bloqué. Certificat Let's Encrypt (VPS) ou certificat local (ordinateur). |
| `mariadb/init/01-bases.sh` | Une base et un utilisateur MariaDB par société. |
| `dolibarr/init/10-configuration-nc.sh` | XPF sans décimales, français, pays NC, taux TGC 0/3/6/11/22 % (à vérifier), libellés TVA → TGC, captcha de connexion. |
| `dolibarr/init/20-securite.php` | Re-hachage du mot de passe admin en bcrypt (l'image le stocke en MD5). |
| `scripts/initialiser.sh` | Crée `.env` avec des mots de passe aléatoires (24 à 40 caractères), en accès restreint (permissions 600). |
| `scripts/sauvegarde.sh` | Dump des 3 bases + documents, chiffrement GPG AES-256, vérification, copie rclone hors serveur, rotation. |
| `scripts/restauration.sh` | Restaure une société ou toutes, avec confirmation ; les autres sociétés ne sont pas touchées. |
| `scripts/recuperer-distante.sh` | Liste ou rapatrie une archive depuis la copie distante. |
| `scripts/installer-sauvegarde-auto.sh` | Programme la sauvegarde chaque nuit à 2 h 30 (cron). |
| `tests/test-complet.sh` | Test de bout en bout sur une copie jetable (voir ci-dessous). |

## Test de bout en bout

```bash
tests/test-complet.sh
```

Le test travaille sur une copie jetable du projet, sur la machine locale, puis supprime tout. Il vérifie dans l'ordre :

1. les permissions de `.env` et la longueur des mots de passe ;
2. l'installation automatique des 3 sociétés ;
3. le HTTPS sur les 3 sous-domaines, la redirection HTTP → HTTPS, l'en-tête HSTS, le blocage de `/install`, et l'absence de port publié pour MariaDB et Dolibarr ; en mode local, le proxy n'écoute que sur 127.0.0.1 ;
4. pour chaque société : XPF, 0 décimale, français, pays NC, les 5 taux TGC, le libellé TGC, les 6 modules actifs, et le mot de passe admin en bcrypt et reconnu ;
5. la sauvegarde : archive chiffrée et copie distante présente ;
6. la restauration locale après suppression d'un tiers et d'un document : les deux reviennent et les autres sociétés ne sont pas touchées ;
7. la restauration depuis la copie distante après suppression de l'archive locale et d'une table ;
8. le refus d'une mauvaise phrase de chiffrement, sans aucune modification des données.

## Hypothèses retenues — à valider

- **3 instances au lieu du module Multicompany** : ce module est payant (DoliStore) et doit être maintenu à chaque mise à jour. La consolidation est faite par le tableau de bord du groupe.
- **Taux de TGC** : ceux du dictionnaire Dolibarr pour la Nouvelle-Calédonie (0, 3, 6, 11, 22 %), marqués « à vérifier ». À confirmer avec l'expert-comptable, ainsi que le taux à appliquer à chaque prestation.
- **Export comptable** : export CSV des factures, règlements et écritures bancaires. L'export au format logiciel comptable (FEC) demande le module Comptabilité et un plan comptable calédonien, à paramétrer avec l'expert-comptable.
- **Version** : Dolibarr 22.0.5. Les versions 23 et 24 existent ; la 22 a été retenue car c'est celle qui est testée ici. Une montée de version se fait d'une version majeure à la suivante, après sauvegarde (voir le guide, étape 10).

## Sécurité

- Seul Caddy est joignable. En mode ordinateur, il n'écoute que sur 127.0.0.1.
- Rien n'est en clair dans le dépôt : `.env`, `donnees/`, `sauvegardes/` et `rclone/rclone.conf` sont exclus de Git.
- **La phrase de sauvegarde doit être conservée hors du serveur** (gestionnaire de mots de passe). Sans elle, les archives sont illisibles.
