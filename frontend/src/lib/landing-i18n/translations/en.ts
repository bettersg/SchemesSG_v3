import type { Translations } from "../types"

export const en: Translations = {
  nav: {
    about: "About",
    contribute: "Contribute",
    catalog: "Catalog",
    comingSoon: "Coming Soon",
    searchSchemes: "Search Schemes",
  },

  hero: {
    headline: "Find the Right\nSchemes, All in\nOne Place",
    subtitle:
      "AI-powered search to help you discover the social assistance schemes you deserve. Over 500 schemes from 200+ agencies.",
    volunteerBanner: "Built by volunteers at",
    getInvolved: "Get involved",
    searchPlaceholder: "I'm a single parent looking for financial assistance...",
    searchHint:
      'Try: \u201Chealthcare subsidies for seniors\u201D or \u201Ceducation grants for low-income families\u201D',
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
        title: "500+ Schemes, One Place.",
        description:
          "Access government and community schemes from agencies like MSF, MOH, HDB, CPF, and more \u2014 all in one searchable database.",
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
          "Our AI engine searches across 500+ schemes and ranks them by relevance to your specific situation.",
      },
      {
        title: "Apply with Confidence",
        description:
          "Get clear details on eligibility criteria, benefit amounts, and direct links to apply for each scheme.",
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
        "I had no idea there were schemes for my situation until I tried Schemes.sg. It matched me with three programmes I actually qualified for, and one of them covered my kids' school fees. I wish I'd found this sooner.",
      author: "Sarah T.",
      role: "Single mother, Jurong West",
    },
    {
      quote:
        "We used to spend a lot of time manually searching for schemes on behalf of our clients. With Schemes.sg, our social workers can pull up relevant options in seconds. It's become part of our daily workflow.",
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
          "Our search is powered by the same technology behind the best-in-class search engines in the world. We index information from eligibility criteria, location, and many more factors across 500+ schemes. You can also chat with your search results to refine them further based on your needs.",
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

  footer: {
    tagline: "Making social assistance accessible for everyone.",
    productHeading: "PRODUCT",
    resourcesHeading: "RESOURCES",
    legalHeading: "LEGAL",
    productLinks: [
      { label: "Search", href: "#" },
      { label: "Features", href: "#features" },
      { label: "FAQ", href: "#faq" },
    ],
    resourceLinks: [
      { label: "About", href: "#about", comingSoon: true },
      { label: "Contribute", href: "#contribute" },
      { label: "Contact", href: "#", comingSoon: true },
    ],
    legalLinks: [
      { label: "Privacy Policy", href: "#" },
      { label: "Terms of Service", href: "#" },
    ],
    copyright: "\u00A9 {year} Schemes.sg. All rights reserved.",
    madeIn: "Made with care in Singapore",
  },

  a11y: {
    openMenu: "Open menu",
    closeMenu: "Close menu",
    search: "Search",
  },
}
