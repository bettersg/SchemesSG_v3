import { writeFile } from "node:fs/promises";
import { test as base } from "@playwright/test";
import {
  classifyStagingRequest,
  type StagingRequestDecision,
} from "./read-only-network";

type ObservedRequest = {
  method: string;
  resourceType: string;
  url: string;
};

type BlockedRequest = ObservedRequest & {
  reason: Extract<StagingRequestDecision, { action: "block" }>["reason"];
};

type ReadOnlyNetwork = {
  allowedRequests: ObservedRequest[];
  blockedRequests: BlockedRequest[];
};

export const test = base.extend<{ readOnlyNetwork: ReadOnlyNetwork }>({
  readOnlyNetwork: [
    async ({ context }, use, testInfo) => {
      const allowedRequests: ObservedRequest[] = [];
      const blockedRequests: BlockedRequest[] = [];

      await context.route("**/*", async (route) => {
        const request = route.request();
        const observedRequest = {
          method: request.method(),
          resourceType: request.resourceType(),
          url: request.url(),
        };
        const decision = classifyStagingRequest(
          request.method(),
          request.url(),
        );
        if (decision.action === "continue") {
          allowedRequests.push(observedRequest);
          await route.continue();
          return;
        }

        blockedRequests.push({
          ...observedRequest,
          reason: decision.reason,
        });
        await route.abort("blockedbyclient");
      });

      await use({ allowedRequests, blockedRequests });

      const networkLogPath = testInfo.outputPath(
        "read-only-network-guard.json",
      );
      await writeFile(
        networkLogPath,
        JSON.stringify({ allowedRequests, blockedRequests }, null, 2),
      );
      await testInfo.attach("read-only-network-guard.json", {
        path: networkLogPath,
        contentType: "application/json",
      });
    },
    { auto: true },
  ],
});

export { expect } from "@playwright/test";
