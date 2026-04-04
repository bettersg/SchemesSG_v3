"use client"

import { ArrowUpRight } from "lucide-react"
import { Separator } from "@/components/ui/separator"
import { useLanguage } from "@/lib/landing-i18n"

function FooterLinkColumn({ heading, links }: {
  heading: string
  links: { label: string; href: string; comingSoon?: boolean }[]
}) {
  return (
    <div>
      <h3 className="text-xs font-semibold uppercase tracking-wider text-white/40 mb-4">
        {heading}
      </h3>
      <ul className="space-y-3">
        {links.map((link) => (
          <li key={link.label}>
            {link.comingSoon ? (
              <span className="text-sm text-white/25 flex items-center gap-2">
                {link.label}
                <span className="text-[10px] tracking-wider font-medium text-white/20 bg-white/8 rounded-full px-2 py-0.5 border border-white/10">
                  Coming Soon
                </span>
              </span>
            ) : (
              <a
                href={link.href}
                className="text-sm text-white/50 hover:text-white transition-colors duration-200 cursor-pointer"
              >
                {link.label}
              </a>
            )}
          </li>
        ))}
      </ul>
    </div>
  )
}

export function Footer() {
  const { t } = useLanguage()

  return (
    <footer className="bg-[#042C53] text-white/50 py-16 px-6">
      <div className="mx-auto max-w-7xl">
        <div className="grid grid-cols-2 gap-12 md:grid-cols-4">
          {/* Brand column */}
          <div className="col-span-2 md:col-span-1">
            <a href="/" className="flex items-center gap-2 font-[var(--font-head)] text-xl tracking-tight">
              <img src="/landing/logo.svg" alt="SchemesSG" className="h-7 w-auto brightness-0 invert" />
              <span className="text-white font-bold">Schemes</span>
              <span className="text-[#EF9F27] -ml-1 font-bold">SG</span>
            </a>
            <p className="mt-4 text-sm leading-relaxed text-white/40 max-w-[260px]">
              {t.footer.tagline}
            </p>
          </div>

          <FooterLinkColumn heading={t.footer.productHeading} links={t.footer.productLinks} />
          <FooterLinkColumn heading={t.footer.resourcesHeading} links={t.footer.resourceLinks} />
          <FooterLinkColumn heading={t.footer.legalHeading} links={t.footer.legalLinks} />
        </div>

        <Separator className="my-10 bg-white/10" />

        {/* Better.sg attribution */}
        <div className="flex justify-center mb-6">
          <a
            href="https://better.sg"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-3 rounded-full bg-white/5 border border-white/10 px-4 py-1.5 text-xs text-white/40 hover:border-white/20 hover:text-white/60 transition-colors duration-200 cursor-pointer"
          >
            <span className="leading-none">{t.hero.volunteerBanner}</span>
            <img
              src="/landing/featured/bettersg-logo.svg"
              alt="better.sg"
              className="h-3.5 w-auto brightness-0 invert opacity-50 -mx-1.5 translate-y-[1px]"
            />
            <span className="h-3 w-px bg-white/15 shrink-0" />
            <span className="font-medium text-white/50 leading-none flex items-center gap-1">
              {t.hero.getInvolved} <ArrowUpRight className="h-3 w-3" />
            </span>
          </a>
        </div>

        <div className="flex flex-col items-center justify-between gap-4 text-xs text-white/25 sm:flex-row">
          <p>{t.footer.copyright.replace("{year}", String(new Date().getFullYear()))}</p>
          <p>{t.footer.madeIn}</p>
        </div>
      </div>
    </footer>
  )
}
