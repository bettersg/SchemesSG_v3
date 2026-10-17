import { describe, expect, it } from "vitest";
import { getSeoImageMetadata, SCHEMES_SG_OG_IMAGE_URL } from "./seo";

describe("getSeoImageMetadata", () => {
  it("includes dimensions for the shared OG image", () => {
    const metadata = getSeoImageMetadata(SCHEMES_SG_OG_IMAGE_URL);

    expect(metadata).toEqual({
      url: SCHEMES_SG_OG_IMAGE_URL,
      width: 1200,
      height: 630,
    });
  });

  it("omits dimensions for external agency images", () => {
    const externalUrl = "https://agency.gov.sg/logo.png";
    const metadata = getSeoImageMetadata(externalUrl);

    expect(metadata).toEqual({
      url: externalUrl,
    });
    expect(metadata).not.toHaveProperty("width");
    expect(metadata).not.toHaveProperty("height");
  });

  it("omits dimensions for another external URL", () => {
    const externalUrl = "https://example.com/image.jpg";
    const metadata = getSeoImageMetadata(externalUrl);

    expect(metadata).toEqual({
      url: externalUrl,
    });
  });
});
