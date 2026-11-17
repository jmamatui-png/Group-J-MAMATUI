#!/bin/bash
# Restaure une sauvegarde : bases + documents, pour une société ou toutes.
# Usage : scripts/restauration.sh sauvegardes/dolibarr_AAAA-MM-JJ_HHMM.tar.gz.gpg [terrawaves|mge|holding|toutes] [--oui]
# Une archive distante se récupère d'abord avec : scripts/recuperer-distante.sh
set -euo pipefail
cd "$(dirname "$0")/.."
set -a; source .env; set +a

archive="${1:?Indiquez le fichier de sauvegarde à restaurer}"
cible="${2:-toutes}"
confirmer="${3:-}"
[[ -f "$archive" ]] || { echo "Fichier introuvable : $archive"; exit 1; }
case "$cible" in terrawaves|mge|holding) societes=("$cible");; toutes) societes=(terrawaves mge holding);;
  *) echo "Société inconnue : $cible"; exit 1;; esac

echo "Vous allez REMPLACER les données actuelles de : ${societes[*]}"
echo "par celles de la sauvegarde : $(basename "$archive")"
if [[ "$confirmer" != "--oui" ]]; then
  read -rp "Tapez RESTAURER pour confirmer : " rep
  [[ "$rep" == "RESTAURER" ]] || { echo "Annulé."; exit 1; }
fi

tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
gpg --batch --pinentry-mode loopback --passphrase-fd 3 -d "$archive" 3<<<"$SAUVEGARDE_PHRASE" 2>/dev/null | tar -C "$tmp" -xzf - \
  || { echo "Impossible de déchiffrer l'archive (phrase de chiffrement incorrecte ?)"; exit 1; }

docker compose up -d mariadb
docker compose exec -T mariadb sh -c 'until healthcheck.sh --connect --innodb_initialized; do sleep 2; done'
for societe in "${societes[@]}"; do
  [[ -f "$tmp/bases/${societe}.sql" ]] || { echo "Pas de base ${societe} dans l'archive"; exit 1; }
  echo "Restauration ${societe}…"
  docker compose stop "$societe"
  docker compose exec -T mariadb sh -c 'exec mariadb -uroot -p"$MARIADB_ROOT_PASSWORD" "$@"' -- -e "DROP DATABASE IF EXISTS dolibarr_${societe};"
  docker compose exec -T mariadb sh -c 'exec mariadb -uroot -p"$MARIADB_ROOT_PASSWORD" "$@"' -- < "$tmp/bases/${societe}.sql"
  docker compose exec -T mariadb sh -c 'exec mariadb -uroot -p"$MARIADB_ROOT_PASSWORD" "$@"' -- -e \
    "GRANT ALL PRIVILEGES ON dolibarr_${societe}.* TO '${societe}'@'%'; FLUSH PRIVILEGES;"
  # Depuis un conteneur, pour conserver propriétaires et droits (www-data) des documents.
  docker run --rm -v "$PWD/donnees/documents:/d" -v "$tmp/documents:/a:ro" alpine:3.20 sh -c \
    'rm -rf "/d/$0.avant-restauration"; if [ -d "/d/$0" ]; then mv "/d/$0" "/d/$0.avant-restauration"; fi; tar -C /d -xpf "/a/$0.tar"' "$societe"
  docker compose up -d "$societe"
  echo "  ${societe} restaurée (anciens documents conservés dans donnees/documents/${societe}.avant-restauration)."
done
echo "Restauration terminée. Vérifiez dans Dolibarr, puis supprimez les dossiers *.avant-restauration."
