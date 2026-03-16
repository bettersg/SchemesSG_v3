# SchemesSG v3

Two main folders: `backend/` and `frontend/`. See their respective `CLAUDE.md` files for details.

## Firebase Projects

- **Production**: `schemessg` — deployed from `main` branch
- **Development**: `schemessg-v3-dev` — deployed from `stg` branch

## Git Workflow

- Branch from `stg`, PR to `stg`, then PR `stg` → `main` for production
- Commit style: imperative mood, under 50 chars, no co-author lines

## Git Commits

Always use one-liner format without Claude signature:

```bash
git add <files> && git commit -m "Add feature description"
```
