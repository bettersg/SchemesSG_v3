import type { Page } from "@playwright/test";
import {
  E2E_API_ORIGIN,
  LANDING_RESULT_EVENTS,
  interceptLandingResultsJourney,
} from "./landing-results";

export const CANCELLATION_QUERY = "Help me compare support for my family";
export const CANCELLED_STREAM_TEXT =
  "I am still comparing the available family support schemes.";
export const FAILURE_QUERY = "Which option should I apply for first?";
export const FAILED_STREAM_TEXT =
  "I started comparing the application steps, but the connection dropped.";
export const RECOVERY_ANSWER =
  "Apply for Household Essentials Support first because it covers urgent costs.";

type ChatStreamScenario = {
  events: Array<{ type: string; data: unknown }>;
  finish: "complete" | "controlled-error" | "hold";
};

export const completedLandingScenario: ChatStreamScenario = {
  events: LANDING_RESULT_EVENTS,
  finish: "complete",
};

type ChatStreamControls = {
  failActive: () => Promise<void>;
};

export async function interceptChatStreamScenarios(
  page: Page,
  scenarios: ChatStreamScenario[],
): Promise<ChatStreamControls> {
  await interceptLandingResultsJourney(page);
  await page.addInitScript(
    ({ apiOrigin, streamScenarios }) => {
      const nativeFetch = window.fetch.bind(window);
      let scenarioIndex = 0;
      let activeController:
        | ReadableStreamDefaultController<Uint8Array>
        | undefined;

      (
        window as typeof window & {
          __e2eFailActiveChatStream?: () => void;
        }
      ).__e2eFailActiveChatStream = () => {
        if (!activeController) {
          throw new Error("No controlled E2E chat stream is active");
        }
        activeController.error(new TypeError("Simulated chat stream failure"));
        activeController = undefined;
      };

      window.fetch = async (input, init) => {
        const requestUrl =
          typeof input === "string"
            ? input
            : input instanceof URL
              ? input.toString()
              : input.url;

        if (requestUrl !== `${apiOrigin}/agent_chat_message`) {
          return nativeFetch(input, init);
        }

        const scenario = streamScenarios[scenarioIndex];
        scenarioIndex += 1;
        if (!scenario) {
          return new Response("Missing E2E chat stream scenario", {
            status: 500,
          });
        }

        const encoder = new TextEncoder();
        const body = new ReadableStream<Uint8Array>({
          start(controller) {
            for (const event of scenario.events) {
              controller.enqueue(
                encoder.encode(`data: ${JSON.stringify(event)}\n\n`),
              );
            }

            if (scenario.finish === "complete") {
              controller.close();
              return;
            }

            if (scenario.finish === "controlled-error") {
              activeController = controller;
            }

            init?.signal?.addEventListener(
              "abort",
              () => {
                controller.error(
                  init.signal?.reason ??
                    new DOMException("The request was aborted", "AbortError"),
                );
              },
              { once: true },
            );
          },
        });

        return new Response(body, {
          status: 200,
          headers: { "content-type": "text/event-stream; charset=utf-8" },
        });
      };
    },
    { apiOrigin: E2E_API_ORIGIN, streamScenarios: scenarios },
  );

  return {
    failActive: async () => {
      await page.evaluate(() => {
        const failActive = (
          window as typeof window & {
            __e2eFailActiveChatStream?: () => void;
          }
        ).__e2eFailActiveChatStream;
        if (!failActive) {
          throw new Error("E2E chat stream controls are unavailable");
        }
        failActive();
      });
    },
  };
}
