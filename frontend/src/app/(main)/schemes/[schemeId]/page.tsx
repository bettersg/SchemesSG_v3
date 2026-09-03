import type { Metadata } from "next";
import { notFound, permanentRedirect } from "next/navigation";
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
