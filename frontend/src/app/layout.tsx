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
