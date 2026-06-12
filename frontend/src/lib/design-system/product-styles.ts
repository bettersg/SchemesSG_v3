import { cn } from "@/lib/utils";

export const productPageShell =
  "h-full w-full overflow-y-auto bg-(--schemes-bg)";

export const productPageContent = "mx-auto w-full max-w-5xl px-4 py-8 sm:px-8";

export const productFormContent = "mx-auto w-full max-w-2xl px-4 py-8 sm:px-8";

export const productHeading =
  "text-2xl font-semibold text-(--schemes-blue-900) sm:text-3xl";

export const productHeadingHero =
  "font-(--font-head) text-3xl font-semibold leading-[1.1] tracking-tight text-(--schemes-blue-900) sm:text-4xl";

export const productSubheading = "text-sm font-medium text-(--schemes-muted)";

export const productCard =
  "rounded-lg border border-(--schemes-border) bg-(--schemes-surface)";

export const productCardPadded = cn(productCard, "p-6");

export const productCardHeading =
  "mb-4 text-base font-semibold text-(--schemes-blue-900)";

export const productCardHeadingLg =
  "mb-4 text-lg font-semibold text-(--schemes-blue-900)";

const productButtonBase =
  "inline-flex items-center justify-center gap-2 rounded-lg text-sm font-semibold transition-[background-color,border-color,color,opacity] disabled:cursor-not-allowed disabled:opacity-45";

export const productBlueOutlineSurface =
  "border-(--schemes-blue-100) bg-white text-(--schemes-blue-600)";

// Primary action. Matches the /about landing CTA (amber fill, dark ink,
// darken-on-hover). Blue is reserved for structural/secondary use.
export const productButtonSolidAmber = cn(
  productButtonBase,
  "bg-(--schemes-amber-400) text-(--schemes-ink) hover:bg-(--schemes-amber-500)",
);

export const productButtonSolidBlue = cn(
  productButtonBase,
  "bg-(--schemes-blue-600) text-white hover:bg-(--schemes-blue-800)",
);

export const productButtonOutlineBlue = cn(
  productButtonBase,
  "border",
  productBlueOutlineSurface,
  "hover:bg-(--schemes-blue-50) hover:text-(--schemes-blue-900)",
);

export const productButtonOutlineNeutral = cn(
  productButtonBase,
  "border border-(--schemes-border-neutral) bg-white text-(--schemes-ink-soft) hover:bg-(--schemes-blue-50) hover:text-(--schemes-blue-900)",
);

// Quiet toolbar control: thin neutral border, transparent fill, muted ink,
// subtle blue-tint on hover. For utility actions (filter, new chat) that should
// recede beneath the content, not compete as filled pills.
export const productButtonGhost = cn(
  productButtonBase,
  "border border-(--schemes-border-neutral) bg-transparent text-(--schemes-muted) hover:border-(--schemes-blue-100) hover:bg-(--schemes-blue-50) hover:text-(--schemes-blue-600)",
);

export const productButtonCompact = "h-11 min-h-11 px-3 py-2 text-xs";
export const productButtonDefault = "min-h-11 px-4 py-2.5";
export const productButtonProminent = "min-h-12 px-6 py-3";

export const productSegmentedList =
  "rounded-xl border border-(--schemes-border) bg-(--schemes-blue-50) p-1";

export const productSegmentedTab =
  "relative z-10 rounded-lg text-sm font-semibold !text-(--schemes-blue-900)";

export const productSegmentedIndicator = "rounded-lg bg-white shadow-sm";

export const productInputText =
  "text-(--schemes-ink) placeholder:text-(--schemes-muted)";

export const productFormLabel =
  "text-xs font-semibold text-(--schemes-blue-900)";

export const productInputSurface =
  "rounded-lg border border-(--schemes-blue-100) bg-white text-(--schemes-ink) shadow-none transition-[background-color,border-color,box-shadow] placeholder:text-(--schemes-muted) focus-visible:border-(--schemes-blue-400) focus-visible:ring-2 focus-visible:ring-(--schemes-blue-100)";

export const productFormInfoMessage =
  "rounded-lg border border-(--schemes-status-info-border) bg-(--schemes-status-info-bg) p-4 text-sm font-medium text-(--schemes-status-info-text)";

export const productFormAlertMessage =
  "rounded-lg border border-(--schemes-status-alert-border) bg-(--schemes-status-alert-bg) p-4 text-sm font-medium text-(--schemes-status-alert-text)";
