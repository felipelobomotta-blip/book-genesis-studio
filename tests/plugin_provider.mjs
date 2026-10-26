import assert from 'node:assert/strict';
import { pathToFileURL } from 'node:url';
import path from 'node:path';
import { readFile } from 'node:fs/promises';

const root = process.argv[2];
const plugin = await import(pathToFileURL(path.join(root, 'distribution/deepseek/index.mjs')));
assert.deepEqual(plugin.inject, ['skills']);
let provider;
plugin.apply({ skills: { registerProvider(factory) { provider = factory(); } } });
const candidates = await provider.list({ cwd: process.cwd() });
assert.equal(candidates.length, 4);
for (const candidate of candidates) {
  const definition = await provider.get(candidate);
  assert.equal(definition.name, candidate.name);
  assert.ok(definition.content.includes('# '));
  assert.ok(!definition.content.startsWith('---'));
  assert.deepEqual(definition.invocation, { modelInvocable: true, userInvocable: true });
  assert.equal(definition.resourceBase.path, path.join(root, 'skills', candidate.name));
}
assert.equal(await provider.get({name: '../../private'}), undefined);
const safe = await provider.get({ ...candidates[0], locator: '/private', resourceBase: {path: '/private'} });
assert.equal(safe.resourceBase.path, candidates[0].resourceBase.path);
const content = await readFile(path.join(root, 'skills/book-genesis/references/pipeline/plugin-onboarding.md'), 'utf8');
assert.ok(content.includes('controller-owned'));
console.log('DeepSeek skill-provider contract: four skills and resource boundaries verified (no live host).');
