export type Lang = 'fr' | 'en';
export const langs: Lang[] = ['fr', 'en'];

export const routes = {
  home: { fr: '/', en: '/en/' },
  offers: { fr: '/offres/', en: '/en/services/' },
  about: { fr: '/a-propos/', en: '/en/about/' },
  contact: { fr: '/contact/', en: '/en/contact/' },
  legal: { fr: '/mentions-legales/', en: '/en/legal-notice/' },
  privacy: { fr: '/confidentialite/', en: '/en/privacy/' },
} as const;

export type RouteKey = keyof typeof routes;
