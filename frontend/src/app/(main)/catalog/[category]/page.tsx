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

type CatalogCategoryPageProps = {
  params: Promise<{ category: string }>;
};

export const dynamicParams = false;

export function generateStaticParams() {
  return CATALOG_CATEGORY_ROUTES.map(({ slug }) => ({
    category: slug,
  }));
}

export async function generateMetadata({
  params,
}: CatalogCategoryPageProps): Promise<Metadata> {
  const { category: slug } = await params;
  const category = getCatalogCategoryFromSlug(slug);

  if (!category) {
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

  if (!category) {
    notFound();
  }

  const jsonLd = getCatalogJsonLd({
    category,
    path: getCatalogCategoryPath(category),
  });

  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{
          __html: JSON.stringify(jsonLd).replace(/</g, "\\u003c"),
        }}
      />
      <CatalogPageClient initialCategory={category} />
    </>
  );
}
