"""Ground-truth query set for the AGENT eval harness.

Unlike the search benchmark (which scores retrieval), this evaluates the LangGraph
router agent end to end: which TOOLS it calls, and the QUALITY of its final answer.

Each item:
  id            : stable id
  query         : the user turn (single-turn; multi-turn ones carry context in the text)
  kind          : "search" (reused from search benchmark) | "agent" (exercises other tools)
  expected_tools: set of tool names the agent SHOULD call, per the router system prompt
                  (functions/agent/prompts/router.py). Ground truth for Tool-Use Accuracy.
                  Order not required; this is a set-membership judgment.
  allow_extra   : tools that are acceptable-but-not-required (not penalised if called,
                  not required if absent). Keeps precision fair for legitimately-optional steps.

Tool names (functions/agent/tools/*): search_schemes, filter_rerank_by_directive,
retrieve_schemes_by_ids, duckduckgo_web_search, fetch_webpage, load_skills.

Routing rules distilled from the system prompt:
- New recommendation / eligibility match            -> search_schemes
- "the best N" / shortlist / rank a subset          -> search_schemes + filter_rerank_by_directive
- "tell me more" / eligibility / how-to / compare   -> retrieve_schemes_by_ids (needs prior schemes)
- refine current results                            -> filter_rerank_by_directive
- contact/apply detail not in data                  -> fetch_webpage (and/or duckduckgo_web_search)
- external / not-in-DB facts                         -> duckduckgo_web_search
- draft / rewrite / polish an email                  -> load_skills(skill="draft_email")
"""

AGENT_QUERIES = [
    # ---- reused from the search benchmark (should route to search_schemes) ----
    {
        "id": "a01",
        "query": "I'm a single parent looking for financial assistance",
        "kind": "search",
        "expected_tools": {"search_schemes"},
        "allow_extra": {"filter_rerank_by_directive"},
    },
    {
        "id": "a02",
        "query": "healthcare subsidies for seniors",
        "kind": "search",
        "expected_tools": {"search_schemes"},
        "allow_extra": {"filter_rerank_by_directive"},
    },
    {
        "id": "a03",
        "query": "education grants for low-income families",
        "kind": "search",
        "expected_tools": {"search_schemes"},
        "allow_extra": {"filter_rerank_by_directive"},
    },
    {
        "id": "a04",
        "query": "I need support for seniors or caregivers",
        "kind": "search",
        "expected_tools": {"search_schemes"},
        "allow_extra": {"filter_rerank_by_directive"},
    },
    {
        "id": "a05",
        "query": "I need disability or transport support",
        "kind": "search",
        "expected_tools": {"search_schemes"},
        "allow_extra": {"filter_rerank_by_directive"},
    },
    {
        "id": "a06",
        "query": "I need legal or safety support",
        "kind": "search",
        "expected_tools": {"search_schemes"},
        "allow_extra": {"filter_rerank_by_directive"},
    },
    # ---- agent-specific: exercise the non-search tools ----
    {
        "id": "a07",
        "query": "Find me financial assistance schemes, then show me just the best 3.",
        "kind": "agent",
        # New search + explicit shortlist -> must sync cards via filter_rerank_by_directive.
        "expected_tools": {"search_schemes", "filter_rerank_by_directive"},
        "allow_extra": set(),
    },
    {
        "id": "a08",
        "query": "Find me schemes for single parents, then tell me how to apply for the top one, "
        "including its contact details.",
        "kind": "agent",
        # Recommendation -> then apply/contact detail -> retrieve details, and if not present, fetch the page.
        "expected_tools": {"search_schemes", "retrieve_schemes_by_ids"},
        "allow_extra": {"fetch_webpage", "duckduckgo_web_search", "filter_rerank_by_directive"},
    },
    {
        "id": "a09",
        "query": "Help me draft an email to a social worker asking about ComCare eligibility for my family.",
        "kind": "agent",
        # Email drafting -> must load the draft_email skill first.
        "expected_tools": {"load_skills"},
        "allow_extra": {"search_schemes", "retrieve_schemes_by_ids"},
    },
    {
        "id": "a10",
        "query": "Are there any brand-new government grants announced in Singapore this month that "
        "aren't in your database yet?",
        "kind": "agent",
        # Up-to-date external facts not in scheme data -> web search.
        "expected_tools": {"duckduckgo_web_search"},
        "allow_extra": {"fetch_webpage", "search_schemes"},
    },
]
