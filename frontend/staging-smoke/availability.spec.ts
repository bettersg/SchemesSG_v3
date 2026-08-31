import { expect, test } from "@playwright/test";
import {
  STAGING_API_ORIGIN,
  STAGING_FIREBASE_PROJECT_ID,
  STAGING_ORIGIN,
} from "./read-only-network";

const PRODUCTION_API_ORIGIN =
  "https://asia-southeast1-schemessg.cloudfunctions.net";
const PRODUCTION_FIREBASE_AUTH_DOMAIN = "schemessg.firebaseapp.com";
const STAGING_FIREBASE_AUTH_DOMAIN = "schemessg-v3-dev.firebaseapp.com";

test("staging deployment is available and serves the expected application", async ({
  request,
}) => {
  const response = await request.get("/", {
    headers: { accept: "text/html" },
    maxRedirects: 0,
  });

  expect(response.status(), "staging hosting did not return HTTP 200").toBe(200);
  expect(new URL(response.url()).origin, "staging redirected to another host").toBe(
    STAGING_ORIGIN,
  );
  await expect(response).toBeOK();

  const html = await response.text();
  expect(html).toContain(
    "<title>Find the Right Schemes, All in One Place | Schemes.sg</title>",
  );
  expect(html).toContain('<html lang="en"');

  const scriptUrls = [...html.matchAll(/<script[^>]+src="([^"]+)"/g)].map(
    ([, source]) => new URL(source, STAGING_ORIGIN),
  );
  expect(
    scriptUrls.length,
    "staging HTML did not reference application scripts",
  ).toBeGreaterThan(0);
  expect(
    scriptUrls.every((url) => url.origin === STAGING_ORIGIN),
    "staging HTML referenced a script outside development hosting",
  ).toBe(true);

  const scripts = await Promise.all(
    scriptUrls.map(async (url) => {
      const scriptResponse = await request.get(url.toString(), {
        maxRedirects: 0,
      });
      expect(scriptResponse.status(), `${url.pathname} was unavailable`).toBe(
        200,
      );
      expect(new URL(scriptResponse.url()).origin).toBe(STAGING_ORIGIN);
      return scriptResponse.text();
    }),
  );
  const deployedJavascript = scripts.join("\n");
  expect(deployedJavascript).toContain(STAGING_API_ORIGIN);
  expect(deployedJavascript).toContain(
    `projectId:"${STAGING_FIREBASE_PROJECT_ID}"`,
  );
  expect(deployedJavascript).toContain(STAGING_FIREBASE_AUTH_DOMAIN);
  expect(deployedJavascript).not.toContain(PRODUCTION_API_ORIGIN);
  expect(deployedJavascript).not.toContain(PRODUCTION_FIREBASE_AUTH_DOMAIN);
});
