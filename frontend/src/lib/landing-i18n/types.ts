export type Locale = "en" | "zh";
// Future: "ms" | "ta"

export interface Translations {
  nav: {
    about: string;
    contribute: string;
    catalog: string;
    comingSoon: string;
    searchSchemes: string;
  };

  chat: {
    headline: string;
    subtitle: string;
    volunteerBanner: string;
    getInvolved: string;
    searchPlaceholder: string;
    searchHint: string;
    categoryChips: Array<{
      label: string;
      prompt: string;
    }>;
  };

  hero: {
    headline: string;
    subtitle: string;
    volunteerBanner: string;
    getInvolved: string;
    searchPlaceholder: string;
    searchHint: string;
  };

  schemeCategories: string[];

  featured: {
    heading: string;
    partnersHeading: string;
  };

  features: {
    heading: string;
    subtitle: string;
    cards: {
      search: { title: string; description: string };
      suggest: { title: string; description: string };
      database: { title: string; description: string };
      filter: { title: string; description: string };
      agencies: { title: string; description: string };
    };
    tutorial: {
      step: string;
      composerLabel: string;
      categoryPrompts: string[];
      progress: string[];
      assistant: string;
      found: string;
      filterAll: string;
      filterAgency: string;
      filterHealthcare: string;
      filters: string;
      detailTabs: string[];
      previewSchemes: Array<{
        agency: string;
        name: string;
        summary: string;
        typeLabel: string;
      }>;
      detailAgency: string;
      detailScheme: string;
      detailCategoryLabel: string;
      overview: string;
      qualifies: string[];
      apply: string;
      serviceArea: string;
      serviceAreaValue: string;
      contacts: string;
      branchCentral: string;
      branchWest: string;
      centralAddress: string;
      westAddress: string;
      phone: string;
      email: string;
      visit: string;
      share: string;
    };
  };

  agencies: {
    heading: string;
    subtitle: string;
    cta: string;
  };

  howItWorks: {
    badge: string;
    heading: string;
    steps: Array<{
      title: string;
      description: string;
    }>;
  };

  stats: {
    items: Array<{
      label: string;
    }>;
  };

  testimonials: Array<{
    quote: string;
    author: string;
    role: string;
    avatar?: string;
  }>;

  faq: {
    heading: string;
    subtitle: string;
    items: Array<{
      question: string;
      answer: string;
      /** Optional trailing link. Only set where an answer points somewhere. */
      answerLink?: { href: string; label: string };
    }>;
    sidebar: {
      title: string;
      description: string;
      cta: string;
    };
  };

  cta: {
    headline: string;
    subtitle: string;
    button: string;
    note: string;
  };

  /**
   * Developer docs (`/developers`). Narrative copy only: paths, field names,
   * types and error codes are identifiers and live untranslated in
   * `lib/partner-api-reference.ts`.
   */
  developers: {
    heading: string;
    subtitle: string;
    accessBadge: string;
    requestAccess: string;
    contentsHeading: string;
    sections: {
      access: { heading: string; body: string; gate: string };
      quickStart: { heading: string; body: string };
      auth: { heading: string; body: string; warning: string };
      baseUrl: { heading: string; body: string; versionNote: string };
      operations: { heading: string; body: string };
      fields: { heading: string; body: string; omitted: string };
      errors: { heading: string; body: string };
      rateLimits: { heading: string; body: string };
      retired: { heading: string; body: string };
    };
    labels: {
      required: string;
      optional: string;
      example: string;
      queryParams: string;
      pathParams: string;
      bodyParams: string;
      exampleRequest: string;
      exampleResponse: string;
      copy: string;
      copied: string;
      field: string;
      type: string;
      status: string;
      code: string;
      meaning: string;
      header: string;
      description: string;
    };
    errorMeanings: Record<string, string>;
    rateLimitHeaderNotes: Record<string, string>;
  };

  /**
   * Privacy and terms pages. Both currently carry a drafting notice rather than
   * policy text: the pages exist so the footer links resolve, and the real
   * content is slotted in when it is ready.
   */
  legal: {
    privacyHeading: string;
    termsHeading: string;
    noticeTitle: string;
    noticeBody: string;
    interimHeading: string;
    interimBody: string;
    partnerHeading: string;
    partnerBody: string;
    contactCta: string;
  };

  footer: {
    tagline: string;
    schemesHeading: string;
    productHeading: string;
    resourcesHeading: string;
    legalHeading: string;
    schemesLinks: Array<{ label: string; href: string; comingSoon?: boolean }>;
    productLinks: Array<{ label: string; href: string; comingSoon?: boolean }>;
    resourceLinks: Array<{ label: string; href: string; comingSoon?: boolean }>;
    legalLinks: Array<{ label: string; href: string; comingSoon?: boolean }>;
    copyright: string;
    madeIn: string;
  };

  a11y: {
    openMenu: string;
    closeMenu: string;
    search: string;
    expandInput: string;
    collapseInput: string;
    submitExampleQuery: string;
  };
}
