# Groupe J Mamatui — outils internes

Dépôt privé des outils du groupe (Terrawaves Logistics, MGE Conseil, GROUP J MAMATUI). Chaque dossier est un projet indépendant, avec son propre README en français : installation, utilisation, sauvegarde.

| Dossier | Contenu | Tests |
|---|---|---|
| [`mge-conseil-site/`](mge-conseil-site/) | Site vitrine MGE Conseil (Astro + Tailwind), FR/EN, pages légales | `npm test` |
| [`mge-propositions/`](mge-propositions/) | Propositions commerciales et lettres de mission MGE (DOCX/PDF, CLI + Streamlit) | `python -m pytest` |
| [`mge-tresorerie/`](mge-tresorerie/) | Prévision de trésorerie à 13 semaines pour les PME clientes (Streamlit, PDF/XLSX) | `python -m pytest` |
| [`groupe-dolibarr/`](groupe-dolibarr/) | Installation Dolibarr 3 sociétés (Docker, HTTPS, XPF, TGC), sauvegarde et restauration — **guide : `docs/GUIDE.md`** | `tests/test-complet.sh` |
| [`groupe-tableau-de-bord/`](groupe-tableau-de-bord/) | Tableau de bord consolidé du groupe à partir des exports Dolibarr (Streamlit) | `python -m pytest` |

## Règles du dépôt

- **Aucune donnée client réelle ni aucun secret** : les fichiers `.env`, les dossiers de données (`donnees/`, `donnees_clients/`, `data/`, `clients/`, `sortie/`, `sauvegardes/`) et la configuration rclone sont exclus par les `.gitignore` de chaque projet. Les données présentes sont **fictives**.
- Montants en F CFP (XPF), sans décimales. Taxe : **TGC**, 6 % par défaut pour les prestations de service (validé le 17/11/2026).
