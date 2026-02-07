import { Separator } from "@/components/ui/separator"
import { useLanguage } from "@/i18n"

export function Footer() {
  const { t } = useLanguage()

  return (
    <footer className="bg-neutral-950 text-neutral-400 py-16 px-6">
      <div className="mx-auto max-w-7xl">
        <div className="grid grid-cols-2 gap-12 md:grid-cols-4">
          {/* Brand column */}
          <div className="col-span-2 md:col-span-1">
            <a href="/" className="flex items-center gap-2 font-serif text-xl tracking-tight">
              <img src="/logo.svg" alt="" className="h-7 w-auto" />
              <span className="text-white font-bold">Schemes</span>
              <span className="text-neutral-500 -ml-1">.sg</span>
            </a>
            <p className="mt-4 text-sm leading-relaxed text-neutral-500 max-w-[260px]">
              {t.footer.tagline}
            </p>
          </div>

          {/* Product links */}
          <div>
            <h3 className="text-xs font-semibold uppercase tracking-wider text-neutral-300 mb-4">
              {t.footer.productHeading}
            </h3>
            <ul className="space-y-3">
              {t.footer.productLinks.map((link) => (
                <li key={link.href}>
                  <a
                    href={link.href}
                    className="text-sm hover:text-white transition-colors cursor-pointer"
                  >
                    {link.label}
                  </a>
                </li>
              ))}
            </ul>
          </div>

          {/* Resources links */}
          <div>
            <h3 className="text-xs font-semibold uppercase tracking-wider text-neutral-300 mb-4">
              {t.footer.resourcesHeading}
            </h3>
            <ul className="space-y-3">
              {t.footer.resourceLinks.map((link) => (
                <li key={link.href}>
                  <a
                    href={link.href}
                    className="text-sm hover:text-white transition-colors cursor-pointer"
                  >
                    {link.label}
                  </a>
                </li>
              ))}
            </ul>
          </div>

          {/* Legal links */}
          <div>
            <h3 className="text-xs font-semibold uppercase tracking-wider text-neutral-300 mb-4">
              {t.footer.legalHeading}
            </h3>
            <ul className="space-y-3">
              {t.footer.legalLinks.map((link) => (
                <li key={link.href}>
                  <a
                    href={link.href}
                    className="text-sm hover:text-white transition-colors cursor-pointer"
                  >
                    {link.label}
                  </a>
                </li>
              ))}
            </ul>
          </div>
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
