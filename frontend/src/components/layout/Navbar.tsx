"use client";

import { useState, useEffect } from "react";
import { Menu, X, ArrowRight } from "lucide-react";
import { Button } from "@/components/landing/ui/button";
import { useLanguage } from "@/lib/landing-i18n";
import { LanguageToggle } from "@/components/landing/shared/LanguageToggle";
import { cn } from "@/lib/utils";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Tabs } from "@heroui/react";

type NavLink = {
  label: string;
  href: string;
  disabled?: boolean;
};

export function Navbar() {
  const { t } = useLanguage();
  const pathname = usePathname();
  const [scrolled, setScrolled] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  const navLinks: NavLink[] = [
    { label: t.nav.catalog, href: "/catalog" },
    { label: t.nav.searchSchemes, href: "/" },
    { label: t.nav.contribute, href: "/contribute" },
    { label: t.nav.about, href: "/about" },
  ];

  // Determine selected tab from pathname
  const selectedKey =
    navLinks.find(
      (link) =>
        link.href === pathname ||
        (link.href !== "/" && pathname.startsWith(link.href)),
    )?.href ?? "/";

  useEffect(() => {
    function onScroll() {
      setScrolled(window.scrollY > 20);
    }
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  return (
    <header
      className={cn(
        "fixed h-nav top-0 left-0 right-0 z-50 transition-all duration-300",
        scrolled
          ? "bg-white/70 backdrop-blur-xl border-b border-neutral-200/60 shadow-sm"
          : "bg-transparent",
      )}
    >
      <nav className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
        {/* Logo */}
        <a
          href="/"
          className="flex items-center gap-2 font-serif text-xl tracking-tight cursor-pointer"
        >
          <img src="/logo.svg" alt="Schemes.sg" className="h-7 w-auto" />
          <span className="text-neutral-900 font-bold">Schemes</span>
          <span className="text-neutral-400 -ml-1">.sg</span>
        </a>

        {/* Center pill nav - desktop (HeroUI Tabs) */}
        <div className="hidden md:flex">
          <Tabs selectedKey={selectedKey} aria-label="Navigation">
            <Tabs.ListContainer>
              <Tabs.List
                aria-label="Navigation tabs"
                className="rounded-full px-2 py-1.5 gap-1 bg-transparent"
              >
                {navLinks.map((link) => (
                  <Tabs.Tab
                    key={link.href}
                    id={link.href}
                    isDisabled={link.disabled}
                    className={cn(
                      "w-fit px-4 py-1.5 text-sm font-medium rounded-full transition-all duration-200 cursor-pointer",
                      "text-neutral-500",
                      "hover:text-neutral-900",
                      "aria-selected:font-semibold aria-selected:text-neutral-900",
                      "aria-disabled:text-neutral-300 aria-disabled:cursor-default",
                    )}
                  >
                    <Link href={link.href}>
                      {link.label}
                      {link.href === "/" && (
                        <ArrowRight className="inline h-3.5 w-3.5 ml-1.5" />
                      )}
                      <Tabs.Indicator className="rounded-full bg-amber-400" />
                    </Link>
                  </Tabs.Tab>
                ))}
              </Tabs.List>
            </Tabs.ListContainer>
          </Tabs>
        </div>

        {/* Language toggle - desktop */}
        <div className="hidden md:flex items-center">
          <LanguageToggle />
        </div>

        {/* Mobile menu toggle */}
        <button
          className="md:hidden p-2 cursor-pointer"
          onClick={() => setMobileOpen(!mobileOpen)}
          aria-label={mobileOpen ? t.a11y.closeMenu : t.a11y.openMenu}
        >
          {mobileOpen ? (
            <X className="h-5 w-5" />
          ) : (
            <Menu className="h-5 w-5" />
          )}
        </button>
      </nav>

      {/* Mobile menu */}
      {mobileOpen && (
        <div className="md:hidden bg-white/95 backdrop-blur-xl border-b border-neutral-200 px-6 pb-6">
          <div className="flex flex-col items-center gap-1 w-full">
            {navLinks
              .filter((link) => link.href !== "/")
              .map((link) => (
                <a
                  key={link.label}
                  href={link.href}
                  onClick={() => setMobileOpen(false)}
                  className="px-3 py-3 text-sm font-medium text-neutral-900 hover:bg-neutral-100 rounded-lg transition-colors cursor-pointer"
                >
                  {link.label}
                </a>
              ))}
          </div>
          <div className="mt-3 flex justify-center">
            <LanguageToggle />
          </div>
          <div className="mt-3 flex justify-center">
            <Link href="/">
              <Button
                size="sm"
                className="w-full rounded-full bg-amber-400 hover:bg-amber-500 text-neutral-900 font-semibold gap-1.5 cursor-pointer"
              >
                {t.nav.searchSchemes} <ArrowRight className="h-3.5 w-3.5" />
              </Button>
            </Link>
          </div>
        </div>
      )}
    </header>
  );
}
