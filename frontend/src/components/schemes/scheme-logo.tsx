import clsx from "clsx";
import { useState } from "react";

export default function SchemeLogo({
  agency,
  image,
  size = "md",
}: {
  agency: string;
  image?: string;
  size?: "md" | "lg";
}) {
  const [imageError, setImageError] = useState(
    image === undefined || image === "",
  );
  if (!imageError) {
    return (
      <img
        className={clsx(size == "md" && "h-8 w-8", size == "lg" && "h-18 w-18")}
        src={image}
        alt={`${agency} image`}
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
        size == "md" && "h-8 w-8",
        size == "lg" && "h-18 w-18",
        "flex shrink-0 items-center justify-center rounded-lg border border-(--schemes-blue-100) bg-(--schemes-blue-50) text-[10px] font-semibold text-(--schemes-blue-600)",
      )}
    >
      {initials}
    </div>
  );
}
