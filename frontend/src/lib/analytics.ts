import { logEvent, type Analytics } from "firebase/analytics";

/**
 * A scheme in GA4's ecommerce item shape. Item-scoped fields sit on a separate
 * quota from custom dimensions, and GA4 buckets anything past 500 distinct
 * values into "(other)", so with 600+ schemes a scheme_id dimension would be
 * unusable.
 */
export interface SchemeItem {
  item_id: string;
  item_name: string;
  item_category?: string;
}

/**
 * Every tracked event, mapped from name to parameter shape. Must stay a map,
 * not a union: a union signature lets any event name accept any other event's
 * params. Names follow GA4's recommended ones where they exist, and GA4 cannot
 * rename an event after collection.
 */
export interface EventMap {
  /** Custom: documentation section scrolled into view */
  docs_section_view: { section_id: string };
  /** Custom: code sample copied from the developer docs */
  code_sample_copy: { operation: string; code_language: string };
  /** GA4 recommended: "Request access" clicked on /developers */
  generate_lead: { method: "developers_page" };
  /** GA4 recommended: FAQ link into the docs */
  select_content: { content_type: "faq_link"; item_id: string };
  /** GA4 recommended: search run. Deliberately omits search_term (no PII). */
  search: { result_count: number; has_results: boolean };
  /** GA4 recommended: scheme opened from a list */
  select_item: { item_list_id: string; index: number; items: SchemeItem[] };
  /** GA4 recommended: scheme detail viewed */
  view_item: { items: SchemeItem[] };
  /** Custom: catalog filter applied */
  filter_apply: { filter_name: string };
  /**
   * Custom: chat message sent. Never carries message text. `send_trigger`
   * separates a real submit from ChatPage's automatic re-fire on mount, which
   * would otherwise inflate send counts with no way to filter them apart.
   */
  chat_message_send: {
    turn_index: number;
    send_trigger: "user_submit" | "auto_resume";
  };
  /**
   * Custom: agency phone or email tapped on a scheme page. Enhanced Measurement's
   * outbound click only fires for http(s), so tel: and mailto: are invisible to
   * it; the https Maps link is excluded because it is already counted. Read
   * split by viewport: a phone tap on desktop means little.
   */
  agency_contact_click: { contact_method: "phone" | "email" };
  /**
   * Custom: scheme page shared. Enhanced Measurement only reports link clicks,
   * and sharing is a navigator.share or clipboard call. "dismissed" is the
   * native sheet being cancelled, which otherwise leaves no trace.
   */
  scheme_shared: {
    share_outcome: "web_share" | "dismissed" | "clipboard" | "failed";
  };
  /** Custom: answer stream completed, with its latency. */
  chat_answer_shown: {
    turn_index: number;
    schemes_found: number;
    ms_to_first_token: number;
    ms_to_done: number;
  };
  /**
   * Custom: user pressed Stop. Distinct from a failure even though both run the
   * same rollback. ms_since_send with had_streamed_text separates giving up
   * from changing your mind.
   */
  chat_turn_aborted: { ms_since_send: number; had_streamed_text: boolean };
  /** Custom: the request or stream failed. Carries no error message text. */
  chat_turn_failed: {
    failure_stage: "request" | "stream" | "unknown";
    ms_since_send: number;
    had_streamed_text: boolean;
  };
  /**
   * Custom: user left mid-stream, which no completion event would record. On
   * visibilitychange to hidden rather than pagehide, because logEvent has no
   * beacon transport. Overcounts a tab switch that later returns.
   */
  chat_turn_abandoned: {
    last_milestone: "sent" | "status" | "token" | "results";
    ms_since_send: number;
  };
}

export type EventName = keyof EventMap;

/**
 * Event names at runtime, so tests can assert naming rules over all of them.
 * The exhaustiveness check below fails the build if this falls behind EventMap.
 */
export const EVENT_NAMES = [
  "docs_section_view",
  "code_sample_copy",
  "generate_lead",
  "select_content",
  "search",
  "select_item",
  "view_item",
  "filter_apply",
  "chat_message_send",
  "agency_contact_click",
  "scheme_shared",
  "chat_answer_shown",
  "chat_turn_aborted",
  "chat_turn_failed",
  "chat_turn_abandoned",
] as const satisfies readonly EventName[];

/**
 * Parameter keys at runtime, for the PII denylist test. The type forces every
 * event to appear and every key listed to be a real parameter of that event.
 */
export const EVENT_PARAM_KEYS: {
  readonly [K in EventName]: readonly (keyof EventMap[K] & string)[];
} = {
  docs_section_view: ["section_id"],
  code_sample_copy: ["operation", "code_language"],
  generate_lead: ["method"],
  select_content: ["content_type", "item_id"],
  search: ["result_count", "has_results"],
  select_item: ["item_list_id", "index", "items"],
  view_item: ["items"],
  filter_apply: ["filter_name"],
  chat_message_send: ["turn_index", "send_trigger"],
  agency_contact_click: ["contact_method"],
  scheme_shared: ["share_outcome"],
  chat_answer_shown: [
    "turn_index",
    "schemes_found",
    "ms_to_first_token",
    "ms_to_done",
  ],
  chat_turn_aborted: ["ms_since_send", "had_streamed_text"],
  chat_turn_failed: ["failure_stage", "ms_since_send", "had_streamed_text"],
  chat_turn_abandoned: ["last_milestone", "ms_since_send"],
};

// Fails the build if EventMap gains a key missing from EVENT_NAMES.
type MissingFromEventNames = Exclude<EventName, (typeof EVENT_NAMES)[number]>;
const _eventNamesAreExhaustive: MissingFromEventNames extends never ? true : never =
  true;
void _eventNamesAreExhaustive;

/**
 * Records an analytics event. Never throws and never blocks render: no-ops
 * silently server-side, when the measurement ID is absent, when isSupported()
 * is false, and when an extension blocks the SDK. Callers can therefore call it
 * unconditionally.
 *
 * Never pass raw search queries, chat message text, emails, phone numbers or
 * names. Parameters carry counts, durations, enums and booleans only.
 */
export function track<K extends EventName>(event: K, params: EventMap[K]): void {
  try {
    if (typeof window === "undefined") {
      return;
    }

    const globalForAnalytics = globalThis as typeof globalThis & {
      __schemesSgAnalytics?: Analytics;
    };

    if (!globalForAnalytics.__schemesSgAnalytics) {
      return;
    }

    // Asserted: logEvent's overloads do not narrow against a mapped type.
    logEvent(
      globalForAnalytics.__schemesSgAnalytics,
      event as string,
      params as Record<string, unknown>,
    );
  } catch {
    // Analytics must never surface to the user.
  }
}
