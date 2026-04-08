"use client";

import { LanguageProvider } from "@/lib/landing-i18n";
import { Footer } from "@/components/layout/Footer";

export default function LandingLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <LanguageProvider>
      <div className="min-h-screen bg-background text-foreground font-landing-sans">
        <main>{children}</main>
        <Footer />
      </div>
    </LanguageProvider>
  );
}