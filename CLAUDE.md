# SchemesSG v3

Two main folders: `backend/` and `frontend/`. See their respective `CLAUDE.md` files for details.

## Firebase Projects

- **Production**: `schemessg` — deployed from `main` branch
- **Development**: `schemessg-v3-dev` — deployed from `stg` branch

## Git Workflow

- Branch from `stg`, PR to `stg`, then PR `stg` → `main` for production
- Commit style: imperative mood, under 50 chars, no co-author lines

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

Always use one-liner format without Claude signature:

```bash
git add <files> && git commit -m "Add feature description"
```
