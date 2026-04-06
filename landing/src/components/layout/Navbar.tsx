"use client"

import { useState, useEffect } from "react"
import { Menu, X, ArrowRight } from "lucide-react"
import { Button } from "@/components/ui/button"
import { useLanguage } from "@/lib/landing-i18n"
import { LanguageToggle } from "@/components/shared/LanguageToggle"
import { cn } from "@/lib/utils"

type NavLink = { label: string; href: string; disabled?: boolean }

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
    function onScroll() { setScrolled(window.scrollY > 20) }
    window.addEventListener("scroll", onScroll, { passive: true })
    return () => window.removeEventListener("scroll", onScroll)
  }, [])

  return (
    <header className={cn(
      "fixed top-0 left-0 right-0 z-50 transition-all duration-300",
      scrolled ? "bg-white/90 backdrop-blur-xl border-b border-[#e8eef6] shadow-sm" : "bg-transparent"
    )}>
      <nav className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
        {/* Logo */}
        <a href="/" className="flex items-center gap-2 font-[var(--font-head)] text-xl tracking-tight cursor-pointer">
          <img src="/logo.svg" alt="SchemesSG" className="h-7 w-auto" />
          <span className="text-[#185FA5] font-bold">Schemes</span>
          <span className="text-[#EF9F27] -ml-1 font-bold">SG</span>
        </a>

        {/* Center pill nav — desktop */}
        <div className="hidden md:flex items-center gap-1 rounded-full bg-[#f0f6ff]/80 backdrop-blur-sm px-2 py-1.5 border border-[#d0e4f7]">
          {navLinks.map((link) =>
            link.disabled ? (
              <span key={link.label} className="relative px-4 py-1.5 text-sm font-medium text-[#B4B2A9] cursor-default rounded-full flex flex-col items-center">
                {link.label}
                <span className="text-[8px] tracking-wider font-semibold text-[#D3D1C7] leading-none">{t.nav.comingSoon}</span>
              </span>
            ) : link.href === "/" ? (
              <a key={link.label} href={link.href}
                className="px-4 py-1.5 text-sm font-semibold text-white rounded-full cursor-pointer transition-all duration-200 bg-[#EF9F27] hover:bg-[#BA7517] flex items-center gap-1"
              >
                {link.label}<ArrowRight className="h-3.5 w-3.5" />
              </a>
            ) : (
              <a key={link.label} href={link.href}
                className="px-4 py-1.5 text-sm font-medium text-[#5F5E5A] rounded-full cursor-pointer transition-all duration-200 hover:bg-[#E6F1FB] hover:text-[#185FA5]"
              >
                {link.label}
              </a>
            )
          )}
        </div>

        {/* Language toggle — desktop */}
        <div className="hidden md:flex items-center"><LanguageToggle /></div>

        {/* Mobile toggle */}
        <button
          className="md:hidden p-2 cursor-pointer text-[#444441]"
          onClick={() => setMobileOpen(!mobileOpen)}
          aria-label={mobileOpen ? t.a11y.closeMenu : t.a11y.openMenu}
        >
          {mobileOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
        </button>
      </nav>

      {/* Mobile menu */}
      {mobileOpen && (
        <div className="md:hidden bg-white/95 backdrop-blur-xl border-b border-[#e8eef6] px-6 pb-6">
          <div className="flex flex-col items-center gap-1 w-full">
            {navLinks.filter((l) => l.href !== "/").map((link) =>
              link.disabled ? (
                <span key={link.label} className="px-3 py-3 text-sm font-medium text-[#B4B2A9] flex flex-col items-center">
                  {link.label}
                  <span className="text-[8px] tracking-wider font-semibold text-[#D3D1C7] leading-none">{t.nav.comingSoon}</span>
                </span>
              ) : (
                <a key={link.label} href={link.href} onClick={() => setMobileOpen(false)}
                  className="w-full px-3 py-3 text-sm font-medium text-[#042C53] hover:bg-[#E6F1FB] hover:text-[#185FA5] rounded-xl transition-colors cursor-pointer text-center"
                >
                  {link.label}
                </a>
              )
            )}
          </div>
          <div className="mt-3 flex justify-center"><LanguageToggle /></div>
          <div className="mt-3 flex justify-center">
            <Button size="sm" className="w-full rounded-xl bg-[#EF9F27] hover:bg-[#BA7517] text-white font-semibold gap-1.5 cursor-pointer border-0" asChild>
              <a href="/">{t.nav.searchSchemes} <ArrowRight className="h-3.5 w-3.5" /></a>
            </Button>
          </div>
        </div>
      )}
    </header>
  )
}
