import { describe, expect, it, vi, beforeEach } from "vitest";

const firebaseAnalyticsMocks = vi.hoisted(() => ({
  logEvent: vi.fn(),
  isSupported: vi.fn(async () => false),
}));

vi.mock("firebase/analytics", () => ({
  logEvent: firebaseAnalyticsMocks.logEvent,
  isSupported: firebaseAnalyticsMocks.isSupported,
}));

import {
  EVENT_NAMES,
  EVENT_PARAM_KEYS,
  flushPendingEvents,
  track,
  type SchemeItem,
} from "./analytics";

describe("analytics", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    const globalForAnalytics = globalThis as typeof globalThis & {
      __schemesSgAnalytics?: unknown;
    };
    delete globalForAnalytics.__schemesSgAnalytics;
  });

  describe("type safety", () => {
    it("accepts valid event with correct params", () => {
      track("docs_section_view", { section_id: "getting-started" });
      track("code_sample_copy", {
        operation: "create",
        code_language: "typescript",
      });
      track("generate_lead", { method: "developers_page" });
      track("select_content", { content_type: "faq_link", item_id: "faq-1" });
      track("search", { result_count: 5, has_results: true });
      track("select_item", {
        item_list_id: "category_education",
        index: 0,
        items: [{ item_id: "scheme-123", item_name: "Education Grant" }],
      });
      track("view_item", {
        items: [{ item_id: "scheme-123", item_name: "Education Grant" }],
      });
      track("filter_apply", { filter_name: "category" });
      track("chat_message_send", { turn_index: 1, send_trigger: "user_submit" });
      track("agency_contact_click", { contact_method: "phone" });
      track("scheme_shared", { share_outcome: "web_share" });
      track("chat_answer_shown", {
        turn_index: 1,
        schemes_found: 12,
        ms_to_first_token: 2400,
        ms_to_done: 18200,
      });
      track("chat_turn_aborted", {
        ms_since_send: 9400,
        had_streamed_text: false,
      });
      track("chat_turn_failed", {
        failure_stage: "stream",
        ms_since_send: 14000,
        had_streamed_text: true,
      });
      track("chat_turn_abandoned", {
        last_milestone: "status",
        ms_since_send: 48200,
      });

      expect(true).toBe(true);
    });

    it("rejects unknown event names at compile time", () => {
      // @ts-expect-error - unknown event name should fail type check
      track("unknown_event", { foo: "bar" });

      // @ts-expect-error - misspelled event name should fail type check
      track("view_items", { items: [] });
    });

    it("rejects incorrect params at compile time", () => {
      // @ts-expect-error - wrong param name
      track("docs_section_view", { section: "test" });

      // @ts-expect-error - wrong param type
      track("search", { result_count: "5", has_results: true });

      // @ts-expect-error - missing required param
      track("select_item", { item_list_id: "test", index: 0 });
    });

    it("rejects params belonging to a different event", () => {
      // These pin params to *this* event's shape, which a union would not.

      // @ts-expect-error - docs params on the search event
      track("search", { section_id: "oops" });

      // @ts-expect-error - chat params on the view_item event
      track("view_item", { turn_index: 3 });

      // @ts-expect-error - search params on the filter_apply event
      track("filter_apply", { result_count: 1, has_results: true });
    });
  });

  describe("track() never throws", () => {
    it("returns without throwing when analytics is not supported", async () => {
      firebaseAnalyticsMocks.isSupported.mockResolvedValue(false);

      expect(() => {
        track("docs_section_view", { section_id: "test" });
      }).not.toThrow();

      expect(firebaseAnalyticsMocks.logEvent).not.toHaveBeenCalled();
    });

    it("returns without throwing when analytics is not initialized", () => {
      expect(() => {
        track("search", { result_count: 0, has_results: false });
      }).not.toThrow();

      expect(firebaseAnalyticsMocks.logEvent).not.toHaveBeenCalled();
    });

    it("returns without throwing when logEvent throws", () => {
      const mockAnalytics = { name: "test-analytics" };
      (globalThis as typeof globalThis & { __schemesSgAnalytics: unknown }).__schemesSgAnalytics = mockAnalytics;

      firebaseAnalyticsMocks.logEvent.mockImplementation(() => {
        throw new Error("Analytics blocked by extension");
      });

      expect(() => {
        track("filter_apply", { filter_name: "eligibility" });
      }).not.toThrow();
    });
  });

  describe("events reported before initialisation", () => {
    const mockAnalytics = { name: "test-analytics" };
    type GlobalWithAnalytics = typeof globalThis & {
      __schemesSgAnalytics?: unknown;
    };
    const setInitialised = () => {
      (globalThis as GlobalWithAnalytics).__schemesSgAnalytics = mockAnalytics;
    };
    const setUninitialised = () => {
      delete (globalThis as GlobalWithAnalytics).__schemesSgAnalytics;
    };

    beforeEach(() => {
      // The queue is module state, so drain whatever earlier tests left in it.
      setInitialised();
      flushPendingEvents();
      setUninitialised();
      vi.clearAllMocks();
      // clearAllMocks keeps implementations, and an earlier test makes logEvent
      // throw.
      firebaseAnalyticsMocks.logEvent.mockImplementation(() => {});
    });

    it("delivers a mount-time event once analytics initialises", () => {
      const items: SchemeItem[] = [
        { item_id: "scheme-1", item_name: "Rental Support" },
      ];
      track("view_item", { items });
      expect(firebaseAnalyticsMocks.logEvent).not.toHaveBeenCalled();

      setInitialised();
      flushPendingEvents();

      expect(firebaseAnalyticsMocks.logEvent).toHaveBeenCalledTimes(1);
      expect(firebaseAnalyticsMocks.logEvent).toHaveBeenCalledWith(
        mockAnalytics,
        "view_item",
        { items },
      );
    });

    it("keeps order and does not replay on a second flush", () => {
      track("chat_message_send", {
        turn_index: 1,
        send_trigger: "auto_resume",
      });
      track("docs_section_view", { section_id: "getting-started" });

      setInitialised();
      flushPendingEvents();
      flushPendingEvents();

      expect(
        firebaseAnalyticsMocks.logEvent.mock.calls.map((call) => call[1]),
      ).toEqual(["chat_message_send", "docs_section_view"]);
    });

    it("stops queueing rather than growing without bound", () => {
      // A browser where isSupported() resolves false never flushes.
      for (let i = 0; i < 50; i += 1) {
        track("docs_section_view", { section_id: `section-${i}` });
      }

      setInitialised();
      flushPendingEvents();

      expect(firebaseAnalyticsMocks.logEvent).toHaveBeenCalledTimes(20);
    });
  });

  describe("event naming conventions", () => {
    // Derived, not copied: a hand-written list would fall behind EventMap.
    const eventNames: readonly string[] = EVENT_NAMES;

    it("covers every event in EventMap", () => {
      expect(eventNames).toHaveLength(Object.keys(EVENT_PARAM_KEYS).length);
    });

    it("all event names are snake_case", () => {
      const snakeCaseRegex = /^[a-z][a-z0-9_]*$/;
      for (const name of eventNames) {
        expect(name).toMatch(snakeCaseRegex);
      }
    });

    it("all event names are 40 characters or less", () => {
      for (const name of eventNames) {
        expect(name.length).toBeLessThanOrEqual(40);
      }
    });

    it("no event names use reserved prefixes", () => {
      const reservedPrefixes = ["google_", "firebase_", "ga_", "gtm_"];
      for (const name of eventNames) {
        for (const prefix of reservedPrefixes) {
          expect(name).not.toMatch(new RegExp(`^${prefix}`));
        }
      }
    });
  });

  describe("PII denylist enforcement", () => {
    const piiParamNames = [
      "query",
      "search_term",
      "text",
      "message",
      "label",
      "email",
      "name",
      "phone",
      "session_id",
      "user_id",
      "uid",
    ];

    // Derived, not copied: EVENT_PARAM_KEYS is typed against EventMap.
    const allParamNames = new Set<string>(
      Object.values(EVENT_PARAM_KEYS).flat(),
    );

    it("no param names match PII denylist", () => {
      for (const paramName of allParamNames) {
        expect(piiParamNames).not.toContain(paramName);
      }
    });

    it("item_name is allowed (not confused with 'name')", () => {
      // item_name is a legitimate GA4 field, so the denylist matches exact
      // keys rather than substrings.
      expect(allParamNames).not.toContain("name");
      const item: SchemeItem = {
        item_id: "test",
        item_name: "Test Scheme",
      };
      expect(item.item_name).toBe("Test Scheme");
    });
  });

  describe("server-side safety", () => {
    it("no-ops silently on server-side", () => {
      const originalWindow = global.window;
      // @ts-expect-error - testing server-side behavior
      delete global.window;

      expect(() => {
        track("view_item", {
          items: [{ item_id: "test", item_name: "Test" }],
        });
      }).not.toThrow();

      expect(firebaseAnalyticsMocks.logEvent).not.toHaveBeenCalled();

      global.window = originalWindow;
    });
  });
});
