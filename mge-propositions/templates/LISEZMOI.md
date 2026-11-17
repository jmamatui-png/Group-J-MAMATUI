# Modèles de documents

Les fichiers `*.md.j2` sont des modèles **Jinja2**, écrits dans un Markdown simplifié :

| Syntaxe | Rendu |
|---|---|
| `# Titre`, `## Sous-titre`, `### Section` | titres |
| ligne vide | nouveau paragraphe |
| `- élément` | liste à puces |
| `**texte**` | gras |
| `| a | b |` (lignes consécutives) | tableau, la 1re ligne est l'en-tête |
| `[[saut-de-page]]` | saut de page |

Variables disponibles : `client`, `offre`, `mission`, `montants`, `cabinet`, `conditions`, `numero`, `date_document`.
Filtres : `xpf` (montant), `date_fr`, `pct` (taux), `ac` (affiche « [À compléter] » si vide).

Ne supprimez pas les clauses obligatoires de la lettre de mission : les tests vérifient leur présence.
