/**
 * Textes du site, en français (référence) et en anglais.
 * Règles : aucun prix, aucun chiffre non vérifié, aucun témoignage ni logo client inventé.
 */
import type { Lang } from './routes';

const fr = {
  ui: {
    todo: 'À compléter',
    skip: 'Aller au contenu',
    menu: 'Menu',
    nav: { home: 'Accueil', offers: 'Offres', about: 'À propos', contact: 'Contact' },
    switchLang: 'English',
    switchLangLabel: 'Read this page in English',
    ctaPrimary: 'Prendre rendez-vous',
    ctaOffers: 'Découvrir les offres',
    footerTagline: 'Direction financière à temps partagé pour les PME de Nouvelle-Calédonie.',
    legal: 'Mentions légales',
    privacy: 'Confidentialité',
    rights: 'Tous droits réservés.',
  },
  home: {
    title: 'MGE Conseil — Direction financière à temps partagé à Nouméa',
    description:
      'MGE Conseil accompagne les PME de Nouméa et de Nouvelle-Calédonie : DAF à temps partagé, pilotage de trésorerie, budget et dossiers de financement bancaire.',
    eyebrow: 'Nouméa · Nouvelle-Calédonie',
    h1: 'Votre direction financière à temps partagé',
    lead:
      'Les compétences d’un directeur administratif et financier, au rythme et à la mesure de votre entreprise. Pour décider avec des chiffres fiables, anticiper votre trésorerie et préparer vos projets de financement.',
    forWhoTitle: 'Pour qui ?',
    forWho: [
      'Dirigeants de PME et d’ETI calédoniennes qui n’ont pas encore de DAF à temps plein.',
      'Entreprises en croissance qui préparent un investissement, une levée de fonds ou un financement bancaire.',
      'Sociétés qui veulent un regard extérieur sur leur rentabilité, leur trésorerie et leur organisation financière.',
    ],
    pillarsTitle: 'Ce que nous prenons en charge',
    pillars: [
      { t: 'Piloter', d: 'Tableaux de bord, indicateurs clés et reporting adaptés à vos décisions.' },
      { t: 'Anticiper', d: 'Budget, prévisionnel de trésorerie et scénarios pour éviter les mauvaises surprises.' },
      { t: 'Financer', d: 'Business plan, dossiers bancaires et dialogue avec vos partenaires financiers.' },
      { t: 'Structurer', d: 'Procédures, outils et coordination avec votre expert-comptable.' },
    ],
    methodTitle: 'Notre méthode',
    method: [
      { t: 'Échange initial', d: 'Comprendre votre activité, vos enjeux et vos priorités.' },
      { t: 'Diagnostic', d: 'Un état des lieux clair de votre situation financière.' },
      { t: 'Plan d’action', d: 'Des recommandations hiérarchisées et réalistes.' },
      { t: 'Accompagnement', d: 'Une présence régulière pour mettre en œuvre et suivre les résultats.' },
    ],
    refsTitle: 'Ils nous font confiance',
    refsTodo: 'références clients réelles, avec leur accord écrit (logos ou citations)',
    ctaTitle: 'Parlons de votre entreprise',
    ctaText: 'Un premier échange pour comprendre vos besoins et voir si notre accompagnement vous correspond.',
  },
  offers: {
    title: 'Offres — DAF à temps partagé et dossiers de financement | MGE Conseil',
    description:
      'Diagnostic flash 360, DAF Essentiel, DAF Pilotage, DAF Croissance et dossier de financement : les offres de MGE Conseil pour les entreprises de Nouvelle-Calédonie.',
    h1: 'Nos offres',
    lead:
      'Des formules modulables selon la taille de votre entreprise et vos enjeux. Les tarifs sont établis sur devis, après un premier échange.',
    deliverables: 'Ce qui est inclus',
    forWho: 'Pour qui',
    rhythm: 'Rythme d’intervention',
    rhythmTodo: 'fréquence / volume d’intervention',
    quote: 'Demander un devis',
    items: [
      {
        id: 'diagnostic-flash-360',
        name: 'Diagnostic flash 360',
        pitch: 'Un état des lieux complet et rapide de la santé financière de votre entreprise.',
        forWho: 'Dirigeants qui veulent un regard extérieur avant de prendre une décision importante.',
        items: [
          'Analyse de la rentabilité, de la trésorerie et du besoin en fonds de roulement',
          'Lecture de la structure financière et de l’endettement',
          'Revue de l’organisation administrative et financière',
          'Rapport de synthèse et plan d’action priorisé',
        ],
      },
      {
        id: 'daf-essentiel',
        name: 'DAF Essentiel',
        pitch: 'Les fondamentaux du pilotage financier, pour garder le cap au quotidien.',
        forWho: 'Petites entreprises qui souhaitent structurer leur suivi financier.',
        items: [
          'Tableau de bord mensuel des indicateurs clés',
          'Suivi de la trésorerie',
          'Coordination avec l’expert-comptable',
          'Point régulier avec le dirigeant',
        ],
      },
      {
        id: 'daf-pilotage',
        name: 'DAF Pilotage',
        pitch: 'Un pilotage complet : budget, prévisions et reporting pour décider en confiance.',
        forWho: 'PME qui ont besoin d’anticiper et de suivre leurs performances de près.',
        items: [
          'Tout le contenu de DAF Essentiel',
          'Construction et suivi du budget annuel',
          'Prévisionnel de trésorerie glissant',
          'Reporting de gestion et analyse des écarts',
          'Mise en place ou amélioration des procédures',
        ],
      },
      {
        id: 'daf-croissance',
        name: 'DAF Croissance',
        pitch: 'Un partenaire financier impliqué pour accompagner vos projets de développement.',
        forWho: 'Entreprises en croissance, en investissement ou en restructuration.',
        items: [
          'Tout le contenu de DAF Pilotage',
          'Business plan et modélisation financière',
          'Préparation et suivi des relations bancaires',
          'Accompagnement des projets d’investissement et de structuration',
          'Présence aux réunions stratégiques',
        ],
      },
      {
        id: 'dossier-de-financement',
        name: 'Dossier de financement',
        pitch: 'Un dossier solide et argumenté pour présenter votre projet à vos financeurs.',
        forWho: 'Projets de création, de reprise, d’investissement ou de renforcement de trésorerie.',
        items: [
          'Analyse du besoin et du plan de financement',
          'Comptes prévisionnels et plan de trésorerie',
          'Rédaction du dossier de présentation',
          'Préparation des rendez-vous avec les partenaires financiers',
        ],
      },
    ],
    disclaimer:
      'MGE Conseil prépare et présente votre dossier : la décision d’accorder un financement appartient exclusivement aux établissements et organismes sollicités.',
  },
  about: {
    title: 'À propos — MGE Conseil, conseil financier à Nouméa',
    description:
      'MGE Conseil : un parcours en comptabilité, en défiscalisation et en agence bancaire au service des dirigeants d’entreprise en Nouvelle-Calédonie.',
    h1: 'À propos',
    lead:
      'MGE Conseil est né d’une conviction : les PME calédoniennes méritent le même niveau de pilotage financier que les grandes entreprises, sans en supporter le coût fixe.',
    founderTitle: 'Le fondateur',
    photoTodo: 'photo du dirigeant',
    pathTitle: 'Un parcours à 360° de la finance d’entreprise',
    path: [
      {
        t: 'Comptabilité',
        d: 'La maîtrise des comptes, de la clôture et des obligations déclaratives : la base de toute analyse financière fiable.',
      },
      {
        t: 'Défiscalisation',
        d: 'La connaissance des dispositifs d’aide à l’investissement et de leurs contraintes, au service de projets bien montés.',
      },
      {
        t: 'Second d’agence bancaire',
        d: 'Le point de vue du banquier : comment un dossier est analysé, ce qui rassure et ce qui bloque une décision de crédit.',
      },
    ],
    pathTodo: 'années, établissements et diplômes (informations vérifiées uniquement)',
    valuesTitle: 'Nos engagements',
    values: [
      { t: 'Indépendance', d: 'Des recommandations dans l’intérêt de votre entreprise uniquement.' },
      { t: 'Confidentialité', d: 'Vos informations restent strictement confidentielles.' },
      { t: 'Clarté', d: 'Des chiffres expliqués simplement, pour décider en connaissance de cause.' },
      { t: 'Proximité', d: 'Une présence locale, à Nouméa, au plus près de vos équipes.' },
    ],
  },
  contact: {
    title: 'Contact — MGE Conseil, Nouméa',
    description:
      'Contactez MGE Conseil à Nouméa pour un premier échange sur la gestion financière de votre entreprise : formulaire en ligne ou WhatsApp.',
    h1: 'Contact',
    lead: 'Décrivez-nous brièvement votre besoin : nous revenons vers vous rapidement.',
    form: {
      name: 'Nom et prénom',
      company: 'Entreprise',
      email: 'E-mail',
      phone: 'Téléphone (facultatif)',
      subject: 'Objet de votre demande',
      subjectOther: 'Autre demande',
      message: 'Votre message',
      consent:
        'J’accepte que mes données soient utilisées pour répondre à ma demande, conformément à la politique de confidentialité.',
      privacyLink: 'Lire la politique de confidentialité',
      submit: 'Envoyer',
      sending: 'Envoi en cours…',
      success: 'Merci, votre message a bien été envoyé. Nous vous répondons rapidement.',
      error: 'L’envoi a échoué. Merci de réessayer ou de nous contacter via WhatsApp.',
      notConfigured: 'identifiant Formspree dans src/config.ts — le formulaire est désactivé tant qu’il est vide',
      required: 'Champ obligatoire',
    },
    whatsappTitle: 'Plutôt WhatsApp ?',
    whatsappText: 'Écrivez-nous directement, nous répondons aux heures ouvrées.',
    whatsappBtn: 'Écrire sur WhatsApp',
    whatsappMsg: 'Bonjour, je souhaite échanger avec MGE Conseil au sujet de mon entreprise.',
    whatsappTodo: 'numéro WhatsApp',
    detailsTitle: 'Coordonnées',
    address: 'Adresse',
    email: 'E-mail',
    phone: 'Téléphone',
    hoursTitle: 'Horaires',
    hoursTodo: 'horaires d’ouverture',
  },
  legal: {
    title: 'Mentions légales | MGE Conseil',
    description: 'Mentions légales du site de MGE Conseil, cabinet de conseil financier aux entreprises à Nouméa, Nouvelle-Calédonie.',
    h1: 'Mentions légales',
  },
  privacy: {
    title: 'Politique de confidentialité | MGE Conseil',
    description: 'Politique de confidentialité et de protection des données personnelles du site de MGE Conseil.',
    h1: 'Politique de confidentialité',
  },
};

export type Content = typeof fr;

const en: Content = {
  ui: {
    todo: 'To be completed',
    skip: 'Skip to content',
    menu: 'Menu',
    nav: { home: 'Home', offers: 'Services', about: 'About', contact: 'Contact' },
    switchLang: 'Français',
    switchLangLabel: 'Lire cette page en français',
    ctaPrimary: 'Book a meeting',
    ctaOffers: 'See our services',
    footerTagline: 'Fractional finance leadership for businesses in New Caledonia.',
    legal: 'Legal notice',
    privacy: 'Privacy',
    rights: 'All rights reserved.',
  },
  home: {
    title: 'MGE Conseil — Fractional CFO services in Nouméa, New Caledonia',
    description:
      'MGE Conseil supports small and mid-sized businesses in Nouméa and New Caledonia: fractional CFO, cash-flow management, budgeting and bank financing applications.',
    eyebrow: 'Nouméa · New Caledonia',
    h1: 'Your fractional finance director',
    lead:
      'The expertise of a chief financial officer, sized and paced for your business. Make decisions on reliable numbers, anticipate your cash position and prepare your financing projects.',
    forWhoTitle: 'Who we work with',
    forWho: [
      'Owners of New Caledonian SMEs who do not yet have a full-time CFO.',
      'Growing companies preparing an investment, an equity raise or a bank loan.',
      'Businesses looking for an outside view of their profitability, cash flow and finance organisation.',
    ],
    pillarsTitle: 'What we take on',
    pillars: [
      { t: 'Steer', d: 'Dashboards, key indicators and reporting built around your decisions.' },
      { t: 'Anticipate', d: 'Budgets, cash-flow forecasts and scenarios to avoid surprises.' },
      { t: 'Finance', d: 'Business plans, bank applications and dialogue with your financial partners.' },
      { t: 'Structure', d: 'Processes, tools and coordination with your chartered accountant.' },
    ],
    methodTitle: 'How we work',
    method: [
      { t: 'First conversation', d: 'Understanding your business, your challenges and your priorities.' },
      { t: 'Assessment', d: 'A clear picture of your financial position.' },
      { t: 'Action plan', d: 'Prioritised, realistic recommendations.' },
      { t: 'Ongoing support', d: 'A regular presence to implement and track results.' },
    ],
    refsTitle: 'They trust us',
    refsTodo: 'genuine client references, with their written consent (logos or quotes)',
    ctaTitle: 'Let’s talk about your business',
    ctaText: 'A first conversation to understand your needs and see whether we are the right fit.',
  },
  offers: {
    title: 'Services — Fractional CFO and financing applications | MGE Conseil',
    description:
      '360 Quick Assessment, CFO Essentials, CFO Performance, CFO Growth and financing applications: MGE Conseil services for businesses in New Caledonia.',
    h1: 'Our services',
    lead: 'Flexible packages tailored to the size of your business and its challenges. Fees are quoted after a first conversation.',
    deliverables: 'What is included',
    forWho: 'Best suited for',
    rhythm: 'Engagement rhythm',
    rhythmTodo: 'frequency / volume of work',
    quote: 'Request a quote',
    items: [
      {
        id: 'diagnostic-flash-360',
        name: '360 Quick Assessment (Diagnostic flash 360)',
        pitch: 'A fast, complete review of your company’s financial health.',
        forWho: 'Business owners who want an outside view before a major decision.',
        items: [
          'Analysis of profitability, cash flow and working capital',
          'Review of financial structure and debt',
          'Review of the administrative and finance organisation',
          'Summary report and prioritised action plan',
        ],
      },
      {
        id: 'daf-essentiel',
        name: 'CFO Essentials (DAF Essentiel)',
        pitch: 'The fundamentals of financial management, to stay on course day to day.',
        forWho: 'Small businesses that want to structure their financial monitoring.',
        items: [
          'Monthly dashboard of key indicators',
          'Cash monitoring',
          'Coordination with your chartered accountant',
          'Regular review meeting with the owner',
        ],
      },
      {
        id: 'daf-pilotage',
        name: 'CFO Performance (DAF Pilotage)',
        pitch: 'Full financial steering: budget, forecasts and reporting to decide with confidence.',
        forWho: 'SMEs that need to anticipate and closely track performance.',
        items: [
          'Everything in CFO Essentials',
          'Annual budget preparation and tracking',
          'Rolling cash-flow forecast',
          'Management reporting and variance analysis',
          'Setting up or improving finance processes',
        ],
      },
      {
        id: 'daf-croissance',
        name: 'CFO Growth (DAF Croissance)',
        pitch: 'A committed finance partner to support your development projects.',
        forWho: 'Companies that are growing, investing or restructuring.',
        items: [
          'Everything in CFO Performance',
          'Business plan and financial modelling',
          'Preparation and follow-up of banking relationships',
          'Support for investment and restructuring projects',
          'Attendance at strategic meetings',
        ],
      },
      {
        id: 'dossier-de-financement',
        name: 'Financing application (Dossier de financement)',
        pitch: 'A solid, well-argued file to present your project to funders.',
        forWho: 'Start-up, acquisition, investment or working-capital projects.',
        items: [
          'Analysis of the need and the financing plan',
          'Forecast financial statements and cash-flow plan',
          'Drafting of the presentation file',
          'Preparation of meetings with financial partners',
        ],
      },
    ],
    disclaimer:
      'MGE Conseil prepares and presents your application: the decision to grant financing rests solely with the institutions approached.',
  },
  about: {
    title: 'About — MGE Conseil, financial advisory in Nouméa',
    description:
      'MGE Conseil: a background in accounting, tax-incentive investment schemes and retail banking, serving business owners in New Caledonia.',
    h1: 'About us',
    lead:
      'MGE Conseil was founded on a simple belief: New Caledonian SMEs deserve the same quality of financial management as large companies, without the fixed cost.',
    founderTitle: 'The founder',
    photoTodo: 'founder photo',
    pathTitle: 'A 360° background in corporate finance',
    path: [
      {
        t: 'Accounting',
        d: 'Command of accounts, year-end closing and reporting obligations: the foundation of any reliable financial analysis.',
      },
      {
        t: 'Tax-incentive investment schemes',
        d: 'Knowledge of investment support schemes and their constraints, in service of well-structured projects.',
      },
      {
        t: 'Deputy bank branch manager',
        d: 'The banker’s perspective: how an application is assessed, what reassures and what blocks a credit decision.',
      },
    ],
    pathTodo: 'years, institutions and qualifications (verified information only)',
    valuesTitle: 'Our commitments',
    values: [
      { t: 'Independence', d: 'Recommendations made solely in your company’s interest.' },
      { t: 'Confidentiality', d: 'Your information remains strictly confidential.' },
      { t: 'Clarity', d: 'Numbers explained simply, so you can decide with full knowledge.' },
      { t: 'Proximity', d: 'A local presence in Nouméa, close to your teams.' },
    ],
  },
  contact: {
    title: 'Contact — MGE Conseil, Nouméa, New Caledonia',
    description:
      'Contact MGE Conseil in Nouméa for a first conversation about your company’s financial management: online form or WhatsApp.',
    h1: 'Contact',
    lead: 'Tell us briefly what you need and we will get back to you promptly. We reply in French or English.',
    form: {
      name: 'Full name',
      company: 'Company',
      email: 'Email',
      phone: 'Phone (optional)',
      subject: 'Subject',
      subjectOther: 'Other request',
      message: 'Your message',
      consent: 'I agree that my data may be used to respond to my request, in accordance with the privacy policy.',
      privacyLink: 'Read the privacy policy',
      submit: 'Send',
      sending: 'Sending…',
      success: 'Thank you, your message has been sent. We will reply shortly.',
      error: 'Sending failed. Please try again or contact us on WhatsApp.',
      notConfigured: 'Formspree ID in src/config.ts — the form is disabled until it is set',
      required: 'Required field',
    },
    whatsappTitle: 'Prefer WhatsApp?',
    whatsappText: 'Message us directly; we reply during business hours.',
    whatsappBtn: 'Message us on WhatsApp',
    whatsappMsg: 'Hello, I would like to talk to MGE Conseil about my business.',
    whatsappTodo: 'WhatsApp number',
    detailsTitle: 'Contact details',
    address: 'Address',
    email: 'Email',
    phone: 'Phone',
    hoursTitle: 'Business hours',
    hoursTodo: 'opening hours',
  },
  legal: {
    title: 'Legal notice | MGE Conseil',
    description: 'Legal notice for the website of MGE Conseil, a financial advisory firm for businesses in Nouméa, New Caledonia.',
    h1: 'Legal notice',
  },
  privacy: {
    title: 'Privacy policy | MGE Conseil',
    description: 'Privacy and personal data protection policy for the website of MGE Conseil, Nouméa, New Caledonia.',
    h1: 'Privacy policy',
  },
};

export const content: Record<Lang, Content> = { fr, en };
