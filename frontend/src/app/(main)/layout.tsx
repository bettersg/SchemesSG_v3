"use client";

import { Navbar } from "@/components/layout/navbar";
import { cssTransition } from "@/lib/design-system/motion";

export default function MainLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <>
      <Navbar />
      <div
        className={`${cssTransition.heightState} h-[var(--schemes-mobile-nav-offset)] md:h-nav`}
      ></div>
      <main
        className={`${cssTransition.heightState} h-[calc(100dvh-var(--schemes-mobile-nav-offset))] md:h-[calc(100dvh-var(--spacing-nav))]`}
      >
        {children}
      </main>
    </>
  );
}
