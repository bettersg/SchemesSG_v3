"use client";

import { ArrowUpRight } from "lucide-react";
import { Separator } from "@heroui/react";
import Image from "next/image";
import Link from "next/link";
import { cssTransition } from "@/lib/design-system/motion";
import type { MessageDescriptor } from "@lingui/core";
import { Trans, useLingui } from "@lingui/react/macro";
import { CATALOG_CATEGORY_OPTIONS } from "@/lib/design-system/categories";
import { CATEGORY_LABELS } from "@/lib/design-system/category-labels";
import { getCatalogCategoryPath } from "@/lib/catalog-seo";

function FooterLinkColumn({
  heading,
  links,
}: {
  heading: React.ReactNode;
  links: { label: React.ReactNode; href: string; comingSoon?: boolean }[];
}) {
  return (
    <div>
      <h2 className="text-xs font-semibold uppercase tracking-wider text-neutral-300 mb-4">
        {heading}
      </h2>
      <ul className="space-y-3 break-words">
        {links.map((link, index) => (
          <li key={index}>
            {link.comingSoon ? (
              <span className="text-sm text-neutral-400 flex flex-wrap items-center gap-2">
                {link.label}
                <span className="text-[10px] tracking-wider font-medium text-neutral-400 bg-neutral-800 rounded-full px-2 py-0.5">
                  <Trans comment="Badge shown on footer links that are not yet available">
                    Coming soon
                  </Trans>
                </span>
              </span>
            ) : link.href.startsWith("/") ? (
              <Link
                href={link.href}
                className="text-sm hover:text-white transition-colors cursor-pointer"
              >
                {link.label}
              </Link>
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
  );
}

/**
 * Every category route, so each page carries server-rendered links into the
 * catalog.
 */
function getSchemesLinks(label: (descriptor: MessageDescriptor) => string) {
  const categoryLinks = CATALOG_CATEGORY_OPTIONS.filter(
    (cat) => cat !== "All",
  ).map((cat) => ({
    label: label(CATEGORY_LABELS[cat]),
    href: getCatalogCategoryPath(cat),
  }));
  return [
    ...categoryLinks,
    { label: label(CATEGORY_LABELS.All), href: "/catalog" },
  ];
}

export function Footer() {
  const { i18n } = useLingui();
  const schemesLinks = getSchemesLinks((d) => i18n._(d));

  const productLinks = [
    { label: <Trans comment="Footer link">Search</Trans>, href: "/" },
    { label: <Trans comment="Footer link">Features</Trans>, href: "#features" },
    { label: <Trans comment="Footer link">FAQ</Trans>, href: "#faq" },
  ];

  const resourceLinks = [
    { label: <Trans comment="Footer link">About</Trans>, href: "/about" },
    {
      label: <Trans comment="Footer link">Contribute</Trans>,
      href: "/contribute",
    },
    { label: <Trans comment="Footer link">Feedback</Trans>, href: "/feedback" },
    {
      label: <Trans comment="Footer link">Developers</Trans>,
      href: "/developers",
    },
    {
      label: <Trans comment="Footer link">Sitemap</Trans>,
      href: "/sitemap.xml",
    },
    {
      label: <Trans comment="Footer link">Contact</Trans>,
      href: "#",
      comingSoon: true,
    },
  ];

  const legalLinks = [
    {
      label: <Trans comment="Footer link">Privacy Policy</Trans>,
      href: "/privacy",
    },
    {
      label: <Trans comment="Footer link">Terms of Service</Trans>,
      href: "/terms",
    },
  ];

  const year = new Date().getFullYear();

  return (
    <footer className="bg-neutral-950 text-neutral-400 py-16 px-6">
      <div className="mx-auto max-w-7xl">
        <div className="grid grid-cols-2 gap-x-6 gap-y-12 md:grid-cols-5 md:gap-12">
          <div className="col-span-2 md:col-span-1">
            <a
              href="/"
              className="flex items-center gap-2 font-serif text-xl tracking-tight"
            >
              <Image
                src="/logo.svg"
                alt=""
                width={28}
                height={28}
                className="h-7 w-7"
              />
              <span className="text-white font-bold">Schemes</span>
              <span className="text-neutral-400 -ml-1">.sg</span>
            </a>
            <p className="mt-4 text-sm leading-relaxed text-neutral-400">
              <Trans comment="Footer tagline">
                Making social assistance accessible for everyone.
              </Trans>
            </p>
          </div>

          <FooterLinkColumn
            heading={<Trans comment="Footer column heading">Schemes</Trans>}
            links={schemesLinks}
          />
          <FooterLinkColumn
            heading={<Trans comment="Footer column heading">Product</Trans>}
            links={productLinks}
          />
          <FooterLinkColumn
            heading={<Trans comment="Footer column heading">Resources</Trans>}
            links={resourceLinks}
          />
          <FooterLinkColumn
            heading={<Trans comment="Footer column heading">Legal</Trans>}
            links={legalLinks}
          />
        </div>

        <Separator className="my-10 bg-neutral-800" />

        <div className="flex justify-center mb-6">
          <a
            href="https://better.sg"
            target="_blank"
            rel="noopener noreferrer"
            className={`${cssTransition.colorsState} inline-flex max-w-full flex-wrap items-center justify-center gap-x-3 gap-y-1 rounded-full bg-neutral-900 border border-neutral-800 px-4 py-1.5 text-xs text-neutral-400 hover:border-neutral-700 hover:text-neutral-300 cursor-pointer`}
          >
            <span className="leading-none">
              <Trans comment="Footer banner, followed by the better.sg logo image: the sentence must end where the logo starts">
                Built by volunteers at
              </Trans>
            </span>
            <Image
              src="/landing/featured/bettersg-logo.svg"
              alt="better.sg"
              width={64}
              height={14}
              className="-mx-1.5 h-3.5 w-auto translate-y-[1px] brightness-0 invert"
            />
            <span className="h-3 w-px bg-neutral-700 shrink-0" />
            <span className="font-medium text-neutral-300 leading-none flex items-center gap-1">
              <Trans comment="Footer link to better.sg">Get involved</Trans>{" "}
              <ArrowUpRight className="h-3 w-3" />
            </span>
          </a>
        </div>

        <div className="flex flex-col items-center justify-between gap-4 text-xs text-neutral-400 sm:flex-row">
          <p>
            <Trans comment="Footer copyright notice with year placeholder">
              © {year} Schemes.sg. All rights reserved.
            </Trans>
          </p>
          <p>
            <Trans comment="Footer location text">
              Made with care in Singapore
            </Trans>
          </p>
        </div>
      </div>
    </footer>
  );
}
