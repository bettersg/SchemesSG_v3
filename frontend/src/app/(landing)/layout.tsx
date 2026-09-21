"use client";

import { Footer } from "@/components/layout/footer";
import { Navbar } from "@/components/layout/navbar";

/**
 * Chrome for every page in the `(landing)` group: /about, /developers, /privacy,
 * /terms.
 *
 * One layout at the group level rather than an identical copy per route — the four
 * per-route files this replaces were byte-for-byte the same. A new landing page now
 * gets the navbar and footer by being in the group, with nothing to remember.
 */
export default function LandingLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <>
      <Navbar />
      <main>{children}</main>
      <Footer />
    </>
  );
}
