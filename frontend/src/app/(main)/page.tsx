import type { Metadata } from "next";
import ChatHome from "@/components/chat/chat-home";
import { SCHEMES_SG_LOGO_URL, SEO_COPY, SITE_URL } from "@/lib/seo";

export const metadata: Metadata = {
  title: SEO_COPY.homeTitle,
  description: SEO_COPY.homeDescription,
  alternates: {
    canonical: "/",
  },
  openGraph: {
    title: SEO_COPY.homeTitle,
    description: SEO_COPY.homeDescription,
    url: "/",
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
    title: SEO_COPY.homeTitle,
    description: SEO_COPY.homeDescription,
    images: [SCHEMES_SG_LOGO_URL],
  },
};

const jsonLd = {
  "@context": "https://schema.org",
  "@type": "WebApplication",
  name: "Schemes.sg",
  applicationCategory: "SearchApplication",
  operatingSystem: "Web",
  url: `${SITE_URL}/`,
  description: SEO_COPY.homeDescription,
};

export default function Home() {
  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{
          __html: JSON.stringify(jsonLd).replace(/</g, "\\u003c"),
        }}
      />
      <ChatHome />
    </>
  );
}
