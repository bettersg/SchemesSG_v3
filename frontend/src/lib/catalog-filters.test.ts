import { describe, expect, it } from "vitest";
import {
  formatPlanningArea,
  getCatalogFilterHref,
  getSelectedCategories,
  parseCatalogQuery,
  toggleValue,
} from "./catalog-filters";

describe("catalog filters", () => {
  it("keeps the first category on its static route and puts the rest in the query", () => {
    expect(getCatalogFilterHref([], [])).toBe("/catalog");
    expect(getCatalogFilterHref(["Financial Assistance"], [])).toBe(
      "/catalog/financial-assistance",
    );
    expect(
      getCatalogFilterHref(
        ["Financial Assistance", "Education"],
        ["BEDOK", "TOA PAYOH"],
      ),
    ).toBe(
      "/catalog/financial-assistance?category=Education&area=BEDOK&area=TOA+PAYOH",
    );
    expect(getCatalogFilterHref([], ["BEDOK"])).toBe("/catalog?area=BEDOK");
  });

  it("reads repeated query values, ignoring unknown categories and the route's own", () => {
    const params = new URLSearchParams(
      "category=education&category=Bogus&category=Financial%20Assistance&area=bedok&area=BEDOK",
    );

    expect(parseCatalogQuery(params, "Financial Assistance")).toEqual({
      categories: ["Education"],
      areas: ["BEDOK"],
    });
  });

  it("puts the route category first and treats All as no category", () => {
    expect(getSelectedCategories("Education", ["Housing & Food"])).toEqual([
      "Education",
      "Housing & Food",
    ]);
    expect(getSelectedCategories("All", ["Housing & Food"])).toEqual([
      "Housing & Food",
    ]);
  });

  it("toggles a value in or out of a selection", () => {
    expect(toggleValue(["A"], "B")).toEqual(["A", "B"]);
    expect(toggleValue(["A", "B"], "A")).toEqual(["B"]);
  });

  it("formats planning areas for display", () => {
    expect(formatPlanningArea("TOA PAYOH")).toBe("Toa Payoh");
    expect(formatPlanningArea("NORTH-EASTERN ISLANDS")).toBe(
      "North-Eastern Islands",
    );
  });
});
