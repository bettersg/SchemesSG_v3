import type { MetadataRoute } from "next";
import { getSchemesForSitemap } from "@/lib/schemes.server";
import { CATALOG_ROUTE_PATHS } from "@/lib/catalog-seo";
import { hasIndexableContent } from "@/lib/scheme-indexing";

const SITE_URL = "https://schemes.sg";

// Only returns a date when the source has one. Falling back to new Date()
// stamps every entry with the build time, so crawlers learn to ignore lastmod.
const getLastModified = (value?: string) => {
  if (!value) return undefined;

  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? undefined : date;
};

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  // `changeFrequency` and `priority` are omitted throughout: Google ignores both.
  const staticRoutes: MetadataRoute.Sitemap = [
    "",
    "/about",
    "/developers",
    "/privacy",
    "/terms",
    ...CATALOG_ROUTE_PATHS,
  ].map((route) => ({
    url: `${SITE_URL}${route}`,
  }));

  const schemes = await getSchemesForSitemap();
  const schemeRoutes: MetadataRoute.Sitemap = schemes
    .filter((scheme) => hasIndexableContent(scheme))
    .map((scheme) => ({
      url: `${SITE_URL}/schemes/${scheme.schemeId}`,
      lastModified: getLastModified(scheme.lastUpdated),
    }));

  return [...staticRoutes, ...schemeRoutes];
}
