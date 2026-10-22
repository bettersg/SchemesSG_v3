import { describe, expect, it } from "vitest";
import { getSchemeCategory, resolveSchemeCategory } from "./categories";

describe("resolveSchemeCategory", () => {
  it("returns undefined for empty array", () => {
    expect(resolveSchemeCategory([])).toBeUndefined();
  });

  it("returns the category when first type is recognized", () => {
    expect(resolveSchemeCategory(["Financial Assistance"])).toBe(
      "Financial Assistance",
    );
  });

  it("returns the first recognized category when leading types are not categories", () => {
    const types = ["Other", "Financial Assistance"];
    expect(resolveSchemeCategory(types)).toBe("Financial Assistance");
  });

  it("returns the first recognized category from multiple non-category types", () => {
    const types = ["Other", "low income", "family"];
    expect(resolveSchemeCategory(types)).toBe("Financial Assistance");
  });

  it("returns undefined when no types map to categories", () => {
    const types = ["Unknown", "Other", "Miscellaneous"];
    expect(resolveSchemeCategory(types)).toBeUndefined();
  });

  it("maps scheme types to categories via SCHEME_TYPE_CATEGORY_MAP", () => {
    expect(resolveSchemeCategory(["low income"])).toBe("Financial Assistance");
    expect(resolveSchemeCategory(["elderly"])).toBe("Seniors & Caregiving");
    expect(resolveSchemeCategory(["healthcare"])).toBe("Health & Wellbeing");
  });

  it("stops at the first match", () => {
    const types = [
      "Other",
      "family",
      "Financial Assistance",
      "elderly",
    ];
    expect(resolveSchemeCategory(types)).toBe("Family & Children");
  });
});

describe("NCSS-aligned (v2) scheme types", () => {
  it("maps v2 terms and keeps the pre-v2 ones", () => {
    expect(getSchemeCategory("Child and Youth Services")).toBe(
      "Family & Children",
    );
    expect(getSchemeCategory("Disability Support")).toBe(
      "Disability & Transport",
    );
    expect(getSchemeCategory("Elderly")).toBe("Seniors & Caregiving");
  });
});
