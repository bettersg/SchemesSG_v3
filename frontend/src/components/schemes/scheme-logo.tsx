import clsx from "clsx";
import Image from "next/image";
import { useState } from "react";

// px is passed to next/image so the raster is requested at the size it renders.
const SIZES = {
  sm: { tile: "h-10 w-10 p-1", px: 40, initials: "text-sm" },
  md: { tile: "h-16 w-16 p-1.5", px: 64, initials: "text-xl" },
  lg: { tile: "h-20 w-20 p-2", px: 80, initials: "text-2xl" },
  xl: { tile: "h-24 w-24 p-2.5", px: 96, initials: "text-3xl" },
} as const;

export default function SchemeLogo({
  agency,
  image,
  size = "md",
}: {
  agency: string;
  image?: string;
  size?: keyof typeof SIZES;
}) {
  const [imageError, setImageError] = useState(
    image === undefined || image === "",
  );

  // Every logo sits in the same calm white tile (border, radius, inner padding)
  // so wildly different source logos — full-colour lockups, tiny marks, mono-
  // grams — read as a uniform, curated row instead of a ransom note.
  const { tile: tileSize, px, initials: initialsSize } = SIZES[size];
  const tile = clsx(
    "flex shrink-0 items-center justify-center overflow-hidden rounded-lg border border-(--schemes-border) bg-white",
    tileSize,
  );

  if (!imageError && image) {
    return (
      <div className={tile}>
        <Image
          className="h-full w-full object-contain"
          src={image}
          alt={`${agency} image`}
          width={px}
          height={px}
          unoptimized
          onError={() => setImageError(true)}
        />
      </div>
    );
  }
  const initials = agency
    .split(" ")
    .slice(0, 2)
    .map((w) => w[0])
    .join("")
    .toUpperCase();
  return (
    <div
      className={clsx(
        tile,
        initialsSize,
        "font-semibold text-(--schemes-blue-600)",
      )}
    >
      {initials}
    </div>
  );
}
