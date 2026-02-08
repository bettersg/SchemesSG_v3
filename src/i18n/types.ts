export type Locale = "en" | "zh"
// Future: "ms" | "ta"

export interface Translations {
  nav: {
    about: string
    features: string
    contribute: string
    findSchemes: string
  }

  hero: {
    headline: string
    subtitle: string
    volunteerBanner: string
    getInvolved: string
    searchPlaceholder: string
    searchHint: string
  }

  schemeCategories: string[]

  featured: {
    heading: string
    partnersHeading: string
  }

  features: {
    heading: string
    subtitle: string
    cards: {
      search: { title: string; description: string }
      suggest: { title: string; description: string }
      database: { title: string; description: string }
      filter: { title: string; description: string }
      agencies: { title: string; description: string }
    }
  }

  agencies: {
    heading: string
    subtitle: string
    cta: string
  }

  howItWorks: {
    badge: string
    heading: string
    steps: Array<{
      title: string
      description: string
    }>
  }

  stats: {
    items: Array<{
      label: string
    }>
  }

  testimonials: Array<{
    quote: string
    author: string
    role: string
    avatar?: string
  }>

  faq: {
    heading: string
    subtitle: string
    items: Array<{
      question: string
      answer: string
    }>
    sidebar: {
      title: string
      description: string
      cta: string
    }
  }

  cta: {
    headline: string
    subtitle: string
    button: string
    note: string
  }

  footer: {
    tagline: string
    productHeading: string
    resourcesHeading: string
    legalHeading: string
    productLinks: Array<{ label: string; href: string; comingSoon?: boolean }>
    resourceLinks: Array<{ label: string; href: string; comingSoon?: boolean }>
    legalLinks: Array<{ label: string; href: string; comingSoon?: boolean }>
    copyright: string
    madeIn: string
  }

  a11y: {
    openMenu: string
    closeMenu: string
    search: string
  }
}
