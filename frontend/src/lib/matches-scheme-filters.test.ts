import { describe, expect, it } from "vitest";
import { matchesSchemeFilters } from "./matches-scheme-filters";
import { Scheme } from "@/types/types";

// Minimal scheme factory — only the fields the filter reads matter.
function scheme(overrides: Partial<Scheme> = {}): Scheme {
  return {
    schemeId: "s1",
    schemeType: [],
    schemeName: "Test Scheme",
    agency: "Test Agency",
    description: "",
    targetAudience: [],
    scrapedText: "",
    benefits: [],
    link: "",
    image: "",
    searchBooster: "",
    query: "",
    planningArea: [],
    summary: "",
    contact: [],
    howToApply: "",
    eligibilityText: "",
    lastUpdated: "",
    serviceArea: "",
    ...overrides,
  };
}

describe("matchesSchemeFilters", () => {
  it("matches any scheme when no filters are active", () => {
    expect(matchesSchemeFilters(scheme(), {})).toBe(true);
  });

  it("filters by agency: includes a matching agency, excludes others", () => {
    const filter = { agency: new Set(["MSF"]) };
    expect(matchesSchemeFilters(scheme({ agency: "MSF" }), filter)).toBe(true);
    expect(matchesSchemeFilters(scheme({ agency: "AIC" }), filter)).toBe(false);
  });

  it("filters by location when planningArea is an array", () => {
    const filter = { planningArea: new Set(["BEDOK"]) };
    expect(
      matchesSchemeFilters(scheme({ planningArea: ["BEDOK", "YISHUN"] }), filter),
    ).toBe(true);
    expect(
      matchesSchemeFilters(scheme({ planningArea: ["TAMPINES"] }), filter),
    ).toBe(false);
  });

  it("filters by location when planningArea is a scalar string", () => {
    const filter = { planningArea: new Set(["QUEENSTOWN"]) };
    expect(
      matchesSchemeFilters(scheme({ planningArea: "QUEENSTOWN" }), filter),
    ).toBe(true);
    expect(
      matchesSchemeFilters(scheme({ planningArea: "BEDOK" }), filter),
    ).toBe(false);
  });

  it("requires every active dimension to match (AND across location + agency)", () => {
    const filter = {
      planningArea: new Set(["BEDOK"]),
      agency: new Set(["MSF"]),
    };
    // both match
    expect(
      matchesSchemeFilters(
        scheme({ planningArea: ["BEDOK"], agency: "MSF" }),
        filter,
      ),
    ).toBe(true);
    // location matches but agency doesn't
    expect(
      matchesSchemeFilters(
        scheme({ planningArea: ["BEDOK"], agency: "AIC" }),
        filter,
      ),
    ).toBe(false);
    // agency matches but location doesn't
    expect(
      matchesSchemeFilters(
        scheme({ planningArea: ["TAMPINES"], agency: "MSF" }),
        filter,
      ),
    ).toBe(false);
  });

  it("matches if the scheme satisfies ANY selected value within a dimension (OR)", () => {
    const filter = { planningArea: new Set(["BEDOK", "YISHUN"]) };
    // scheme is only in YISHUN — still matches because YISHUN is selected
    expect(
      matchesSchemeFilters(scheme({ planningArea: ["YISHUN"] }), filter),
    ).toBe(true);
    // scheme in neither selected area
    expect(
      matchesSchemeFilters(scheme({ planningArea: ["TAMPINES"] }), filter),
    ).toBe(false);
  });
});
