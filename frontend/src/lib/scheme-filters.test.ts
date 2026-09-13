import { describe, expect, it } from "vitest";
import { makeScheme } from "@/test/fixtures/scheme";
import { filterSchemes } from "./scheme-filters";

describe("filterSchemes", () => {
  it("keeps schemes matching both a selected location and agency", () => {
    const matching = makeScheme({
      schemeId: "matching",
      agency: "Agency A",
      planningArea: ["Bedok", "Tampines"],
    });
    const wrongAgency = makeScheme({
      schemeId: "wrong-agency",
      agency: "Agency B",
      planningArea: "Tampines",
    });
    const wrongLocation = makeScheme({
      schemeId: "wrong-location",
      agency: "Agency A",
      planningArea: "Jurong East",
    });

    expect(
      filterSchemes([matching, wrongAgency, wrongLocation], {
        planningArea: new Set(["Tampines"]),
        agency: new Set(["Agency A"]),
      }),
    ).toEqual([matching]);
  });

  it("returns the complete list when no filters are selected", () => {
    const schemes = [
      makeScheme({ schemeId: "first" }),
      makeScheme({ schemeId: "second" }),
    ];

    expect(filterSchemes(schemes, {})).toEqual(schemes);
  });
});
