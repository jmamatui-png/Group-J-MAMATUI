#!/bin/bash
# Exécuté une seule fois, à la création de la base : une base et un utilisateur par société.
set -euo pipefail
for societe in terrawaves mge holding; do
  var="DB_PASSWORD_${societe^^}"
  mdp="${!var}"
  mariadb -uroot -p"${MARIADB_ROOT_PASSWORD}" <<SQL
CREATE DATABASE IF NOT EXISTS dolibarr_${societe} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS '${societe}'@'%' IDENTIFIED BY '${mdp}';
GRANT ALL PRIVILEGES ON dolibarr_${societe}.* TO '${societe}'@'%';
SQL
done
mariadb -uroot -p"${MARIADB_ROOT_PASSWORD}" -e "FLUSH PRIVILEGES;"
