<<<<<<< HEAD
import type { Metadata } from "next";
import localFont from "next/font/local";
import { Plus_Jakarta_Sans, DM_Serif_Display } from "next/font/google";
import React from "react";
import "./globals.css";

const geistSans = localFont({
  src: "../assets/fonts/GeistVF.woff",
  variable: "--font-geist-sans",
  weight: "100 200 300 400 500 600 700 800 900",
  fallback: ["ui-sans-serif", "system-ui", "sans-serif"],
});

const plusJakartaSans = Plus_Jakarta_Sans({
  subsets: ["latin"],
  variable: "--font-landing-sans",
});

const dmSerifDisplay = DM_Serif_Display({
  weight: "400",
  subsets: ["latin"],
  variable: "--font-landing-serif",
});

export const metadata: Metadata = {
  title: "Schemes SG",
  description:
    "One stop directory and AI-enabled search to help make sense of assistance schemes in Singapore.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="!p-0 !overflow-visible">
      <body
        className={`${geistSans.className} ${plusJakartaSans.variable} ${dmSerifDisplay.variable} antialiased`}
      >
        {children}
      </body>
    </html>
  );
}
=======
import MainHeader from "@/components/main-header";
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
import { ChatProvider } from "../providers";
import { AuthProvider } from "../providers/AuthProvider";
import { LanguageProvider } from "@/lib/landing-i18n";
import { Navbar } from "@/components/layout/Navbar";
import { Footer } from "@/components/layout/Footer";

const openSans = Open_Sans({
  subsets: ["latin"],
  weight: ["300", "400", "500", "600"],
  variable: "--font-body",
});

const lexend = Lexend({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700", "800"],
  variable: "--font-head",
});

const plusJakartaSans = Plus_Jakarta_Sans({
  subsets: ["latin"],
  variable: "--font-sans",
});

const dmSerifDisplay = DM_Serif_Display({
  weight: "400",
  subsets: ["latin"],
  variable: "--font-serif",
});

// Keep Geist as fallback
const geistSans = localFont({
  src: "../assets/fonts/GeistVF.woff",
  variable: "--font-geist-sans",
  weight: "100 200 300 400 500 600 700 800 900",
  fallback: ["ui-sans-serif", "system-ui", "sans-serif"],
});

export const metadata: Metadata = {
  title: "SchemesSG — Find the right support",
  description:
    "Singapore's AI-powered directory of social assistance schemes. Find the right support for your situation — anonymously and for free.",
  openGraph: {
    title: "SchemesSG — Find the right support",
    description:
      "500+ social assistance schemes across Singapore. AI-powered, anonymous, free.",
    siteName: "SchemesSG",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="!p-0 !overflow-visible">
      <body
        className={`${openSans.variable} ${lexend.variable} ${geistSans.variable} ${plusJakartaSans.variable} ${dmSerifDisplay.variable} antialiased`}
        style={{
          fontFamily:
            "var(--font-body), var(--font-geist-sans), ui-sans-serif, system-ui, sans-serif",
        }}
      >
        <LanguageProvider>
          <AuthProvider>
            <ChatProvider>
              <div className="min-h-screen flex flex-col bg-[#f4f7fb]">
                <Navbar />
                <div className="flex-1 flex flex-col">{children}</div>
                <Footer />
              </div>
            </ChatProvider>
          </AuthProvider>
        </LanguageProvider>
      </body>
    </html>
  );
}
>>>>>>> f8cdbe2 (Removed separate landing page app, revert old about page)
