import type { Metadata } from "next";
import { notFound } from "next/navigation";
import SchemeDetail from "@/components/schemes/scheme-detail";
import { getSchemeById } from "@/lib/schemes";
import {
  getSeoImages,
  SCHEMES_SG_LOGO_URL,
  SEO_COPY,
  SITE_URL,
} from "@/lib/seo";
import SchemeSkeleton from "@/components/schemes/scheme-skeleton";
import { Suspense } from "react";

type SchemePageProps = {
  params: Promise<{ schemeId: string }>;
};

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

  const title = `${scheme.schemeName || scheme.agency} | Schemes.sg`;
  const description = truncateDescription(
    scheme.summary ||
      scheme.description ||
      scheme.searchBooster ||
      SEO_COPY.schemeDescriptionFallback,
  );
  const canonicalUrl = `${SITE_URL}/schemes/${schemeId}`;
  const imageUrls = getSeoImages(scheme.image);

  return {
    title,
    description,
    alternates: {
      canonical: canonicalUrl,
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
          url === SCHEMES_SG_LOGO_URL
            ? "Schemes.sg logo"
            : `${scheme.agency || scheme.schemeName} logo`,
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

  const canonicalUrl = `${SITE_URL}/schemes/${schemeId}`;
  const jsonLd = {
    "@context": "https://schema.org",
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
  };

  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{
          __html: JSON.stringify(jsonLd).replace(/</g, "\\u003c"),
        }}
      />
      <Suspense fallback={<SchemeSkeleton />}>
        <SchemeDetail scheme={scheme} />
      </Suspense>
    </>
  );
}
