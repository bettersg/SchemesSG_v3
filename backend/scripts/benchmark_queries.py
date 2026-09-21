"""Ground-truth query set for search-retrieval benchmarking.

CURATION METHOD (v2) — see BENCHMARK_README.md for the full rationale.

Two relevance signals per query, kept separate:

1. GOLD (primary, human-judged, uncontaminated):
   `gold_relevant` is a hand-picked set of scheme_ids that a caseworker would
   consider genuinely on-target for the query, judged from each scheme's
   DESCRIPTION — NOT from its category tag. This matters because `scheme_type`
   is concatenated into the text that gets embedded (see populate_embeddings.py
   `build_desc_booster`), so category-match relevance is partly circular. The
   gold set is judged independently of both the tag and the ranking, so metrics
   over it are not circular. It is deliberately small and precise.

2. CATEGORY POOL (secondary, weak signal, for recall context only):
   `pool_categories` with `pool_mode` = "and" | "or". A scheme is pool-relevant
   if its scheme_type facets satisfy the mode. Reported separately and clearly
   labelled as a weak/contaminated signal.

Queries are the ACTUAL product-invited prompts, taken verbatim from the frontend
(frontend/src/lib/landing-i18n/translations/en.ts): the search placeholder, the
search hint examples, and the category chips. `tier`:
  "specific" — real compound help-seeker phrasings (the discriminating tests)
  "generic"  — the "I need X support" chips (a floor, not a real test; broad by design)

scheme_ids verified present in prod via the candidate dump.
"""

QUERIES = [
    # ---------------------------------------------------------------- specific (real) prompts
    {
        "id": "s01",
        "query": "I'm a single parent looking for financial assistance",
        "tier": "specific",
        # RULE (verified via who_is_it_for): relevant = financial aid whose target group
        # includes single parents OR general low-income families. Single-parent-specific
        # (who names "Single parents") is ideal but broad low-income family aid also counts,
        # applied consistently to ALL such schemes in the pool (fixes v2 inconsistency).
        "intent": "Financial aid for a single-parent / low-income family; single-parent-specific support is ideal.",
        "gold_relevant": [
            "Zp8NHt34Fn0iPMQVnA7v",  # HCSA Dayspring SPIN — single-parent specific (who: Single parents)
            "fw9CubwfGkAcgqB5sVpB",  # Family LifeAid — who: Single parents; cash/vouchers
            "d5d8Cc0BgYXlwC6uFIyT",  # Breadline Group — who: Single parents; cash/food
            "QrSK1ke7AHmiiJ1350Qq",  # Child Care Financial Assistance (CCFA) — MSF, low-income families
            "b8dH5ktNQLqbRUYbhtVh",  # ONE Emergency Fund — low-income families
            "IVTZrp8zeTbuLgec60bG",  # ComCare Interim Assistance — MSF
            "sT2x8sh5Ge8hrLqvzk6M",  # Sikh Welfare FA & Food — low-income families
            "aw2skODcmT2Yzc0ih6ef",  # Muslimin Trust Fund — cash for low-income families
            "z9hOQiEgpSK36wD8bZNo",  # MOE-FAS — school-fee aid for low-income families
            "M5B6DUSKLDoGL97z0t56",  # ST School Pocket Money Fund
        ],
        "pool_categories": ["Single Parents", "Financial Assistance"],
        "pool_mode": "or",
    },
    {
        "id": "s02",
        "query": "healthcare subsidies for seniors",
        "tier": "specific",
        "intent": "Government/community healthcare cost subsidies specifically for elderly. Non-healthcare senior perks are NOT relevant.",
        "gold_relevant": [
            "iol6ea7rylJvuK14byGY",  # Pioneer Generation Package
            "qA6GtDXuV49biV9ER6qX",  # Merdeka Generation Package
            "zaLdcbwlK49THVXQbtBi",  # CHAS
            "4IkhF2VckuRoJrNY281V",  # Subsidies for Services & Drugs at Public Healthcare Institutions
            "VHMs8PD8AxFHFCMSds8x",  # Medifund
            "puq0Bq1cZqkQl6swG3N2",  # Seniors' Mobility & Enabling Fund (SMF)
            "xLzabY4HEQmB6nXqOeKE",  # SMF (dup listing)
            "g46qLiec2dbf0M9GCash",  # Medical Fee Exemption Card
        ],
        # NOT gold (senior-related but not healthcare subsidies): Mobile Access for Seniors,
        # Silver Housing Bonus, EASE — good negative-precision probes.
        "pool_categories": ["Elderly", "Healthcare"],
        "pool_mode": "and",
    },
    {
        "id": "s03",
        "query": "education grants for low-income families",
        "tier": "specific",
        # RULE: relevant = education grant/bursary/subsidy whose who names low-income
        # students/families. Applied to ALL such schemes in the pool (added ECF, Howe
        # Yoon Chong, SIWEC that v2 wrongly omitted).
        "intent": "Bursaries/grants covering school costs for low-income households.",
        "gold_relevant": [
            "z9hOQiEgpSK36wD8bZNo",  # MOE-FAS
            "Vk4emzGVkvsgWIIjtgeH",  # Tzu Chi Education Assistance
            "2PH8aoyT5krvcKlNKO8m",  # Bless Community Services Bursary
            "M5B6DUSKLDoGL97z0t56",  # ST School Pocket Money Fund
            "PpJJ4VMJgBTQ5Et86OkK",  # FaithActs Bursary
            "PYkEuLhFx3lrLsoNpnDP",  # Student Care Fee Assistance
            "xZ2Y52vJR4GYuZtVyuaq",  # KiFAS
            "uRviEIAFnGEg0FerpwvN",  # SINDA Bursary
            "ui0ZzB5ZHLEfdbOPOhkj",  # ECF-MSF Youth Study Sponsorship — low-income youth
            "PsYGAqqFCJoQYqzFBxpy",  # Howe Yoon Chong PSA Endowment — lower-income students
            "GWLtNdrg2hlYbLXt3rgI",  # SIWEC Education Support — low-income families
        ],
        "pool_categories": ["Education Support", "Low Income"],
        "pool_mode": "and",
    },
    {
        "id": "s04",
        "query": "I need support for seniors or caregivers",
        "tier": "specific",
        # RULE: query is "seniors OR caregivers" -> relevant = caregiver-support service
        # OR eldercare/senior-support service. v2 undercounted; added Apex, REACH,
        # SingHealth DSG, Fun with Seniors, Aces HelpLife, TCN, Touch Care Line.
        "intent": "Caregiver support and/or eldercare services (support groups, respite, care coordination, senior support).",
        "gold_relevant": [
            "VmfvFBf6IV0aShBbnTuf",  # Caregiver support — Apex Day Rehab
            "TmW9ZKqncGcIIjsIwGiH",  # Dementia Caregiver Support Group — SingHealth
            "Sss8NdSTBpSyENQys6H7",  # Fun with Seniors — eldercare (Bartley)
            "wEA8flbaEVctMSiG7qkf",  # Caregiver Empowerment Programme — Fei Yue
            "xjc0lc4YgvEkyTUZwIcj",  # Senior Service — REACH (caregiver group + elder-sitting)
            "i2XNihts4QddyEViFaox",  # Caregiver Support Group — Care Corner
            "Z4Qs1QdK2631MgfeZuFf",  # Dementia Support Group — SingHealth
            "WfrZx3QSQS3bpkzic8C1",  # Caregiver Support Group (Dementia) — ADA
            "7Hro3wmRTKB6dWgWDPJf",  # Caregiver Support — Caregivers Alliance
            "5TkaUtDBWCe7D1EtHKbu",  # Caregiver Support - ABLE (respite)
            "UNwSsM4Axo1Xjl7Z9x2v",  # Aces HelpLife — senior helpline/support
            "LJpeo2hSu3mAcdM0OqfT",  # The Compassionate Network — caregiver support
            "VtPfls03nudIeFT6v3mg",  # TOUCH Caregivers Support
            "1c0yDwyGxsxXnLQSmd9N",  # Caregivers Support Care Line — TOUCH
            "0IfTwD0f8BbxmpxapZQ2",  # South West Caregiver Support Fund
        ],
        "pool_categories": ["Caregiver Support", "Elderly"],
        "pool_mode": "or",
    },
    {
        "id": "s05",
        "query": "I need disability or transport support",
        "tier": "specific",
        # RULE: query is "disability OR transport" -> relevant = disability support
        # (any form) OR transport subsidy. v2 counted only transport-flavoured PWD schemes;
        # added general PWD support (SPD, SG Enable T&E, GCT Enable Fund, DDRID, MDW levy).
        "intent": "Disability support (any form) and/or transport subsidies for persons with disabilities.",
        "gold_relevant": [
            "KNL65E3Xboyaq7g1SMSv",  # Transport Subsidy & Assistive Device — MDAS
            "s012QOvPD7My1dhAQ2Ps",  # VWO Transport Subsidy Scheme — SG Enable
            "xN1HJc8wwG8ayfLS4jIb",  # PWD Concession Card
            "e2egFPQrZ9bpHLXLJrFB",  # Car Park Label Scheme
            "BBnps4FBmDd4IEehux5i",  # Mediacorp Enable Fund
            "Urm8NdzC86hhSjPT8lQI",  # Disabled Persons Scheme
            "RtO56I4mM2idhkkIZ77I",  # Taxi Subsidy Scheme — SG Enable
            "wlHkIcBIE3uzOr1PVJlv",  # Red Cross TransportAid
            "yLpsEHsa73tzCs6vWNy1",  # DDRID Card — PWD benefits
            "iHouZVRtBS5Ae3HscUvI",  # Employment Support Services — SPD (PWD)
            "6cq8DH2FxDqt3tVzzu8N",  # Training & Employment — SG Enable (PWD)
            "BcNpEGRsH4qulMHwGjgn",  # Goh Chok Tong Enable Fund — PWD financial aid
            "v9iMpVdmfoMmxN6rwrTz",  # MDW Levy Concession for PWD
        ],
        "pool_categories": ["Persons with Disabilities (PWD)", "Transport Support"],
        "pool_mode": "or",
    },
    {
        "id": "s06",
        "query": "I need legal or safety support",
        "tier": "specific",
        # RULE: query is "legal OR safety" -> relevant = legal aid/advice service OR
        # protection-from-violence / personal-safety service. Added NuLife, MWC clinic,
        # CLAS, HOME helpdesk, SHECARES that v2 omitted.
        "intent": "Legal aid/advice and/or protection from violence / personal safety services.",
        "gold_relevant": [
            "d6eSRmm58kbDpA6Qka5X",  # Legal Aid Bureau
            "5VYXSODNu5FoZb2eCftd",  # Family Justice Support Scheme — Pro Bono SG
            "u3DWJt5hXjR03US6HFeA",  # Family Violence Protection — Care Corner
            "Tfp7Xk9kP7bSI43uPtL0",  # FV Protection & Sexual Violence Recovery — TRANS SAFE
            "Oacf2JttJ03Y2KpMZW75",  # CLG Legal Clinic
            "k6IoeMjmBcrp3FrrE2CS",  # Legal Counselling — NuLife (PPO, legal aid)
            "jbMJoeGWRnlMaFydHdCs",  # SHECARES — online-harms safety + pro bono legal
            "oNsKWVfQKblXSiuDIKhX",  # Sexual Assault Care Centre — AWARE
            "00uFr8EP5kJsqgh7G33h",  # PAVE — PPO info
            "SXUEBKl0ABcYmxqw1gjS",  # HOME — legal aid + shelter for migrant workers
            "19mcPrH8hmMFW9fMaK8B",  # Free Legal Clinic for Migrant Workers — MWC
            "drouKyI7r0aBS0yVqZab",  # PAVE Integrated Services PSC
            "zhtMoyXOfxzAIRxolRSe",  # Criminal Legal Aid Scheme (CLAS) — Pro Bono SG
        ],
        "pool_categories": ["Legal Aid", "Protection from Violence", "Abuse/Family Violence"],
        "pool_mode": "or",
    },
    # ---------------------------------------------------------------- generic chips (floor, not a real test)
    {"id": "g01", "query": "I need financial assistance", "tier": "generic", "intent": "Broad financial aid.",
     "gold_relevant": [], "pool_categories": ["Financial Assistance"], "pool_mode": "or"},
    {"id": "g02", "query": "I need support for my family or children", "tier": "generic", "intent": "Broad family/children.",
     "gold_relevant": [], "pool_categories": ["Family", "Children"], "pool_mode": "or"},
    {"id": "g03", "query": "I need health and wellbeing support", "tier": "generic", "intent": "Broad health/mental health.",
     "gold_relevant": [], "pool_categories": ["Healthcare", "Mental Health"], "pool_mode": "or"},
    {"id": "g04", "query": "I need housing or food support", "tier": "generic", "intent": "Broad housing/food.",
     "gold_relevant": [], "pool_categories": ["Housing/Shelter", "Food Support"], "pool_mode": "or"},
    {"id": "g05", "query": "I need education support", "tier": "generic", "intent": "Broad education.",
     "gold_relevant": [], "pool_categories": ["Education Support"], "pool_mode": "or"},
    {"id": "g06", "query": "I need employment or training support", "tier": "generic", "intent": "Broad employment/training.",
     "gold_relevant": [], "pool_categories": ["Employment Support", "Vocational Training"], "pool_mode": "or"},
    {"id": "g07", "query": "I need support for seniors or caregivers", "tier": "generic", "intent": "Broad senior/caregiver.",
     "gold_relevant": [], "pool_categories": ["Elderly", "Caregiver Support"], "pool_mode": "or"},
    {"id": "g08", "query": "I need disability or transport support", "tier": "generic", "intent": "Broad disability/transport.",
     "gold_relevant": [], "pool_categories": ["Persons with Disabilities (PWD)", "Transport Support"], "pool_mode": "or"},
    {"id": "g09", "query": "I need legal or safety support", "tier": "generic", "intent": "Broad legal/safety.",
     "gold_relevant": [], "pool_categories": ["Legal Aid", "Protection from Violence"], "pool_mode": "or"},
    {"id": "g10", "query": "I need community support", "tier": "generic", "intent": "Broad community.",
     "gold_relevant": [], "pool_categories": ["General Public Support", "Community Support", "Community Funding"], "pool_mode": "or"},
]
