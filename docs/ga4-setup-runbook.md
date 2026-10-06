# GA4 setup runbook

A repeatable procedure for configuring a Schemes.sg GA4 property. Run it twice
— **staging first**, then production — because nothing carries between
properties and several steps cannot be undone or back-filled.

For what each event and parameter *means*, see `analytics.md`. This document is
only the click-path and the field values.

| Property | Measurement ID | Site |
| --- | --- | --- |
| Staging | `G-QXYGFZZ7X6` | `schemessg-v3-dev.web.app` |
| Production | `G-VBPLJL8GYV` | `schemes.sg` |

## Before you start

### Current state, staging property (2026-10-05)

**Steps 1 to 7 are done on staging.** Retention and reporting identity,
Enhanced Measurement and its sub-toggles, the internal traffic rule (filter left
in Testing), all 12 custom dimensions, all 5 custom metrics, and both audiences.

Outstanding on staging: steps 8 to 12. Steps 9, 10 and 11 all need the custom
events to have fired, which step 8 does from a local `npm run dev`. Only step 12
needs a deploy, because it needs 14 days of genuine user traffic.

`Developer visitors` exists but cannot populate until `docs_section_view`,
`code_sample_copy` and `generate_lead` are instrumented. Its conditions are
immutable, so if instrumentation changes any of those three names, the audience
has to be rebuilt and the original archived.

Production: **nothing done.** Access is staging only at present. Note step 4's
production filter is the one box in steps 1 to 7 still unticked.

### Prerequisites

- You need the **Editor** role on the property. Editor is "full control of the
  property, cannot manage users" — enough for every step here. A Firebase IAM
  role does **not** grant this; it has to be granted inside Analytics.
- **Only step 12 needs a deployment.** Steps 9, 10 and 11 need events to have
  *fired*, which is not the same thing: `analytics-provider.tsx` gates only on
  `NEXT_PUBLIC_FIREBASE_MEASUREMENT_ID` and has no environment check, so
  `npm run dev` against the staging measurement ID emits real events into the
  staging property. Step 8 is the procedure for that. Step 12 needs 14 days of
  genuine user traffic, which only a deploy provides.
- **Allow up to 24 hours between steps 8 and 9.** Step 9 needs the event in the
  Events table, which is fed by the processing pipeline. DebugView shows the
  same event within seconds, but it is a different surface.
- **Step 7's `Developer visitors` is blocked by instrumentation, not by
  deployment.** Three of its events have no call sites yet.
- Steps 1, 3, 4, 7 and 9 are **not retroactive**. Data collected before them
  is not recoverable. Do them before relying on any report.
- **Record progress only in the Sign-off table at the end.** Every step has to
  be done once per property, so the steps themselves carry no checkboxes: a tick
  beside a step cannot say which property it refers to.
- **A note on navigation.** Google reorganised the GA4 Admin menu, so your
  property may show either the current labels (used below) or the older ones
  (noted in italics). If neither matches, the Admin page has a **search box at
  the top of its left column** — searching the setting name is the most reliable
  route and survives future reshuffles.

## Step 0 — confirm you are in the right property

Getting this wrong means configuring staging twice and production never.

1. Click **Admin** (the gear icon, bottom of the far-left nav).
2. In the left column, go to **Property → Property details**.
3. Note the property name and ID.
4. Go to **Data collection and modification → Data streams**, click the web
   stream, and read the **Measurement ID** in the top right.
5. Confirm it matches the table above for the environment you intend to
   configure.
6. While here: if the stream is still called **my-web-app** (the GA4 default),
   rename it to `Schemes.sg staging` or `Schemes.sg production`. With two
   properties to configure, an unnamed stream is the easiest way to lose track
   of which one you are in.

## Step 1 — Data retention

**Admin → Data collection and modification → Data retention**
*(older layout: Admin → Data Settings → Data Retention)*

| Field | Value |
| --- | --- |
| Event data retention | **14 months** |
| Reset user data on new activity | **Off** |

Press **Save**.

The default is 2 months, and it is the single most commonly regretted default —
raising it later does not recover expired data.

"Reset user data on new activity" is deliberately **off**: with it on, a
returning visitor's data is retained indefinitely, which is hard to reconcile
with PDPA's Retention Limitation Obligation and makes the `/privacy` retention
statement impossible to phrase honestly. Turning it off does **not** affect
standard aggregated reports — it only bounds how far back a *new* exploration
can reach.

## Step 2 — Reporting identity

**Admin → Data display → Reporting identity**
*(older layout: Admin → Reporting Identity)*

Select **Observed**. Press **Save**.

The panel offers **Blended** and **Observed**. Observed evaluates user ID then
device ID, with no modelling. The app never calls `setUserId`, so device ID is
the only identifier it can reach.

Do not leave **Blended** selected. This property currently reports modelling as
unavailable, but the panel also states it will be turned on by default once it
becomes available. Left on Blended, that would add modelled users to an already
low-volume key-event count partway through the baseline window, with no action
from you and no notice in the reports.

Unlike steps 1, 3, 4, 7 and 9, this setting applies when a report is queried
rather than when data is collected. It is reversible, and it restates historical
reports as well as new ones, so revisiting it later costs nothing.

## Step 3 — Enhanced Measurement toggles

**Admin → Data collection and modification → Data streams** → click the web
stream → under **Enhanced measurement**, click the **gear icon** to expand all
toggles.

GA4 de-duplicates nothing except `purchase`. Any custom event that duplicates an
Enhanced Measurement event produces **permanently doubled data** with no way to
separate it afterwards. That is why this step comes before instrumenting
anything.

| Toggle | Set to | Why |
| --- | --- | --- |
| Page views | **On** | This is our source of `page_view`; the app does not send its own |
| → *Page changes based on browser history events* | **Off** | Expand "Page views" to find this sub-option. Left on, every App Router client navigation produces a duplicate `page_view` |
| Scrolls | **Off** | No decision rides on 90% scroll depth |
| Outbound clicks | **On** | Free, and supplies `link_domain`. We deliberately do not track outbound scheme links ourselves to avoid duplicating this |
| Site search | **Off** | Catalog keyword search does not exist yet (it is commented out) |
| Form interactions | **Off** | Would attach form metadata we have no reason to hold |
| Video engagement | **Off** | No video |
| File downloads | **Off** | No downloads |

Press **Save**.

> Switching Enhanced Measurement on as a whole enables every sub-feature by
> default, including the history-based page view. Expand the toggles and set
> each one explicitly; do not assume the master switch gave you this table.

## Step 4 — Internal traffic definition and filter

Two separate places. Doing only the first has no effect.

### 4a — define what internal traffic is

**Admin → Data collection and modification → Data streams** → web stream →
**Configure tag settings** → **Show all** → **Define internal traffic** →
**Create**.

| Field | Value |
| --- | --- |
| Rule name | `Team traffic` |
| `traffic_type` value | `internal` (leave as default) |
| Match type | **IP address equals** |
| Value | your team's public IP, one rule per address |

Press **Create**.

Find your public IP by searching "what is my IP". Add a row for each person
who will test, and for any office address.

> **Do not commit the actual IP addresses to this file.** They belong in the
> GA4 console and, if the team needs a shared record, in the private team drive
> alongside the other configuration. Everything else in this runbook is safe in
> a public repo — the measurement IDs already ship in the client bundle of every
> page, and the project IDs are already in `.firebaserc` and the workflows.
> Home and office IPs are the one exception.

### 4b — activate the filter

**Admin → Data collection and modification → Data filters**
*(older layout: Admin → Data Settings → Data Filters)*

4a only stamps matching traffic with `traffic_type = internal`. Nothing is
withheld until a filter acts on that stamp. GA4 pre-creates one named **Internal
Traffic**, and its state decides what happens:

| State | Effect |
| --- | --- |
| **Testing** | Nothing is dropped. Events process as normal, and `traffic_type` is available as a dimension, so you can segment internal traffic in or out by hand. |
| **Active** | Matching events are discarded at processing time. They never reach reports and are not recoverable. |
| **Inactive** | The filter does nothing, and `traffic_type` is not usable for segmenting. |

Either way the tag still fires and the request still leaves the browser. The
exclusion happens on Google's side during processing, so a filter is never a way
to stop collection.

**On staging, leave it in Testing.** The team is the only traffic this property
will ever see, so Active would leave every report, exploration and funnel empty
and give steps 10 to 12 nothing to validate against. Testing gets you the stamp
without the loss.

**On production, set it to Active**, once 4a holds the team's IPs.

## Step 5 — Register 12 custom dimensions

**Admin → Data display → Custom definitions** → **Custom dimensions** tab →
**Create custom dimensions** (top right).

All 12 are **Scope: Event**.

> The **Event parameter** must match the code string character-for-character. A
> typo produces a dimension that silently never populates, and GA4 will not let
> you repoint it later.
>
> Display names allow **letters, numbers, spaces and underscores only** and must
> start with a letter — no colons, hyphens or parentheses.

| # | Dimension name | Scope | Event parameter | Description |
| --- | --- | --- | --- | --- |
| 1 | `Chat Send Trigger` | Event | `send_trigger` | Chat — whether a send was a real user submit or an automatic resume after a page refresh. Always filter to user_submit; auto_resume inflates send counts. |
| 2 | `Chat Turn Index` | Event | `turn_index` | Chat — which user turn in the conversation, 1-indexed. |
| 3 | `Chat Failure Stage` | Event | `failure_stage` | Chat — where a turn failed: request (before any token) or stream (mid-flight). |
| 4 | `Chat Last Milestone` | Event | `last_milestone` | Chat — how far a turn got before the user left: sent, status, token or results. |
| 5 | `Chat Had Streamed Text` | Event | `had_streamed_text` | Chat — whether answer text had appeared before the turn was stopped or failed. Distinguishes "gave up" from "changed my mind". |
| 6 | `Scheme Page Contact Method` | Event | `contact_method` | Scheme detail page — agency phone or email tapped. Excludes the Maps link, which Enhanced Measurement already counts. |
| 7 | `Scheme Page Share Outcome` | Event | `share_outcome` | Scheme detail page — how a share ended: native share sheet, dismissed, copied to clipboard, or failed. |
| 8 | `Search Has Results` | Event | `has_results` | Scheme search — whether any schemes were returned. |
| 9 | `Catalog Filter Name` | Event | `filter_name` | Catalog browse — which filter was applied. |
| 10 | `Developer Docs Section` | Event | `section_id` | Developer docs (/developers) — which documentation section scrolled into view. Partner API audience, not scheme seekers. |
| 11 | `Developer Docs Code Sample Operation` | Event | `operation` | Developer docs (/developers) — which partner API operation a copied code sample demonstrates. |
| 12 | `Developer Docs Code Sample Language` | Event | `code_language` | Developer docs (/developers) — programming language of a copied code sample. |

Rows 1 to 7 belong to instrumented events and will populate. Rows 8 to 12
belong to events that have no call sites yet and will stay empty — expected,
not a misconfiguration.

> **Row 12 depends on a code change.** The app currently sends `language`, not
> `code_language`. `language` is an automatically collected GA4 parameter, so it
> must not be used for a custom dimension. Register `code_language` as above and
> rename it in `src/lib/analytics.ts` before `code_sample_copy` is instrumented.

## Step 6 — Register 5 custom metrics

Same page, **Custom metrics** tab → **Create custom metrics**.

Custom metrics are always event-scoped, so there may be no Scope selector.
Ignore the **Calculated metrics** tab — that is a different feature.

| # | Metric name | Event parameter | Unit of measurement | Description |
| --- | --- | --- | --- | --- |
| 1 | `Chat Time to First Token` | `ms_to_first_token` | **Milliseconds** | Chat — send until the first visible answer text. The latency that decides whether someone waits; UI was built for ~45s. |
| 2 | `Chat Time to Answer Complete` | `ms_to_done` | **Milliseconds** | Chat — send until the stream finished. |
| 3 | `Chat Time Since Send` | `ms_since_send` | **Milliseconds** | Chat — elapsed time when a turn was stopped, failed or abandoned. |
| 4 | `Chat Schemes Found` | `schemes_found` | **Standard** | Chat — number of schemes returned with an answer. |
| 5 | `Search Result Count` | `result_count` | **Standard** | Scheme search — number of results returned. |

Getting **Unit of measurement** wrong does not break collection, but the three
timing metrics will render as bare numbers instead of durations, which makes the
latency card much harder to read.

A parameter can be registered as a dimension **or** a metric, never both. If a
metric is rejected, check it was not created as a dimension by mistake.

## Step 7 — Create audiences

**Admin → Data display → Audiences** → **New audience** → **Create a custom
audience**.

> **Conditions cannot be edited after creation.** Only the name and description
> stay editable; the rules are fixed for the life of the audience. Getting one
> wrong means building a replacement and archiving the original, which GA4
> archives rather than deletes. Check the event names against
> `src/lib/analytics.ts` before pressing Save.
>
> Audiences are also not retroactive, so membership only accrues from creation
> onward. Creating one early buys nothing.

### Developer visitors

> **Defer this one.** Its three events have no call sites yet (see the status
> table in `analytics.md`), so it cannot populate, and an audience created now
> is an immutable definition pinned to event names that instrumentation might
> still change. Create it when `docs_section_view`, `code_sample_copy` and
> `generate_lead` are instrumented. `Mobile chat users` below has no such
> problem: `chat_message_send` is already instrumented.

| Field | Value |
| --- | --- |
| Audience name | `Developer visitors` |
| Description | Visitors who used the partner API documentation on /developers |
| Condition | `Event name` → **is one of** → `docs_section_view`, `code_sample_copy`, `generate_lead` |
| Membership duration | 30 days (default) |

Use **is one of** with all three values in one condition rather than three OR'd
conditions. Both audiences use only built-in dimensions (`Event name`,
`Device category`), so neither depends on a custom dimension being searchable,
which they are not until data has been collected.

The `/developers` page serves partner-API integrators — a different audience
from people seeking assistance. Conflating them makes every site-wide metric
harder to read. An audience is the right mechanism for "what kind of visitor is
this"; prefixing parameter names with `dev_` was considered and rejected.

### Mobile chat users

| Field | Value |
| --- | --- |
| Audience name | `Mobile chat users` |
| Description | Mobile visitors who sent at least one chat message |
| Condition | `Event name` → **is one of** → `chat_message_send`, **AND** `Device category` → **exactly matches** → `mobile` |

Needed because on mobile the results panel sits behind a tab, while desktop
shows it permanently. Pooled metrics across both are close to meaningless.

## Step 8 — Fire the events locally and verify in DebugView

Nothing after this point works until the custom events have fired at least
once. No deploy is required:
`analytics-provider.tsx` gates only on the measurement ID and carries no
environment check, so `npm run dev` emits real events into the staging property.

### 8a — one-time setup

**Do this in Chrome.** Google's own debugger extension is Chrome-only, and the
third-party "GA debugger" add-ons for other browsers are mostly Universal
Analytics era: they turn on console logging but never set the `debug_mode` that
DebugView keys off, so the stream stays empty and the setup looks broken.

1. Install **Google Analytics Debugger**, published by Google, from the Chrome
   Web Store. Enable it on the tab under test. **Staging only.**
2. Add three keys to `frontend/.env.local`, values copied from
   `.env.development`:

   ```env
   NEXT_PUBLIC_FIREBASE_PROJECT_ID=
   NEXT_PUBLIC_FIREBASE_APP_ID=
   NEXT_PUBLIC_FIREBASE_MEASUREMENT_ID=
   ```

   The **staging** measurement ID, never production. With no measurement ID the
   provider returns early and every `track()` call is a silent no-op, which
   looks identical to the events being broken.
3. Run `npm run dev`. If `.env.development` points the API at `localhost:5001`,
   start the Firebase emulator too, or no scheme page will load and flows 6 and
   7 below are unreachable.
4. Open **Admin → Data display → DebugView** and leave it visible.

Local events land in staging alongside real staging data. That is the reason
step 4 leaves the internal traffic filter in **Testing** rather than Active.

### 8b — the seven flows

Run each once, then click the event in the DebugView timeline to read its
parameters. The Top Events card is not enough on its own: it shows counts, and
nearly every assumption here lives in a parameter.

| # | Do this | Expect |
| --- | --- | --- |
| 1 | From `/`, submit a real query and let the stream finish | `chat_message_send` (`turn_index: 1`, `send_trigger: user_submit`), then `chat_answer_shown` with a **non-zero** `ms_to_first_token`. Always zero means the stream emits no `text` events and that assumption is wrong |
| 2 | Submit, then **refresh while it is still streaming** | `chat_message_send` with `send_trigger: auto_resume`. Let it finish first and nothing fires: the reply commits on stream end, so there is no trailing user turn left to resume |
| 3 | Press **Stop** mid-stream twice: once before any text, once after | `chat_turn_aborted` with `had_streamed_text` **false**, then **true**. Zero `chat_turn_failed` either time |
| 4 | Break the request two ways (see 8c) | `chat_turn_failed` with `failure_stage: request` and `failure_stage: stream`. Zero `chat_turn_aborted` |
| 5 | Submit, then switch browser tabs mid-stream | One `chat_turn_abandoned`. Return and switch away again: **no second event**. Opening DevTools does not count, the tab stays visible |
| 6 | On a scheme that lists contact details, tap a **phone** then an **email** link | `agency_contact_click` with `contact_method: phone` and `email`. Most schemes render no contact card at all, so pick one that does |
| 7 | **Share** a scheme, once per outcome (see 8c) | `scheme_shared` covering `share_outcome` values `web_share`, `dismissed`, `clipboard` |

### 8c — forcing the failure and share paths

**`failure_stage: request`.** DevTools → **Network**. Send one message so the
request appears, then right-click `agent_chat_message` → **Block request URL**
and send again. The full URL is `{NEXT_PUBLIC_API_BASE_URL}/agent_chat_message`.
The rule persists under **Network request blocking** (⋮ → More tools) until
cleared, so remove it before running the other flows.

**`failure_stage: stream`.** Blocking cannot produce this: the request never
starts, so no text ever streams and the stage is always `request`. Send
normally, wait for answer text to appear, then set Network throttling to
**Offline**.

**Share outcomes.** Windows Chrome *does* implement `navigator.share`, so the
button takes the Web Share path by default:

- `web_share` — click Share, complete the share in the Windows sheet
- `dismissed` — click Share, close the sheet without sharing
- `clipboard` — disable Web Share first, then click Share:

  ```js
  Object.defineProperty(navigator, "share", { value: undefined, configurable: true });
  ```

  `share` lives on `Navigator.prototype`, so `delete navigator.share` does
  nothing. The override resets on reload.
- `failed` — disable both, then click Share:

  ```js
  ["share", "clipboard"].forEach((k) =>
    Object.defineProperty(navigator, k, { value: undefined, configurable: true }),
  );
  ```

If `clipboard` yields `failed` instead, the document was not focused:
`clipboard.writeText` requires focus. Click into the page, then click Share. A
`Clipboard write failed:` line in the console confirms that was the cause.

### 8d — negative checks

These matter more than the positive ones: each is an assumption the taxonomy
rests on, and each fails silently.

- Tap the agency **Maps** link → Enhanced Measurement `click` only, and **no**
  `agency_contact_click`. This is what excluding Maps depends on
- A `tel:` tap fires `agency_contact_click` and **no** Enhanced Measurement
  `click`
- Exactly **one** `page_view` per full page load, and **none** on in-app
  navigation. An in-app navigation that produces a `page_view` means step 3's
  history sub-toggle is still on

Without DebugView access the same checks work in the browser's **Network** tab
filtered to `collect`, where `en=` is the event name and `ep.*` / `epn.*` are
the string and numeric parameters.

Record the Enhanced Measurement findings in `analytics.md`'s audit section.
## Step 9 — Mark the key event

**Admin → Data display → Events** → **Key events** tab

Key events are a **tab on the Events page**, not a separate nav item, and there
is no "New key event" button. The on-page banner states the mechanism: *"To mark
an event as a key event, select the star next to the event name."*

> ### This step is blocked until the event has fired
>
> The Events page shows *"All key events and only events from the last 28 days"*.
> `agency_contact_click` will not appear in the list — and therefore cannot be
> starred — until it has been collected at least once. There is no
> pre-registration path in this UI.
>
> Sequence:
>
> 1. Run **step 8**, flow 6: tap an agency **phone** or **email** link on a
>    scheme that lists contact details. No deploy is needed; a local
>    `npm run dev` against the staging measurement ID is enough.
> 2. Confirm it arrives in **DebugView**, which is immediate.
> 3. Then go to **Events → Recent events** and locate `agency_contact_click`.
>    This list can lag up to 24 hours even when DebugView is instant, so expect
>    to come back the next day.
> 4. Click the **star** beside it.
> 5. Open the row's **⋮** menu to set the counting method and confirm no default
>    value.
>
> Because marking is **not retroactive**, do it as soon as the event appears
> rather than at the end of the setup.
>
> GA4 pre-creates a `purchase` key event with no data. It will never fire here —
> harmless to leave, or unstar it to keep the list honest.

Once the event appears and you have starred it, set via the row's **⋮** menu:

| Field | Value |
| --- | --- |
| Event name | `agency_contact_click` (starred in the list) |
| Counting method | **Once per event** |
| Default key event value | **Leave unset** — do not set a value or currency |

> ### Do not use the "Create an event" dialog
>
> The **Events** page has a prominent **Create event** button that opens a
> dialog titled *"Create an event"*, offering **Create without code** and
> **Create with code**. It is easy to land there, and **both options are wrong
> here.**
>
> - *Create without code* derives a brand-new event from an existing one plus
>   conditions — it will demand a trigger event and a URL, and produce an event
>   that is not the one your code sends.
> - *Create with code* only reserves a name and tells you to install code. The
>   code is already installed, and this does **not** mark anything as a key
>   event.
>
> You are not creating an event. `agency_contact_click` already exists —
> `agency-contact-card.tsx` calls `track("agency_contact_click", ...)` on `tel:`
> and `mailto:` taps. You are marking an existing name as a key event by
> starring it in the list, as described above.

**Why "Once per event":** the headline metric is the share of *sessions* with at
least one key event, which GA4's native Session key event rate computes
correctly under either setting. "Once per event" therefore costs nothing at the
session level while preserving the detail of someone tapping both phone and
email — detail that "Once per session" discards permanently.

**Why no default value:** that field feeds GA4's revenue metrics. Contacting an
agency has no monetary value, and assigning a nominal one would fill revenue
columns with meaningless figures. Weighting a key event is an analysis decision,
not a collection one.

Mark **only** this one. Contacting a human is the strongest observable evidence
someone actually got help. Do **not** mark `chat_answer_shown` (it measures our
delivery, not the user's outcome) or `scheme_detail_view` (mid-funnel; marking it
would push conversion toward 100% for search traffic and destroy the headline
number).

## Step 10 — Build the explorations

> ### Do this once events are arriving, deployed or not
>
> Explorations query collected data. On an empty property every table renders
> blank, and a Funnel exploration's event picker is populated from events GA4
> has actually seen — so `chat_message_send` will not be offered until it has
> fired. A local `npm run dev` session against the staging measurement ID
> satisfies that; a deploy is not required.

### How the Explore UI works

This is the part that trips people up. Three panels, left to right:

1. **Variables** — the *pool* of what is available. Contains EXPLORATION NAME,
   the date range, and SEGMENTS / DIMENSIONS / METRICS, each with a **+**.
   Clicking **+** opens a picker; custom definitions are under the **Custom**
   group, or search by display name, then **Confirm**. Adding something here
   makes it available — it does **not** put it on the report.
2. **Settings** — the *report itself*. Starts with a **TECHNIQUE** dropdown
   (Free form, Funnel exploration, …). The slots below change with the
   technique, so a Free form and a funnel look nothing alike.
3. **The canvas** — the output. "No data for this combination of segments,
   values, filters and date range" means exactly that: usually an empty
   property or a date range before the events existed, not a configuration
   error.

The rule: **add to Variables first, then drag into Settings.** A dimension
sitting in Variables with nothing on screen is the missing second half.

Note that **funnels do not use ROWS or VALUES** — those are Free form slots. A
funnel's conditions live in its **STEPS** editor. Adding a dimension to
Variables for a funnel is only needed if you want it as a BREAKDOWN.

Start with the integrity strip below — it is the simplest and teaches the UI.

### 10a — Integrity strip (Free form, start here)

**Explore** → **Free form**.

| Panel | Action |
| --- | --- |
| Variables → DIMENSIONS **+** | add `Event name` and `Chat Send Trigger`, Confirm |
| Variables → METRICS **+** | add `Event count`, Confirm |
| Settings → ROWS | drag `Chat Send Trigger` |
| Settings → VALUES | drag `Event count` |
| Settings → FILTERS | `Event name` **exactly matches** `chat_message_send` |

Rename the exploration (top left) to `Integrity strip`.

Watch the `auto_resume` share. If it climbs, either the backend slowed down or
the resume dedupe broke — and every other number is suspect until that is
explained.

### 10b — Turn outcome mix (Free form)

| Panel | Action |
| --- | --- |
| Variables → DIMENSIONS | `Event name` |
| Variables → METRICS | `Event count` |
| Settings → ROWS | `Event name` |
| Settings → VALUES | `Event count` |
| Settings → FILTERS | `Event name` **matches regex** `chat_answer_shown\|chat_turn_aborted\|chat_turn_failed\|chat_turn_abandoned` |
| Settings → Visualization | **Stacked bar chart** |

The four-way split is the payoff of keeping stop and failure separate: it
distinguishes giving up, changing your mind, and hitting a bug.

### 10c — Answer latency (Free form)

| Panel | Action |
| --- | --- |
| Variables → DIMENSIONS | `Device category` |
| Variables → METRICS | `Chat Time to First Token`, `Chat Time to Answer Complete` |
| Settings → ROWS | `Device category` |
| Settings → VALUES | both metrics |

Click each metric chip in VALUES to change its aggregation from Sum to
**Median**. Sum of a duration is meaningless — this is the easiest thing to get
wrong here.

First real evidence on whether anyone tolerates the ~45 second wait the UI was
designed around.

### 10d — Search to help funnel (Funnel exploration)

**Explore** → **Funnel exploration**.

Set these in the **Settings** panel, top to bottom:

| Setting | Value |
| --- | --- |
| TECHNIQUE | `Funnel exploration` |
| VISUALISATION | `Standard funnel` |
| MAKE OPEN FUNNEL | **on** (toggle blue) |
| SEGMENT COMPARISONS | leave empty |
| STEPS | click the **pencil icon** — see below |
| BREAKDOWN | leave empty for now; `Device category` is the useful one once data exists |
| ROWS PER DIMENSION | `5` (default, only matters with a breakdown) |
| SHOW ELAPSED TIME | **on** — shows average time between steps, which is the latency question this whole design cares about |
| NEXT ACTION | leave empty |

**MAKE OPEN FUNNEL** matters: a closed funnel only counts people who entered at
step 1, silently excluding anyone who arrives mid-journey.

Then click the **pencil** beside STEPS. Each step takes a name and a condition:

| Step | Name | Condition |
| --- | --- | --- |
| 1 | Question sent | event `chat_message_send`, then **Add parameter** → `send_trigger` **exactly matches** `user_submit` |
| 2 | Answer shown | event `chat_answer_shown` |
| 3 | Agency contacted | event `agency_contact_click` |

**Apply**, then set EXPLORATION NAME (Variables panel) to `Search to help`.

The step-1 parameter filter is not optional: without it, auto-resumed turns
after a page refresh inflate the funnel's entry count. Note this condition goes
**inside the STEPS editor** — adding `Chat Send Trigger` to Variables does not
filter anything, it only makes the dimension available as a BREAKDOWN.

## Step 11 — Report collection

**Reports → Library** (bottom of the left nav) → **Create new collection**.

| Field | Value |
| --- | --- |
| Collection name | `Schemes.sg` |

Drag in the saved explorations plus the standard **Acquisition** and
**Engagement** reports, then **Save** and **Publish** the collection so it
appears in the left nav for the whole team.

A curated collection means people land on the right view instead of browsing —
which is the entire point of keeping the event list small.

## Step 12 — Baseline, do not set targets

There are no custom events in history, so every number starts from zero. Record
values for **14 days** and set no thresholds. Any "below X% means act" rule
written before that window is a guess wearing a number.

## Sign-off

This table is the only place progress is recorded. The steps above deliberately
carry no checkboxes: every one of them has to be done once per property, so a
tick inside a step would claim more than it can know.

| Step | Staging | Production |
| --- | --- | --- |
| 0 — Property confirmed | ☑ | ☐ |
| 1 — Data retention | ☑ | ☐ |
| 2 — Reporting identity | ☑ | ☐ |
| 3 — Enhanced Measurement | ☑ | ☐ |
| 4 — Internal traffic rule | ☑ | ☐ |
| 4 — Filter state | ☑ Testing | ☐ Active |
| 5 — 12 custom dimensions | ☑ | ☐ |
| 6 — 5 custom metrics | ☑ | ☐ |
| 7 — Audiences | ☑ | ☐ |
| 8 — Events fired, DebugView verified | ☑ | n/a |
| 9 — Key event | ☐ | ☐ |
| 10 — Explorations | ☐ | ☐ |
| 11 — Report collection | ☐ | ☐ |
| 12 — Baseline started | ☐ | ☐ |

Staging measurement ID confirmed: `G-________________`
Production measurement ID confirmed: `G-________________`
Baseline window start date: ______________________

Completed by / date: ______________________

> **Step 8, outstanding detail (2026-10-05).** The run confirmed
> `agency_contact_click`, `chat_answer_shown`, `chat_turn_aborted`,
> `chat_turn_failed`, `chat_turn_abandoned` and `scheme_shared` in DebugView.
> Still unconfirmed: `chat_message_send`, which did not appear in the Top
> Events card even though every outcome event above gates on the same
> `sendAtRef` that is set beside it, so its absence is not possible as read.
> Check **Reports → Realtime**, which has no processing lag, before treating
> step 8 as fully closed. Also unverified: `send_trigger: auto_resume`
> (flow 2), `had_streamed_text: true` from a second Stop (flow 3), and the
> flow-6 Maps negative check.
