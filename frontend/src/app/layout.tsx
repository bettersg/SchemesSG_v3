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
import { Open_Sans, Lexend } from "next/font/google";
import React from "react";
import "@/globals.css";
import { ChatProvider } from "../providers";
import { AuthProvider } from "../providers/AuthProvider";

const openSans = Open_Sans({
  subsets: ["latin"],
  weight: ["300", "400", "500", "600"],
  variable: "--font-body",
  display: "swap",
});

const lexend = Lexend({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700", "800"],
  variable: "--font-head",
  display: "swap",
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
    description: "500+ social assistance schemes across Singapore. AI-powered, anonymous, free.",
    siteName: "SchemesSG",
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="!p-0 !overflow-visible">
      <body className={`${openSans.variable} ${lexend.variable} ${geistSans.variable} antialiased`}
        style={{ fontFamily: "var(--font-body), var(--font-geist-sans), ui-sans-serif, system-ui, sans-serif" }}
      >
		<AuthProvider>
		<ChatProvider>
			<div className="min-h-screen flex flex-col bg-[#f4f7fb]">
			<MainHeader />
			<div className="flex-1 flex justify-center ">{children}</div>
			</div>
		</ChatProvider>
		</AuthProvider>
      </body>
    </html>
  );
}
>>>>>>> 5bcdda1 (New design initial draft)
