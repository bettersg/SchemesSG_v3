"use client"

import { Separator } from "@/components/landing/ui/separator"
import { useLanguage } from "@/lib/landing-i18n"

function FooterLinkColumn({ heading, links }: { heading: string; links: { label: string; href: string; comingSoon?: boolean }[] }) {
  return (
    <div>
      <h3 className="text-xs font-semibold uppercase tracking-wider text-neutral-300 mb-4">
        {heading}
      </h3>
      <ul className="space-y-3">
        {links.map((link) => (
          <li key={link.label}>
            {link.comingSoon ? (
              <span className="text-sm text-neutral-600 flex items-center gap-2">
                {link.label}
                <span className="text-[10px] tracking-wider font-medium text-neutral-500 bg-neutral-800 rounded-full px-2 py-0.5">
                  Coming Soon
                </span>
              </span>
            ) : (
              <a
                href={link.href}
                className="text-sm hover:text-white transition-colors cursor-pointer"
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
    <footer className="bg-neutral-950 text-neutral-400 py-16 px-6">
      <div className="mx-auto max-w-7xl">
        <div className="grid grid-cols-2 gap-12 md:grid-cols-4">
          {/* Brand column */}
          <div className="col-span-2 md:col-span-1">
            <a href="/" className="flex items-center gap-2 font-landing-serif text-xl tracking-tight">
              <img src="/landing/logo.svg" alt="Schemes.sg" className="h-7 w-auto" />
              <span className="text-white font-bold">Schemes</span>
              <span className="text-neutral-500 -ml-1">.sg</span>
            </a>
            <p className="mt-4 text-sm leading-relaxed text-neutral-500 max-w-[260px]">
              {t.footer.tagline}
            </p>
          </div>

          <FooterLinkColumn heading={t.footer.productHeading} links={t.footer.productLinks} />
          <FooterLinkColumn heading={t.footer.resourcesHeading} links={t.footer.resourceLinks} />
          <FooterLinkColumn heading={t.footer.legalHeading} links={t.footer.legalLinks} />
        </div>

        <Separator className="my-10 bg-neutral-800" />

        <div className="flex flex-col items-center justify-between gap-4 text-xs text-neutral-600 sm:flex-row">
          <p>{t.footer.copyright.replace("{year}", String(new Date().getFullYear()))}</p>
          <p>{t.footer.madeIn}</p>
        </div>
      </div>
    </footer>
  )
}
