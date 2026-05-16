export const SITE_URL = "https://schemes.sg";
export const SCHEMES_SG_LOGO_URL = `${SITE_URL}/logo.svg`;

export const SEO_COPY = {
  productName: "Schemes.sg",
  homeTitle: "Find the Right Schemes, All in One Place | Schemes.sg",
  homeDescription:
    "AI-powered search to help you discover the social assistance schemes you deserve. Over 500 schemes from 200+ agencies.",
  aboutTitle: "About Schemes.sg | Find the Right Schemes, All in One Place",
  aboutDescription:
    "Schemes.sg is an AI-powered search engine that helps you discover public social assistance schemes you may be eligible for.",
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
