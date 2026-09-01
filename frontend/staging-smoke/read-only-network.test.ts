import { describe, expect, it } from "vitest";
import { STAGING_ORIGIN, classifyStagingRequest } from "./read-only-network";

describe("deployed staging read-only network policy", () => {
  it.each(["POST", "PUT", "PATCH", "DELETE"])(
    "blocks %s requests even when they target staging",
    (method) => {
      expect(
        classifyStagingRequest(method, `${STAGING_ORIGIN}/feedback`),
      ).toEqual({ action: "block", reason: "mutating-method" });
    },
  );

  it("blocks every request outside the deployed staging origin", () => {
    expect(classifyStagingRequest("GET", "https://schemes.sg/catalog")).toEqual(
      {
        action: "block",
        reason: "outside-staging",
      },
    );
    expect(
      classifyStagingRequest(
        "GET",
        "https://identitytoolkit.googleapis.com/v1/accounts:lookup",
      ),
    ).toEqual({ action: "block", reason: "outside-staging" });
  });

  it.each(["GET", "HEAD", "OPTIONS"])(
    "allows same-origin %s requests needed to render staging",
    (method) => {
      expect(classifyStagingRequest(method, `${STAGING_ORIGIN}/catalog`)).toEqual(
        { action: "continue" },
      );
    },
  );
});
