#!/bin/bash
# Programme la sauvegarde chaque nuit à 2 h 30 (heure du serveur) dans la crontab de l'utilisateur courant.
set -euo pipefail
cd "$(dirname "$0")/.."
ligne="30 2 * * * cd $PWD && scripts/sauvegarde.sh >> sauvegardes/sauvegarde.log 2>&1"
( crontab -l 2>/dev/null | grep -v 'scripts/sauvegarde.sh' ; echo "$ligne" ) | crontab -
echo "Sauvegarde automatique programmée :"
crontab -l | grep sauvegarde.sh
