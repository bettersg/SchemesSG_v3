import { expect, test } from "@playwright/test";
import { interceptChatStreamScenarios } from "./fixtures/chat-resilience";
import { LANDING_QUERY } from "./fixtures/landing-results";
import { THINKING_PHRASES } from "../src/components/chat/thinking-phrases";

// Any of the 20 can open the rotation, so match the set rather than an index.
// See thinkingPhraseOrder: pinning an opener meant every send showed the same
// words, because the dwell floor outlasts a healthy backend's first status step.
const ANY_PHRASE = new RegExp(
  `^(${THINKING_PHRASES.map((phrase) =>
    phrase.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"),
  ).join("|")})$`,
);
const REAL_STEP_LABEL = "Matching support schemes";

// Every locator below is filtered to visible matches: the chat page renders the
// message list twice — desktop split layout and mobile tab panel — so on a
// desktop viewport each match has a display:none twin. Same filter the rest of
// the suite uses.

// A bare aria-live span, not role="status": the schemes panel owns the page's
// only status role ("Finding the best schemes..."), and a second one makes every
// bare getByRole("status") in this suite and in dev-smoke ambiguous while a
// response is in flight.
const LIVE_REGION = 'span[aria-live="polite"][aria-atomic="true"]';

test("thinking indicator appears before the agent sends anything at all", async ({
  page,
}) => {
  // No events, ever: the stream opens and stays silent. This is the window the
  // indicator used to sit out — it was gated on a chunk or a status step
  // arriving, and the agent's first status event only fires once it decides to
  // call a tool.
  await interceptChatStreamScenarios(page, [{ events: [], finish: "hold" }]);

  await page.goto("/");
  await page.getByRole("textbox").fill(LANDING_QUERY);
  await page.getByRole("button", { name: "Search" }).click();

  await expect(
    page.getByText(ANY_PHRASE).filter({ visible: true }),
  ).toBeVisible();
  // One stable announcement rather than 20 rotating decorative phrases.
  await expect(
    page.locator(LIVE_REGION).filter({ visible: true }),
  ).toHaveText("Working on your answer");
});

// The suite runs reduced-motion by default, which pins the rotation to its first
// phrase — correct behaviour, and what the test above exercises, but the index
// can never advance, so the clamp below would pass with or without the fix. This
// block is the one place motion has to be real.
test.describe("with motion enabled", () => {
  test.use({ contextOptions: { reducedMotion: "no-preference" } });

  test("a real status step replaces the placeholder mid-rotation without blanking the row", async ({
    page,
  }) => {
    await interceptChatStreamScenarios(page, [
      {
        events: [
          {
            type: "status",
            data: { phase: "session_started", sessionID: "e2e-session" },
          },
          {
            // Longer than the rotation's maximum dwell (3200ms), so the phrase
            // index is guaranteed to have advanced past 0 before the real label
            // arrives and the word list shrinks to a single entry.
            delayMs: 4000,
            type: "action_message",
            data: {
              label: REAL_STEP_LABEL,
              message:
                "Compared trusted schemes with the stated household need.",
            },
          },
        ],
        finish: "hold",
      },
    ]);

    await page.goto("/");
    await page.getByRole("textbox").fill(LANDING_QUERY);
    await page.getByRole("button", { name: "Search" }).click();

    await expect(
      page.getByText(ANY_PHRASE).filter({ visible: true }),
    ).toBeVisible();
    await expect(
      page.locator(LIVE_REGION).filter({ visible: true }),
    ).toHaveText(REAL_STEP_LABEL, { timeout: 10_000 });

    // Two nodes: the live region and the visible row. Without the index clamp
    // in WordRotate the stale index reads past the end of the one-entry list,
    // the row renders empty, and this count drops to 1.
    await expect(
      page.getByText(REAL_STEP_LABEL).filter({ visible: true }),
    ).toHaveCount(2);
  });
});
