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

The product also depends on community correction. Each chat response carries a quiet action row where users can give a thumbs up or down (toggleable, and recorded server-side against the session), copy the answer, or open detailed feedback. They can also suggest a correction from a specific scheme section, contribute a missing scheme, or submit general product feedback. Context such as scheme ID and section is carried into the existing feedback text without exposing chat content or session identifiers.

## Agent Behavior

The chat agent is the product's front door. Its behavior is shaped by these expectations, not just its tools:

- **Relevance-driven results, not a fixed count.** A search returns as many schemes as are genuinely relevant to the situation — a narrow need returns a short list, a broad one returns many. The agent does not pad to or cap at a fixed number; it only requests a specific count when the user explicitly asks for one ("show me 20").
- **Reads the source, not just snippets.** When a user needs a contact, phone, email, or application step that isn't in our stored scheme record, the agent fetches the scheme's live page (and follows a relevant child link such as a Contact or Apply page) to find the concrete detail, rather than stopping at a search snippet or handing back a homepage URL. If a web search is needed first, it does that, then reads the page. It reports what it found or states plainly which detail isn't published.
- **Brief by default, detailed on request.** Replies are answer-first and short (a few sentences or bullets) because the scheme cards are already visible, and end by offering one or two specific things to elaborate on. When the user explicitly asks to explain, compare, or go deeper, the agent pulls full scheme details and gives a thorough, well-structured answer.
- **Speaks the user's language.** The agent replies in the language the user writes in (Chinese, Malay, Tamil, etc.), best-effort, defaulting to English when unclear. Follow-up suggestions match the same language. Proper nouns — scheme names, agencies, URLs, emails — stay in their original form. This is independent of the EN/中文 UI toggle, which only translates static page chrome.
- **Cites, never freelances.** Every scheme claim traces to its source; the agent does not invent eligibility or benefits beyond available data (reinforces *Trust through citation*).

## Safety

The agent refuses to produce sexual or sexually suggestive content, racist or hateful content toward any group, and content that attacks or seeks to inflame Singapore's racial or religious harmony, national identity, or institutions — including attempts to bait or roleplay around these limits. Refusals are brief and calm in the user's language, never preachy, and redirect back to finding support schemes. Genuine, good-faith questions about schemes that touch on race, religion, or nationality (for example, schemes for a specific community) are answered normally. The platform's underlying model provider also moderates input and output; when a request is blocked at that layer, the user still sees a calm refusal rather than an error.

## Brand Personality

**Warm, hopeful, plainspoken.**

Voice is human and direct. We talk to people, not applicants. We don't perform sympathy; we treat asking for help as a normal, competent act. We're hopeful without being saccharine: the situation is hard, the path forward is real, here it is. Plainspoken means short sentences, ordinary words, and no bureaucratic euphemism (no "beneficiaries," no "uplift," no "empowerment").

Emotional goal: a user closes the tab feeling clearer and less alone, not lectured at and not pitied.

## Anti-references

- **Generic gov.sg / Whole-of-Government starchy formal.** No navy + white + Helvetica template, no stiff officialese, no dense paragraphs of policy language, no mandatory-looking interfaces.
- **Charity / NGO sympathy aesthetic.** No stock photos of sad people, no donation-CTA framing, no "those in need" language, no pity-driven hierarchy. We are a wayfinding tool, not a fundraiser.
- **Crypto / SaaS hype aesthetic.** No neon gradients, glassmorphism, hero-metric templates, or decorative "AI" shimmer. A restrained loading highlight may communicate active work, but the agent is a feature, not the headline.
- **Generic Tailwind/HeroUI demo look.** No identical icon-heading-text card grids, no out-of-the-box component soup with zero opinion.

Reference lanes we're drawing from: **Linear / Notion / Stripe docs** for product clarity (confident type, generous spacing, restrained color, content-led hierarchy) and **Headspace / Calm** for warmth in tone and pacing — but only in voice and rhythm, not in visual chrome. Visual chrome stays product-restrained; warmth lives in copy and typography.

## Design Principles

1. **Plain language over polish.** Every word in the UI is in everyday English. If a sentence needs rereading, rewrite it. Labels, errors, empty states, and AI output are all held to the same bar.
2. **Dignity by default.** Never frame users as needy, beneficiaries, or recipients. Searching for help is a normal, competent act. Tone, illustration, and microcopy all reflect this.
3. **Answer first, browse second.** The agent and search are the front door. Catalog browsing is a secondary affordance, not the default. A user with a real situation should reach a relevant scheme in one or two interactions.
4. **Trust through citation, quiet chrome.** Every claim about a scheme links to its source agency. The AI never freelances. Visually, UI chrome recedes so content (scheme names, eligibility, next steps) carries the page.
5. **Invite correction at the point of evidence.** Feedback prompts appear only after users have enough context to judge the information. Chat rating stays subtle; scheme corrections are visible but remain secondary to visiting the official source.

## Accessibility & Inclusion

WCAG 2.1 AA baseline. Target contrast: 4.5:1 for body, 3:1 for large text and non-text indicators. Full keyboard reachability for search, agent, results, and detail flows. Respect `prefers-reduced-motion`: persistent animation becomes an explicit static equivalent, and motion is never required to convey state. No information conveyed by color alone. Tap targets ≥ 44px on mobile, including compact filters, tabs, icon controls, and contextual feedback actions. Forms and agent inputs are labeled, with errors announced to assistive tech.

Beyond WCAG: copy is readable at roughly a Primary 6 / lower-secondary level wherever possible, given the citizen audience. Avoid jargon and acronyms without expansion on first use.
