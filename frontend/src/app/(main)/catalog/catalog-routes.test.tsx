import { describe, expect, it } from "vitest";
import { generateStaticParams } from "./[category]/page";

describe("catalog routes", () => {
  it("leaves the unfiltered view out of the category routes", () => {
    const slugs = generateStaticParams().map(({ category }) => category);

    expect(slugs).not.toContain("all");
    expect(slugs).toContain("financial-assistance");
  });
});
