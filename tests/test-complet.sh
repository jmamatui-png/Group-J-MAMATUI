#!/bin/bash
# Test de bout en bout, sur une copie jetable du projet (aucun serveur réel) :
# installation -> contrôles de configuration et de sécurité -> sauvegarde -> perte de données
# -> restauration locale -> restauration depuis la copie distante.
set -euo pipefail
SRC="$(cd "$(dirname "$0")/.." && pwd)"
T=$(mktemp -d /tmp/test-dolibarr.XXXX)
cp -r "$SRC"/{docker-compose.yml,caddy,mariadb,dolibarr,scripts} "$T"/
mkdir -p "$T/rclone"
cd "$T"
export COMPOSE_PROJECT_NAME=testdoli
ok() { echo "  OK  $*"; }
ko() { echo "  ÉCHEC  $*"; exit 1; }
nettoyer() { docker compose down -v --remove-orphans >/dev/null 2>&1 || true; docker run --rm -v "$T:/t" alpine:3.20 rm -rf /t/donnees /t/sauvegardes /t/rclone >/dev/null 2>&1 || true; rm -rf "$T"; }
trap nettoyer EXIT

echo "1. Initialisation (.env, mode ordinateur local)"
echo 1 | scripts/initialiser.sh >/dev/null
[[ $(stat -c %a .env) == 600 ]] && ok ".env en 600" || ko ".env permissions"
sed -i 's|^RCLONE_DESTINATION=.*|RCLONE_DESTINATION=:local:/config/rclone/distant|' .env
set -a; source .env; set +a
[[ ${#DOLI_ADMIN_PASSWORD} -ge 24 ]] && ok "mot de passe admin de ${#DOLI_ADMIN_PASSWORD} caractères" || ko "mdp"

echo "2. Démarrage"
docker compose up -d >/dev/null 2>&1
for s in terrawaves mge holding; do
  for i in $(seq 1 120); do
    docker compose logs "$s" 2>/dev/null | grep -q "\[securite\]" && docker compose exec -T "$s" test -f /var/www/documents/install.lock 2>/dev/null && break
    sleep 3
  done
  docker compose exec -T "$s" test -f /var/www/documents/install.lock && ok "$s installé" || { docker compose logs "$s" | tail -30; ko "$s non installé"; }
done
sleep 5

echo "3. HTTPS et exposition"
for s in terrawaves mge holding; do
  code=$(curl -sk -o /tmp/page.$s -w '%{http_code}' --resolve "$s.localhost:443:127.0.0.1" "https://$s.localhost/")
  [[ "$code" == 200 ]] && grep -qi "dolibarr" /tmp/page.$s && ok "$s : page de connexion en HTTPS" || ko "$s HTTPS ($code)"
done
code=$(curl -s -o /dev/null -w '%{http_code} %{redirect_url}' --resolve "mge.localhost:80:127.0.0.1" "http://mge.localhost/")
[[ "$code" == 308* && "$code" == *https://* ]] && ok "HTTP redirigé vers HTTPS ($code)" || ko "redirection HTTP ($code)"
curl -sk -D - -o /dev/null --resolve "mge.localhost:443:127.0.0.1" https://mge.localhost/ | grep -qi "strict-transport-security" && ok "en-tête HSTS" || ko "HSTS"
code=$(curl -sk -o /dev/null -w '%{http_code}' --resolve "mge.localhost:443:127.0.0.1" "https://mge.localhost/install/index.php")
[[ "$code" == 403 ]] && ok "/install bloqué (403)" || ko "/install accessible ($code)"
publie() { docker inspect "$(docker compose ps -q "$1")" --format '{{range $p, $b := .HostConfig.PortBindings}}{{$p}} {{end}}'; }
for s in mariadb terrawaves mge holding; do [[ -z "$(publie $s)" ]] || ko "$s publie un port : $(publie $s)"; done
ok "MariaDB et Dolibarr ne publient aucun port (accès uniquement via le proxy HTTPS)"
[[ "$(publie caddy | tr " " "\n" | sort | xargs)" == "443/tcp 80/tcp" ]] && ok "seul le proxy publie 80 et 443" || ko "ports du proxy : $(publie caddy)"
docker inspect "$(docker compose ps -q caddy)" --format '{{range $p, $b := .HostConfig.PortBindings}}{{range $b}}{{.HostIp}} {{end}}{{end}}' | grep -qv "0.0.0.0" \
  && ok "mode local : proxy limité à 127.0.0.1" || ko "proxy ouvert sur toutes les interfaces en mode local"

echo "4. Configuration Nouvelle-Calédonie"
q() { docker compose exec -T mariadb sh -c 'exec mariadb -uroot -p"$MARIADB_ROOT_PASSWORD" -N -B "$0" -e "$1"' "dolibarr_$1" "$2"; }
for s in terrawaves mge holding; do
  [[ "$(q $s "SELECT value FROM llx_const WHERE name='MAIN_MONNAIE' AND entity=1")" == XPF ]] || ko "$s devise"
  [[ "$(q $s "SELECT value FROM llx_const WHERE name='MAIN_MAX_DECIMALS_TOT' AND entity=1")" == 0 ]] || ko "$s décimales"
  [[ "$(q $s "SELECT value FROM llx_const WHERE name='MAIN_LANG_DEFAULT' AND entity=1")" == fr_FR ]] || ko "$s langue"
  q $s "SELECT value FROM llx_const WHERE name='MAIN_INFO_SOCIETE_COUNTRY'" | grep -q "NC" || ko "$s pays"
  [[ "$(q $s "SELECT GROUP_CONCAT(CAST(taux AS UNSIGNED) ORDER BY taux) FROM llx_c_tva WHERE fk_pays=165 AND active=1")" == "0,3,6,11,22" ]] || ko "$s taux TGC"
  [[ "$(q $s "SELECT transvalue FROM llx_overwrite_trans WHERE transkey='VAT' AND lang='fr_FR'")" == TGC ]] || ko "$s libellé TGC"
  for m in SOCIETE PROPALE FACTURE PROJET BANQUE EXPORT; do
    [[ "$(q $s "SELECT value FROM llx_const WHERE name='MAIN_MODULE_$m' AND entity=1")" == 1 ]] || ko "$s module $m"
  done
  [[ "$(q $s "SELECT LEFT(pass_crypted,4) FROM llx_user WHERE login='admin'")" == '$2y$' ]] || ko "$s hachage admin"
done
ok "XPF sans décimales, français, pays NC, TGC 0/3/6/11/22 %, modules actifs, mot de passe en bcrypt (3 sociétés)"
docker compose exec -T mge php -r 'chdir("/var/www/html"); require "/var/www/html/master.inc.php"; require_once DOL_DOCUMENT_ROOT."/core/lib/security.lib.php";
  $h=$db->getRow("SELECT pass_crypted FROM llx_user WHERE login=\"admin\"")->pass_crypted;
  exit(dol_verifyHash(getenv("DOLI_ADMIN_PASSWORD"), $h) ? 0 : 1);' && ok "le mot de passe admin est bien reconnu" || ko "mot de passe admin"

echo "5. Sauvegarde"
q terrawaves "INSERT INTO llx_societe(nom, entity, client, datec, status) VALUES ('Client témoin restauration', 1, 1, NOW(), 1)"
echo "piece justificative" | docker compose exec -T terrawaves sh -c 'mkdir -p /var/www/documents/facture/TEST && cat > /var/www/documents/facture/TEST/piece.txt'
scripts/sauvegarde.sh > /tmp/sauvegarde.log 2>&1 || { cat /tmp/sauvegarde.log; ko "sauvegarde"; }
archive=$(ls sauvegardes/dolibarr_*.tar.gz.gpg | tail -1)
ok "archive chiffrée créée : $(basename "$archive")"
! gzip -t "$archive" 2>/dev/null && (gpg --batch --list-packets "$archive" </dev/null 2>&1 || true) | grep -q "AES256" \
  && ok "archive chiffrée (AES, illisible sans la phrase)" || ko "chiffrement"
ls rclone/distant/"$(basename "$archive")" >/dev/null && ok "copie hors serveur présente" || ko "copie distante"

echo "6. Perte de données puis restauration locale"
q terrawaves "DELETE FROM llx_societe WHERE nom='Client témoin restauration'"
docker compose exec -T terrawaves rm -rf /var/www/documents/facture/TEST
q mge "INSERT INTO llx_societe(nom, entity, client, datec, status) VALUES ('Saisie MGE postérieure', 1, 1, NOW(), 1)"
scripts/restauration.sh "$archive" terrawaves --oui >/tmp/restau.log 2>&1 || { cat /tmp/restau.log; ko "restauration"; }
[[ "$(q terrawaves "SELECT COUNT(*) FROM llx_societe WHERE nom='Client témoin restauration'")" == 1 ]] && ok "tiers restauré" || ko "tiers non restauré"
docker compose exec -T terrawaves cat /var/www/documents/facture/TEST/piece.txt | grep -q "piece justificative" && ok "document restauré" || ko "document"
[[ "$(docker compose exec -T terrawaves stat -c %U /var/www/documents/install.lock)" == www-data ]] && ok "propriétaire des documents conservé (www-data)" || ko "propriétaire des documents"
[[ "$(q mge "SELECT COUNT(*) FROM llx_societe WHERE nom='Saisie MGE postérieure'")" == 1 ]] && ok "les autres sociétés ne sont pas touchées" || ko "MGE modifiée à tort"
for i in $(seq 1 40); do
  code=$(curl -sk -o /dev/null -w '%{http_code}' --resolve "terrawaves.localhost:443:127.0.0.1" https://terrawaves.localhost/) ; [[ $code == 200 ]] && break; sleep 3
done
[[ $code == 200 ]] && ok "Terrawaves de nouveau en ligne après restauration" || ko "Terrawaves hors ligne ($code)"
[[ "$(q terrawaves "SELECT value FROM llx_const WHERE name='MAIN_MONNAIE' AND entity=1")" == XPF ]] && ok "configuration conservée" || ko "configuration"

echo "7. Restauration depuis la copie distante (serveur perdu)"
nom=$(basename "$archive"); rm -f "$archive"
scripts/recuperer-distante.sh "$nom" >/dev/null 2>&1 && [[ -f "sauvegardes/$nom" ]] && ok "archive rapatriée" || ko "rapatriement"
q terrawaves "DELETE FROM llx_societe WHERE nom='Client témoin restauration'"
scripts/restauration.sh "sauvegardes/$nom" terrawaves --oui >/tmp/restau2.log 2>&1 || { cat /tmp/restau2.log; ko "restauration distante"; }
[[ "$(q terrawaves "SELECT COUNT(*) FROM llx_societe WHERE nom='Client témoin restauration'")" == 1 ]] \
  && ok "Terrawaves restaurée depuis la copie distante" || ko "restauration distante"

echo "8. Mauvaise phrase de chiffrement refusée"
sed -i 's|^SAUVEGARDE_PHRASE=.*|SAUVEGARDE_PHRASE=mauvaise|' .env
scripts/restauration.sh "sauvegardes/$nom" mge --oui >/dev/null 2>&1 && ko "restauration acceptée avec une mauvaise phrase" || ok "refus avec une mauvaise phrase, aucune donnée touchée"
[[ "$(q mge "SELECT COUNT(*) FROM llx_societe WHERE nom='Saisie MGE postérieure'")" == 1 ]] && ok "MGE intacte" || ko "MGE"

echo
echo "TOUS LES TESTS SONT PASSÉS"
