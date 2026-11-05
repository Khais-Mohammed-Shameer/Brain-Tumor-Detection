import { build } from 'esbuild';
import { mkdir, readFile, writeFile } from 'node:fs/promises';
import assert from 'node:assert/strict';
import path from 'node:path';
import { pathToFileURL } from 'node:url';

// Run the actual application engine in Node/CPU against independently generated
// Python/OpenCV fixtures. No browser or inference server is required.
await mkdir('.sites-runtime', { recursive: true });
const outfile = path.resolve('.sites-runtime/inference-test.mjs');
await build({ entryPoints: ['src/lib/inference.ts'], outfile, bundle: true, platform: 'node', format: 'esm', packages: 'external' });
globalThis.fetch = async url => {
  const file = path.resolve('public', String(url).replace(/^\//, ''));
  assert.ok(file.startsWith(path.resolve('public') + path.sep));
  return new Response(await readFile(file));
};
const engine = await import(pathToFileURL(outfile).href);
const cases = [
  ['reference-tumor', 0.9997071623802185],
  ['reference-no-tumor', 0.006684683263301849],
];
const results = [];
for (const [name, expected] of cases) {
  const bytes = await readFile(`tests/${name}.f32`);
  const values = new Float32Array(bytes.buffer, bytes.byteOffset, bytes.byteLength / 4);
  const result = await engine.predict(values);
  const delta = Math.abs(result.score - expected);
  assert.ok(delta < 0.00002, `${name}: ${result.score} vs Python ${expected}`);
  results.push({ fixture: name, python_score: expected, javascript_score: result.score, absolute_delta: delta });
}
const baseline = await engine.engineMemory();
for (let i = 0; i < 5; i++) await engine.predict(new Float32Array(240 * 240 * 3));
assert.equal(await engine.engineMemory(), baseline, 'Repeated predictions must not leak tensors');
const summary = { scope: 'Numerical compatibility only, not clinical performance.', tolerance: 0.00002, results, repeated_prediction_tensor_leak: false };
await writeFile('tests/model-parity-results.json', JSON.stringify(summary, null, 2) + '\n');
console.log(JSON.stringify(summary, null, 2));
