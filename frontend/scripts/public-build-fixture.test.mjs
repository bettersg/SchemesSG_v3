import assert from "node:assert/strict";
import { after, before, test } from "node:test";
import { createPublicBuildFixtureServer } from "./public-build-fixture.mjs";

let server;
let baseUrl;

before(async () => {
  server = createPublicBuildFixtureServer();
  await new Promise((resolve, reject) => {
    server.once("error", reject);
    server.listen(0, "127.0.0.1", resolve);
  });
  const address = server.address();
  assert(address && typeof address === "object");
  baseUrl = `http://127.0.0.1:${address.port}`;
});

after(async () => {
  await new Promise((resolve, reject) =>
    server.close((error) => (error ? reject(error) : resolve())),
  );
});

test("serves a complete public catalog page without authorization", async () => {
  const response = await fetch(`${baseUrl}/catalog?limit=20`);
  const payload = await response.json();

  assert.equal(response.status, 200);
  assert.equal(response.headers.get("content-type"), "application/json");
  assert.equal(payload.total_count, 4);
  assert.equal(payload.has_more, false);
  assert.equal(payload.data[0].scheme_id, "fixture-public-scheme");
  assert.equal(payload.data[0].status, "active");
});

test("serves the full public scheme detail used by static rendering", async () => {
  const response = await fetch(`${baseUrl}/schemes/fixture-public-scheme`);
  const payload = await response.json();

  assert.equal(response.status, 200);
  assert.equal(payload.data.scheme_id, "fixture-public-scheme");
  assert.equal(payload.data.scheme, "Fixture Public Scheme");
  assert.match(payload.data.description, /deterministic public SSG build/);
});

test("filters the catalog for server-rendered category pages", async () => {
  const response = await fetch(
    `${baseUrl}/catalog?limit=20&category=Financial%20Assistance`,
  );
  const payload = await response.json();

  assert.equal(response.status, 200);
  assert.equal(payload.total_count, 3);
  assert.deepEqual(
    payload.data.map((item) => item.scheme_id),
    ["bright-start-support", "daily-needs-grant", "family-care-fund"],
  );
});

test("rejects unsupported fixture routes", async () => {
  const response = await fetch(`${baseUrl}/agent_chat_message`);

  assert.equal(response.status, 404);
});

test("rejects authorization on public build routes", async () => {
  const response = await fetch(`${baseUrl}/catalog?limit=20`, {
    headers: { authorization: "Bearer should-not-be-sent" },
  });

  assert.equal(response.status, 400);
});

test("records public reads so E2E specs can assert the anonymous contract", async () => {
  const reset = await fetch(`${baseUrl}/__fixture/requests`, {
    method: "DELETE",
  });
  assert.equal(reset.status, 200);
  assert.deepEqual((await reset.json()).requests, []);

  await fetch(`${baseUrl}/catalog?limit=20&category=Financial%20Assistance`);
  await fetch(`${baseUrl}/schemes/bright-start-support`);
  await fetch(`${baseUrl}/catalog?limit=20`, {
    headers: { authorization: "Bearer should-not-be-sent" },
  });

  const response = await fetch(`${baseUrl}/__fixture/requests`);
  const { requests } = await response.json();

  assert.equal(response.status, 200);
  assert.deepEqual(requests, [
    {
      resource: "catalog",
      method: "GET",
      authorization: null,
      category: "Financial Assistance",
      cursor: null,
      limit: "20",
    },
    {
      resource: "scheme",
      method: "GET",
      authorization: null,
      schemeId: "bright-start-support",
    },
    // Rejected reads are still recorded, so a leaked token is visible rather
    // than silently dropped.
    {
      resource: "catalog",
      method: "GET",
      authorization: "Bearer should-not-be-sent",
      category: null,
      cursor: null,
      limit: "20",
    },
  ]);
});
