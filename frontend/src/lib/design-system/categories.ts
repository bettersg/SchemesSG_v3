import { cn } from "@/lib/utils";

export const SCHEME_CATEGORIES = [
  "Financial Assistance",
  "Mental Health",
  "Family",
  "Healthcare",
  "Housing",
  "Employment",
  "Food Support",
  "Education",
  "Eldercare",
  "Disability",
] as const;

export type SchemeCategory = (typeof SCHEME_CATEGORIES)[number];

const CATEGORY_ALIASES: Record<string, SchemeCategory> = {
  "financial aid": "Financial Assistance",
  "financial assistance": "Financial Assistance",
  "mental health": "Mental Health",
  "family support": "Family",
  family: "Family",
  healthcare: "Healthcare",
  housing: "Housing",
  employment: "Employment",
  "food assistance": "Food Support",
  "food support": "Food Support",
  education: "Education",
  eldercare: "Eldercare",
  disability: "Disability",
};

const CATEGORY_CLASS_NAMES: Record<SchemeCategory, string> = {
  "Financial Assistance":
    "border-(--schemes-category-financial-border) bg-(--schemes-category-financial-bg) text-(--schemes-category-financial-text)",
  "Mental Health":
    "border-(--schemes-category-mental-border) bg-(--schemes-category-mental-bg) text-(--schemes-category-mental-text)",
  Family:
    "border-(--schemes-category-family-border) bg-(--schemes-category-family-bg) text-(--schemes-category-family-text)",
  Healthcare:
    "border-(--schemes-category-healthcare-border) bg-(--schemes-category-healthcare-bg) text-(--schemes-category-healthcare-text)",
  Housing:
    "border-(--schemes-category-housing-border) bg-(--schemes-category-housing-bg) text-(--schemes-category-housing-text)",
  Employment:
    "border-(--schemes-category-employment-border) bg-(--schemes-category-employment-bg) text-(--schemes-category-employment-text)",
  "Food Support":
    "border-(--schemes-category-food-border) bg-(--schemes-category-food-bg) text-(--schemes-category-food-text)",
  Education:
    "border-(--schemes-category-education-border) bg-(--schemes-category-education-bg) text-(--schemes-category-education-text)",
  Eldercare:
    "border-(--schemes-category-eldercare-border) bg-(--schemes-category-eldercare-bg) text-(--schemes-category-eldercare-text)",
  Disability:
    "border-(--schemes-category-disability-border) bg-(--schemes-category-disability-bg) text-(--schemes-category-disability-text)",
};

export function normalizeSchemeCategory(label: string): SchemeCategory | string {
  const normalized = label.trim().toLowerCase();
  return CATEGORY_ALIASES[normalized] ?? label.trim();
}

export function getSchemeCategoryClassName(label: string) {
  const category = normalizeSchemeCategory(label);
  if (SCHEME_CATEGORIES.includes(category as SchemeCategory)) {
    return CATEGORY_CLASS_NAMES[category as SchemeCategory];
  }

  return "border-(--schemes-blue-100) bg-(--schemes-blue-50) text-(--schemes-blue-800)";
}

export function getSchemeCategoryChipClassName(label: string, className?: string) {
  return cn(
    "inline-flex whitespace-nowrap rounded-full border font-semibold",
    getSchemeCategoryClassName(label),
    className,
  );
}
