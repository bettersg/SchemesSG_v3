# Dark code panel on the developers reference

## Status

Accepted

## Date

2026-09-01

## Context

`DESIGN.md` sets a Flat-By-Default product register and keeps large dark fields to
the landing CTA fold: "the only large blue field". The `/developers` partner API
reference breaks that shape, because its defining element is a code sample and a
code sample on a warm off-white surface reads as prose rather than as something to
copy.

`developers-page-content.tsx` originally recorded this as a `DEVIATION:` comment in
the file header. Root `AGENTS.md` routes accepted decisions to `docs/adr/`, so a
self-declared deviation in a source comment is not an accepted one — it is an
undocumented departure with a note attached.

Two adjacent constraints also apply:

- **The Wayfinding Rule** (`DESIGN.md:167`): "Color carries meaning or it doesn't
  appear. ... Amber means 'pay attention' and is limited to alerts or rare strong
  CTAs. Anything else is neutral. No decorative color, anywhere."
- **Amber** (`DESIGN.md:149`) is "Reserved for alerts, advisories, and rare strong
  CTAs ... Never decorative."

An earlier revision of the code panel used `--schemes-amber-100` as the
syntax-highlight colour for quoted strings, which is exactly the decorative use
both rules forbid.

## Decision

1. **The code panel is dark, using `--schemes-blue-900`** — the deepest navy
   already in the palette. No new token, and no importing another product's slate.
   Scoped to `CodeBlock`; the rest of the page stays in the light product register.
2. **Syntax highlighting is monochrome.** Structure is carried by contrast, not
   hue: string values sit at full `text-white` against scaffolding dimmed to
   `text-white/70`. No syntax palette is introduced, so the Wayfinding Rule holds —
   colour on this page still means only what it means everywhere else.
3. **HTTP method badges keep their colour**, because method *is* meaning: `GET`
   borrows the existing info tokens (a read), `POST` the alert tokens (a deliberate
   action). This is wayfinding, not decoration, and introduces no new tokens.

## Consequences

- The dark surface is confined to one component, so the deviation cannot spread by
  copy-paste without a reviewer noticing.
- Dropping the syntax palette also dropped the gutter line numbers and the
  per-line render they required, which made `CodeBlock` markedly smaller.
- A real syntax highlighter is now a deliberate future decision rather than
  something that arrives token by token. If the samples ever grow past curl and
  JSON, revisit this ADR rather than adding colours to `highlight()`.
