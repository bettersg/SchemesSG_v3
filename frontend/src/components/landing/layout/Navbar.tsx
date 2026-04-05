/* eslint-disable @next/next/no-img-element */
"use client"

import { useState, useEffect } from "react"
import { Menu, X, ArrowRight } from "lucide-react"
import { Button } from "@/components/landing/ui/button"
import { useLanguage } from "@/lib/landing-i18n"
import { LanguageToggle } from "@/components/landing/shared/LanguageToggle"
import { cn } from "@/lib/landing-utils"

type NavLink = {
  label: string
  href: string
  disabled?: boolean
}

export function Navbar() {
  const { t } = useLanguage()
  const [scrolled, setScrolled] = useState(false)
  const [mobileOpen, setMobileOpen] = useState(false)

  const navLinks: NavLink[] = [
    { label: t.nav.catalog, href: "#", disabled: true },
    { label: t.nav.searchSchemes, href: "/" },
    { label: t.nav.contribute, href: "/contribute" },
    { label: t.nav.about, href: "/about" },
  ]

  useEffect(() => {
    function onScroll() {
      setScrolled(window.scrollY > 20)
    }
    window.addEventListener("scroll", onScroll, { passive: true })
    return () => window.removeEventListener("scroll", onScroll)
  }, [])

  return (
    <header
      className={cn(
        "fixed top-0 left-0 right-0 z-50 transition-all duration-300",
        scrolled
          ? "bg-white/80 backdrop-blur-xl border-b border-neutral-200/60 shadow-sm"
          : "bg-transparent"
      )}
    >
      <nav className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
        {/* Logo */}
        <a
          href="/"
          className="flex items-center gap-2 font-landing-serif text-xl tracking-tight cursor-pointer"
        >
          <img src="/landing/logo.svg" alt="Schemes.sg" className="h-7 w-auto" />
          <span className="text-neutral-900 font-bold">Schemes</span>
          <span className="text-neutral-400 -ml-1">.sg</span>
        </a>

        {/* Center pill nav - desktop */}
        <div className="hidden md:flex items-center gap-1 rounded-full bg-neutral-100/80 backdrop-blur-sm px-2 py-1.5 border border-neutral-200/60">
          {navLinks.map((link) =>
            link.disabled ? (
              <span
                key={link.label}
                className="relative px-4 py-1.5 text-sm font-medium text-neutral-300 cursor-default rounded-full flex flex-col items-center"
              >
                {link.label}
                <span className="text-[8px] tracking-wider font-semibold text-neutral-400 leading-none">
                  {t.nav.comingSoon}
                </span>
              </span>
            ) : link.href === "/" ? (
              <a
                key={link.label}
                href={link.href}
                className="px-4 py-1.5 text-sm font-semibold text-neutral-900 rounded-full cursor-pointer transition-all duration-200 bg-amber-400 hover:bg-amber-500"
              >
                {link.label}
                <ArrowRight className="inline h-3.5 w-3.5 ml-1.5" />
              </a>
            ) : (
              <a
                key={link.label}
                href={link.href}
                className="px-4 py-1.5 text-sm font-medium text-neutral-500 rounded-full cursor-pointer transition-all duration-200 hover:bg-neutral-200/80 hover:text-neutral-900"
              >
                {link.label}
              </a>
            )
          )}
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
          {mobileOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
        </button>
      </nav>

      {/* Mobile menu */}
      {mobileOpen && (
        <div className="md:hidden bg-white/95 backdrop-blur-xl border-b border-neutral-200 px-6 pb-6">
          <div className="flex flex-col items-center gap-1 w-full">
            {navLinks.filter((link) => link.href !== "/").map((link) =>
              link.disabled ? (
                <span
                  key={link.label}
                  className="px-3 py-3 text-sm font-medium text-neutral-300 flex flex-col items-center"
                >
                  {link.label}
                  <span className="text-[8px] tracking-wider font-semibold text-neutral-400 leading-none">
                    {t.nav.comingSoon}
                  </span>
                </span>
              ) : (
                <a
                  key={link.label}
                  href={link.href}
                  onClick={() => setMobileOpen(false)}
                  className="px-3 py-3 text-sm font-medium text-neutral-900 hover:bg-neutral-100 rounded-lg transition-colors cursor-pointer"
                >
                  {link.label}
                </a>
              )
            )}
          </div>
          <div className="mt-3 flex justify-center">
            <LanguageToggle />
          </div>
          <div className="mt-3 flex justify-center">
            <Button
              size="sm"
              className="w-full rounded-lg bg-amber-400 hover:bg-amber-500 text-neutral-900 font-semibold gap-1.5 cursor-pointer"
              asChild
            >
              <a href="/">
                {t.nav.searchSchemes} <ArrowRight className="h-3.5 w-3.5" />
              </a>
            </Button>
          </div>
        </div>
      )}
    </header>
  )
}
