import { test as base } from "@playwright/test";
import {
  classifyStagingRequest,
  type StagingRequestDecision,
} from "./read-only-network";

type BlockedRequest = {
  method: string;
  reason: Extract<StagingRequestDecision, { action: "block" }>["reason"];
  url: string;
};

type ReadOnlyNetwork = {
  blockedRequests: BlockedRequest[];
};

export const test = base.extend<{ readOnlyNetwork: ReadOnlyNetwork }>({
  readOnlyNetwork: [
    async ({ context }, use, testInfo) => {
      const blockedRequests: BlockedRequest[] = [];

      await context.route("**/*", async (route) => {
        const request = route.request();
        const decision = classifyStagingRequest(
          request.method(),
          request.url(),
        );
        if (decision.action === "continue") {
          await route.continue();
          return;
        }

        blockedRequests.push({
          method: request.method(),
          reason: decision.reason,
          url: request.url(),
        });
        await route.abort("blockedbyclient");
      });

      await use({ blockedRequests });

      await testInfo.attach("read-only-network-guard.json", {
        body: Buffer.from(JSON.stringify({ blockedRequests }, null, 2)),
        contentType: "application/json",
      });
    },
    { auto: true },
  ],
});

export { expect } from "@playwright/test";
