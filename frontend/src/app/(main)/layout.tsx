"use client";

import { Navbar } from "@/components/layout/Navbar";

export default function MainLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <>
      <Navbar />
      <div className="h-[var(--schemes-mobile-nav-offset)] transition-[height] duration-300 md:h-nav"></div>
      <main className="h-[calc(100vh-var(--schemes-mobile-nav-offset))] transition-[height] duration-300 md:h-[calc(100vh-var(--spacing-nav))]">
        {children}
      </main>
    </>
  );
}
