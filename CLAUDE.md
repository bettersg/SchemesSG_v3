# SchemesSG v3

Two main folders: `backend/` and `frontend/`. See their respective `CLAUDE.md` files for details.

## Firebase Projects

- **Production**: `schemessg` — deployed from `main` branch
- **Development**: `schemessg-v3-dev` — deployed from `stg` branch

## Git Workflow

- Branch from `stg`, PR to `stg`, then PR `stg` → `main` for production
- Commit style: **Conventional Commits** (`feat:`, `fix:`, `chore:`, `docs:`, …), imperative mood, no co-author lines. The `release.yml` workflow runs **semantic-release**, which bumps the version *only* from `feat:`/`fix:` (and `BREAKING CHANGE:`) commits — a plain `Fix …`/`Add …` subject is ignored and produces **no release**.

## Branch Creation — STRICT RULE

When asked to "create a new branch from X" (or hotfix from main, feature from stg, etc.):

**Mandatory sequence:**
```bash
git fetch origin
git switch -c <new-branch> origin/<base> --no-track
git push -u origin <new-branch>          # push EMPTY branch first, sets upstream to itself
git rev-parse --abbrev-ref @{upstream}    # MUST return origin/<new-branch>
# only NOW cherry-pick / commit
```

**Forbidden:**
- `git checkout -b <new> origin/<base>` — sets upstream to base, later `git push` lands on base (e.g. main)
- Cherry-picking or committing onto a new branch before its remote upstream is correctly set
- Treating "create branch" as local-only — it always means local + remote with correct upstream

**Why:** A new branch tracking `origin/main` will have any bare `git push` (from any tool/hook/alias) write commits directly to `main`, bypassing PR review and corrupting production history. This has happened before. Do not repeat.

## Git Commits

Always use one-liner Conventional Commit format without Claude signature:

```bash
git add <files> && git commit -m "feat: add scheme catalog filter"
git add <files> && git commit -m "fix: show phone/email on scheme detail"
```

Use `fix:` for bug fixes (patch bump), `feat:` for features (minor bump), and
append `!` or a `BREAKING CHANGE:` footer for a major bump. Use `chore:`/`docs:`
for changes that should **not** trigger a release.
