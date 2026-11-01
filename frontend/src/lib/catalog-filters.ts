import {
  CATALOG_CATEGORY_OPTIONS,
  SCHEME_CATEGORIES,
  type CatalogCategory,
  type SchemeCategory,
} from "@/lib/design-system/categories";
import { getCatalogCategoryPath } from "@/lib/catalog-seo";

/**
 * URA Master Plan planning areas, as stored in `planning_area` (upper case).
 * The catalog API matches them case-insensitively.
 */
export const PLANNING_AREAS = [
  "ANG MO KIO",
  "BEDOK",
  "BISHAN",
  "BOON LAY",
  "BUKIT BATOK",
  "BUKIT MERAH",
  "BUKIT PANJANG",
  "BUKIT TIMAH",
  "CENTRAL WATER CATCHMENT",
  "CHANGI",
  "CHANGI BAY",
  "CHOA CHU KANG",
  "CLEMENTI",
  "DOWNTOWN CORE",
  "GEYLANG",
  "HOUGANG",
  "JURONG EAST",
  "JURONG WEST",
  "KALLANG",
  "LIM CHU KANG",
  "MANDAI",
  "MARINA EAST",
  "MARINA SOUTH",
  "MARINE PARADE",
  "MUSEUM",
  "NEWTON",
  "NORTH-EASTERN ISLANDS",
  "NOVENA",
  "ORCHARD",
  "OUTRAM",
  "PASIR RIS",
  "PAYA LEBAR",
  "PIONEER",
  "PUNGGOL",
  "QUEENSTOWN",
  "RIVER VALLEY",
  "ROCHOR",
  "SELETAR",
  "SEMBAWANG",
  "SENGKANG",
  "SERANGOON",
  "SIMPANG",
  "SINGAPORE RIVER",
  "SOUTHERN ISLANDS",
  "STRAITS VIEW",
  "SUNGEI KADUT",
  "TAMPINES",
  "TANGLIN",
  "TENGAH",
  "TOA PAYOH",
  "TUAS",
  "WESTERN ISLANDS",
  "WESTERN WATER CATCHMENT",
  "WOODLANDS",
  "YISHUN",
] as const;

/** Categories and areas selected on top of the route's category. */
export type CatalogFilterState = {
  categories: SchemeCategory[];
  areas: string[];
};

const CATEGORY_BY_LOWER = new Map(
  SCHEME_CATEGORIES.map((category) => [category.toLowerCase(), category]),
);

/** "TOA PAYOH" → "Toa Payoh" */
export function formatPlanningArea(area: string) {
  return area
    .toLowerCase()
    .replace(
      /(^|[\s-])([a-z])/g,
      (_, sep: string, ch: string) => sep + ch.toUpperCase(),
    );
}

/**
 * Every category the view filters by: the route's category first, then the
 * extra ones from the query string. Empty means all categories.
 */
export function getSelectedCategories(
  routeCategory: CatalogCategory,
  extraCategories: SchemeCategory[],
): SchemeCategory[] {
  const selected = routeCategory === "All" ? [] : [routeCategory];
  return [...new Set([...selected, ...extraCategories])];
}

/**
 * Read `?category=` and `?area=` (each repeatable). Unknown categories are
 * ignored, and the route's own category is not repeated.
 */
export function parseCatalogQuery(
  params: Pick<URLSearchParams, "getAll">,
  routeCategory: CatalogCategory,
): CatalogFilterState {
  const categories = params
    .getAll("category")
    .map((value) => CATEGORY_BY_LOWER.get(value.trim().toLowerCase()))
    .filter(
      (category): category is SchemeCategory =>
        category !== undefined && category !== routeCategory,
    );
  const areas = params
    .getAll("area")
    .map((value) => value.trim().toUpperCase())
    .filter(Boolean);
  return {
    categories: [...new Set(categories)],
    areas: [...new Set(areas)],
  };
}

/**
 * The catalog URL for a selection. The first category keeps its static,
 * prerendered route; extra categories and areas ride in the query string, so
 * existing category links and their search-engine standing stay unchanged.
 */
export function getCatalogFilterHref(
  categories: SchemeCategory[],
  areas: string[],
): string {
  const [first, ...rest] = categories;
  const path = getCatalogCategoryPath(first ?? CATALOG_CATEGORY_OPTIONS[0]);
  const params = new URLSearchParams();
  rest.forEach((category) => params.append("category", category));
  areas.forEach((area) => params.append("area", area));
  const query = params.toString();
  return query ? `${path}?${query}` : path;
}

export function toggleValue<T>(values: T[], value: T): T[] {
  return values.includes(value)
    ? values.filter((item) => item !== value)
    : [...values, value];
}

/** Stable identity for a selection, to key fetches on. */
export function catalogFilterKey(categories: string[], areas: string[]) {
  return JSON.stringify([categories, areas]);
}
