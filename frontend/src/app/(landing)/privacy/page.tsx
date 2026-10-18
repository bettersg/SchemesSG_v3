import type { Metadata } from "next";
import LegalDocument from "@/components/landing/legal/legal-document";
import { getLegalDocument } from "@/lib/legal-content";
import { SCHEMES_SG_OG_IMAGE_URL, SEO_COPY } from "@/lib/seo";

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
        url: SCHEMES_SG_OG_IMAGE_URL,
        alt: "Schemes.sg logo",
        width: 1200,
        height: 630,
      },
    ],
  },
};

export default function PrivacyPage() {
  const doc = getLegalDocument("privacy");
  return (
    <LegalDocument
      heading="Privacy Policy"
      effectiveDate={doc.effectiveDate}
      markdown={doc.content}
    />
  );
}
