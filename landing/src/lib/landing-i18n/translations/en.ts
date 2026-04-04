import type { Translations } from "../types"

export const en: Translations = {
  nav: {
    about: "About",
    contribute: "Contribute",
    catalog: "Explore",
    comingSoon: "Coming Soon",
    searchSchemes: "Find Schemes",
  },

  hero: {
    headline: "Find the \nRight Schemes, \nAll in One Place",
    subtitle:
      "Singapore's AI-powered directory of social assistance schemes",
    volunteerBanner: "Built by volunteers at",
    getInvolved: "Get involved",
    searchPlaceholder: "E.g. I am a cancer patient in need of financial assistance…",
    searchHint: '500+ schemes · 200+ agencies · 100% anonymous',
  },

  schemeCategories: [
    "Financial Aid",
    "Healthcare",
    "Mental Health",
    "Family Support",
    "Housing",
    "Employment",
    "Food Assistance",
    "Education",
    "Eldercare",
    "Disability Support",
    "Childcare",
    "Legal Aid",
  ],

  featured: {
    heading: "FEATURED ON",
    partnersHeading: "OUR PARTNERS",
  },

  features: {
    heading: "Everything you need to find the right help",
    subtitle:
      "From AI-powered search to a comprehensive scheme database — built to cut through the noise.",
    cards: {
      search: {
        title: "Describe your situation, get matched schemes",
        description:
          "Type naturally — no forms, no jargon. Our AI understands context and surfaces the most relevant schemes for your situation.",
      },
      suggest: {
        title: "Suggest a missing scheme",
        description:
          "Know a scheme that's not listed? Submit a link. Our AI agents responsibly extract the details, then a volunteer reviews and approves before it goes live.",
      },
      database: {
        title: "500+ schemes. One place.",
        description:
          "Government and community schemes from MSF, MOH, HDB, CPF, and 200+ agencies — all in one searchable database, always up to date.",
      },
      filter: {
        title: "Filter by agency, category, or location",
        description:
          "Narrow results by scheme type, eligibility criteria, planning area, or agency — so you see only what's relevant to you.",
      },
      agencies: {
        title: "200+ trusted agencies.",
        description:
          "Government ministries, statutory boards, and community organisations.",
      },
    },
  },

  agencies: {
    heading: "Schemes from 200+\nagencies, all in one place",
    subtitle:
      "We index schemes from government ministries, statutory boards, and community organisations across Singapore.",
    cta: "Find Schemes Now",
  },

  howItWorks: {
    badge: "How It Works",
    heading: "Find your schemes in 3 steps",
    steps: [
      {
        title: "Describe your situation",
        description:
          "Tell us about yourself — your household, employment status, and what kind of help you're looking for.",
      },
      {
        title: "Get AI-matched results",
        description:
          "Our AI searches across 500+ schemes and ranks them by relevance to your specific situation.",
      },
      {
        title: "Take action directly",
        description:
          "Get eligibility details, benefit amounts, and direct links to apply — without leaving the page.",
      },
    ],
  },

  stats: {
    items: [
      { label: "Schemes Indexed" },
      { label: "Agencies Covered" },
    ],
  },

  testimonials: [
    {
      quote:
        "I had no idea there were schemes for my situation until I tried Schemes.sg. It matched me with three programmes I actually qualified for — one covered my kids' school fees. I wish I'd found this sooner.",
      author: "Sarah T.",
      role: "Single mother, Jurong West",
    },
    {
      quote:
        "Schemes.sg helps our staff quickly find relevant support options for service users. We're excited to see how this tool can strengthen our work with the community.",
      author: "Care Corner Singapore",
      role: "Community Partner",
      avatar: "/featured/carecorner-avatar.png",
    },
  ],

  faq: {
    heading: "Common questions",
    subtitle:
      "Everything you need to know about how SchemesSG works.",
    items: [
      {
        question: "What is SchemesSG?",
        answer:
          "SchemesSG is an AI-powered search tool that helps you discover social assistance schemes you may be eligible for. We aggregate information from 200+ government agencies and community organisations across Singapore.",
      },
      {
        question: "Is it free to use?",
        answer:
          "Yes, completely free. Our mission is to make social assistance information accessible to everyone — no account, no sign-up required.",
      },
      {
        question: "How does the AI matching work?",
        answer:
          "Describe your situation in plain language. Our AI searches across 500+ schemes and ranks results by relevance to your context — income level, household type, health condition, and more. You can also chat with your results to refine further.",
      },
      {
        question: "What types of schemes are covered?",
        answer:
          "Healthcare subsidies, education bursaries, housing grants, financial assistance, eldercare services, disability support, employment aid, family services, childcare subsidies, food assistance, and more.",
      },
      {
        question: "Is my personal information safe?",
        answer:
          "Your privacy is protected by design. No login, no account — there's no way for us to know who you are. Searches are encrypted in transit and we never share your information.",
      },
      {
        question: "How current is the information?",
        answer:
          "Our database is updated regularly to reflect the latest scheme details, eligibility criteria, and application procedures. Community contributions also help us stay current.",
      },
    ],
    sidebar: {
      title: "Know a missing scheme?",
      description:
        "Help us grow the database. Submit a scheme link and our AI agents will extract the details for volunteer review.",
      cta: "Suggest a scheme",
    },
  },

  cta: {
    headline: "Find the right support today.",
    subtitle:
      "Anonymous and free. No sign-up required.",
    button: "Chat with AI",
    note: "500+ schemes · 200+ agencies · 100% private",
  },

  footer: {
    tagline: "Making social assistance accessible for everyone in Singapore.",
    productHeading: "PRODUCT",
    resourcesHeading: "RESOURCES",
    legalHeading: "LEGAL",
    productLinks: [
      { label: "Search", href: "#" },
      { label: "Features", href: "#features" },
      { label: "FAQ", href: "#faq" },
    ],
    resourceLinks: [
      { label: "About", href: "/about" },
      { label: "Contribute", href: "/contribute" },
      { label: "Feedback", href: "/feedback" },
      { label: "Contact", href: "#", comingSoon: true },
    ],
    legalLinks: [
      { label: "Privacy Policy", href: "#" },
      { label: "Terms of Service", href: "#" },
    ],
    copyright: "\u00A9 {year} SchemesSG. All rights reserved.",
    madeIn: "Built by the community, for the community · Supported by Better.sg",
  },

  a11y: {
    openMenu: "Open menu",
    closeMenu: "Close menu",
    search: "Search",
  },
}
