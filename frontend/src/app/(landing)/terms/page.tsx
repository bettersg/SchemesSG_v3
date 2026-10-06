import type { Metadata } from "next";
import LegalPageContent from "@/components/landing/legal-page-content";
import { SCHEMES_SG_OG_IMAGE_URL, SEO_COPY } from "@/lib/seo";

export const metadata: Metadata = {
  title: SEO_COPY.termsTitle,
  description: SEO_COPY.termsDescription,
  alternates: {
    canonical: "/terms",
  },
  openGraph: {
    title: SEO_COPY.termsTitle,
    description: SEO_COPY.termsDescription,
    url: "/terms",
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
};

export default function TermsPage() {
  return <LegalPageContent document="terms" />;
}
