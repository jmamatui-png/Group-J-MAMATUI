#!/bin/bash
# Exécuté une seule fois, à la première installation de chaque société.
# Configuration Nouvelle-Calédonie : XPF sans décimales, français, TGC.
set -uo pipefail
SQL() { mysql -u "${DOLI_DB_USER}" -p"${DOLI_DB_PASSWORD}" -h "${DOLI_DB_HOST}" "${DOLI_DB_NAME}" -e "$1"; }
CONST() {  # nom valeur
  SQL "DELETE FROM llx_const WHERE name='$1' AND entity=1;
       INSERT INTO llx_const(name, value, type, visible, note, entity) VALUES ('$1', '$2', 'chaine', 0, 'Config groupe', 1);"
}
echo "[config-nc] Devise XPF, sans décimales"
CONST MAIN_MONNAIE XPF
CONST MAIN_MAX_DECIMALS_UNIT 0
CONST MAIN_MAX_DECIMALS_TOT 0
CONST MAIN_MAX_DECIMALS_SHOWN 1     # l'écran de Dolibarr refuse 0 ; sans effet puisque les montants sont entiers
echo "[config-nc] Langue française"
CONST MAIN_LANG_DEFAULT fr_FR
echo "[config-nc] Assujetti à la taxe (TGC)"
CONST FACTURE_TVAOPTION 1
echo "[config-nc] Captcha sur la page de connexion"
CONST MAIN_SECURITY_ENABLECAPTCHA 1

echo "[config-nc] Taux de TGC (Nouvelle-Calédonie, pays 165) — à faire vérifier"
SQL "UPDATE llx_c_tva SET note = CONCAT('TGC ', taux, ' % (à vérifier)'), active = 1 WHERE fk_pays = 165;"
SQL "UPDATE llx_c_tva SET note = 'TGC 0 % / exonéré (à vérifier)' WHERE fk_pays = 165 AND taux = 0;"
# Taux validé par le dirigeant le 17/11/2026 : 6 % pour les prestations de service -> taux proposé par défaut.
SQL "UPDATE llx_c_tva SET use_default = 0 WHERE fk_pays = 165;
     UPDATE llx_c_tva SET use_default = 1, note = 'TGC 6 % - prestations de service (validé)' WHERE fk_pays = 165 AND taux = 6;"

echo "[config-nc] Libellés : TVA -> TGC"
for paire in "VAT|TGC" "VATs|TGC" "AmountVAT|Montant TGC" "TotalVAT|Total TGC" "VATRate|Taux TGC" \
             "VATCode|Code taux TGC" "VATIsUsed|Assujetti à la TGC" "VATIsNotUsed|Non assujetti à la TGC"; do
  cle="${paire%%|*}"; val="${paire#*|}"
  SQL "DELETE FROM llx_overwrite_trans WHERE lang='fr_FR' AND transkey='${cle}' AND entity=1;
       INSERT INTO llx_overwrite_trans(lang, transkey, transvalue, entity) VALUES ('fr_FR', '${cle}', '${val}', 1);"
done
echo "[config-nc] Terminé"
