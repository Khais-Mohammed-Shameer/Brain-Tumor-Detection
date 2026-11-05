import { readdir, readFile, writeFile } from 'node:fs/promises';
import { createHash } from 'node:crypto';
import path from 'node:path';

async function files(directory) {
  const entries = await readdir(directory, { withFileTypes: true });
  const nested = await Promise.all(entries.map(entry => entry.isDirectory() ? files(path.join(directory, entry.name)) : path.join(directory, entry.name)));
  return nested.flat();
}
const assets = (await files('dist')).filter(file => !file.endsWith('/sw.js')).sort();
const hash = createHash('sha256');
for (const file of assets) hash.update(await readFile(file));
const version = hash.digest('hex').slice(0, 16);
const urls = ['/', ...assets.map(file => '/' + path.relative('dist', file).split(path.sep).join('/'))];
const worker = `// Generated from this exact production build. Never caches user image blobs.
const CACHE = 'care-studio-${version}';
const ASSETS = ${JSON.stringify(urls)};
self.addEventListener('install', event => { event.waitUntil(caches.open(CACHE).then(cache => cache.addAll(ASSETS))); });
self.addEventListener('activate', event => { event.waitUntil(Promise.all([
  caches.keys().then(keys => Promise.all(keys.filter(key => key.startsWith('care-studio-') && key !== CACHE).map(key => caches.delete(key)))),
  self.clients.claim()
])); });
self.addEventListener('fetch', event => {
  if (event.request.method !== 'GET' || new URL(event.request.url).origin !== self.location.origin) return;
  const url = new URL(event.request.url);
  if (url.protocol !== 'http:' && url.protocol !== 'https:') return;
  const key = event.request.mode === 'navigate' ? '/' : url.pathname;
  if (!ASSETS.includes(key)) return;
  event.respondWith(caches.open(CACHE).then(async cache => (await cache.match(key)) || fetch(event.request)));
});
`;
await writeFile('dist/sw.js', worker);
console.log(`Prepared offline cache ${version}: ${urls.length} application assets; no user data.`);
