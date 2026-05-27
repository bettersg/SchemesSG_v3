"use client";

import { useState, useEffect, useRef } from "react";
import { Menu, X, ArrowRight } from "lucide-react";
import { AnimatePresence, motion } from "framer-motion";
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
  const [mobileHidden, setMobileHidden] = useState(false);
  const lastScrollYRef = useRef(0);
  const activeScrollTargetRef = useRef<EventTarget | null>(null);

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
    setMobileHidden(false);
    setMobileOpen(false);
    lastScrollYRef.current = 0;
    activeScrollTargetRef.current = null;
  }, [pathname]);

  useEffect(() => {
    document.documentElement.dataset.mobileNavHidden =
      mobileHidden && !mobileOpen ? "true" : "false";

    return () => {
      delete document.documentElement.dataset.mobileNavHidden;
    };
  }, [mobileHidden, mobileOpen]);

  useEffect(() => {
    function getScrollMetrics(event: Event) {
      const target = event.target;

      if (
        target === document ||
        target === document.documentElement ||
        target === document.body
      ) {
        const scrollHeight = document.documentElement.scrollHeight;
        return {
          maxScrollTop: Math.max(scrollHeight - window.innerHeight, 0),
          scrollTop: window.scrollY,
          target,
        };
      }

      if (target instanceof Element) {
        return {
          maxScrollTop: Math.max(target.scrollHeight - target.clientHeight, 0),
          scrollTop: target.scrollTop,
          target,
        };
      }

      return {
        maxScrollTop: Math.max(
          document.documentElement.scrollHeight - window.innerHeight,
          0,
        ),
        scrollTop: window.scrollY,
        target,
      };
    }

    function onScroll(event: Event) {
      const { maxScrollTop, scrollTop, target } = getScrollMetrics(event);
      const scrollY = Math.max(scrollTop, 0);
      const isScrollable = maxScrollTop > 0;

      if (!isScrollable) return;

      if (activeScrollTargetRef.current !== target) {
        activeScrollTargetRef.current = target;
        lastScrollYRef.current = scrollY;
        setScrolled(window.scrollY > 20 || scrollY > 20);
        return;
      }

      const delta = scrollY - lastScrollYRef.current;
      const distanceFromBottom = maxScrollTop - scrollY;

      setScrolled(window.scrollY > 20 || scrollY > 20);

      if (scrollY <= 12 || mobileOpen) {
        setMobileHidden(false);
      } else if (delta > 6) {
        setMobileHidden(true);
      } else if (delta < -6 && distanceFromBottom > 24) {
        setMobileHidden(false);
      }

      lastScrollYRef.current = scrollY;
    }

    document.addEventListener("scroll", onScroll, {
      capture: true,
      passive: true,
    });

    return () => {
      document.removeEventListener("scroll", onScroll, { capture: true });
    };
  }, [mobileOpen]);

  return (
    <header
      className={cn(
        "fixed top-0 right-0 left-0 z-50 h-nav transition-all duration-300 md:translate-y-0",
        mobileHidden && !mobileOpen
          ? "max-md:-translate-y-full"
          : "translate-y-0",
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
                      <Tabs.Indicator className="rounded-full bg-(--schemes-amber-400)" />
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
      <AnimatePresence initial={false}>
        {mobileOpen && (
          <motion.div
            key="mobile-menu"
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.18, ease: "easeOut" }}
            className="z-50 border-b border-neutral-200 bg-background px-6 pb-6 backdrop-blur-xl md:hidden"
          >
            <div className="flex w-full flex-col items-center gap-1">
              {navLinks
                .filter((link) => link.href !== "/")
                .map((link) => {
                  const isActive = selectedKey === link.href;

                  return (
                    <a
                      key={link.label}
                      href={link.href}
                      onClick={() => setMobileOpen(false)}
                      className={cn(
                        "cursor-pointer rounded-full px-4 py-2 text-sm font-medium transition-colors",
                        isActive
                          ? "bg-(--schemes-amber-400) font-semibold text-neutral-900 hover:bg-(--schemes-amber-100)"
                          : "text-neutral-900 hover:bg-neutral-100",
                      )}
                    >
                      {link.label}
                    </a>
                  );
                })}
            </div>
            <div className="mt-3 flex justify-center">
              <LanguageToggle />
            </div>
            <div className="mt-3 flex justify-center">
              <Link href="/">
                <Button
                  size="sm"
                  className={cn(
                    "w-full cursor-pointer gap-1.5 rounded-full font-semibold",
                    selectedKey === "/"
                      ? "bg-(--schemes-amber-400) text-neutral-900 hover:bg-(--schemes-amber-100)"
                      : "bg-transparent text-neutral-900 shadow-none hover:bg-neutral-100",
                  )}
                >
                  {t.nav.searchSchemes} <ArrowRight className="h-3.5 w-3.5" />
                </Button>
              </Link>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </header>
  );
}
