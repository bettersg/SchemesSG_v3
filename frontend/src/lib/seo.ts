export const SITE_URL = "https://schemes.sg";
export const SCHEMES_SG_LOGO_URL = `${SITE_URL}/logo.svg`;

export const SEO_COPY = {
  productName: "Schemes.sg",
  homeTitle: "Find the Right Schemes, All in One Place | Schemes.sg",
  homeDescription:
    "AI-powered search to help you discover the social assistance schemes you deserve. Over 600 schemes from 200+ agencies.",
  aboutTitle: "About Schemes.sg | Find the Right Schemes, All in One Place",
  aboutDescription:
    "Schemes.sg is an AI-powered search engine that helps you discover public social assistance schemes you may be eligible for.",
  catalogTitle: "Explore Social Assistance Schemes in Singapore | Schemes.sg",
  catalogDescription:
    "Browse 600+ government and community schemes from 200+ agencies, all in one searchable database.",
  developersTitle: "Partner API | Schemes.sg for Developers",
  developersDescription:
    "Read access to the Schemes.sg catalogue for partner organisations. Authentication, endpoints, fields, and errors for the partner API.",
  privacyTitle: "Privacy Policy | Schemes.sg",
  privacyDescription:
    "How Schemes.sg handles your information, and who we share scheme data with.",
  termsTitle: "Terms of Service | Schemes.sg",
  termsDescription:
    "The terms that apply when you use Schemes.sg or access its scheme data.",
  schemeDescriptionFallback:
    "Access government and community schemes from agencies like MSF, MOH, HDB, CPF, and more, all in one searchable database.",
};

export const getSeoImages = (image?: string) => {
  const primaryImage =
    image?.startsWith("http://") || image?.startsWith("https://")
      ? image
      : SCHEMES_SG_LOGO_URL;

  if (primaryImage === SCHEMES_SG_LOGO_URL) {
    return [SCHEMES_SG_LOGO_URL];
  }

  return [primaryImage, SCHEMES_SG_LOGO_URL];
};
