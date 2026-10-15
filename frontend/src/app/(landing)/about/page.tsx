import type { Metadata } from "next";
import AboutPageContent from "@/components/landing/about-page-content";
import { SCHEMES_SG_OG_IMAGE_URL, SEO_COPY, SITE_URL } from "@/lib/seo";

export const metadata: Metadata = {
  title: SEO_COPY.aboutTitle,
  description: SEO_COPY.aboutDescription,
  alternates: {
    canonical: "/about",
  },
  openGraph: {
    title: SEO_COPY.aboutTitle,
    description: SEO_COPY.aboutDescription,
    url: "/about",
    siteName: SEO_COPY.productName,
    type: "website",
    images: [
      {
        url: SCHEMES_SG_OG_IMAGE_URL,
        alt: "Schemes.sg logo",
        width: 1200,
        height: 630,
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: SEO_COPY.aboutTitle,
    description: SEO_COPY.aboutDescription,
    images: [SCHEMES_SG_OG_IMAGE_URL],
  },
};

const jsonLd = {
  "@context": "https://schema.org",
  "@type": "AboutPage",
  name: "About Schemes.sg",
  url: `${SITE_URL}/about`,
  description: SEO_COPY.aboutDescription,
  mainEntity: {
    "@type": "Organization",
    name: SEO_COPY.productName,
    url: SITE_URL,
  },
};

export default function AboutPage() {
  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{
          __html: JSON.stringify(jsonLd).replace(/</g, "\\u003c"),
        }}
      />
      <AboutPageContent />
    </>
  );
}
