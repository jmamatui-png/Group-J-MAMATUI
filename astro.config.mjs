// @ts-check
import { defineConfig } from 'astro/config';
import sitemap from '@astrojs/sitemap';
import tailwindcss from '@tailwindcss/vite';

// URL publique du site (à définir au déploiement : variable d'environnement SITE_URL).
const SITE_URL = process.env.SITE_URL ?? 'https://www.a-completer.nc';

export default defineConfig({
  site: SITE_URL,
  trailingSlash: 'always',
  build: { format: 'directory' },
  integrations: [
    sitemap({
      i18n: { defaultLocale: 'fr', locales: { fr: 'fr-NC', en: 'en' } },
    }),
  ],
  vite: { plugins: [tailwindcss()] },
});
