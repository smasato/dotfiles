import { readFileSync, writeFileSync, renameSync, existsSync } from 'node:fs';
import { resolve, dirname, join } from 'node:path';
import { homedir } from 'node:os';

const manifest = JSON.parse(
  readFileSync(new URL('../references/upstream.json', import.meta.url), 'utf8'),
);
const lockPath = resolve(
  process.argv[2] ?? join(homedir(), '.agents/.skill-lock.json'),
);
if (existsSync(lockPath)) {
  const original = readFileSync(lockPath, 'utf8');
  const lock = JSON.parse(original);
  if (!lock.skills || typeof lock.skills !== 'object')
    throw new Error('Unexpected skills lock format');
  let removed = 0;
  for (const skill of manifest.skills) {
    for (const name of new Set([skill.name, skill.dir])) {
      const entry = lock.skills[name];
      if (
        entry?.source === 'cursor/plugins' &&
        entry.skillPath === skill.source
      ) {
        delete lock.skills[name];
        removed++;
      }
    }
  }
  if (removed) {
    // Keep the pre-migration record for recovery; never replace an earlier backup.
    const backup = `${lockPath}.before-pstack-port`;
    if (!existsSync(backup))
      writeFileSync(backup, original, { flag: 'wx', mode: 0o600 });
    const temporary = join(
      dirname(lockPath),
      `.pstack-lock-${process.pid}.json`,
    );
    writeFileSync(temporary, JSON.stringify(lock, null, 2) + '\n', {
      flag: 'wx',
      mode: 0o600,
    });
    renameSync(temporary, lockPath);
  }
  console.log(`pstack: detached ${removed} upstream CLI ownership entries`);
}
