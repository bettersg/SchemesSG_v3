import type { Metadata } from "next";
import DevelopersPageContent from "@/components/landing/developers-page-content";
import { SCHEMES_SG_LOGO_URL, SEO_COPY } from "@/lib/seo";

export const metadata: Metadata = {
  title: SEO_COPY.developersTitle,
  description: SEO_COPY.developersDescription,
  alternates: {
    canonical: "/developers",
  },
  openGraph: {
    title: SEO_COPY.developersTitle,
    description: SEO_COPY.developersDescription,
    url: "/developers",
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
    title: SEO_COPY.developersTitle,
    description: SEO_COPY.developersDescription,
    images: [SCHEMES_SG_LOGO_URL],
  },
};

export default function DevelopersPage() {
  return <DevelopersPageContent />;
}
