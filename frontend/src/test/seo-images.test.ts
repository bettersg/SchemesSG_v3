import { existsSync, readFileSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";

/**
 * Guards the metadata images in src/app/. icon.png and apple-icon.png are
 * build artifacts of `npm run seo:images`; opengraph-image.png is a committed
 * designer asset the script only validates. Nothing in the build checks any of
 * them, so each assertion here pins a property that would otherwise fail
 * silently.
 */

const appDir = join(process.cwd(), "src", "app");

/**
 * Reads width/height from a PNG's IHDR chunk. Avoids importing sharp into the
 * jsdom test environment for what is eight bytes of header.
 */
const pngSize = (path: string) => {
  const buf = readFileSync(path);
  const signature = buf.subarray(0, 8).toString("hex");
  expect(signature, `${path} is not a PNG`).toBe("89504e470d0a1a0a");
  return { width: buf.readUInt32BE(16), height: buf.readUInt32BE(20) };
};

describe("SEO metadata images", () => {
  it("keeps the share image at 1200x630", () => {
    // 1.91:1. Facebook and LinkedIn render this in full; X trims ~15px top and
    // bottom to reach 2:1; WhatsApp centre-crops to roughly a square.
    expect(pngSize(join(appDir, "opengraph-image.png"))).toEqual({
      width: 1200,
      height: 630,
    });
  });

  it.each([
    ["icon.png", 512],
    ["apple-icon.png", 180],
  ])("keeps %s square at %ipx", (file, size) => {
    // Both favicon slots are square. A non-square source is squashed by
    // Google's square slot rather than letterboxed.
    expect(pngSize(join(appDir, file))).toEqual({
      width: size,
      height: size,
    });
  });

  it("does not ship a twitter-image.png", () => {
    // lib/seo.ts sets twitter.images to the OG URL, which overrides Next's
    // twitter-image convention, so re-adding the file needs that removed first.
    expect(existsSync(join(appDir, "twitter-image.png"))).toBe(false);
  });
});
