import type { FilterObjType, Scheme } from "@/types/types";
import { parseArrayString } from "@/lib/utils";

export function filterSchemes(
  schemes: Scheme[],
  filters: FilterObjType,
): Scheme[] {
  return schemes.filter((scheme) => {
    if (filters.planningArea?.size) {
      const planningAreas = parseArrayString(scheme.planningArea) ?? [];
      if (!planningAreas.some((area) => filters.planningArea?.has(area))) {
        return false;
      }
    }

    if (filters.agency?.size && !filters.agency.has(scheme.agency)) {
      return false;
    }

    return true;
  });
}
