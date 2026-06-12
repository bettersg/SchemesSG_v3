import CatalogDetail from "@/components/catalog/catalog-detail";
import { getCatalogJsonLd, getCatalogMetadata } from "@/lib/catalog-seo";
import {
  CATALOG_CATEGORY_ROUTES,
  type CatalogCategory,
} from "@/lib/design-system/categories";

export const metadata = getCatalogMetadata({
  path: "/catalog",
});

const jsonLd = getCatalogJsonLd({
  path: "/catalog",
});

type CatalogPageProps = {
  params: Promise<{ category: string }>;
};

export default async function CatalogPage({ params }: CatalogPageProps) {
  const { category } = await params;
  const initialCategory = CATALOG_CATEGORY_ROUTES.find(
    (route) => route.slug === category,
  )?.category;
  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{
          __html: JSON.stringify(jsonLd).replace(/</g, "\\u003c"),
        }}
      />
      <CatalogDetail initialCategory={initialCategory} />
    </>
  );
}
