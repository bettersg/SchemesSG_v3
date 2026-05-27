import type { Metadata } from "next";
import localFont from "next/font/local";
import {
  Open_Sans,
  Lexend,
  Plus_Jakarta_Sans,
  DM_Serif_Display,
} from "next/font/google";
import React from "react";
import "@/globals.css";
import { AppProviders } from "@/providers";
import { SCHEMES_SG_LOGO_URL, SEO_COPY, SITE_URL } from "@/lib/seo";

const openSans = Open_Sans({
  subsets: ["latin"],
  weight: ["300", "400", "500", "600"],
  variable: "--font-body",
  preload: false,
});

const lexend = Lexend({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700", "800"],
  variable: "--font-head",
  preload: false,
});

const plusJakartaSans = Plus_Jakarta_Sans({
  subsets: ["latin"],
  variable: "--font-sans",
  preload: false,
});

const dmSerifDisplay = DM_Serif_Display({
  weight: "400",
  subsets: ["latin"],
  variable: "--font-serif",
  preload: false,
});

// Keep Geist as fallback
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
          <div className="h-full min-h-screen">{children}</div>
        </AppProviders>
      </body>
    </html>
  );
}
