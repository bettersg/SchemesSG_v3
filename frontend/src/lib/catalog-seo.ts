import type { Metadata } from "next";
import {
  CATALOG_CATEGORY_ROUTES,
  CATALOG_CATEGORY_SLUGS,
  type CatalogCategory,
} from "@/lib/design-system/categories";
import { SCHEMES_SG_LOGO_URL, SEO_COPY, SITE_URL } from "@/lib/seo";

const lowerFirst = (value: string) =>
  value.charAt(0).toLowerCase() + value.slice(1);

export const CATALOG_ROUTE_PATHS = [
  "/catalog",
  ...CATALOG_CATEGORY_ROUTES.map(({ slug }) => `/catalog/${slug}`),
];

export function getCatalogCategoryPath(category: CatalogCategory) {
  return `/catalog/${CATALOG_CATEGORY_SLUGS[category]}`;
}

export function getCatalogTitle(category?: CatalogCategory) {
  if (!category || category === "All") {
    return SEO_COPY.catalogTitle;
  }

  return `${category} Schemes in Singapore | Schemes.sg`;
}

export function getCatalogDescription(category?: CatalogCategory) {
  if (!category || category === "All") {
    return SEO_COPY.catalogDescription;
  }

  return `Browse ${lowerFirst(category)} schemes in Singapore from government agencies and community organisations. Find eligibility, benefits, application links, and contact details.`;
}

export function getCatalogMetadata({
  category,
  path,
}: {
  category?: CatalogCategory;
  path: string;
}): Metadata {
  const title = getCatalogTitle(category);
  const description = getCatalogDescription(category);

  return {
    title,
    description,
    alternates: {
      canonical: path,
    },
    openGraph: {
      title,
      description,
      url: path,
      siteName: SEO_COPY.productName,
      type: "website",
      images: [
        {
          url: SCHEMES_SG_LOGO_URL,
          alt: "Schemes.sg logo",
        },
      ],
    },
    twitter: {
      card: "summary_large_image",
      title,
      description,
      images: [SCHEMES_SG_LOGO_URL],
    },
  };
}

export function getCatalogJsonLd({
  category,
  path,
}: {
  category?: CatalogCategory;
  path: string;
}) {
  const pageUrl = `${SITE_URL}${path}`;
  const title = getCatalogTitle(category).replace(" | Schemes.sg", "");
  const description = getCatalogDescription(category);
  const categorySlug = category ? CATALOG_CATEGORY_SLUGS[category] : "catalog";
  const categoryName =
    category && category !== "All"
      ? `${category} schemes`
      : "Social assistance schemes";
  const topic =
    category && category !== "All"
      ? {
          "@type": "DefinedTerm",
          "@id": `${SITE_URL}/catalog#${categorySlug}`,
          name: category,
          description: `${category} is one of the social assistance scheme categories indexed by Schemes.sg.`,
          inDefinedTermSet: {
            "@id": `${SITE_URL}/catalog#scheme-categories`,
          },
        }
      : {
          "@type": "DefinedTermSet",
          "@id": `${SITE_URL}/catalog#scheme-categories`,
          name: "Social assistance scheme categories",
          description:
            "Categories used by Schemes.sg to organise government and community assistance schemes in Singapore.",
          hasDefinedTerm: CATALOG_CATEGORY_ROUTES.filter(
            ({ category: routeCategory }) => routeCategory !== "All",
          ).map(({ category: routeCategory, slug }) => ({
            "@type": "DefinedTerm",
            "@id": `${SITE_URL}/catalog#${slug}`,
            name: routeCategory,
          })),
        };

  return {
    "@context": "https://schema.org",
    "@graph": [
      {
        "@type": "CollectionPage",
        "@id": `${pageUrl}#webpage`,
        url: pageUrl,
        name: title,
        description,
        inLanguage: "en-SG",
        isPartOf: {
          "@id": `${SITE_URL}/#website`,
        },
        publisher: {
          "@id": `${SITE_URL}/#organization`,
        },
        about: {
          "@id":
            category && category !== "All"
              ? `${SITE_URL}/catalog#${categorySlug}`
              : `${SITE_URL}/catalog#scheme-categories`,
        },
        mainEntity: {
          "@id": `${pageUrl}#scheme-catalog`,
        },
      },
      {
        "@type": "ItemList",
        "@id": `${pageUrl}#scheme-catalog`,
        name: `${categoryName} in Singapore`,
        description:
          category && category !== "All"
            ? `A browsable list of ${lowerFirst(category)} schemes indexed by Schemes.sg.`
            : "A browsable database of social assistance schemes indexed by Schemes.sg.",
        itemListOrder: "https://schema.org/ItemListUnordered",
      },
      topic,
      {
        "@type": "WebSite",
        "@id": `${SITE_URL}/#website`,
        name: SEO_COPY.productName,
        url: SITE_URL,
        description: SEO_COPY.homeDescription,
        publisher: {
          "@id": `${SITE_URL}/#organization`,
        },
        potentialAction: {
          "@type": "SearchAction",
          target: `${SITE_URL}/?q={search_term_string}`,
          "query-input": "required name=search_term_string",
        },
      },
      {
        "@type": "Organization",
        "@id": `${SITE_URL}/#organization`,
        name: SEO_COPY.productName,
        url: SITE_URL,
        logo: SCHEMES_SG_LOGO_URL,
        description:
          "Schemes.sg is an AI-powered search engine that makes social assistance information accessible by indexing public schemes from government agencies and community organisations.",
      },
    ],
  };
}
