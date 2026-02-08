import { useState, useEffect } from "react"
import { Menu, X, ArrowRight } from "lucide-react"
import { Button } from "@/components/ui/button"
import { useLanguage } from "@/i18n"
import { LanguageToggle } from "@/components/shared/LanguageToggle"
import { cn } from "@/lib/utils"

const navLinkHrefs = ["#about", "#features", "#contribute"]

export function Navbar() {
  const { t } = useLanguage()
  const [scrolled, setScrolled] = useState(false)
  const [mobileOpen, setMobileOpen] = useState(false)

  const navLinks = [
    { label: t.nav.about, href: navLinkHrefs[0] },
    { label: t.nav.features, href: navLinkHrefs[1] },
    { label: t.nav.contribute, href: navLinkHrefs[2] },
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
          className="flex items-center gap-2 font-serif text-xl tracking-tight cursor-pointer"
        >
          <img src="/logo.svg" alt="Schemes.sg" className="h-7 w-auto" />
          <span className="text-neutral-900 font-bold">Schemes</span>
          <span className="text-neutral-400 -ml-1">.sg</span>
        </a>

        {/* Center pill nav - desktop */}
        <div className="hidden md:flex items-center gap-1 rounded-full bg-neutral-100/80 backdrop-blur-sm px-2 py-1.5 border border-neutral-200/60">
          {navLinks.map((link) => (
            <a
              key={link.href}
              href={link.href}
              className="px-4 py-1.5 text-sm font-medium text-neutral-500 hover:text-neutral-900 transition-colors rounded-full cursor-pointer"
            >
              {link.label}
            </a>
          ))}
          <Button
            size="sm"
            className="rounded-full bg-amber-400 hover:bg-amber-500 text-neutral-900 font-semibold gap-1.5 cursor-pointer border-0 shadow-none"
            asChild
          >
            <a href="https://schemes.sg" target="_blank" rel="noopener noreferrer">
              {t.nav.findSchemes} <ArrowRight className="h-3.5 w-3.5" />
            </a>
          </Button>
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
          <div className="flex flex-col items-center gap-1">
            {navLinks.map((link) => (
              <a
                key={link.href}
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
            <Button
              size="sm"
              className="w-full rounded-lg bg-amber-400 hover:bg-amber-500 text-neutral-900 font-semibold gap-1.5 cursor-pointer"
              asChild
            >
              <a href="https://schemes.sg" target="_blank" rel="noopener noreferrer">
                {t.nav.findSchemes} <ArrowRight className="h-3.5 w-3.5" />
              </a>
            </Button>
          </div>
        </div>
      )}
    </header>
  )
}
