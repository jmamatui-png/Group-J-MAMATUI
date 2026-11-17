#!/bin/bash
# Liste ou rapatrie une sauvegarde depuis la copie hors serveur.
# Usage : scripts/recuperer-distante.sh            -> liste
#         scripts/recuperer-distante.sh NOM_FICHIER  -> télécharge dans sauvegardes/
set -euo pipefail
cd "$(dirname "$0")/.."
set -a; source .env; set +a
: "${RCLONE_DESTINATION:?RCLONE_DESTINATION vide dans .env}"
r() { docker run --rm -v "$PWD/rclone:/config/rclone" -v "$PWD/sauvegardes:/data" rclone/rclone:1.71 "$@" --config /config/rclone/rclone.conf; }
if [[ -z "${1:-}" ]]; then r lsl "$RCLONE_DESTINATION"; else r copy "$RCLONE_DESTINATION/$1" /data; echo "Récupéré : sauvegardes/$1"; fi
