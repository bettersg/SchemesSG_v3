import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { makeScheme } from "@/test/fixtures/scheme";
import SchemeDetail from "./scheme-detail";

const originalClipboard = Object.getOwnPropertyDescriptor(
  navigator,
  "clipboard",
);

afterEach(() => {
  if (originalClipboard) {
    Object.defineProperty(navigator, "clipboard", originalClipboard);
  } else {
    Reflect.deleteProperty(navigator, "clipboard");
  }
  window.history.replaceState(null, "", "/");
});

describe("SchemeDetail", () => {
  it("shows actionable scheme content and supports section and share navigation", async () => {
    const writeText = vi.fn().mockResolvedValue(undefined);
    Object.defineProperty(navigator, "clipboard", {
      configurable: true,
      value: { writeText },
    });
    window.history.replaceState(null, "", "/schemes/family-support");
    const scheme = makeScheme({
      schemeId: "family-support",
      schemeName: "Family Support Grant",
      agency: "Community Agency",
      summary: "Help for families who need short-term support.",
      description:
        "Support includes:\n\n• Cash assistance\n\n• Case guidance\n\nApply when ready.",
      schemeType: ["Other", "Financial Assistance"],
      targetAudience: ["Families with children"],
      benefits: ["Monthly support"],
      eligibilityText: "Household income is assessed.",
      howToApply: "Apply through the agency portal.",
      serviceArea: "Singapore",
      contact: [
        {
          planningArea: "Bedok",
          phones: ["6123 4567"],
          emails: ["help@example.org"],
          address: "1 Support Street",
        },
      ],
      link: "https://example.test/family-support",
    });

    render(<SchemeDetail scheme={scheme} />);

    expect(
      screen.getByRole("heading", { name: "Family Support Grant", level: 1 }),
    ).toBeVisible();
    expect(
      screen.getByRole("heading", { name: "Who qualifies" }),
    ).toBeVisible();
    expect(screen.getByRole("heading", { name: "How to apply" })).toBeVisible();
    expect(
      screen.getByRole("heading", { name: "Agency details" }),
    ).toBeVisible();
    expect(screen.getByRole("list")).toHaveTextContent(
      "Cash assistance Case guidance",
    );
    expect(screen.getByRole("link", { name: "6123 4567" })).toHaveAttribute(
      "href",
      "tel:6123 4567",
    );
    expect(
      screen.getByRole("link", { name: "help@example.org" }),
    ).toHaveAttribute("href", "mailto:help@example.org");
    expect(
      screen.getAllByRole("link", { name: "Visit website" })[0],
    ).toHaveAttribute("href", "https://example.test/family-support");

    const agencyAnchor = screen.getByRole("link", {
      name: "Agency details",
    });
    const agencySection = document.getElementById("agency");
    expect(agencySection).not.toBeNull();
    if (agencySection) agencySection.scrollIntoView = vi.fn();
    fireEvent.click(agencyAnchor);
    expect(window.location.hash).toBe("#agency");

    fireEvent.click(screen.getAllByRole("button", { name: "Share scheme" })[0]);
    await waitFor(() =>
      expect(writeText).toHaveBeenCalledWith(window.location.href),
    );
    expect(
      screen.getAllByRole("button", { name: "Link copied" })[0],
    ).toBeVisible();

    expect(
      screen.getByRole("link", { name: "Suggest a correction" }),
    ).toHaveAttribute(
      "href",
      "/feedback?source=scheme&schemeId=family-support&scheme=Family+Support+Grant",
    );
    expect(
      screen.getByRole("link", { name: "Share general feedback" }),
    ).toHaveAttribute("href", "/feedback");
  });

  it("guides users to the agency when structured details are unavailable", () => {
    render(
      <SchemeDetail
        scheme={makeScheme({
          schemeId: "sparse",
          schemeName: "Sparse Scheme",
          link: "https://example.test/sparse",
        })}
      />,
    );

    expect(
      screen.getByText(/don.t have detailed information for this scheme yet/i),
    ).toBeVisible();
    expect(
      screen.getByRole("link", { name: "Visit the agency website →" }),
    ).toHaveAttribute("href", "https://example.test/sparse");
    expect(
      screen.queryByRole("navigation", { name: "On this page" }),
    ).not.toBeInTheDocument();
  });
});
