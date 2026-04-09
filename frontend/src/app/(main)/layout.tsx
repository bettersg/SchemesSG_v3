"use client";

import { Navbar } from "@/components/layout/Navbar";

export default function MainLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <>
      <Navbar fixed/>
      <div className="h-nav"></div>
      <main className="h-[calc(100vh-var(--spacing-nav))]">{children}</main>
    </>
  );
}
