import { cn } from "@/lib/utils";
import { productBlueOutlineSurface } from "@/lib/design-system/product-styles";

export const SCHEME_CATEGORIES = [
  "Financial Assistance",
  "Family & Children",
  "Health & Wellbeing",
  "Housing & Food",
  "Education",
  "Employment & Training",
  "Seniors & Caregiving",
  "Disability & Transport",
  "Legal & Safety",
  "Community Support",
] as const;

export type SchemeCategory = (typeof SCHEME_CATEGORIES)[number];

export const CATALOG_CATEGORY_OPTIONS = ["All", ...SCHEME_CATEGORIES] as const;

export type CatalogCategory = (typeof CATALOG_CATEGORY_OPTIONS)[number];

export const CATALOG_CATEGORY_SLUGS: Record<CatalogCategory, string> = {
  All: "all",
  "Financial Assistance": "financial-assistance",
  "Family & Children": "family-children",
  "Health & Wellbeing": "health-wellbeing",
  "Housing & Food": "housing-food",
  Education: "education",
  "Employment & Training": "employment-training",
  "Seniors & Caregiving": "seniors-caregiving",
  "Disability & Transport": "disability-transport",
  "Legal & Safety": "legal-safety",
  "Community Support": "community-support",
};

export const CATALOG_CATEGORIES_BY_SLUG = Object.fromEntries(
  CATALOG_CATEGORY_OPTIONS.map((category) => [
    CATALOG_CATEGORY_SLUGS[category],
    category,
  ]),
) as Record<string, CatalogCategory>;

export const CATALOG_CATEGORY_ROUTES = CATALOG_CATEGORY_OPTIONS.map(
  (category) => ({
    category,
    slug: CATALOG_CATEGORY_SLUGS[category],
  }),
);

export function getCatalogCategoryFromSlug(slug: string) {
  return CATALOG_CATEGORIES_BY_SLUG[slug] ?? null;
}

const SCHEME_TYPE_CATEGORY_MAP: Record<string, SchemeCategory> = {
  "financial assistance": "Financial Assistance",
  "low income": "Financial Assistance",
  "covid-19 support": "Financial Assistance",

  family: "Family & Children",
  children: "Family & Children",
  youth: "Family & Children",
  "youth-at-risk": "Family & Children",
  "single parents": "Family & Children",
  women: "Family & Children",

  healthcare: "Health & Wellbeing",
  "mental health": "Health & Wellbeing",
  "end-of-life/palliative care": "Health & Wellbeing",
  "counselling and emotional support": "Health & Wellbeing",

  "housing/shelter": "Housing & Food",
  "food support": "Housing & Food",

  "education support": "Education",

  "employment support": "Employment & Training",
  "vocational training": "Employment & Training",
  "ex-offender support": "Employment & Training",

  elderly: "Seniors & Caregiving",
  "caregiver support": "Seniors & Caregiving",

  "persons with disabilities (pwd)": "Disability & Transport",
  "special needs": "Disability & Transport",
  "transport support": "Disability & Transport",

  "legal aid": "Legal & Safety",
  "abuse/family violence": "Legal & Safety",

  "general public support": "Community Support",
};

// const CATEGORY_ALIASES: Record<string, SchemeCategory> = {
//   "financial aid": "Financial Assistance",
//   "financial assistance": "Financial Assistance",

//   "family & children": "Family & Children",
//   "family and children": "Family & Children",
//   "family support": "Family & Children",
//   family: "Family & Children",
//   childcare: "Family & Children",

//   "health & wellbeing": "Health & Wellbeing",
//   "health and wellbeing": "Health & Wellbeing",
//   healthcare: "Health & Wellbeing",

//   "housing & food": "Housing & Food",
//   "housing and food": "Housing & Food",
//   housing: "Housing & Food",
//   "food assistance": "Housing & Food",
//   "food support": "Housing & Food",
//   "housing/shelter": "Housing & Food",
//   "housing shelter": "Housing & Food",

//   education: "Education",
//   "education support": "Education",

//   "employment & training": "Employment & Training",
//   "employment and training": "Employment & Training",
//   employment: "Employment & Training",
//   "employment support": "Employment & Training",

//   "seniors & caregiving": "Seniors & Caregiving",
//   "seniors and caregiving": "Seniors & Caregiving",
//   seniors: "Seniors & Caregiving",
//   eldercare: "Seniors & Caregiving",
//   elderly: "Seniors & Caregiving",

//   "disability & transport": "Disability & Transport",
//   "disability and transport": "Disability & Transport",
//   disability: "Disability & Transport",
//   "persons with disabilities (pwd)": "Disability & Transport",
//   "persons with disabilities": "Disability & Transport",
//   pwd: "Disability & Transport",

//   "legal & safety": "Legal & Safety",
//   "legal and safety": "Legal & Safety",
//   "legal aid": "Legal & Safety",
//   "abuse/family violence": "Legal & Safety",
//   "abuse family violence": "Legal & Safety",
//   "family violence": "Legal & Safety",

//   "community support": "Community Support",
//   "general public support": "Community Support",
// };

const CATEGORY_CLASS_NAMES: Record<SchemeCategory, string> = {
  "Financial Assistance":
    "border-(--schemes-category-financial-border) bg-(--schemes-category-financial-bg) text-(--schemes-category-financial-text)",
  "Family & Children":
    "border-(--schemes-category-family-border) bg-(--schemes-category-family-bg) text-(--schemes-category-family-text)",
  "Health & Wellbeing":
    "border-(--schemes-category-healthcare-border) bg-(--schemes-category-healthcare-bg) text-(--schemes-category-healthcare-text)",
  "Housing & Food":
    "border-(--schemes-category-housing-border) bg-(--schemes-category-housing-bg) text-(--schemes-category-housing-text)",
  Education:
    "border-(--schemes-category-education-border) bg-(--schemes-category-education-bg) text-(--schemes-category-education-text)",
  "Employment & Training":
    "border-(--schemes-category-employment-border) bg-(--schemes-category-employment-bg) text-(--schemes-category-employment-text)",
  "Seniors & Caregiving":
    "border-(--schemes-category-eldercare-border) bg-(--schemes-category-eldercare-bg) text-(--schemes-category-eldercare-text)",
  "Disability & Transport":
    "border-(--schemes-category-disability-border) bg-(--schemes-category-disability-bg) text-(--schemes-category-disability-text)",
  "Legal & Safety":
    "border-(--schemes-category-mental-border) bg-(--schemes-category-mental-bg) text-(--schemes-category-mental-text)",
  "Community Support":
    "border-(--schemes-category-food-border) bg-(--schemes-category-food-bg) text-(--schemes-category-food-text)",
};

export function getSchemeCategory(label: string): SchemeCategory | undefined {
  const normalized = label.trim().toLowerCase();
  const canonicalCategory = SCHEME_CATEGORIES.find(
    (category) => category.toLowerCase() === normalized,
  );

  return canonicalCategory ?? SCHEME_TYPE_CATEGORY_MAP[normalized];
}

export function getSchemeCategoryClassName(label: string) {
  const category = getSchemeCategory(label);
  if (category) {
    return CATEGORY_CLASS_NAMES[category];
  }
  return productBlueOutlineSurface;
}

export function getSchemeCategoryChipClassName(
  label: string,
  className?: string,
) {
  return cn(
    "inline-flex whitespace-nowrap rounded-full border font-semibold",
    getSchemeCategoryClassName(label),
    className,
  );
}
