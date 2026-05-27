import type { MetadataRoute } from "next";
import { getSchemesForSitemap } from "@/lib/scheme-detail";
import { CATALOG_ROUTE_PATHS } from "@/lib/catalog-seo";

const SITE_URL = "https://schemes.sg";

const getLastModified = (value?: string) => {
  if (!value) {
    return new Date();
  }

  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? new Date() : date;
};

const getStaticRoutePriority = (route: string) => {
  if (route === "") return 1;
  if (route === "/about") return 0.9;
  if (route.startsWith("/catalog")) return 0.75;
  return 0.7;
};

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const staticRoutes: MetadataRoute.Sitemap = [
    "",
    "/about",
    "/contribute",
    "/feedback",
    ...CATALOG_ROUTE_PATHS,
  ].map((route) => ({
    url: `${SITE_URL}${route}`,
    lastModified: new Date(),
    changeFrequency: "weekly",
    priority: getStaticRoutePriority(route),
  }));

  const schemes = await getSchemesForSitemap();
  const schemeRoutes: MetadataRoute.Sitemap = schemes.map((scheme) => ({
    url: `${SITE_URL}/schemes/${scheme.schemeId}`,
    lastModified: getLastModified(scheme.lastUpdated),
    changeFrequency: "weekly",
    priority: 0.8,
  }));

  return [...staticRoutes, ...schemeRoutes];
}
