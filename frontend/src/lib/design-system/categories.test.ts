import { describe, expect, it } from "vitest";
import {
  getCatalogCategoryFromSlug,
  getSchemeCategory,
} from "./categories";

describe("scheme categories", () => {
  it("normalizes backend scheme types into catalog categories", () => {
    expect(getSchemeCategory("  low income ")).toBe("Financial Assistance");
  });

  it("maps NCSS-aligned (v2) scheme types and keeps the pre-v2 ones", () => {
    expect(getSchemeCategory("Child and Youth Services")).toBe(
      "Family & Children",
    );
    expect(getSchemeCategory("Seniors Housing and Home Improvement")).toBe(
      "Housing & Food",
    );
    expect(getSchemeCategory("Elderly")).toBe("Seniors & Caregiving");
  });

  it("resolves catalog route slugs", () => {
    expect(getCatalogCategoryFromSlug("family-children")).toBe(
      "Family & Children",
    );
  });

  it("rejects unknown catalog route slugs", () => {
    expect(getCatalogCategoryFromSlug("unknown-category")).toBeNull();
  });
});
