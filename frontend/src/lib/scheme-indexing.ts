import type { Scheme } from "@/types/types";

/**
 * Whether a scheme has enough content to be worth indexing. Stricter than the
 * rendering threshold in SchemeDetail, which also counts contact details and
 * so admits pages whose only content is a phone number.
 */
export function hasIndexableContent(scheme: Scheme): boolean {
  return Boolean(
    scheme.description || scheme.eligibilityText || scheme.howToApply,
  );
}
