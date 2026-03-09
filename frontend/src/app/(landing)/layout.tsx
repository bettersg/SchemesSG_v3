"use client";

import { LanguageProvider } from "@/lib/landing-i18n";
import { Navbar } from "@/components/landing/layout/Navbar";
import { Footer } from "@/components/landing/layout/Footer";

export default function LandingLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <LanguageProvider>
      <div className="min-h-screen bg-background text-foreground font-landing-sans">
        <Navbar />
        <main>{children}</main>
        <Footer />
      </div>
    </LanguageProvider>
  );
}
