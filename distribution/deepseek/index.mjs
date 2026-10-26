/** Native DSH skill provider. No model client, credentials or background loop. */
import { readFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';

export const name = 'book-genesis';
export const inject = ['skills'];
const suiteURL = new URL('../portable-suite.json', import.meta.url);
const skillsURL = new URL('../../skills/', import.meta.url);
const invocation = Object.freeze({ modelInvocable: true, userInvocable: true });

async function catalog() {
  const suite = JSON.parse(await readFile(suiteURL, 'utf8'));
  const names = suite.skills;
  if (!Array.isArray(names) || names.some(n => typeof n !== 'string' || !/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(n))
      || new Set(names).size !== names.length) throw new Error('Invalid Book Genesis skill catalog');
  return Promise.all(names.map(async skill => {
    const directory = new URL(`${skill}/`, skillsURL);
    const text = await readFile(new URL('SKILL.md', directory), 'utf8');
    const header = /^---\r?\n([\s\S]*?)\r?\n---\r?\n/.exec(text);
    const declaredName = header?.[1].match(/^name: (.+)$/m)?.[1].trim();
    const description = header?.[1].match(/^description: (.+)$/m)?.[1].trim();
    if (declaredName !== skill || !description || description.length > 1024)
      throw new Error(`Invalid skill metadata: ${skill}`);
    return { name: skill, description, invocation, provider: name, source: 'bundled',
      resourceBase: { kind: 'directory', path: fileURLToPath(directory).replace(/[\\/]$/, '') },
      rank: 600, locator: skill, content: text.slice(header[0].length) };
  }));
}

export function apply(ctx) {
  // The host owns registration disposal. Read only files named by our packaged catalog.
  ctx.skills.registerProvider(() => ({
    name,
    async list() {
      return (await catalog()).map(({ content, ...candidate }) => candidate);
    },
    async get(candidate) {
      const entry = (await catalog()).find(item => item.name === candidate?.name);
      if (!entry) return undefined;
      const { rank, locator, ...definition } = entry;
      return definition;
    },
  }));
}
