import type { Metadata } from "next";
import localFont from "next/font/local";
import React from "react";
import "@/globals.css";
import { AppProviders } from "@/providers";
import { SCHEMES_SG_OG_IMAGE_URL, SEO_COPY, SITE_URL } from "@/lib/seo";

// The Google Fonts latin files, kept in the repo. `next/font/google` downloads
// them on every dev start and build, and a failed download silently swaps in
// the fallback font.
const openSans = localFont({
  src: "../assets/fonts/OpenSansVF-latin.woff2",
  weight: "300 600",
  variable: "--font-body",
  preload: false,
});

const lexend = localFont({
  src: "../assets/fonts/LexendVF-latin.woff2",
  weight: "400 800",
  variable: "--font-head",
  preload: false,
});

const plusJakartaSans = localFont({
  src: "../assets/fonts/PlusJakartaSansVF-latin.woff2",
  weight: "200 800",
  variable: "--font-sans",
  preload: false,
});

const dmSerifDisplay = localFont({
  src: "../assets/fonts/DMSerifDisplay-latin.woff2",
  weight: "400",
  variable: "--font-serif",
  adjustFontFallback: "Times New Roman",
  preload: false,
});

const geistSans = localFont({
  src: "../assets/fonts/GeistVF.woff",
  variable: "--font-geist-sans",
  weight: "100 200 300 400 500 600 700 800 900",
  fallback: ["ui-sans-serif", "system-ui", "sans-serif"],
  preload: false,
});

export const metadata: Metadata = {
  metadataBase: new URL(SITE_URL),
  title: {
    default: SEO_COPY.homeTitle,
    template: "%s",
  },
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
    locale: "en_SG",
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
    title: SEO_COPY.homeTitle,
    description: SEO_COPY.homeDescription,
    images: [SCHEMES_SG_OG_IMAGE_URL],
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="!overflow-visible !p-0">
      <body
        className={`${openSans.variable} ${lexend.variable} ${geistSans.variable} ${plusJakartaSans.variable} ${dmSerifDisplay.variable} font-landing-sans text-foreground antialiased`}
        style={{
          fontFamily:
            "var(--font-body), var(--font-geist-sans), ui-sans-serif, system-ui, sans-serif",
        }}
      >
        <AppProviders>
          <div className="h-full min-h-dvh">{children}</div>
        </AppProviders>
      </body>
    </html>
  );
}
