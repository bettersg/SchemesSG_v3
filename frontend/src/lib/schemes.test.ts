import { describe, expect, it } from "vitest";
import type { RawScheme } from "@/types/types";
import { mapToFullScheme, mapToScheme } from "./scheme-mappers";

describe("scheme mapping", () => {
  it("maps legacy search fields into the public scheme shape", () => {
    const scheme = mapToScheme({
      Scheme: "ComCare Assistance",
      Agency: "MSF",
      "Scheme Type": ["Financial Assistance"],
      "Who's it for": ["Lower-income households"],
      "What it gives": ["Temporary financial support"],
      Description: "Help with essential living expenses.",
      Link: "https://example.test/comcare",
      scheme_id: "comcare",
    });

    expect(scheme).toMatchObject({
      schemeId: "comcare",
      schemeName: "ComCare Assistance",
      agency: "MSF",
      schemeType: ["Financial Assistance"],
      targetAudience: ["Lower-income households"],
      benefits: ["Temporary financial support"],
      description: "Help with essential living expenses.",
      link: "https://example.test/comcare",
    });
  });

  it("cleans branch contacts before exposing a full scheme", () => {
    const raw: RawScheme = {
      scheme_id: "branch-support",
      scheme: "Branch Support",
      planning_area: ["Bedok", "No Location"],
      phone: ["6123 4567, 6123 4568", "6999 0000"],
      email: [
        "help@example.org, This email address is being protected from spambots",
        "not-an-email",
      ],
      address: ["1 Bedok Road", "2 Central Road"],
    };

    expect(mapToFullScheme(raw).contact).toEqual([
      {
        planningArea: "Bedok",
        phones: ["6123 4567", "6123 4568"],
        emails: ["help@example.org"],
        address: "1 Bedok Road",
      },
      {
        planningArea: undefined,
        phones: ["6999 0000"],
        emails: undefined,
        address: "2 Central Road",
      },
    ]);
  });

  it("drops placeholder and duplicate planning-area-only contacts", () => {
    const raw: RawScheme = {
      scheme_id: "area-support",
      scheme: "Area Support",
      planning_area: ["No Location", "Bedok", "Bedok"],
    };

    expect(mapToFullScheme(raw).contact).toEqual([
      {
        planningArea: "Bedok",
        phones: undefined,
        emails: undefined,
        address: undefined,
      },
    ]);
  });
});
