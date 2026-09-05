import { execFileSync } from 'node:child_process';
import type { FrontierPr } from './store.ts';

function gh(repo: string, args: string[]): unknown {
  const raw = execFileSync('gh', args, {
    cwd: repo,
    encoding: 'utf8',
    env: process.env,
    stdio: ['ignore', 'pipe', 'pipe'],
  });
  return JSON.parse(raw);
}

export function parsePullRequest(value: unknown): FrontierPr {
  if (
    value === null ||
    typeof value !== 'object' ||
    !('number' in value) ||
    !Number.isSafeInteger(value.number) ||
    typeof value.number !== 'number' ||
    value.number < 1 ||
    !('headRefName' in value) ||
    typeof value.headRefName !== 'string' ||
    !value.headRefName ||
    !('headRefOid' in value) ||
    typeof value.headRefOid !== 'string' ||
    !/^[0-9a-f]{40,64}$/i.test(value.headRefOid) ||
    !('state' in value) ||
    !['OPEN', 'MERGED', 'CLOSED'].includes(String(value.state))
  ) {
    throw new Error('GitHub returned an invalid pull request');
  }
  const state = value.state;
  if (state !== 'OPEN' && state !== 'MERGED' && state !== 'CLOSED') {
    throw new Error('GitHub returned an invalid PR state');
  }
  return {
    pr: value.number,
    branches: value.headRefName,
    sha: value.headRefOid,
    state,
  };
}

export function parseStack(
  value: unknown,
): { pr: number; branch: string; sha: string }[] {
  if (
    value === null ||
    typeof value !== 'object' ||
    !('branches' in value) ||
    !Array.isArray(value.branches)
  ) {
    throw new Error('gh stack returned invalid stack data');
  }
  const entries = value.branches.map((branch: unknown) => {
    if (
      branch === null ||
      typeof branch !== 'object' ||
      !('name' in branch) ||
      typeof branch.name !== 'string' ||
      !branch.name ||
      !('head' in branch) ||
      typeof branch.head !== 'string' ||
      !/^[0-9a-f]{40,64}$/i.test(branch.head) ||
      !('pr' in branch) ||
      branch.pr === null ||
      typeof branch.pr !== 'object' ||
      !('number' in branch.pr) ||
      typeof branch.pr.number !== 'number' ||
      !Number.isSafeInteger(branch.pr.number) ||
      branch.pr.number < 1
    ) {
      throw new Error(
        'gh stack branch has no valid submitted PR; submit the stack first',
      );
    }
    return { pr: branch.pr.number, branch: branch.name, sha: branch.head };
  });
  if (new Set(entries.map((entry) => entry.pr)).size !== entries.length) {
    throw new Error('gh stack returned duplicate pull requests');
  }
  return entries;
}

export function githubFrontier(
  repo: string,
  queue?: readonly number[],
): FrontierPr[] {
  const stack =
    queue === undefined
      ? parseStack(gh(repo, ['stack', 'view', '--json']))
      : null;
  const numbers = queue ?? stack?.map((entry) => entry.pr) ?? [];
  return numbers.map((number) => {
    const pr = parsePullRequest(
      gh(repo, [
        'pr',
        'view',
        String(number),
        '--json',
        'number,headRefName,headRefOid,state',
      ]),
    );
    if (pr.pr !== number)
      throw new Error(`GitHub returned PR #${pr.pr} for #${number}`);
    const local = stack?.find((entry) => entry.pr === number);
    if (local && (local.branch !== pr.branches || local.sha !== pr.sha)) {
      throw new Error(
        `PR #${number} differs from the local stack; reconcile heads before recording the frontier`,
      );
    }
    return pr;
  });
}
