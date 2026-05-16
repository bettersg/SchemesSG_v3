import type { MetadataRoute } from "next";
import { getSchemesForSitemap } from "@/lib/scheme-detail";

const SITE_URL = "https://schemes.sg";

const getLastModified = (value?: string) => {
  if (!value) {
    return new Date();
  }

  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? new Date() : date;
};

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const staticRoutes: MetadataRoute.Sitemap = [
    "",
    "/catalog",
    "/about",
    "/contribute",
    "/feedback",
  ].map((route) => ({
    url: `${SITE_URL}${route}`,
    lastModified: new Date(),
    changeFrequency: "weekly",
    priority: route === "" ? 1 : 0.7,
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
