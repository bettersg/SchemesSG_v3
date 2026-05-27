# Product

## Register

product

The product surfaces (search, agentic chat, results, scheme detail, account) are the default. The `/about` route is the one brand surface and may be designed against the brand register when explicitly named in a task.

## Users

**Primary: Singaporeans looking for help.** Often in a stressful moment (job loss, medical bills, eldercare, housing, caregiving). Frequently mobile, varied digital fluency, varied English fluency. They want a clear answer about what schemes apply to their situation and what to do next, not a catalog to browse.

**Secondary: intermediaries.** Social workers, VWO staff, MP meet-the-people volunteers, family members helping a relative. They scan many cases per day, compare schemes, and share findings with clients. They benefit when the citizen view is already fast and scannable; we don't build a separate "pro" UI.

The job to be done, in one line: *given my situation, tell me which schemes I likely qualify for, link me to the source, and tell me the next concrete step.*

## Product Purpose

SchemesSG helps Singaporeans find government and community assistance schemes through search and an AI agent that interprets natural-language situations. Success is a user reaching a relevant, sourced scheme and knowing the next action within their first session. The site exists because the official scheme landscape is fragmented across agencies, sites, and PDFs, and most people in need don't have time or expertise to navigate it.

## Brand Personality

**Warm, hopeful, plainspoken.**

Voice is human and direct. We talk to people, not applicants. We don't perform sympathy; we treat asking for help as a normal, competent act. We're hopeful without being saccharine: the situation is hard, the path forward is real, here it is. Plainspoken means short sentences, ordinary words, and no bureaucratic euphemism (no "beneficiaries," no "uplift," no "empowerment").

Emotional goal: a user closes the tab feeling clearer and less alone, not lectured at and not pitied.

## Anti-references

- **Generic gov.sg / Whole-of-Government starchy formal.** No navy + white + Helvetica template, no stiff officialese, no dense paragraphs of policy language, no mandatory-looking interfaces.
- **Charity / NGO sympathy aesthetic.** No stock photos of sad people, no donation-CTA framing, no "those in need" language, no pity-driven hierarchy. We are a wayfinding tool, not a fundraiser.
- **Crypto / SaaS hype aesthetic.** No neon gradients, glassmorphism, hero-metric templates, or "AI" shimmer. The agent is a feature, not the headline.
- **Generic Tailwind/HeroUI demo look.** No identical icon-heading-text card grids, no out-of-the-box component soup with zero opinion.

Reference lanes we're drawing from: **Linear / Notion / Stripe docs** for product clarity (confident type, generous spacing, restrained color, content-led hierarchy) and **Headspace / Calm** for warmth in tone and pacing — but only in voice and rhythm, not in visual chrome. Visual chrome stays product-restrained; warmth lives in copy and typography.

## Design Principles

1. **Plain language over polish.** Every word in the UI is in everyday English. If a sentence needs rereading, rewrite it. Labels, errors, empty states, and AI output are all held to the same bar.
2. **Dignity by default.** Never frame users as needy, beneficiaries, or recipients. Searching for help is a normal, competent act. Tone, illustration, and microcopy all reflect this.
3. **Answer first, browse second.** The agent and search are the front door. Catalog browsing is a secondary affordance, not the default. A user with a real situation should reach a relevant scheme in one or two interactions.
4. **Trust through citation, quiet chrome.** Every claim about a scheme links to its source agency. The AI never freelances. Visually, UI chrome recedes so content (scheme names, eligibility, next steps) carries the page.

## Accessibility & Inclusion

WCAG 2.1 AA baseline. Target contrast: 4.5:1 for body, 3:1 for large text and non-text indicators. Full keyboard reachability for search, agent, results, and detail flows. Respect `prefers-reduced-motion`: motion is decorative, never required to convey state. No information conveyed by color alone. Tap targets ≥ 44px on mobile. Forms and agent inputs labeled, with errors announced to assistive tech.

Beyond WCAG: copy is readable at roughly a Primary 6 / lower-secondary level wherever possible, given the citizen audience. Avoid jargon and acronyms without expansion on first use.
