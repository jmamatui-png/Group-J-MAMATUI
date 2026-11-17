#!/bin/bash
# Sauvegarde des 3 bases et des documents, chiffrée (GPG AES-256), puis copie hors du serveur (rclone).
# Usage : scripts/sauvegarde.sh        (lancé chaque nuit par la tâche planifiée)
set -euo pipefail
cd "$(dirname "$0")/.."
set -a; source .env; set +a
: "${SAUVEGARDE_PHRASE:?SAUVEGARDE_PHRASE manquante dans .env}"

horodatage=$(date +%Y-%m-%d_%H%M)
dossier="sauvegardes"
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
mkdir -p "$dossier" "$tmp/bases" "$tmp/documents"
log() { echo "$(date '+%F %T') $*"; }

for societe in terrawaves mge holding; do
  log "Base ${societe}…"
  docker compose exec -T mariadb sh -c 'exec mariadb-dump -uroot -p"$MARIADB_ROOT_PASSWORD" --single-transaction --routines --triggers --databases "$0"' \
    "dolibarr_${societe}" > "$tmp/bases/${societe}.sql"
  # Contrôle : un dump complet se termine par « Dump completed »
  tail -n 1 "$tmp/bases/${societe}.sql" | grep -q "Dump completed" || { log "ERREUR : dump ${societe} incomplet"; exit 1; }
  log "Documents ${societe}…"
  # Archivage depuis un conteneur : les documents appartiennent à l'utilisateur du serveur web (www-data).
  docker run --rm -v "$PWD/donnees/documents:/d:ro" alpine:3.20 tar -C /d -cf - "${societe}" > "$tmp/documents/${societe}.tar"
done
cp docker-compose.yml "$tmp/"

archive="${dossier}/dolibarr_${horodatage}.tar.gz.gpg"
tar -C "$tmp" -czf - bases documents docker-compose.yml \
  | gpg --batch --yes --pinentry-mode loopback --passphrase-fd 3 --symmetric --cipher-algo AES256 -o "$archive" 3<<<"$SAUVEGARDE_PHRASE"
chmod 600 "$archive"
# Vérification : l'archive se déchiffre et se lit
gpg --batch --pinentry-mode loopback --passphrase-fd 3 -d "$archive" 3<<<"$SAUVEGARDE_PHRASE" 2>/dev/null | tar -tzf - >/dev/null \
  || { log "ERREUR : archive illisible"; exit 1; }
log "Archive vérifiée : $archive ($(du -h "$archive" | cut -f1))"

find "$dossier" -name 'dolibarr_*.tar.gz.gpg' -mtime "+${SAUVEGARDE_JOURS_LOCAL:-14}" -delete

if [[ -n "${RCLONE_DESTINATION:-}" ]]; then
  log "Copie hors serveur vers ${RCLONE_DESTINATION}…"
  rclone() { docker run --rm -v "$PWD/rclone:/config/rclone" -v "$PWD/$dossier:/data:ro" rclone/rclone:1.71 "$@"; }
  rclone copy "/data/$(basename "$archive")" "$RCLONE_DESTINATION" --config /config/rclone/rclone.conf
  rclone check "/data" "$RCLONE_DESTINATION" --one-way --include "$(basename "$archive")" --config /config/rclone/rclone.conf
  docker run --rm -v "$PWD/rclone:/config/rclone" rclone/rclone:1.71 delete "$RCLONE_DESTINATION" \
    --min-age "${SAUVEGARDE_JOURS_DISTANT:-60}d" --include 'dolibarr_*.tar.gz.gpg' --config /config/rclone/rclone.conf
  log "Copie distante vérifiée."
else
  log "ATTENTION : aucune copie hors serveur (RCLONE_DESTINATION vide)."
fi
log "Sauvegarde terminée."
