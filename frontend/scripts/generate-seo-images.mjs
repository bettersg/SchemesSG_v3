import { existsSync, readFileSync } from "fs";
import { join, dirname } from "path";
import { fileURLToPath } from "url";
import sharp from "sharp";

const __dirname = dirname(fileURLToPath(import.meta.url));
const projectRoot = join(__dirname, "..");

// --schemes-surface from the design system.
const BACKGROUND = "#ffffff";

const logoSvgPath = join(projectRoot, "public", "logo.svg");
const logoSvg = readFileSync(logoSvgPath);

/**
 * logo.svg has a 64.04x150 viewBox and no width or height, so sharp rasterises
 * it at 64x150. Rasterise at high density, then scale to a target height, so
 * the mark fills its canvas rather than sitting at native size.
 */
async function scaledLogo(targetHeight) {
  return sharp(logoSvg, { density: 600 })
    .resize({ height: targetHeight, fit: "contain" })
    .png()
    .toBuffer();
}

async function generateIcon() {
  const outputPath = join(projectRoot, "src", "app", "icon.png");

  // Opaque, not transparent: the mark's colours are mid-tone and would lose
  // contrast against a dark browser tab bar.
  await sharp({
    create: {
      width: 512,
      height: 512,
      channels: 3,
      background: BACKGROUND,
    },
  })
    .composite([
      {
        input: await scaledLogo(420),
        blend: "over",
      },
    ])
    .png()
    .toFile(outputPath);

  const metadata = await sharp(outputPath).metadata();
  console.log(`Generated icon.png: ${metadata.width}x${metadata.height}`);
}

async function generateAppleIcon() {
  const outputPath = join(projectRoot, "src", "app", "apple-icon.png");

  // 180x180, must be opaque: iOS renders transparency as black.
  await sharp({
    create: {
      width: 180,
      height: 180,
      channels: 3,
      background: BACKGROUND,
    },
  })
    .composite([
      {
        input: await scaledLogo(148),
        blend: "over",
      },
    ])
    .png()
    .toFile(outputPath);

  const metadata = await sharp(outputPath).metadata();
  console.log(`Generated apple-icon.png: ${metadata.width}x${metadata.height}`);
}

/**
 * Validates the designer-authored share image, which is committed directly to
 * src/app/. This script only checks it: regenerating it from logo.svg would
 * replace a wordmark lockup with a bare mark.
 *
 * No twitter-image.png either: lib/seo.ts points twitter.images at the OG URL,
 * so Next's twitter-image convention is overridden and the file is never used.
 */
async function checkShareImage() {
  const name = "opengraph-image.png";
  const path = join(projectRoot, "src", "app", name);

  if (!existsSync(path)) {
    throw new Error(
      `Share image missing: ${path}\n` +
        "Restore the designer asset from version control. Not regenerating " +
        "from logo.svg — that would replace a wordmark lockup with a tiny " +
        "bare logo.",
    );
  }

  const meta = await sharp(path).metadata();
  if (meta.width !== 1200 || meta.height !== 630) {
    throw new Error(
      `Share image must be 1200x630, got ${meta.width}x${meta.height}. ` +
        "Facebook and LinkedIn expect 1.91:1; X crops to 2:1.",
    );
  }
  if (meta.hasAlpha) {
    throw new Error(
      "Share image must be fully opaque — transparency composites " +
        "unpredictably across social platforms.",
    );
  }

  console.log(`Checked ${name}: ${meta.width}x${meta.height} (designer asset)`);
}

async function main() {
  console.log("Preparing SEO metadata images...");
  console.log(`Icon background: ${BACKGROUND}`);

  // Icons are generated from logo.svg: mark only, no wordmark, since text is
  // illegible at the 16px a favicon actually renders at.
  await generateIcon();
  await generateAppleIcon();

  await checkShareImage();

  console.log("\nDone.");
}

main().catch((err) => {
  console.error("Error generating images:", err);
  process.exit(1);
});
