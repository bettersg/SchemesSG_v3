# SchemesSG v3 Frontend

Next.js + TypeScript. See root `AGENTS.md` for shared worktree, branch,
safety, and evidence policy. Full setup and scripts: `README.md`.

## Package Manager

`npm` only — never another lockfile/package manager. `npm ci` to install;
commit `package-lock.json`.

## Stack Conventions

- Next.js App Router under `src/app`, path alias `@/*` → `src/*`.
- TypeScript strict mode (`tsconfig.json`); `npm run typecheck` before
  handoff on any `.ts`/`.tsx` change.
- Env files (`.env.*`) come from the team's shared drive (see `README.md`);
  never commit them. Unit tests, integration tests, and validation builds
  (`npm run build` without env vars) do not need them.

## Verification

- Focused Vitest file while developing (`npx vitest run <path>`), then the
  full scoped set before handoff: `npm run lint`, `npm run typecheck`,
  `npm test`, `npm run build`.
- Any visible UI change: verify in an actual browser (dev server or build
  preview), not just passing tests — screenshot or describe what was
  observed.
- Cross-boundary changes (touching API contracts, auth, streaming, or a
  journey spanning frontend and backend) also require the canonical
  full-stack smoke described from root `docs/verification.md`.

## Pointers

- Scripts, testing tiers, deployment, environment: `README.md`.
- Frontend testing boundaries/decisions: `docs/adr/0001-frontend-testing-foundation.md`.
