import type { Metadata } from "next";
import LegalPageContent from "@/components/landing/legal-page-content";
import { SCHEMES_SG_LOGO_URL, SEO_COPY } from "@/lib/seo";

export const metadata: Metadata = {
  title: SEO_COPY.privacyTitle,
  description: SEO_COPY.privacyDescription,
  alternates: {
    canonical: "/privacy",
  },
  openGraph: {
    title: SEO_COPY.privacyTitle,
    description: SEO_COPY.privacyDescription,
    url: "/privacy",
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

export default function PrivacyPage() {
  return <LegalPageContent document="privacy" />;
}
