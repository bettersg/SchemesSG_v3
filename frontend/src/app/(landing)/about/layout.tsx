"use client";

import { Footer } from "@/components/layout/Footer";
import { Navbar } from "@/components/layout/navbar";

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
