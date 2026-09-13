import { describe, expect, it } from "vitest";
import {
  getCatalogCategoryFromSlug,
  getSchemeCategory,
} from "./categories";

describe("scheme categories", () => {
  it("normalizes backend scheme types into catalog categories", () => {
    expect(getSchemeCategory("  low income ")).toBe("Financial Assistance");
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
