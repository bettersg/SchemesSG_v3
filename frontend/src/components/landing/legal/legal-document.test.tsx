import { render, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import LegalDocument from "./legal-document";

describe("LegalDocument", () => {
  const sampleMarkdown = `
## Privacy Overview

We collect limited data to provide the Service.

### Data Collection

You do not need to provide your name or contact details.

- Search terms
- Chat messages
- Technical data

For questions, contact [info@better.sg](mailto:info@better.sg).

Visit our [Terms of Service](/terms).
`;

  it("renders the heading and effective date", () => {
    render(
      <LegalDocument
        heading="Privacy Policy"
        effectiveDate="20 September 2026"
        markdown={sampleMarkdown}
      />,
    );

    expect(
      screen.getByRole("heading", { level: 1, name: "Privacy Policy" }),
    ).toBeVisible();
    expect(screen.getByText(/Effective date: 20 September 2026/)).toBeVisible();
  });

  it("gives each section an anchor the contents sidebar links to", () => {
    render(
      <LegalDocument heading="Privacy Policy" markdown={sampleMarkdown} />,
    );

    const h2 = screen.getByRole("heading", {
      level: 2,
      name: "Privacy Overview",
    });
    expect(h2.closest("section")).toHaveAttribute("id", "privacy-overview");
    const contents = screen.getByRole("navigation", { name: "Contents" });
    expect(
      within(contents).getByRole("link", { name: "Privacy Overview" }),
    ).toHaveAttribute("href", "#privacy-overview");

    const h3 = screen.getByRole("heading", {
      level: 3,
      name: "Data Collection",
    });
    expect(h3).toHaveAttribute("id", "data-collection");
  });

  it("keeps text before the first section as a preamble, outside the contents", () => {
    render(
      <LegalDocument
        heading="Terms of Service"
        markdown={`**Urgent Help**\n\nCall [995](tel:995).\n\n## 1. About\n\nBody.`}
      />,
    );

    expect(screen.getByRole("link", { name: "995" })).toHaveAttribute(
      "href",
      "tel:995",
    );
    const contents = screen.getByRole("navigation", { name: "Contents" });
    expect(within(contents).getAllByRole("link")).toHaveLength(1);
    expect(
      screen
        .getByRole("heading", { level: 2, name: "1. About" })
        .closest("section"),
    ).toHaveAttribute("id", "1-about");
  });

  it("renders bullet lists", () => {
    render(
      <LegalDocument heading="Privacy Policy" markdown={sampleMarkdown} />,
    );

    expect(screen.getByText("Search terms")).toBeVisible();
    expect(screen.getByText("Chat messages")).toBeVisible();
    expect(screen.getByText("Technical data")).toBeVisible();
  });

  it("renders internal links as Next.js Links", () => {
    render(
      <LegalDocument heading="Privacy Policy" markdown={sampleMarkdown} />,
    );

    const termsLink = screen.getByRole("link", { name: "Terms of Service" });
    expect(termsLink).toHaveAttribute("href", "/terms");
  });

  it("renders mailto links without target blank", () => {
    render(
      <LegalDocument heading="Privacy Policy" markdown={sampleMarkdown} />,
    );

    const emailLink = screen.getByRole("link", { name: "info@better.sg" });
    expect(emailLink).toHaveAttribute("href", "mailto:info@better.sg");
    expect(emailLink).not.toHaveAttribute("target");
    expect(emailLink).not.toHaveAttribute("rel");
  });

  it("renders external links with target blank and rel", () => {
    const markdownWithExternal = `
Visit [Google](https://google.com) for more information.
`;
    render(
      <LegalDocument
        heading="Privacy Policy"
        markdown={markdownWithExternal}
      />,
    );

    const externalLink = screen.getByRole("link", { name: "Google" });
    expect(externalLink).toHaveAttribute("href", "https://google.com");
    expect(externalLink).toHaveAttribute("target", "_blank");
    expect(externalLink).toHaveAttribute("rel", "noopener noreferrer");
  });

  it("does not render the placeholder notice", () => {
    render(
      <LegalDocument heading="Privacy Policy" markdown={sampleMarkdown} />,
    );

    expect(
      screen.queryByText(/This policy is being written/),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByText(/What holds in the meantime/),
    ).not.toBeInTheDocument();
  });
});
