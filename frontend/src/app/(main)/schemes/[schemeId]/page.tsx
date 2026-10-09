import type { Metadata } from "next";
import { notFound, permanentRedirect } from "next/navigation";
import SchemeDetail from "@/components/schemes/scheme-detail";
import { getSchemeById, getSchemesForSitemap } from "@/lib/schemes.server";
import {
  getSeoImages,
  SCHEMES_SG_OG_IMAGE_URL,
  SEO_COPY,
  SITE_URL,
} from "@/lib/seo";
import { getSchemeCategory } from "@/lib/design-system/categories";
import {
  getCatalogCategoryPath,
  getSchemeBreadcrumbListJsonLd,
} from "@/lib/catalog-seo";
import { hasIndexableContent } from "@/lib/scheme-indexing";

type SchemePageProps = {
  params: Promise<{ schemeId: string }>;
};

export async function generateStaticParams() {
  const schemes = await getSchemesForSitemap();
  return schemes.map(({ schemeId }) => ({ schemeId }));
}

const stripMarkdown = (text: string) =>
  text
    .replace(/[#*_`>\-[\]()]/g, " ")
    .replace(/\s+/g, " ")
    .trim();

const truncateDescription = (text: string, maxLength = 155) => {
  const cleanText = stripMarkdown(text);
  if (cleanText.length <= maxLength) {
    return cleanText;
  }
  return `${cleanText.slice(0, maxLength - 1).trim()}...`;
};

export async function generateMetadata({
  params,
}: SchemePageProps): Promise<Metadata> {
  const { schemeId } = await params;
  const scheme = await getSchemeById(schemeId);

  if (!scheme) {
    return {
      title: "Scheme not found | Schemes.sg",
      robots: {
        index: false,
        follow: false,
      },
    };
  }

  if (scheme.status === "retired") {
    return {
      title: scheme.mergedInto
        ? "Scheme moved | Schemes.sg"
        : "Scheme no longer listed | Schemes.sg",
      alternates: scheme.mergedInto
        ? { canonical: SITE_URL + "/schemes/" + scheme.mergedInto }
        : undefined,
      robots: { index: false, follow: Boolean(scheme.mergedInto) },
    };
  }

  const title = `${scheme.schemeName || scheme.agency} | Schemes.sg`;

  let description: string;
  if (scheme.summary) {
    description = truncateDescription(scheme.summary);
  } else if (scheme.description) {
    description = truncateDescription(scheme.description);
  } else if (scheme.searchBooster) {
    description = truncateDescription(scheme.searchBooster);
  } else {
    const parts: string[] = [];
    if (scheme.agency) parts.push(scheme.agency);
    if (scheme.schemeType && scheme.schemeType.length > 0) {
      parts.push(scheme.schemeType[0]);
    }
    if (scheme.targetAudience && scheme.targetAudience.length > 0) {
      parts.push(`for ${scheme.targetAudience.join(", ")}`);
    }

    if (parts.length > 0) {
      description = truncateDescription(
        `${parts.join(" - ")}. ${SEO_COPY.schemeDescriptionFallback}`,
      );
    } else {
      description = SEO_COPY.schemeDescriptionFallback;
    }
  }
  const canonicalUrl = `${SITE_URL}/schemes/${schemeId}`;
  const imageUrls = getSeoImages(scheme.image);
  const shouldIndex = hasIndexableContent(scheme);

  return {
    title,
    description,
    alternates: {
      canonical: canonicalUrl,
    },
    robots: {
      index: shouldIndex,
      follow: true,
    },
    openGraph: {
      title,
      description,
      url: canonicalUrl,
      siteName: SEO_COPY.productName,
      type: "article",
      images: imageUrls.map((url) => ({
        url,
        alt:
          url === SCHEMES_SG_OG_IMAGE_URL
            ? "Schemes.sg logo"
            : `${scheme.agency || scheme.schemeName} logo`,
        width: 1200,
        height: 630,
      })),
    },
    twitter: {
      card: "summary_large_image",
      title,
      description,
      images: imageUrls,
    },
  };
}

export default async function SchemePage({ params }: SchemePageProps) {
  const { schemeId } = await params;
  const scheme = await getSchemeById(schemeId);

  if (!scheme) {
    notFound();
  }

  if (scheme.status === "retired" && scheme.mergedInto) {
    permanentRedirect("/schemes/" + scheme.mergedInto);
  }

  if (scheme.status === "retired") {
    return (
      <section className="mx-auto flex min-h-full max-w-3xl items-center px-6 py-16">
        <div className="w-full rounded-2xl border border-(--schemes-status-info-border) bg-(--schemes-status-info-bg) p-8 text-center">
          <h1 className="mb-3 text-2xl font-semibold text-(--schemes-status-info-text)">
            This scheme is no longer listed
          </h1>
          <p className="text-sm leading-relaxed text-(--schemes-status-info-text)">
            This page has been kept so existing links do not break. Browse the
            catalog to find currently listed support schemes.
          </p>
        </div>
      </section>
    );
  }

  const canonicalUrl = `${SITE_URL}/schemes/${schemeId}`;
  const category =
    scheme.schemeType.length > 0
      ? getSchemeCategory(scheme.schemeType[0])
      : undefined;
  const categoryPath = category ? getCatalogCategoryPath(category) : "";
  const breadcrumbJsonLd = getSchemeBreadcrumbListJsonLd(
    category,
    categoryPath,
    scheme.schemeName || scheme.agency,
    `/schemes/${schemeId}`,
  );

  const jsonLd = {
    "@context": "https://schema.org",
    "@graph": [
      {
        "@type": "SocialService",
        name: scheme.schemeName || scheme.agency,
        description: stripMarkdown(
          scheme.summary ||
            scheme.description ||
            scheme.searchBooster ||
            SEO_COPY.schemeDescriptionFallback,
        ),
        provider: scheme.agency
          ? {
              "@type": "Agency",
              name: scheme.agency,
            }
          : undefined,
        areaServed: "Singapore",
        serviceType: scheme.schemeType?.join(", ") || undefined,
        url: canonicalUrl,
      },
      breadcrumbJsonLd,
    ],
  };

  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{
          __html: JSON.stringify(jsonLd).replace(/</g, "\\u003c"),
        }}
      />
      <SchemeDetail scheme={scheme} />
    </>
  );
}
