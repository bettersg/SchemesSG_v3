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
  if (!imageError && image) {
    return (
      <Image
        className={clsx(
          size == "md" && "h-10 w-10",
          size == "header" && "h-16 w-16",
          size == "lg" && "h-24 w-24",
          "object-contain",
        )}
        src={image}
        alt={`${agency} image`}
        width={size === "lg" ? 96 : size === "header" ? 64 : 40}
        height={size === "lg" ? 96 : size === "header" ? 64 : 40}
        unoptimized
        onError={() => setImageError(true)}
      />
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
        size == "md" && "h-10 w-10",
        size == "header" && "h-16 w-16",
        size == "lg" && "h-24 w-24",
        "flex shrink-0 items-center justify-center rounded-lg border border-(--schemes-blue-100) text-sm font-semibold text-(--schemes-blue-600)",
      )}
    >
      {initials}
    </div>
  );
}
