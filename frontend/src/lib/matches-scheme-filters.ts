import { FilterObjType, Scheme } from "@/types/types";
import { parseArrayString } from "@/lib/utils";

/**
 * Pure predicate: does a scheme pass the active Location/Agency filters?
 *
 * Shared by the chat results list and the catalog. An empty filter set matches
 * everything. Filters combine as AND across dimensions (a scheme must satisfy
 * every active dimension) and OR within a dimension (any selected value).
 */
export function matchesSchemeFilters(
  scheme: Scheme,
  filterObj: FilterObjType,
): boolean {
  if (filterObj.planningArea && filterObj.planningArea.size > 0) {
    // planningArea is stored inconsistently as a string or an array; normalise
    // both, then match if any selected area is present on the scheme.
    const schemeAreas = new Set(parseArrayString(scheme.planningArea));
    if (filterObj.planningArea.intersection(schemeAreas).size === 0) {
      return false;
    }
  }
  if (filterObj.agency && filterObj.agency.size > 0) {
    if (!scheme.agency || !filterObj.agency.has(scheme.agency)) {
      return false;
    }
  }
  return true;
}
