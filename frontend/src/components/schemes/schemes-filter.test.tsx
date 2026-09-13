import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { useState } from "react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { filterSchemes } from "@/lib/scheme-filters";
import { makeScheme } from "@/test/fixtures/scheme";
import type { FilterObjType } from "@/types/types";
import SchemesFilter from "./schemes-filter";

const originalMatchMedia = Object.getOwnPropertyDescriptor(
  window,
  "matchMedia",
);

afterEach(() => {
  if (originalMatchMedia) {
    Object.defineProperty(window, "matchMedia", originalMatchMedia);
  } else {
    Reflect.deleteProperty(window, "matchMedia");
  }
});

const schemes = [
  makeScheme({
    schemeId: "bedok-support",
    schemeName: "Bedok Support",
    agency: "Agency A",
    planningArea: ["Bedok", "Tampines"],
  }),
  makeScheme({
    schemeId: "jurong-support",
    schemeName: "Jurong Support",
    agency: "Agency B",
    planningArea: "Jurong East",
  }),
];

function FilterHarness() {
  const [filter, setFilter] = useState<FilterObjType>({});
  const [locations, setLocations] = useState(new Set<string>());
  const [agencies, setAgencies] = useState(new Set<string>());
  const resetFilters = () => {
    setLocations(new Set());
    setAgencies(new Set());
    setFilter({});
  };
  const visibleSchemes = filterSchemes(schemes, filter);

  return (
    <>
      <SchemesFilter
        schemes={schemes}
        setFilterObj={setFilter}
        selectedLocations={locations}
        setSelectedLocations={setLocations}
        selectedAgencies={agencies}
        setSelectedAgencies={setAgencies}
        resetFilters={resetFilters}
      />
      <ul aria-label="Scheme results">
        {visibleSchemes.map((scheme) => (
          <li key={scheme.schemeId}>{scheme.schemeName}</li>
        ))}
      </ul>
    </>
  );
}

describe("SchemesFilter", () => {
  it("applies and clears live location and agency filters", async () => {
    Object.defineProperty(window, "matchMedia", {
      configurable: true,
      value: vi.fn(() => ({
        matches: true,
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
      })),
    });
    const user = userEvent.setup();
    render(<FilterHarness />);
    const results = () =>
      within(screen.getByRole("list", { name: "Scheme results" }));

    expect(results().getAllByRole("listitem")).toHaveLength(2);
    await user.click(
      screen.getByRole("button", { name: "Filter by Location" }),
    );
    await user.click(await screen.findByRole("button", { name: "Bedok" }));
    await user.click(screen.getAllByRole("button", { name: "Dismiss" })[0]);
    expect(results().getByText("Bedok Support")).toBeVisible();
    expect(results().queryByText("Jurong Support")).not.toBeInTheDocument();

    await user.click(
      screen.getByRole("button", { name: "Clear Location filter" }),
    );
    expect(results().getAllByRole("listitem")).toHaveLength(2);

    await user.click(screen.getByRole("button", { name: "Filter by Agency" }));
    await user.click(await screen.findByRole("button", { name: "Agency B" }));
    await user.click(screen.getAllByRole("button", { name: "Dismiss" })[0]);
    expect(results().getByText("Jurong Support")).toBeVisible();
    expect(results().queryByText("Bedok Support")).not.toBeInTheDocument();
  });
});
