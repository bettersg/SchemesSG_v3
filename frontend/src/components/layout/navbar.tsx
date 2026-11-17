"use client";

import { type MouseEvent, useEffect, useRef, useState } from "react";
import { Menu, X, ArrowRight } from "lucide-react";
import { AnimatePresence, motion } from "framer-motion";
import { Button } from "@/components/landing/ui/button";
import { useLingui } from "@lingui/react/macro";
import { LanguageToggle } from "@/components/landing/shared/language-toggle";
import { cn } from "@/lib/utils";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Tabs } from "@heroui/react";
import Image from "next/image";
import { useHideOnScroll } from "@/hooks/use-hide-on-scroll";
import { useChat } from "@/providers/chat-provider";
import {
  cssTransition,
  motionPreset,
  transition,
} from "@/lib/design-system/motion";

/**
 * Whether the desktop tabs fit beside the logo and language menu. Measured
 * rather than tied to a breakpoint because the tab labels run from about 440px
 * (Malay) to over twice that (Tamil). The tabs stay rendered while collapsed so
 * their width can still be measured.
 */
function useTabsFit() {
  const navRef = useRef<HTMLElement>(null);
  const logoRef = useRef<HTMLAnchorElement>(null);
  const tabsRef = useRef<HTMLDivElement>(null);
  const languageRef = useRef<HTMLDivElement>(null);
  const [fits, setFits] = useState(true);

  useEffect(() => {
    const nav = navRef.current;
    const tabs = tabsRef.current;
    if (!nav || !tabs) return;
    const measure = () => {
      const style = getComputedStyle(nav);
      const inner =
        nav.clientWidth -
        parseFloat(style.paddingLeft) -
        parseFloat(style.paddingRight);
      const taken =
        (logoRef.current?.offsetWidth ?? 0) +
        (languageRef.current?.offsetWidth ?? 0);
      // 32px keeps the tabs from touching the logo or the language menu.
      setFits(tabs.scrollWidth + taken + 32 <= inner);
    };
    // A ResizeObserver reports each element once on observe(), which covers
    // the first measurement.
    const observer = new ResizeObserver(measure);
    for (const el of [nav, tabs, logoRef.current, languageRef.current]) {
      if (el) observer.observe(el);
    }
    return () => observer.disconnect();
  }, []);

  return { navRef, logoRef, tabsRef, languageRef, fits };
}

type NavLink = {
  label: string;
  href: string;
  disabled?: boolean;
};

export function Navbar() {
  const { t } = useLingui();
  const pathname = usePathname();
  const { hasActiveChat, setResetModalIsOpen } = useChat();
  const [mobileOpen, setMobileOpen] = useState(false);
  const { navRef, logoRef, tabsRef, languageRef, fits } = useTabsFit();
  // Below md the menu always collapses; above it, only when the tabs do not fit.
  const collapsed = !fits;
  const { isHidden: mobileHidden, isScrolled: scrolled } = useHideOnScroll({
    disabled: mobileOpen,
    resetKey: pathname,
  });

  const navLinks: NavLink[] = [
    {
      label: t({
        message: "Catalogue",
        comment: "Navbar tab: browse every scheme by category",
      }),
      href: "/catalog",
    },
    {
      label: t({
        message: "Search schemes",
        comment: "Navbar tab and button: open the search page",
      }),
      href: "/",
    },
    {
      label: t({
        message: "Contribute",
        context: "navbar tab",
        comment: "Navbar tab: suggest a scheme that is missing. Keep it short: it shares one row with three other tabs",
      }),
      href: "/contribute",
    },
    { label: t({ message: "About", comment: "Navbar tab" }), href: "/about" },
  ];

  const selectedKey =
    navLinks.find(
      (link) =>
        link.href === pathname ||
        (link.href !== "/" && pathname.startsWith(link.href)),
    )?.href ?? "/";

  useEffect(() => {
    setMobileOpen(false);
  }, [pathname]);

  useEffect(() => {
    document.documentElement.dataset.mobileNavHidden =
      mobileHidden && !mobileOpen ? "true" : "false";

    return () => {
      delete document.documentElement.dataset.mobileNavHidden;
    };
  }, [mobileHidden, mobileOpen]);

  // On the search page these would only reload the same chat, so offer a reset.
  const handleSearchEntryClick = (event: MouseEvent<Element>) => {
    setMobileOpen(false);

    if (pathname === "/" && hasActiveChat) {
      event.preventDefault();
      setResetModalIsOpen(true);
    }
  };

  return (
    <header
      className={cn(
        "fixed top-0 right-0 left-0 z-50 h-nav md:translate-y-0",
        cssTransition.chromeState,
        mobileHidden && !mobileOpen
          ? "max-md:-translate-y-full"
          : "translate-y-0",
        scrolled
          ? "bg-white/70 backdrop-blur-xl border-b border-neutral-200/60 shadow-sm"
          : "bg-transparent",
      )}
    >
      <nav
        ref={navRef}
        className="relative mx-auto h-full flex max-w-7xl items-center justify-between px-6"
      >
        <a
          ref={logoRef}
          href="/"
          onClick={handleSearchEntryClick}
          className="flex items-center gap-2 font-serif text-xl tracking-tight cursor-pointer"
        >
          <Image
            src="/logo.svg"
            alt="Schemes.sg"
            width={28}
            height={28}
            className="h-7 w-7"
          />
          <span className="text-neutral-900 font-bold">Schemes</span>
          <span className="text-neutral-400 -ml-1">.sg</span>
        </a>

        <div
          ref={tabsRef}
          aria-hidden={collapsed || undefined}
          className={cn(
            "hidden md:flex",
            collapsed &&
              "md:pointer-events-none md:invisible md:absolute md:left-0 md:w-max",
          )}
        >
          <Tabs selectedKey={selectedKey} aria-label={t({ message: "Navigation", comment: "Aria label for the main navigation tabs" })}>
            <Tabs.ListContainer>
              <Tabs.List
                aria-label={t`Navigation tabs`}
                className="rounded-full px-2 py-1.5 gap-1 bg-transparent"
              >
                {navLinks.map((link) => (
                  <Tabs.Tab
                    key={link.href}
                    id={link.href}
                    isDisabled={link.disabled}
                    className={cn(
                      "w-fit text-sm font-medium rounded-full cursor-pointer",
                      cssTransition.allState,
                      "text-neutral-500",
                      "hover:text-neutral-900",
                      "aria-selected:font-semibold aria-selected:text-neutral-900",
                      "aria-disabled:text-neutral-300 aria-disabled:cursor-default",
                    )}
                  >
                    <Link
                      href={link.href}
                      onClick={
                        link.href === "/" ? handleSearchEntryClick : undefined
                      }
                    >
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

        <div
          ref={languageRef}
          className={cn("hidden md:flex items-center", collapsed && "md:ml-auto")}
        >
          <LanguageToggle />
        </div>

        <button
          className={cn(
            "inline-flex size-11 items-center justify-center rounded-lg cursor-pointer",
            !collapsed && "md:hidden",
          )}
          onClick={() => setMobileOpen(!mobileOpen)}
          aria-label={mobileOpen ? t`Close menu` : t`Open menu`}
        >
          {mobileOpen ? (
            <X className="h-5 w-5" />
          ) : (
            <Menu className="h-5 w-5" />
          )}
        </button>
      </nav>

      <AnimatePresence initial={false}>
        {mobileOpen && (
          <motion.div
            key="mobile-menu"
            initial={motionPreset.mobileMenu.initial}
            animate={motionPreset.mobileMenu.animate}
            exit={motionPreset.mobileMenu.exit}
            transition={transition.stateEmphasis}
            className={cn(
              "z-50 border-b border-neutral-200 bg-background px-6 pb-6 backdrop-blur-xl",
              !collapsed && "md:hidden",
            )}
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
                        "inline-flex min-h-11 items-center justify-center text-center cursor-pointer rounded-full px-4 py-2 text-sm font-medium transition-colors",
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
            <div className="mt-3 flex justify-center md:hidden">
              <LanguageToggle />
            </div>
            <div className="mt-3 flex justify-center">
              <Link href="/">
                <Button
                  size="sm"
                  onClick={handleSearchEntryClick}
                  className={cn(
                    "min-h-11 w-full cursor-pointer gap-1.5 rounded-full font-semibold",
                    selectedKey === "/"
                      ? "bg-(--schemes-amber-400) text-neutral-900 hover:bg-(--schemes-amber-100)"
                      : "bg-transparent text-neutral-900 shadow-none hover:bg-neutral-100",
                  )}
                >
                  {t`Search schemes`} <ArrowRight className="h-3.5 w-3.5" />
                </Button>
              </Link>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </header>
  );
}
