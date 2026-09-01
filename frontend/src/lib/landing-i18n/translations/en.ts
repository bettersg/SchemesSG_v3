import type { Translations } from "../types";

export const en: Translations = {
  nav: {
    about: "About",
    contribute: "Contribute",
    catalog: "Catalog",
    comingSoon: "Coming Soon",
    searchSchemes: "Search Schemes",
  },

  chat: {
    headline: "SchemeSG",
    subtitle:
      "Let us know how we can help you. Please give us more details on which schemes best suit your needs.",
    volunteerBanner: "Built by volunteers at",
    getInvolved: "Get involved",
    searchPlaceholder:
      "I'm a single parent looking for financial assistance...",
    searchHint:
      "Try: \u201Chealthcare subsidies for seniors\u201D or \u201Ceducation grants for low-income families\u201D",
    categoryChips: [
      {
        label: "Financial Assistance",
        prompt: "I need financial assistance",
      },
      {
        label: "Family & Children",
        prompt: "I need support for my family or children",
      },
      {
        label: "Health & Wellbeing",
        prompt: "I need health and wellbeing support",
      },
      {
        label: "Housing & Food",
        prompt: "I need housing or food support",
      },
      {
        label: "Education",
        prompt: "I need education support",
      },
      {
        label: "Employment & Training",
        prompt: "I need employment or training support",
      },
      {
        label: "Seniors & Caregiving",
        prompt: "I need support for seniors or caregivers",
      },
      {
        label: "Disability & Transport",
        prompt: "I need disability or transport support",
      },
      {
        label: "Legal & Safety",
        prompt: "I need legal or safety support",
      },
      {
        label: "Community Support",
        prompt: "I need community support",
      },
    ],
  },

  hero: {
    headline: "Find the Right\nSchemes, All in\nOne Place",
    subtitle:
      "AI-powered search to help you discover the social assistance schemes you deserve. Over 600 schemes from 200+ agencies.",
    volunteerBanner: "Built by volunteers at",
    getInvolved: "Get involved",
    searchPlaceholder:
      "I'm a single parent looking for financial assistance...",
    searchHint:
      "Try: \u201Chealthcare subsidies for seniors\u201D or \u201Ceducation grants for low-income families\u201D",
  },

  schemeCategories: [
    "Healthcare Schemes",
    "Education Support",
    "Housing Grants",
    "Financial Assistance",
    "Eldercare Services",
    "Disability Support",
    "Employment Aid",
    "Family Services",
    "Childcare Subsidies",
    "Mental Health Support",
    "Food Assistance",
    "Legal Aid",
  ],

  featured: {
    heading: "FEATURED ON",
    partnersHeading: "OUR PARTNERS",
  },

  features: {
    heading: "Tools That Work Hard as You",
    subtitle:
      "Explore features that streamline your search and connect you with the right schemes.",
    cards: {
      search: {
        title: "Find Schemes That Fit You",
        description:
          "Describe your situation in plain English. Our AI understands your needs and finds the most relevant schemes \u2014 no jargon required.",
      },
      suggest: {
        title: "Suggest a New Scheme",
        description:
          "Our AI agents responsibly gather publicly available details from the webpage. A volunteer then reviews and approves the listing before it goes live.",
      },
      database: {
        title: "See How We Find Your Matches",
        description:
          "After you send your question, Schemes.sg searches over 600 government and community schemes from agencies like MSF, MOH, HDB, and CPF, then explains what it found.",
      },
      filter: {
        title: "Find the Right Scheme, No Noise",
        description:
          "Use filters to narrow down schemes by agency, category, eligibility criteria, and the type of support you need.",
      },
      agencies: {
        title: "200+ Trusted Agencies.",
        description:
          "Government ministries, statutory boards, and community organisations.",
      },
    },
    tutorial: {
      step: "Step",
      composerLabel: "Describe your situation",
      categoryPrompts: [
        "Financial Assistance",
        "Family & Children",
        "Health & Wellbeing",
      ],
      progress: [
        "Understanding what support may fit your situation",
        "Comparing schemes from trusted agencies",
      ],
      assistant:
        "I found schemes that may help with household expenses and childcare costs.",
      found: "10 schemes found",
      filterAll: "All matches",
      filterAgency: "MSF",
      filterHealthcare: "Health & Wellbeing",
      filters: "Filter by agency or support type",
      detailTabs: [
        "Overview",
        "Who qualifies",
        "How to apply",
        "Agency details",
      ],
      previewSchemes: [
        {
          agency: "Ministry of Social and Family Development",
          name: "ComCare Short-to-Medium-Term Assistance",
          summary:
            "Financial support for households facing temporary difficulty with essential expenses.",
          typeLabel: "Financial Assistance",
        },
        {
          agency: "Ministry of Health",
          name: "Community Health Assist Scheme (CHAS)",
          summary:
            "Subsidies for medical and dental care at participating clinics.",
          typeLabel: "Health & Wellbeing",
        },
      ],
      detailAgency: "Ministry of Social and Family Development",
      detailScheme: "ComCare Short-to-Medium-Term Assistance",
      detailCategoryLabel: "Financial Assistance",
      overview:
        "Short-term financial support for lower-income households facing temporary difficulty.",
      qualifies: [
        "Singapore Citizens and Permanent Residents",
        "Households needing help with essential expenses",
      ],
      apply:
        "Contact your nearest Social Service Office to discuss your circumstances and next steps.",
      serviceArea: "Service area",
      serviceAreaValue: "Available islandwide through Social Service Offices.",
      contacts: "Branches and contacts",
      branchCentral: "Central Singapore",
      branchWest: "West Singapore",
      centralAddress: "512 Thomson Road, Singapore 298136",
      westAddress: "Block 135 Jurong Gateway Road, Singapore 600135",
      phone: "1800 222 0000",
      email: "comcare@msf.gov.sg",
      visit: "Visit website",
      share: "Share scheme",
    },
  },

  agencies: {
    heading: "Discover Schemes From\n200+ Agencies",
    subtitle:
      "We index schemes from key government ministries, statutory boards, and community organisations.",
    cta: "Get Started",
  },

  howItWorks: {
    badge: "How It Works",
    heading: "Find Your Schemes in 3 Steps",
    steps: [
      {
        title: "Describe Your Situation",
        description:
          "Tell us about yourself\u2014your household, employment status, and what kind of help you\u2019re looking for.",
      },
      {
        title: "Get AI-Matched Results",
        description:
          "Our AI engine searches across 600+ schemes and ranks them by relevance to your specific situation.",
      },
      {
        title: "Apply with Confidence",
        description:
          "Get clear details on eligibility criteria, benefit amounts, and direct links to apply for each scheme.",
      },
    ],
  },

  stats: {
    items: [{ label: "Schemes Indexed" }, { label: "Agencies Covered" }],
  },

  testimonials: [
    {
      quote:
        "I had no idea there were schemes for my situation until I tried Schemes.sg. It matched me with three programmes I actually qualified for, and one of them covered my kids' school fees. I wish I'd found this sooner.",
      author: "Sarah T.",
      role: "Single mother, Jurong West",
    },
    {
      quote:
        "Schemes.sg helps our staff quickly find relevant support options for service users. We're excited to see how this tool can strengthen our work with the community.",
      author: "Care Corner Singapore",
      role: "Community Partner",
      avatar: "/landing/featured/carecorner-avatar.png",
    },
  ],

  faq: {
    heading: "Got Questions? We\u2019ve Got Answers",
    subtitle:
      "Find quick answers to the most common questions about how our platform works, what you get, and how to get the most out of it.",
    items: [
      {
        question: "What is Schemes.sg?",
        answer:
          "Schemes.sg is an AI-powered search engine that helps you discover public social assistance schemes you may be eligible for. We aggregate information from over 200 government agencies and community organisations.",
      },
      {
        question: "Is Schemes.sg free to use?",
        answer:
          "Yes, Schemes.sg is completely free. Our mission is to make social assistance information accessible to everyone.",
      },
      {
        question: "How does the AI matching work?",
        answer:
          "Our search is powered by the same technology behind the best-in-class search engines in the world. We index information from eligibility criteria, location, and many more factors across 600+ schemes. You can also chat with your search results to refine them further based on your needs.",
      },
      {
        question: "What types of schemes are covered?",
        answer:
          "We cover a wide range including healthcare subsidies, education bursaries, housing grants, financial assistance, eldercare services, disability support, employment aid, family services, and childcare subsidies.",
      },
      {
        question: "Is my personal information safe?",
        answer:
          "Your privacy is protected by design. We don't require any login or account, which means there's no way for us to know who you are. Your searches are encrypted in transit and at rest, and we never share your information with anyone.",
      },
      {
        question: "How up-to-date is the information?",
        answer:
          "Our database is regularly updated to reflect the latest scheme details, eligibility criteria, and application procedures. We work to ensure all information is current and accurate.",
      },
      {
        question: "Can I access Schemes.sg data through an API?",
        answer:
          "We share scheme data programmatically with a small number of partner organisations, on request. It is not a self-serve public API. Get in touch if your organisation wants to integrate.",
        answerLink: { href: "/developers", label: "Read the developer docs" },
      },
    ],
    sidebar: {
      title: "Suggest a New Scheme",
      description:
        "Know a scheme that\u2019s missing? Help us grow the database by submitting it.",
      cta: "Suggest a scheme",
    },
  },

  cta: {
    headline: "Find the Support You Deserve",
    subtitle:
      "Stop spending hours searching across normal web search. Let our AI match you with the right schemes in seconds.",
    button: "Search Schemes Now",
    note: "Free to use. No sign-up required.",
  },

  developers: {
    heading: "Partner API",
    subtitle:
      "Read access to the Schemes.sg catalogue, so partner organisations can surface the right scheme inside their own product.",
    accessBadge: "By request",
    requestAccess: "Request access",
    contentsHeading: "On this page",
    sections: {
      access: {
        heading: "Getting access",
        body: "This is not a self-serve API. We work with a small number of partner organisations, and each key is issued by hand so we know who is using the data and can reach them if something changes.",
        gate: "Before a key is issued, we confirm our terms of use and privacy policy cover sharing scheme data with your organisation. You will get a sandbox key first, pointed at our development data, so you can build and test before touching anything live.",
      },
      quickStart: {
        heading: "Quick start",
        body: "One request, to check your key works and see the shape of a scheme.",
      },
      auth: {
        heading: "Authentication",
        body: "Every request carries your key in a header. There is no token exchange, no OAuth dance, and no expiry.",
        warning:
          "Keep the key on your server. It is not safe in a browser, a mobile app, or anything a user can read, because it grants your whole quota to whoever holds it.",
      },
      baseUrl: {
        heading: "Base URL and versioning",
        body: "The version is a path segment, so a future version can ship alongside this one without changing any URL you have already built against.",
        versionNote:
          "There is one version today. A request with no version, or an unknown one, returns 404 rather than quietly falling back to v1.",
      },
      operations: {
        heading: "Operations",
        body: "Three read operations. One key covers all of them.",
      },
      fields: {
        heading: "Scheme fields",
        body: "Every scheme we return carries exactly these fields, whether it came from list, retrieve, or search. A field with no value is null rather than absent, so you can rely on the shape.",
        omitted:
          "We hold other fields internally, for review workflow and ranking. Those are deliberately not part of this contract, so our internal changes cannot break your integration.",
      },
      errors: {
        heading: "Errors",
        body: "Every failure returns the same envelope, so you can branch on error.code and never parse a message.",
      },
      rateLimits: {
        heading: "Rate limits",
        body: "Each partner gets a per-minute budget, shared across all three operations: spending it on list also spends it for search. Every response tells you where you stand, so you never have to discover the limit by hitting it.",
      },
      retired: {
        heading: "When a scheme goes away",
        body: "Schemes close, and some are folded into a replacement. If you store scheme ids, handle this case: a retired scheme that was merged returns 404 with the id that replaced it, so you can follow the change instead of silently dropping the record.",
      },
    },
    labels: {
      required: "required",
      optional: "optional",
      example: "For example",
      queryParams: "Query parameters",
      pathParams: "Path parameters",
      bodyParams: "Body parameters",
      exampleRequest: "Request",
      exampleResponse: "Response",
      copy: "Copy",
      copied: "Copied",
      field: "Field",
      type: "Type",
      status: "Status",
      code: "Code",
      meaning: "What it means",
      header: "Header",
      description: "Description",
    },
    errorMeanings: {
      invalid_request:
        "The parameters are wrong. The message names which one.",
      missing_key: "No X-API-Key header was sent.",
      invalid_key: "The key is not one we issued.",
      revoked_key: "The key was valid and has been turned off. Talk to us.",
      not_found: "No such scheme, or it is no longer published.",
      scheme_retired:
        "The scheme was retired and merged. The body carries merged_into.",
      unsupported_version: "The version segment is missing or unknown.",
      method_not_allowed: "Right path, wrong HTTP method.",
      rate_limited: "Your per-minute budget is spent. Retry-After says when.",
      internal_error: "Something broke on our side. Safe to retry.",
    },
    rateLimitHeaderNotes: {
      "X-RateLimit-Limit": "Your budget, in requests per minute.",
      "X-RateLimit-Remaining": "What is left in the current minute.",
      "Retry-After": "Seconds to wait. Only sent with a 429.",
    },
  },

  legal: {
    privacyHeading: "Privacy Policy",
    termsHeading: "Terms of Service",
    noticeTitle: "This policy is being written",
    noticeBody:
      "We are drafting it properly rather than posting boilerplate. This page exists so the link works and so you can see where we have got to.",
    interimHeading: "What holds in the meantime",
    interimBody:
      "Schemes.sg is a free search tool over publicly published government and community scheme information. You can search and browse without an account. We do not sell your data. Search queries are stored so we can improve results, and the feedback you choose to send is stored with it.",
    partnerHeading: "Sharing scheme data with partners",
    partnerBody:
      "We share scheme catalogue and search data with a small number of named partner organisations through our partner API, so they can help people find schemes inside their own services. This covers scheme information, not anything you type into Schemes.sg.",
    contactCta: "Ask us a question",
  },

  footer: {
    tagline: "Making social assistance accessible for everyone.",
    schemesHeading: "SCHEMES",
    productHeading: "PRODUCT",
    resourcesHeading: "RESOURCES",
    legalHeading: "LEGAL",
    schemesLinks: [
      { label: "Financial Assistance", href: "/catalog/financial-assistance" },
      { label: "Health & Wellbeing", href: "/catalog/health-wellbeing" },
      { label: "Housing & Food", href: "/catalog/housing-food" },
      { label: "All Categories", href: "/catalog" },
    ],
    productLinks: [
      { label: "Search", href: "/" },
      { label: "Features", href: "#features" },
      { label: "FAQ", href: "#faq" },
    ],
    resourceLinks: [
      { label: "About", href: "/about" },
      { label: "Contribute", href: "/contribute" },
      { label: "Feedback", href: "/feedback" },
      { label: "Developers", href: "/developers" },
      { label: "Sitemap", href: "/sitemap.xml" },
      { label: "Contact", href: "#", comingSoon: true },
    ],
    legalLinks: [
      { label: "Privacy Policy", href: "/privacy" },
      { label: "Terms of Service", href: "/terms" },
    ],
    copyright: "\u00A9 {year} Schemes.sg. All rights reserved.",
    madeIn: "Made with care in Singapore",
  },

  a11y: {
    openMenu: "Open menu",
    closeMenu: "Close menu",
    search: "Search",
    expandInput: "Expand input",
    collapseInput: "Collapse input",
    submitExampleQuery: "Submit example query",
  },
};
