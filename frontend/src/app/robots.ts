import type { MetadataRoute } from "next";

const SITE_URL = "https://schemes.sg";

export default function robots(): MetadataRoute.Robots {
  return {
    rules: [
      {
        userAgent: "*",
        allow: "/",
        disallow: [
          // Cursor-paginated catalog URLs. NOTE: this currently also blocks the
          // only path to schemes past the first 20 in a category. It should be
          // narrowed once crawlable, self-canonical paginated URLs exist.
          "/*?cursor=",
          // Every scheme page links to /feedback?source=scheme&schemeId=...
          // ("Suggest a correction"), so without this roughly 600 parameter
          // URLs are crawlable and all canonicalise to /feedback.
          "/feedback?",
        ],
      },
    ],
    sitemap: `${SITE_URL}/sitemap.xml`,
    host: SITE_URL,
  };
}
