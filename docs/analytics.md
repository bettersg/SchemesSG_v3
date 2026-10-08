# Analytics

SchemesSG uses Google Analytics 4 through Firebase Analytics. This is the
reference for what is tracked, what must be registered in the GA4 console, and
the rules that keep the data trustworthy.

For the console click-paths and exact field values, see
**`ga4-setup-runbook.md`** — this document explains what the events and
parameters mean; the runbook is the procedure for configuring a property.

Two properties, one per environment. Nothing carries over between them —
every console step below has to be done twice.

| Environment | Site                       | Measurement ID |
| ----------- | -------------------------- | -------------- |
| Production  | `schemes.sg`               | `G-VBPLJL8GYV` |
| Staging     | `schemessg-v3-dev.web.app` | `G-QXYGFZZ7X6` |

Both come from `vars.NEXT_PUBLIC_FIREBASE_MEASUREMENT_ID`, scoped by the
`environment:` key in `firebase-hosting-prod.yml` and
`firebase-hosting-staging.yml`. GitHub environment variables override
repository variables of the same name — if an environment ever loses its
variable it silently falls back to the repo-level value and both environments
start reporting into one property.

## Status

15 events are defined in `src/lib/analytics.ts`; 12 are instrumented today.

`select_item` and `filter_apply` are defined here but get their call sites with
the catalog work, because those changes share the same files.

`search` has no call site at all: the catalog keyword search it would measure is
still commented out, and its `result_count` overlaps
`chat_answer_shown.schemes_found`. Decide what it measures before wiring it.

| Event                  | Kind        | Instrumented | Call site                                |
| ---------------------- | ----------- | ------------ | ---------------------------------------- |
| `chat_message_send`    | custom      | yes          | `chat-page.tsx` → `fetchResponse`        |
| `chat_answer_shown`    | custom      | yes          | `chat-page.tsx` → `done` branch          |
| `chat_turn_aborted`    | custom      | yes          | `chat-page.tsx` → `handleStopGenerating` |
| `chat_turn_failed`     | custom      | yes          | `chat-page.tsx` → `handleStreamError`    |
| `chat_turn_abandoned`  | custom      | yes          | `chat-page.tsx` → `visibilitychange`     |
| `agency_contact_click` | custom      | yes          | `agency-contact-card.tsx`                |
| `scheme_shared`        | custom      | yes          | `scheme-detail.tsx` → `handleShare`      |
| `search`               | recommended | no           | see Status                               |
| `select_item`          | recommended | no           | lands with the catalog work              |
| `view_item`            | recommended | yes          | `scheme-detail.tsx`, on mount per scheme |
| `filter_apply`         | custom      | no           | lands with the catalog work              |
| `docs_section_view`    | custom      | yes          | `developers-page-content.tsx`            |
| `code_sample_copy`     | custom      | yes          | `developers/code-block.tsx`              |
| `generate_lead`        | recommended | yes          | `developers-page-content.tsx`            |
| `select_content`       | recommended | yes          | `sections/faq-section.tsx`               |

## Event reference

### Chat

**`chat_message_send`** — a request was actually issued to the agent.

- `turn_index` (number) — which user turn this is, 1-indexed
- `send_trigger` (`"user_submit" | "auto_resume"`)

`send_trigger` is not optional decoration. `chat-page.tsx` re-fires the
trailing user turn on mount, and `ChatProvider` rehydrates the transcript from
`sessionStorage`, so a mid-stream refresh silently re-asks the question.
Without this parameter every send count is inflated and unfilterable. The
discriminator is `consumeIsResumedTurn()` in `chat-provider.tsx`, which matches
the specific turn restored from storage and then clears it — deliberately not a
sticky "was rehydrated" boolean, which would stay true for the provider's whole
life and mislabel a genuine submit after a reset.

**`chat_answer_shown`** — the stream reached `done`.

- `turn_index` (number)
- `schemes_found` (number)
- `ms_to_first_token` (number) — send until the first visible text chunk. `0`
  when the stream finished without emitting any text.
- `ms_to_done` (number)

The UI was built for waits of roughly 45 seconds (see `thinking-phrases.ts`)
with no evidence anyone tolerates them. These two timings are that evidence.

**`chat_turn_aborted`** — the user pressed Stop.

- `ms_since_send` (number)
- `had_streamed_text` (boolean)

**`chat_turn_failed`** — the request or stream failed.

- `failure_stage` (`"request" | "stream" | "unknown"`)
- `ms_since_send` (number)
- `had_streamed_text` (boolean)

Aborted and failed are kept separate on purpose. Both run the same
`rollbackActiveRequest`, which splices the user's own message out of the
transcript — so from the data's point of view they look identical, but one is a
user decision and the other is a bug. `ms_since_send` plus `had_streamed_text`
is the "gave up" versus "changed my mind" discriminator. No error message text
is ever sent; `failure_stage` is inferred from whether any token had arrived.

**`chat_turn_abandoned`** — the user left while a turn was still streaming.

- `last_milestone` (`"sent" | "status" | "token" | "results"`)
- `ms_since_send` (number)

This is an absence signal: no done, no stop, no error. It fires at most once
per turn on `visibilitychange → hidden` rather than `pagehide`, because
`logEvent` exposes no beacon transport and the network is still available at
`hidden`. Consequence: `hidden` overcounts a tab switch that later returns, so
treat it as an upper bound. It is also the only instrument that will reveal a
hung backend, since `streamChat` has no client-side timeout.

### Scheme pages

**`agency_contact_click`** — an agency phone or email was tapped.

- `contact_method` (`"phone" | "email"`)

Enhanced Measurement's automatic outbound `click` only fires for `http(s)`
links, so `tel:` and `mailto:` are invisible to it. Contacting a human is the
strongest observable evidence that someone actually got help, which is why this
exists as a custom event.

The Google Maps link on the same card is deliberately **not** tracked: it is
`https`, so Enhanced Measurement already reports it as an outbound click and a
custom event would double-count permanently.

Read this metric split by viewport — a `phone` tap on desktop means little.

**`scheme_shared`** — the scheme page was shared.

- `share_outcome` (`"web_share" | "dismissed" | "clipboard" | "failed"`)

Enhanced Measurement cannot see this: sharing is a `navigator.share` call or a
clipboard write, not a link click. `dismissed` is the native share sheet being
cancelled, which otherwise leaves no trace, because the handler returns without
showing a status flash. `failed` covers a clipboard write that threw.

**`view_item`** — scheme detail viewed.

- `items` (`SchemeItem[]`)

**`select_item`** — scheme opened from a list. `item_list_id` is `catalog` or `chat_results`, so the two surfaces can be compared.

- `item_list_id` (string), `index` (number), `items` (`SchemeItem[]`)

```typescript
type SchemeItem = {
  item_id: string;
  item_name: string;
  item_category?: string;
};
```

The `items[]` ecommerce shape is used instead of a custom `scheme_id`
dimension. GA4 treats any dimension with more than 500 distinct values as
high-cardinality and collapses the rest into an `(other)` row — which degrades
unrelated dimensions in the same report. There are 600+ schemes. Item-scoped
dimensions sit on a separate quota, so `item_id` costs nothing from the
event-scoped budget.

### Catalog and docs

**`search`** — not instrumented; see Status. `result_count` (number),
`has_results` (boolean). `search_term` is deliberately omitted.

**`filter_apply`** — a results filter was applied. `filter_name` is the
dimension (`location`, `agency`), never the chosen value: an agency or planning
area narrows towards a person, and the useful question is which dimension
people reach for.

**`docs_section_view`** — a partner API reference section reached 50% visible.
`section_id` is the heading anchor. Fires once per section per page visit.

**`code_sample_copy`** — a sample was copied. `operation` is the API operation
id where the sample belongs to one, otherwise the section it sits in.
`code_language` is the pill label; it cannot be `language`, which GA4 collects
automatically for the browser locale.

**`generate_lead`** — "Request access" was selected on `/developers`.

**`select_content`** — an FAQ answer's link was followed. `item_id` is the
destination, which is stable across languages and copy edits.

## Custom definitions

**Status: registered 2026-10-05** — all 12 dimensions and 5 metrics created as
specified below. Registration is per property, so confirm both the staging and
production properties are covered before relying on either.

Parameters are invisible in GA4 reports until registered. Registration is
forward-only: data collected beforehand cannot be back-filled, and deleting a
definition also strips it from historical report queries. Register only what
will actually be filtered or segmented on.

Names must match the code strings exactly.

### Dimensions (scope: Event) — 12 of 50

Display names are prefixed by surface so the console list groups sensibly when
sorted, and so nobody has to guess that `section_id` belongs to the partner-API
docs rather than to scheme seekers. Display names and descriptions can be
changed later without losing data; the event parameter cannot.

> GA4 enforces this on the display name: **letters, numbers, spaces and
> underscores only**, and it must start with a letter. No colons, hyphens or
> parentheses. The description field is free-form.

| Display name                         | Event parameter     | Description                                                                                                                                               | Data today |
| ------------------------------------ | ------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------- |
| Chat Send Trigger                    | `send_trigger`      | Chat — whether a send was a real user submit or an automatic resume after a page refresh. Always filter to user_submit; auto_resume inflates send counts. | yes        |
| Chat Turn Index                      | `turn_index`        | Chat — which user turn in the conversation, 1-indexed.                                                                                                    | yes        |
| Chat Failure Stage                   | `failure_stage`     | Chat — where a turn failed: request (before any token) or stream (mid-flight).                                                                            | yes        |
| Chat Last Milestone                  | `last_milestone`    | Chat — how far a turn got before the user left: sent, status, token or results.                                                                           | yes        |
| Chat Had Streamed Text               | `had_streamed_text` | Chat — whether answer text had appeared before the turn was stopped or failed. Distinguishes "gave up" from "changed my mind".                            | yes        |
| Scheme Page Contact Method           | `contact_method`    | Scheme detail page — agency phone or email tapped. Excludes the Maps link, which Enhanced Measurement already counts.                                     | yes        |
| Scheme Page Share Outcome            | `share_outcome`     | Scheme detail page — how a share ended: native share sheet, dismissed, copied to clipboard, or failed.                                                    | yes        |
| Search Has Results                   | `has_results`       | Scheme search — whether any schemes were returned.                                                                                                        | no         |
| Catalog Filter Name                  | `filter_name`       | Catalog browse — which filter was applied.                                                                                                                | no         |
| Developer Docs Section               | `section_id`        | Developer docs (/developers) — which documentation section scrolled into view. Partner API audience, not scheme seekers.                                  | yes        |
| Developer Docs Code Sample Operation | `operation`         | Developer docs (/developers) — which partner API operation a copied code sample demonstrates.                                                             | yes        |
| Developer Docs Code Sample Language  | `code_language`     | Developer docs (/developers) — programming language of a copied code sample.                                                                              | yes        |

> `code_language`, not `language`. GA4 automatically collects a `language`
> parameter (browser language, surfaced as the built-in Language dimension), so
> registering a custom dimension against that name would shadow it. The code
> sends `code_language` already; register exactly that string.

`turn_index` is registered as a dimension rather than a metric: it is an
ordinal, and an average turn index means nothing.

### Metrics (scope: Event) — 5 of 50

GA4 offers no scope choice for custom metrics; they are always event-scoped.

| Display name                 | Event parameter     | Unit         | Description                                                                                                             |
| ---------------------------- | ------------------- | ------------ | ----------------------------------------------------------------------------------------------------------------------- |
| Chat Time to First Token     | `ms_to_first_token` | milliseconds | Chat — send until the first visible answer text. The latency that decides whether someone waits; UI was built for ~45s. |
| Chat Time to Answer Complete | `ms_to_done`        | milliseconds | Chat — send until the stream finished.                                                                                  |
| Chat Time Since Send         | `ms_since_send`     | milliseconds | Chat — elapsed time when a turn was stopped, failed or abandoned.                                                       |
| Chat Schemes Found           | `schemes_found`     | standard     | Chat — number of schemes returned with an answer.                                                                       |
| Search Result Count          | `result_count`      | standard     | Scheme search — number of results returned.                                                                             |

### Do not register

- `items`, `item_id`, `item_name`, `item_category`, `item_list_id`, `index` —
  GA4 ecommerce built-ins on the item-scoped budget.
- `method`, `content_type` — single-valued, nothing to segment.
- Anything resembling a user or session identifier. Google's guidance is
  explicit: never use a custom dimension as a per-user identifier.

### Audiences

Create a **Developer visitors** audience — users who triggered any of
`docs_section_view`, `code_sample_copy` or `generate_lead`. The `/developers`
page serves partner-API integrators, a different audience from people looking
for assistance, and conflating them makes every site-wide metric harder to read.

An audience is the right mechanism for "what kind of visitor is this". A `dev_`
prefix on parameter names was considered and rejected: parameters are already
scoped by their event, prefixing costs the same dimension slots, it says nothing
about the visitor, and `generate_lead` / `select_content` are GA4 recommended
names that cannot be renamed without forfeiting their built-in reporting.

### Key events

- `agency_contact_click` — mark as a key event. Marking is not retroactive.
- `chat_answer_shown` — do **not** mark. It measures our delivery, not the
  user's outcome, and marking it would make the chat segment incomparable to
  search traffic.

## Design rules

**Event names and parameters are correlated at compile time.** `EventMap` in
`src/lib/analytics.ts` is a mapped type, not a discriminated union. With a
union, `track()` could not tie the name argument to the params argument, so any
valid name would accept any valid param shape — `track("view_item", {
turn_index: 3 })` would compile. The mapped-type lookup is what makes that an
error. GA4 silently accepts any event name and names can never be renamed, so
the type system is the only guardrail against a permanent typo.

**`track()` never throws and never blocks render.** It no-ops silently when
running server-side, when the measurement ID is absent, when `isSupported()`
returns false, and when the SDK is blocked by an extension.

**No PII, ever.** Never pass raw search queries, chat messages, AI answers,
names, emails or phone numbers. Log shapes and outcomes: counts, categories,
enums, booleans, durations.

A build-time denylist in `analytics.test.ts` fails compilation if any parameter
is named `query`, `search_term`, `text`, `message`, `label`, `email`, `name`,
`phone`, `session_id`, `user_id` or `uid`. `item_name` is explicitly permitted
as a GA4 ecommerce field. The check derives its parameter list from
`EVENT_PARAM_KEYS`, so it cannot fall behind `EventMap`.

**Naming.** snake*case, 40 characters or fewer, letters/numbers/underscores
only, no `google*`/`firebase*`/`ga*`/`gtm\_`prefix. Asserted over`EVENT_NAMES`, which is exhaustiveness-checked against `EventMap`at compile
time — adding an event without registering it there fails`tsc`.

## Initialisation

`src/providers/analytics-provider.tsx` initialises analytics from a mount
effect and is mounted in `AppProviders`, which the root layout renders on every
route. Three properties follow from that:

1. **No dependency on auth.** Initialisation is independent of
   `getFirebaseAuth()`, so prerendered scheme pages, the catalog index and
   every category page report. Re-coupling them would silence all three.
2. **Runs on prerendered routes**, which is where most search traffic lands.
3. **`page_view` comes from Enhanced Measurement**, not from application code.

Initialisation is gated on `NEXT_PUBLIC_FIREBASE_MEASUREMENT_ID` being present
and on `isSupported()` resolving true. Both failures are silent by design.

`getAnalytics()` is used rather than `initializeAnalytics(app, { config: {
send_page_view: false } })`. The latter does exist in the installed Firebase
version; it is unused because Enhanced Measurement's automatic `page_view` is
the intended source. Revisit only if application-owned page views become
necessary.

## Local development

`.env.local` has no measurement ID, so analytics correctly no-ops during
`npm run dev`. To exercise events locally, add these three keys — copy the
values from `.env.development`, which already points at the dev project:

```env
NEXT_PUBLIC_FIREBASE_PROJECT_ID=
NEXT_PUBLIC_FIREBASE_APP_ID=
NEXT_PUBLIC_FIREBASE_MEASUREMENT_ID=
```

`NEXT_PUBLIC_FB_API_KEY` is already present. `NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN`
is **not** needed: `firebaseConfig.ts` constructs `authDomain` from
`NEXT_PUBLIC_FIREBASE_PROJECT_ID` and never reads that variable, even though the
deployed env files define it.

Use the **staging** measurement ID, never production. Local events land in the
staging property and mix with real staging data, so add your IP to staging's
internal traffic filter, or create a throwaway third property for local work.

For DebugView, install the **Google Analytics Debugger** Chrome extension. The
code sets no `debug_mode` flag, and the extension avoids any risk of shipping
one to production.

`.env.local` is gitignored via the `*.local` pattern. Never commit it.

## Enhanced Measurement

Confirmed on staging, 2026-10-05: page views **on**, page changes based on
browser history events **off**, outbound clicks **on**, and scroll, site
search, form interactions, video and file downloads **off**.

**The rule to maintain:** GA4 de-duplicates nothing except `purchase`. Before
adding a custom event, check it does not restate an Enhanced Measurement one,
because the overlap is permanent and cannot be separated afterwards. This is
why `tel:` and `mailto:` taps need `agency_contact_click` (Enhanced Measurement
only fires for http(s)) while the https Maps link is deliberately untracked.

With history-based page views off, `page_view` fires on full loads only, not on
in-app navigation.

### Open decision: `scheme_outbound_click`

The "Visit website" CTA renders in three placements, all `http(s)`, so
Enhanced Measurement already counts them but reports only `link_url` and
`link_domain`, collapsing the three into one number. Owning the event buys a
`cta_placement` parameter and costs Enhanced Measurement outbound clicks
site-wide. Do not add the custom event while that toggle is on.

## Usage

```typescript
import { track } from "@/lib/analytics";

track("agency_contact_click", { contact_method: "phone" });

track("chat_message_send", { turn_index: 2, send_trigger: "user_submit" });

track("chat_answer_shown", {
  turn_index: 2,
  schemes_found: 12,
  ms_to_first_token: 2400,
  ms_to_done: 18200,
});
```

## Testing

```bash
npx vitest run src/lib/analytics.test.ts
```

Covers: name/params correlation (including params belonging to a _different_
event, which a union-based signature would have accepted), unknown event names
failing compilation, `track()` never throwing when analytics is unavailable,
naming conventions over every event, the PII denylist over every parameter, and
server-side safety.

## Open items

1. **Mark `agency_contact_click` as a key event** (runbook step 9). Not
   retroactive; allow up to 24 hours after the event first fires for it to
   reach the Events table where the star lives.
2. **Confirm `chat_message_send` is collected.** It did not appear in the
   staging DebugView run although every chat outcome event gates on the same
   `sendAtRef` set beside it, so its absence is not possible as read. Check
   Reports → Realtime, which has no processing lag.
3. **Verify three parameters in DebugView:** `send_trigger: auto_resume`, a
   `chat_turn_aborted` carrying `had_streamed_text: true`, and that the Maps
   link fires Enhanced Measurement `click` with no `agency_contact_click`.
4. **Settle `scheme_outbound_click`** (above).
5. **Decide what `search` measures**, or drop the event.
6. **Build the explorations and report collection** (runbook steps 10 and 11),
   then hold a 14-day baseline before setting any target.
7. **Repeat every console step on production.** Nothing carries between
   properties.

## Maintaining this

- **Adding an event:** add it to `EventMap`, then to `EVENT_NAMES` and
  `EVENT_PARAM_KEYS`. Omitting either fails `tsc` via the exhaustiveness check.
  Check it does not restate an Enhanced Measurement event first.
- **A new parameter is invisible in reports until registered** as a custom
  dimension or metric, per property, and registration is forward-only.
- **Never rename an event or parameter after collection starts.** GA4 cannot
  rename, and the old and new names do not merge.
- **Keep parameters out of the PII denylist** in `analytics.test.ts`; it derives
  its list from `EVENT_PARAM_KEYS`, so it cannot fall behind.
- **High-cardinality values do not belong in dimensions.** GA4 buckets anything
  past 500 distinct values into `(other)`; scheme identity goes in the
  ecommerce `items[]` shape instead.

Considered and not planned: a consent banner (notification under PDPA s15A
instead), BigQuery export, and server-side partner API metrics, which Firebase
Analytics cannot reach.
