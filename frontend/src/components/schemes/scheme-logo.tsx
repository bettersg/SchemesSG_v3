import clsx from "clsx";
import Image from "next/image";
import { useState } from "react";

export default function SchemeLogo({
  agency,
  image,
  size = "md",
}: {
  agency: string;
  image?: string;
  size?: "md" | "header" | "lg";
}) {
  const [imageError, setImageError] = useState(
    image === undefined || image === "",
  );

  // Every logo sits in the same calm white tile (border, radius, inner padding)
  // so wildly different source logos — full-colour lockups, tiny marks, mono-
  // grams — read as a uniform, curated row instead of a ransom note.
  const tile = clsx(
    "flex shrink-0 items-center justify-center overflow-hidden rounded-lg border border-(--schemes-border) bg-white",
    size == "md" && "h-10 w-10 p-1",
    size == "header" && "h-16 w-16 p-1.5",
    size == "lg" && "h-24 w-24 p-2",
  );

  if (!imageError && image) {
    return (
      <div className={tile}>
        <Image
          className="h-full w-full object-contain"
          src={image}
          alt={`${agency} image`}
          width={size === "lg" ? 96 : size === "header" ? 64 : 40}
          height={size === "lg" ? 96 : size === "header" ? 64 : 40}
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
        "text-sm font-semibold text-(--schemes-blue-600)",
      )}
    >
      {initials}
    </div>
  );
}
