import { describe, expect, it } from "vitest";
import {
  getCatalogDescription,
  getCatalogJsonLd,
  getCatalogMetadata,
  getCatalogTitle,
} from "./catalog-seo";

describe("catalog SEO", () => {
  it("builds category-specific title and description copy", () => {
    expect({
      title: getCatalogTitle("Health & Wellbeing"),
      description: getCatalogDescription("Health & Wellbeing"),
    }).toEqual({
      title: "Health & Wellbeing Schemes in Singapore | Schemes.sg",
      description:
        "Browse health & Wellbeing schemes in Singapore from government agencies and community organisations. Find eligibility, benefits, application links, and contact details.",
    });
  });

  it("uses the category route as canonical and social metadata", () => {
    const metadata = getCatalogMetadata({
      category: "Education",
      path: "/catalog/education",
    });

    expect(metadata).toMatchObject({
      title: "Education Schemes in Singapore | Schemes.sg",
      alternates: { canonical: "/catalog/education" },
      openGraph: { url: "/catalog/education" },
    });
  });

  it("identifies the selected category in structured data", () => {
    const jsonLd = getCatalogJsonLd({
      category: "Education",
      path: "/catalog/education",
    });

    expect(jsonLd["@graph"][0]).toMatchObject({
      "@type": "CollectionPage",
      about: { "@id": "https://schemes.sg/catalog#education" },
      mainEntity: {
        "@id": "https://schemes.sg/catalog/education#scheme-catalog",
      },
    });
  });
});
