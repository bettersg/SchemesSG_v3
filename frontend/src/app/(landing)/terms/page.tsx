import type { Metadata } from "next";
import LegalPageContent from "@/components/landing/legal-page-content";
import { SCHEMES_SG_LOGO_URL, SEO_COPY } from "@/lib/seo";

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
        url: SCHEMES_SG_LOGO_URL,
        alt: "Schemes.sg logo",
      },
    ],
  },
};

export default function TermsPage() {
  return <LegalPageContent document="terms" />;
}
