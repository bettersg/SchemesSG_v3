# Public catalog and scheme reads for static rendering

## Status

Accepted

## Date

2026-09-13

## Context

`GET /catalog` and `GET /schemes/{id}` previously required a Firebase ID token.
The frontend obtained one anonymously through the auth gateway, so every visitor
was authenticated, but no visitor was identified — the token carried no claim the
handlers used, and the response for a given scheme was the same for everyone.

That arrangement made the two endpoints unreachable at build time. Static
generation runs with no browser, no user, and no gateway: `generateStaticParams`
for `/schemes/[schemeId]` and `/catalog/[category]` cannot mint an anonymous
token, so the scheme corpus could not be prerendered and search crawlers were
served an empty shell. Issue #363 is the consequence.

Two properties made the previous decision worth revisiting rather than
engineering around:

- **Scheme data is visitor-independent.** Nothing in the catalog or detail
  response varies by identity, so authentication was gating public reference
  material.
- **Anonymous sign-in is not access control.** Any client could obtain a token
  by asking, which means the gate deterred nothing while costing every reader a
  round trip.

## Decision

1. **The two catalog GET endpoints are public.** No token is required or read.
   Write paths, chat, feedback, and the partner API keep their existing
   authentication; this covers reads of already-public scheme content only.
2. **`frontend/src/lib/schemes.server.ts` is the only build-time reader**, behind
   an `import "server-only"` boundary, so a client component cannot start
   depending on these reads and quietly reintroduce a per-visitor fetch.
3. **The anonymous contract is asserted, not assumed.** The fixture server in
   `frontend/scripts/public-build-fixture.mjs` rejects any request carrying an
   `Authorization` header with `400` and records every read, so a spec can prove
   the reads Next.js actually made were anonymous. A browser-side interceptor
   cannot do this: the fetch happens during route compilation, outside any
   browser request.
4. **The catalog query projects onto `CATALOG_FIELDS`.** Build-time enumeration
   reads the whole corpus, and Next.js caps a single data-cache entry at 2 MB;
   projecting at the Firestore query keeps detail-only fields such as
   `scraped_text` out of the page payload.

## Consequences

- Scheme pages are indexable, and a visitor's first paint no longer waits on a
  token exchange it never needed.
- Abuse protection for these two routes now rests on rate limiting and caching
  rather than on a token, because the token never provided any.
- An incomplete enumeration fails the build rather than silently publishing a
  partial corpus, which is what #363 asked for. The cost is that catalog data
  quality can now break a deploy: `getAllCatalogSchemes` fails when the API's
  `total_count` disagrees with what pagination returns.
- Anything that must vary per visitor cannot be added to these responses without
  reversing this decision. A personalized field would have to live on a separate
  authenticated endpoint, not be folded into `/catalog`.
