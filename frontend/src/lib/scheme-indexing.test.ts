import { describe, it, expect } from "vitest";
import { hasIndexableContent } from "./scheme-indexing";
import type { Scheme } from "@/types/types";

const baseScheme: Partial<Scheme> = {
  schemeId: "test-scheme",
  schemeName: "Test Scheme",
  agency: "Test Agency",
  schemeType: ["financial assistance"],
  status: "active",
};

describe("hasIndexableContent", () => {
  it("returns true when description exists", () => {
    const scheme = {
      ...baseScheme,
      description: "A comprehensive scheme for support",
    };
    expect(hasIndexableContent(scheme as Scheme)).toBe(true);
  });

  it("returns true when eligibilityText exists", () => {
    const scheme = {
      ...baseScheme,
      eligibilityText: "Must be a Singapore Citizen",
    };
    expect(hasIndexableContent(scheme as Scheme)).toBe(true);
  });

  it("returns true when howToApply exists", () => {
    const scheme = {
      ...baseScheme,
      howToApply: "Apply via agency website",
    };
    expect(hasIndexableContent(scheme as Scheme)).toBe(true);
  });

  it("returns true when multiple qualifying fields exist", () => {
    const scheme = {
      ...baseScheme,
      description: "Support for families",
      eligibilityText: "Must be below income threshold",
      howToApply: "Contact agency",
    };
    expect(hasIndexableContent(scheme as Scheme)).toBe(true);
  });

  it("returns false when only contact info exists", () => {
    const scheme = {
      ...baseScheme,
      contact: [
        {
          phones: ["1800-123-4567"],
        },
      ],
    };
    expect(hasIndexableContent(scheme as Scheme)).toBe(false);
  });

  it("returns false when only targetAudience exists", () => {
    const scheme = {
      ...baseScheme,
      targetAudience: ["Seniors", "Low-income"],
    };
    expect(hasIndexableContent(scheme as Scheme)).toBe(false);
  });

  it("returns false when only benefits exist", () => {
    const scheme = {
      ...baseScheme,
      benefits: ["Cash assistance", "Food vouchers"],
    };
    expect(hasIndexableContent(scheme as Scheme)).toBe(false);
  });

  it("returns false when only serviceArea exists", () => {
    const scheme = {
      ...baseScheme,
      serviceArea: "Available nationwide",
    };
    expect(hasIndexableContent(scheme as Scheme)).toBe(false);
  });

  it("returns false when only summary exists", () => {
    const scheme = {
      ...baseScheme,
      summary: "Short summary of the scheme",
    };
    expect(hasIndexableContent(scheme as Scheme)).toBe(false);
  });

  it("returns false when no qualifying fields exist", () => {
    expect(hasIndexableContent(baseScheme as Scheme)).toBe(false);
  });

  it("returns false when qualifying fields are empty strings", () => {
    const scheme = {
      ...baseScheme,
      description: "",
      eligibilityText: "",
      howToApply: "",
    };
    expect(hasIndexableContent(scheme as Scheme)).toBe(false);
  });
});
