// Contrôles automatiques du site généré (dist/). Lancer avec : npm test
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync, existsSync, readdirSync, statSync } from 'node:fs';
import { join } from 'node:path';

const DIST = new URL('../dist/', import.meta.url).pathname;
const pages = {
  fr: ['/', '/offres/', '/a-propos/', '/contact/', '/mentions-legales/', '/confidentialite/'],
  en: ['/en/', '/en/services/', '/en/about/', '/en/contact/', '/en/legal-notice/', '/en/privacy/'],
};
const file = (p) => join(DIST, p, 'index.html');
const html = (p) => readFileSync(file(p), 'utf8');
const text = (h) => h.replace(/<script[\s\S]*?<\/script>/g, ' ').replace(/<style[\s\S]*?<\/style>/g, ' ').replace(/<[^>]+>/g, ' ').replace(/&#39;|&rsquo;/g, '’');
const allHtml = () => {
  const out = [];
  const walk = (d) => readdirSync(d).forEach((f) => { const p = join(d, f); statSync(p).isDirectory() ? walk(p) : p.endsWith('.html') && out.push(p); });
  walk(DIST);
  return out;
};

test('toutes les pages FR et EN sont générées', () => {
  for (const p of [...pages.fr, ...pages.en]) assert.ok(existsSync(file(p)), `manquante : ${p}`);
  for (const f of ['robots.txt', 'sitemap-index.xml', 'favicon.svg', '404.html']) assert.ok(existsSync(join(DIST, f)), f);
});

test('SEO : langue, title, description, canonical, hreflang', () => {
  for (const [lang, list] of Object.entries(pages)) {
    for (const p of list) {
      const h = html(p);
      assert.match(h, new RegExp(`<html lang="${lang}"`), `${p} lang`);
      const title = h.match(/<title>([^<]+)<\/title>/)?.[1];
      assert.ok(title && title.length >= 15 && title.length <= 75, `${p} title (${title?.length})`);
      const desc = h.match(/<meta name="description" content="([^"]+)"/)?.[1];
      assert.ok(desc && desc.length >= 70 && desc.length <= 170, `${p} description (${desc?.length})`);
      assert.match(h, /<link rel="canonical" href="https?:\/\/[^"]+"/, `${p} canonical`);
      assert.match(h, /hreflang="fr"/); assert.match(h, /hreflang="en"/); assert.match(h, /hreflang="x-default"/);
      assert.equal((h.match(/<h1[\s>]/g) || []).length, 1, `${p} doit avoir un seul h1`);
    }
  }
});

test('titles et descriptions uniques', () => {
  const all = [...pages.fr, ...pages.en].map(html);
  const titles = all.map((h) => h.match(/<title>([^<]+)/)[1]);
  assert.equal(new Set(titles).size, titles.length);
});

test('SEO local : Nouméa / Nouvelle-Calédonie présents sur les pages clés', () => {
  for (const p of ['/', '/offres/', '/a-propos/', '/contact/']) assert.match(html(p), /Nouméa/);
  for (const p of ['/en/', '/en/contact/']) assert.match(html(p), /New Caledonia/);
});

test('données structurées JSON-LD valides', () => {
  for (const p of ['/', '/en/']) {
    const m = html(p).match(/<script type="application\/ld\+json">([\s\S]*?)<\/script>/);
    assert.ok(m, p);
    const d = JSON.parse(m[1]);
    assert.equal(d['@type'], 'ProfessionalService');
    assert.equal(d.address.addressLocality, 'Nouméa');
    assert.equal(d.address.addressCountry, 'NC');
  }
});

test('aucun prix affiché', () => {
  const prix = /\d[\d\s.,  ]*\s?(?:(?:XPF|F\s?CFP|CFP|EUR|USD)\b|€|\$)/i;
  for (const f of allHtml()) {
    const t = text(readFileSync(f, 'utf8'));
    assert.doesNotMatch(t, prix, `prix détecté dans ${f}`);
  }
});

test('vocabulaire : jamais « TVA », jamais de témoignage inventé', () => {
  for (const f of allHtml()) {
    const h = readFileSync(f, 'utf8');
    assert.doesNotMatch(text(h), /\bTVA\b|\bVAT\b/, f);
    assert.doesNotMatch(h, /<blockquote|"@type":\s*"Review"|aggregateRating/i, f);
  }
});

test('les 5 offres sont présentes en FR et EN', () => {
  const ids = ['diagnostic-flash-360', 'daf-essentiel', 'daf-pilotage', 'daf-croissance', 'dossier-de-financement'];
  for (const p of ['/offres/', '/en/services/']) for (const id of ids) assert.match(html(p), new RegExp(`id="${id}"`), `${p} ${id}`);
});

test('tous les liens internes pointent vers une page existante', () => {
  for (const f of allHtml()) {
    for (const [, href] of readFileSync(f, 'utf8').matchAll(/href="(\/[^"#?]*)/g)) {
      const target = href.endsWith('/') ? join(DIST, href, 'index.html') : join(DIST, href);
      assert.ok(existsSync(target), `${f} → lien cassé ${href}`);
    }
  }
});

test('formulaire : consentement obligatoire, anti-spam, lien confidentialité', () => {
  for (const [p, priv] of [['/contact/', '/confidentialite/'], ['/en/contact/', '/en/privacy/']]) {
    const h = html(p);
    assert.match(h, /name="consentement"[^>]*required/);
    assert.match(h, /name="_gotcha"/);
    assert.ok(h.includes(`href="${priv}"`));
  }
});

test('pages légales : champs obligatoires présents', () => {
  const t = text(html('/mentions-legales/'));
  for (const k of ['RIDET', 'Directeur de la publication', 'Hébergeur', 'Capital social', 'Siège social']) assert.ok(t.includes(k), k);
  const c = text(html('/confidentialite/'));
  for (const k of ['Responsable du traitement', 'Durée de conservation', '78-17', 'CNIL', 'Formspree']) assert.ok(c.includes(k), k);
});

test('le contrôle des prix détecte bien un prix (test du test)', () => {
  const prix = /\d[\d\s.,  ]*\s?(?:(?:XPF|F\s?CFP|CFP|EUR|USD)\b|€|\$)/i;
  for (const ok of ['150 000 XPF', '150\u202f000 F CFP', '1 200 €', '99 USD']) assert.match(ok, prix, ok);
  assert.doesNotMatch('capital social en XPF', prix);
});
