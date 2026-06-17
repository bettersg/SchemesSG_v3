"use client";

import { Footer } from "@/components/layout/footer";
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
