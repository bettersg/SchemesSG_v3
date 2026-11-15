import type { MessageDescriptor } from "@lingui/core";
import { msg } from "@lingui/core/macro";
import type { CatalogCategory } from "./categories";

/**
 * Display names for the catalogue categories. The category values themselves
 * stay English: they are route keys and match the scheme data. Typed as a full
 * record so a new category fails the build until it has a label.
 */
export const CATEGORY_LABELS: Record<CatalogCategory, MessageDescriptor> = {
  All: msg({ message: "All categories", comment: "Catalogue category: no filter" }),
  "Financial Assistance": msg({ message: "Financial Assistance", comment: "Scheme category" }),
  "Family & Children": msg({ message: "Family & Children", comment: "Scheme category" }),
  "Health & Wellbeing": msg({ message: "Health & Wellbeing", comment: "Scheme category" }),
  "Housing & Food": msg({ message: "Housing & Food", comment: "Scheme category" }),
  Education: msg({ message: "Education", comment: "Scheme category" }),
  "Employment & Training": msg({ message: "Employment & Training", comment: "Scheme category" }),
  "Seniors & Caregiving": msg({ message: "Seniors & Caregiving", comment: "Scheme category" }),
  "Disability & Transport": msg({ message: "Disability & Transport", comment: "Scheme category" }),
  "Legal & Safety": msg({ message: "Legal & Safety", comment: "Scheme category" }),
  "Community Support": msg({ message: "Community Support", comment: "Scheme category" }),
};
