export const STAGING_ORIGIN = "https://schemessg-v3-dev.web.app";
export const STAGING_API_ORIGIN =
  "https://asia-southeast1-schemessg-v3-dev.cloudfunctions.net";
export const STAGING_FIREBASE_PROJECT_ID = "schemessg-v3-dev";

const READ_ONLY_METHODS = new Set(["GET", "HEAD", "OPTIONS"]);

export type StagingRequestDecision =
  | { action: "continue" }
  | { action: "block"; reason: "mutating-method" | "outside-staging" };

export function classifyStagingRequest(
  method: string,
  url: string,
): StagingRequestDecision {
  if (!READ_ONLY_METHODS.has(method.toUpperCase())) {
    return { action: "block", reason: "mutating-method" };
  }

  if (new URL(url).origin !== STAGING_ORIGIN) {
    return { action: "block", reason: "outside-staging" };
  }

  return { action: "continue" } as const;
}
