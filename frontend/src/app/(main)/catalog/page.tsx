import CatalogPageClient from "@/components/catalog/catalog-detail";
import {
  getCatalogCategoryPath,
  getCatalogJsonLd,
  getCatalogMetadata,
} from "@/lib/catalog-seo";
import { getCatalogData, isPublicApiConfigured } from "@/lib/schemes.server";

const path = getCatalogCategoryPath("All");

export const metadata = getCatalogMetadata({ category: "All", path });

// The unfiltered catalog view. There is no intermediate category picker: a
// category is a filter on this page, reached through the dropdown in the
// results header, so browsing starts with schemes on screen rather than a
// taxonomy to classify yourself into.
export default async function CatalogPage() {
  const initialData = isPublicApiConfigured()
    ? await getCatalogData("All")
    : undefined;

  const jsonLd = getCatalogJsonLd({
    category: "All",
    path,
    schemes: initialData?.schemes,
  });

  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{
          __html: JSON.stringify(jsonLd).replace(/</g, "\\u003c"),
        }}
      />
      <CatalogPageClient initialCategory="All" initialData={initialData} />
    </>
  );
}
