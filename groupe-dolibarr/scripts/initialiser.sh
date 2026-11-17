#!/bin/bash
# Crée le fichier .env avec des mots de passe forts. Ne remplace jamais un .env existant.
set -euo pipefail
cd "$(dirname "$0")/.."
if [[ -f .env ]]; then
  echo "Le fichier .env existe déjà : rien n'est modifié."; exit 0
fi
alea() { openssl rand -base64 48 | tr -dc 'A-Za-z0-9' | head -c "$1"; }

echo "Installation sur : 1) cet ordinateur (accès local uniquement)   2) un serveur VPS avec nom de domaine"
read -rp "Votre choix [1/2] : " choix
if [[ "$choix" == "2" ]]; then
  read -rp "Nom de domaine (ex. mon-groupe.nc) : " domaine
  read -rp "E-mail pour le certificat HTTPS (Let's Encrypt) : " email
  [[ "$domaine" =~ ^[a-z0-9.-]+\.[a-z]{2,}$ ]] || { echo "Nom de domaine invalide."; exit 1; }
  [[ "$email" == *@*.* ]] || { echo "E-mail invalide."; exit 1; }
  tls="$email"; ecoute="0.0.0.0"
else
  domaine="localhost"; tls="internal"; ecoute="127.0.0.1"
fi

umask 077
cat > .env <<ENV
DOMAINE=${domaine}
CADDY_TLS=${tls}
ADRESSE_ECOUTE=${ecoute}
DOLI_ADMIN_LOGIN=admin
DOLI_ADMIN_PASSWORD=$(alea 24)
MARIADB_ROOT_PASSWORD=$(alea 32)
DB_PASSWORD_TERRAWAVES=$(alea 32)
DB_PASSWORD_MGE=$(alea 32)
DB_PASSWORD_HOLDING=$(alea 32)
UNIQUE_ID_TERRAWAVES=$(alea 32)
UNIQUE_ID_MGE=$(alea 32)
UNIQUE_ID_HOLDING=$(alea 32)
SAUVEGARDE_PHRASE=$(alea 40)
SAUVEGARDE_JOURS_LOCAL=14
SAUVEGARDE_JOURS_DISTANT=60
RCLONE_DESTINATION=
ENV
chmod 600 .env
mkdir -p donnees/documents/{terrawaves,mge,holding} donnees/custom/{terrawaves,mge,holding} sauvegardes
echo
echo "Fichier .env créé (lisible par vous seul)."
echo "IMPORTANT : recopiez maintenant dans votre gestionnaire de mots de passe :"
echo "  - le mot de passe administrateur Dolibarr (DOLI_ADMIN_PASSWORD)"
echo "  - la phrase de chiffrement des sauvegardes (SAUVEGARDE_PHRASE)"
echo "Commande pour les afficher :  grep -E 'DOLI_ADMIN_PASSWORD|SAUVEGARDE_PHRASE' .env"
