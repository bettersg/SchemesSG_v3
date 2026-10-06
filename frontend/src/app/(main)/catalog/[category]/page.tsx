import type { Metadata } from "next";
import { notFound } from "next/navigation";
import CatalogPageClient from "@/components/catalog/catalog-detail";
import {
  CATALOG_CATEGORY_ROUTES,
  getCatalogCategoryFromSlug,
} from "@/lib/design-system/categories";
import {
  getCatalogCategoryPath,
  getCatalogJsonLd,
  getCatalogMetadata,
} from "@/lib/catalog-seo";
import { getCatalogData, isPublicApiConfigured } from "@/lib/schemes.server";

type CatalogCategoryPageProps = {
  params: Promise<{ category: string }>;
};

export const dynamicParams = false;

// "All" is excluded: it is /catalog itself, not a slug below it. With
// dynamicParams off, that also makes /catalog/all a 404, and next.config.mjs
// redirects it permanently to /catalog.
export function generateStaticParams() {
  return CATALOG_CATEGORY_ROUTES.filter(
    ({ category }) => category !== "All",
  ).map(({ slug }) => ({
    category: slug,
  }));
}

export async function generateMetadata({
  params,
}: CatalogCategoryPageProps): Promise<Metadata> {
  const { category: slug } = await params;
  const category = getCatalogCategoryFromSlug(slug);

  if (!category || category === "All") {
    return {
      title: "Catalog category not found | Schemes.sg",
      robots: {
        index: false,
        follow: false,
      },
    };
  }

  return getCatalogMetadata({
    category,
    path: getCatalogCategoryPath(category),
  });
}

export default async function CatalogCategoryPage({
  params,
}: CatalogCategoryPageProps) {
  const { category: slug } = await params;
  const category = getCatalogCategoryFromSlug(slug);

  if (!category || category === "All") {
    notFound();
  }

  // Every category route is prerendered, so a secretless build reaches this
  // read with no API behind it and the client refetches after hydration.
  const initialData = isPublicApiConfigured()
    ? await getCatalogData(category)
    : undefined;

  const jsonLd = getCatalogJsonLd({
    category,
    path: getCatalogCategoryPath(category),
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
      <CatalogPageClient
        key={slug}
        initialCategory={category}
        initialData={initialData}
      />
    </>
  );
}
