// Liste les emplacements « À compléter » restants dans le site généré. Lancer après `npm run build`.
import { readFileSync, readdirSync, statSync, existsSync } from 'node:fs';
import { join, relative } from 'node:path';
const DIST = new URL('../dist/', import.meta.url).pathname;
if (!existsSync(DIST)) { console.error('Lancez d’abord : npm run build'); process.exit(1); }
const files = [];
const walk = (d) => readdirSync(d).forEach((f) => { const p = join(d, f); statSync(p).isDirectory() ? walk(p) : p.endsWith('.html') && files.push(p); });
walk(DIST);
let total = 0;
for (const f of files.sort()) {
  const items = [...readFileSync(f, 'utf8').matchAll(/data-todo[^>]*>([^<]+)</g)].map((m) => m[1].replace(/&#39;/g, '’'));
  if (!items.length) continue;
  total += items.length;
  console.log(`\n/${relative(DIST, f).replace(/index\.html$/, '')}  (${items.length})`);
  for (const i of [...new Set(items)]) console.log('  - ' + i);
}
console.log(`\nTotal : ${total} emplacement(s) à compléter.`);
