import { expect, test } from "./read-only-fixture";
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
  page,
}) => {
  const response = await page.goto("/");

  if (response === null) {
    throw new Error("staging hosting did not return a document response");
  }
  expect(
    response.status(),
    "staging hosting did not return HTTP 200",
  ).toBe(200);
  await expect(page).toHaveURL(`${STAGING_ORIGIN}/`);
  await expect(page).toHaveTitle(
    "Find the Right Schemes, All in One Place | Schemes.sg",
  );
  await expect(page.locator("html")).toHaveAttribute("lang", "en");

  const html = await response.text();
  const scriptUrls = [...html.matchAll(/<script[^>]+src="([^"]+)"/g)].map(
    ([, source]) => new URL(source, STAGING_ORIGIN).toString(),
  );
  expect(
    scriptUrls.length,
    "staging HTML did not reference application scripts",
  ).toBeGreaterThan(0);
  expect(
    scriptUrls.every((url) => new URL(url).origin === STAGING_ORIGIN),
    "staging page referenced a script outside development hosting",
  ).toBe(true);

  const scripts = await page.evaluate(
    async (urls) =>
      Promise.all(
        urls.map(async (url) => {
          const scriptResponse = await fetch(url, { redirect: "error" });
          if (!scriptResponse.ok) {
            throw new Error(
              `${new URL(url).pathname} returned HTTP ${scriptResponse.status}`,
            );
          }
          if (new URL(scriptResponse.url).origin !== window.location.origin) {
            throw new Error(`${url} redirected outside development hosting`);
          }
          return scriptResponse.text();
        }),
      ),
    scriptUrls,
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
