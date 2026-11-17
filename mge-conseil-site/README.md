# Site vitrine MGE Conseil

Site statique en français et en anglais : Astro 5 et Tailwind 4. Pas de base de données et pas de cookies. Le seul JavaScript sert à envoyer le formulaire de contact.

| Page | Français | Anglais |
|---|---|---|
| Accueil | `/` | `/en/` |
| Offres | `/offres/` | `/en/services/` |
| À propos | `/a-propos/` | `/en/about/` |
| Contact | `/contact/` | `/en/contact/` |
| Mentions légales | `/mentions-legales/` | `/en/legal-notice/` |
| Confidentialité | `/confidentialite/` | `/en/privacy/` |

## Installation

Il faut Node.js 18.20 ou plus récent (22 recommandé).

```bash
npm install
npm run dev        # aperçu local : http://localhost:4321
```

## Utilisation

| Commande | Rôle |
|---|---|
| `npm run build` | génère le site dans `dist/` |
| `npm test` | génère le site, puis lance les contrôles automatiques |
| `npm run a-completer` | liste les emplacements « À compléter » restants (après un build) |
| `npm run preview` | sert le contenu de `dist/` en local |

### Où modifier quoi

- **Coordonnées, mentions légales, WhatsApp, Formspree** : `src/config.ts`. Un champ vide s'affiche sur le site sous la forme « [À compléter : …] ».
- **Textes FR/EN** : `src/i18n/content.ts`. Les deux langues ont la même structure, que TypeScript vérifie.
- **Couleurs** : `src/styles/global.css` (bleu nuit `#0b1f3a`, accent or `#c9a227`).
- **URL du site** (balises canonical, hreflang et sitemap) : variable d'environnement `SITE_URL`, voir `.env.example`.

### Formulaire de contact (Formspree)

1. Créer un compte sur formspree.io (offre gratuite, nombre d'envois par mois limité) puis un formulaire.
2. Reporter son identifiant (la partie après `/f/`) dans `formspreeId` de `src/config.ts`.
3. Faire un envoi de test. Tant que l'identifiant est vide, le bouton d'envoi reste désactivé.

L'envoi se fait sans recharger la page. Un champ piège anti-spam (`_gotcha`) est inclus, ainsi qu'une case de consentement obligatoire.

### Bouton WhatsApp

Renseigner `whatsapp` dans `src/config.ts`, en chiffres uniquement et avec l'indicatif (ex. `687XXXXXX`).

## Contrôles automatiques (`npm test`)

Les tests vérifient :
- la présence des 12 pages ;
- un seul `h1` par page ;
- un title et une description de longueur correcte et uniques ;
- les balises canonical et hreflang ;
- la validité du JSON-LD `ProfessionalService` (Nouméa, NC) ;
- les liens internes, qui ne doivent pas être cassés ;
- **l'absence de tout prix** (XPF, F CFP, €, $) ;
- l'absence de « TVA » ;
- l'absence de bloc d'avis ou de témoignage ;
- les mentions obligatoires des pages légales ;
- le consentement du formulaire.

Un test supplémentaire vérifie que le détecteur de prix fonctionne bien.

## Mise en ligne (à faire avec mon accord, rien n'est déployé)

- **Netlify (recommandé)** : connecter le dépôt. `netlify.toml` est déjà configuré. Définir `SITE_URL` dans les variables d'environnement Netlify.
- **GitHub Pages** : possible, mais seulement avec un domaine personnalisé. Sinon le site est servi depuis un sous-chemin (`/nom-du-depot/`), ce qui demande d'ajouter `base` dans `astro.config.mjs`.

Après la mise en ligne : déclarer le sitemap (`/sitemap-index.xml`) dans Google Search Console et créer la fiche **Google Business Profile** de Nouméa. C'est le premier levier du référencement local, bien avant le site.

## Sauvegarde

- Le code source est la seule chose à sauvegarder : le site se reconstruit entièrement avec `npm run build`.
- Pousser régulièrement sur un dépôt Git distant privé (GitHub, par exemple). Netlify garde aussi l'historique des déploiements, ce qui permet un retour arrière en un clic.
- Les messages reçus ne sont pas stockés sur le site : ils sont chez Formspree et dans votre boîte mail. À sauvegarder ou archiver selon la durée de conservation affichée dans la politique de confidentialité.

## Hypothèses retenues

- Les noms anglais des offres sont des traductions (« CFO Essentials »…), suivies du nom français entre parenthèses.
- Les descriptions des offres sont une **proposition à valider** : le contenu exact de chaque formule n'était pas fourni.
- Aucun nom de dirigeant, aucune date et aucun diplôme n'est affiché tant qu'ils ne sont pas renseignés.
- Aucun outil de statistiques, donc aucun bandeau cookies. En ajouter un obligera à mettre à jour la politique de confidentialité.

## Points de vigilance juridiques — à faire valider

1. **Expertise comptable** : la tenue et la présentation des comptes sont réservées aux experts-comptables inscrits à l'Ordre. Les textes du site parlent de « coordination avec l'expert-comptable » et non de tenue comptable. Garder cette limite dans les contrats.
2. **Dossier de financement** : préparer un dossier est du conseil. En revanche, être rémunéré par une banque ou agir comme intermédiaire dans l'octroi d'un crédit peut relever du statut d'IOBSP (intermédiaire en opérations de banque). Faire vérifier ce point pour la Nouvelle-Calédonie, puis renseigner `statutReglementaire` si un statut s'applique. La phrase « la décision appartient aux financeurs » doit rester sur le site : elle évite toute promesse de résultat.
3. **Défiscalisation** : présentée uniquement comme une expérience du dirigeant. Proposer du conseil en défiscalisation à des investisseurs relèverait d'autres réglementations.
4. **Données personnelles** : le RGPD ne s'applique pas directement en Nouvelle-Calédonie ; c'est la loi n° 78-17 modifiée qui s'applique. La politique a été rédigée sur cette base. **Formspree est américain** : les données partent donc hors de Nouvelle-Calédonie et de l'UE. Vérifier ses conditions (DPA), ou choisir un service hébergé dans l'UE si nécessaire.
5. **Références clients** : ne publier un logo ou une citation qu'avec l'**accord écrit** du client, et le conserver.
6. **Version anglaise** : la version française prévaut (mention présente sur les pages légales).
