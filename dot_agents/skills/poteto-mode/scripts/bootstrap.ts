import { existsSync, readFileSync } from 'node:fs';
import { join } from 'node:path';

export function ensureDependenciesInstalled(): void {
  const installed = join(
    import.meta.dir,
    'node_modules',
    'commander',
    'package.json',
  );
  if (!existsSync(installed)) {
    throw new Error(
      'pstack dependencies are missing. Run chezmoi apply to install the locked dependencies, or explicitly run bun install --frozen-lockfile in this scripts directory with the required permission.',
    );
  }
  const manifest = JSON.parse(
    readFileSync(join(import.meta.dir, 'package.json'), 'utf8'),
  );
  const dependency = JSON.parse(readFileSync(installed, 'utf8'));
  if (dependency.version !== manifest.dependencies.commander) {
    throw new Error(
      'pstack commander version differs from package.json; install the locked dependencies before running.',
    );
  }
}
