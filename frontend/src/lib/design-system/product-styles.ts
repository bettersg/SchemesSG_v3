import { cn } from "@/lib/utils";

export const productPageShell =
  "h-full w-full overflow-y-auto bg-(--schemes-bg)";

export const productPageContent = "mx-auto w-full max-w-5xl px-4 py-8 sm:px-8";

export const productFormContent = "mx-auto w-full max-w-2xl px-4 py-8 sm:px-8";

export const productHeading =
  "text-2xl font-semibold text-(--schemes-blue-900) sm:text-3xl";

export const productSubheading =
  "text-sm font-medium text-(--schemes-muted)";

export const productCard =
  "rounded-xl border border-(--schemes-border) bg-(--schemes-surface)";

export const productCardPadded = cn(productCard, "p-6");

export const productButtonBase =
  "inline-flex items-center justify-center gap-2 rounded-lg text-sm font-semibold transition-[background-color,border-color,color,opacity] disabled:cursor-not-allowed disabled:opacity-45";

export const productButtonPrimary = cn(
  productButtonBase,
  "bg-(--schemes-amber-400) text-(--schemes-ink) hover:bg-(--schemes-amber-100)",
);

export const productButtonSecondary = cn(
  productButtonBase,
  "border border-(--schemes-blue-100) bg-white text-(--schemes-blue-600) hover:bg-(--schemes-blue-50) hover:text-(--schemes-blue-900)",
);

export const productButtonTertiary = cn(
  productButtonBase,
  "border border-(--schemes-border-neutral) bg-white text-(--schemes-ink-soft) hover:bg-(--schemes-blue-50) hover:text-(--schemes-blue-900)",
);

export const productButtonSm = "h-9 px-3 py-1.5 text-xs";
export const productButtonMd = "px-4 py-2";
export const productButtonLg = "px-6 py-3";
export const productIconButton = "h-8 w-8 rounded-lg p-0";

export const productActionChip = cn(
  productButtonBase,
  "rounded-full border border-(--schemes-blue-100) bg-(--schemes-blue-50) px-3 py-1.5 text-xs text-(--schemes-blue-800) hover:bg-white",
);

export const productSelectTrigger =
  "rounded-lg border border-(--schemes-border) bg-white font-semibold text-(--schemes-blue-900) shadow-none hover:bg-(--schemes-blue-50)";

export const productSelectPopover = "bg-white text-(--schemes-ink)";

export const productSegmentedList =
  "rounded-xl border border-(--schemes-border) bg-(--schemes-blue-50) p-1";

export const productSegmentedTab =
  "relative z-10 rounded-lg px-4 py-2 text-sm font-semibold !text-(--schemes-blue-900)";

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
