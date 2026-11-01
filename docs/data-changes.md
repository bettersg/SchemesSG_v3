# Data changes

How to change scheme data in dev or prod (content corrections, bulk re-tags, backfills) so that search, partners and
the website all pick the change up. Every prod write needs the owner's go. Rehearse on dev first; scheme IDs match
between dev and prod.

## Look before writing

`backend/functions/scripts/firestore_peek.py` prints documents as JSON lines and never writes:

```bash
cd backend/functions
uv run python scripts/firestore_peek.py prod schemes <id> [<id> ...] --fields scheme,summary,phone
uv run python scripts/firestore_peek.py prod schemeEntries --since 2026-11-01T12:30:00Z --fields Scheme,pipeline_status,llm_fields.scheme_type
uv run python scripts/firestore_peek.py prod schemeEntries --where pipeline_status=failed --count
```

Name the fields you need with `--fields`: it reads only those (dotted paths work), so scanning a collection stays
cheap. Without it every field except `scraped_text` and `embedding` prints, with long strings cut.

## Correct a few schemes

`backend/functions/scripts/patch_schemes.py` applies a reviewed `PATCH.json` (format in its docstring):

1. Dry run on dev, then `--write` on dev.
2. Dry run on prod; check every old -> new line.
3. `--write --confirm-project schemessg` on prod. Note the backup path it prints.

What it guarantees:
- Tag fields (`who_is_it_for`, `what_it_gives`, `scheme_type`) accept only current taxonomy terms.
- `expect` guards skip a scheme that was already fixed or edited differently.
- A `last_update_time` precondition skips a scheme edited between the read and the write.
- Each write stamps `last_scraped_update`, so the partner API's `updated_at` / `updated_since` report it.
- `--restore BACKUP --write` puts the old values back.

Bulk re-tags go through `backend/scripts/ncss_eval/reclassify.py` instead (`snapshot` -> `classify` -> `apply`, with
`restore`); it stamps `tags_updated_at`.

## After the write

1. **Search**: when text or tags changed, re-embed: `uv run python scripts/populate_embeddings.py --prod` (from
   `backend/functions`). Search uses the stored embeddings until then.
2. **Website**: catalog and scheme pages are prerendered, and their data fetch is cached for 24 hours
   (`revalidate: 86_400` in `frontend/src/lib/schemes.server.ts`). The pages show the old data until the cache
   expires. To show the change now, re-run the hosting deploy *after the write has finished*; a build that started
   earlier has already read the old data:
   ```bash
   gh run rerun <id of the latest "Deploy Frontend to Firebase Hosting PROD" run on main>
   ```
3. **Check** through public URLs: the catalog API, the page itself, and a search that should find the new text.

## Files from prod

Backups and exports hold prod data: keep them under the repo's gitignored `data/` folder (`data/patches/` is the
patch tool's default, `data/issue-<n>/` for files belonging to an issue) and out of git, issues and PRs.
