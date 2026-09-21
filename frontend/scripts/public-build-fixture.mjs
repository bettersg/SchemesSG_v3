import { createServer } from "node:http";
import { pathToFileURL } from "node:url";

const buildScheme = {
  scheme_id: "fixture-public-scheme",
  scheme: "Fixture Public Scheme",
  agency: "SchemesSG Test Agency",
  scheme_type: ["Community Support"],
  who_is_it_for: ["Singapore residents"],
  description:
    "A stable record used to verify the deterministic public SSG build.",
  summary: "Deterministic public build fixture.",
  what_it_gives: ["Build-time scheme content"],
  link: "https://example.test/fixture-public-scheme",
  image: "",
  planning_area: ["Nationwide"],
  status: "active",
  last_scraped_update: {
    _seconds: 1_788_768_000,
    _nanoseconds: 0,
  },
};

const e2eSchemes = [
  {
    scheme_id: "bright-start-support",
    scheme: "Bright Start Support",
    agency: "Family Services Singapore",
    scheme_type: ["Financial Assistance", "Family"],
    summary: "Help with essential costs while families regain stability.",
    llm_description:
      "Bright Start Support provides temporary help with essential household costs while families work towards stability.",
    who_is_it_for: ["Families with children", "Households facing income loss"],
    what_it_gives: ["Monthly essentials grant", "Support planning session"],
    eligibility:
      "Applicants must live in Singapore and complete a household needs assessment.",
    how_to_apply:
      "Apply online with identification and recent household income documents.",
    link: "https://support.example.test/bright-start",
    planning_area: ["Central"],
    service_area: "Islandwide",
    phone: "+65 6123 4567",
    email: "help@brightstart.example.test",
    address: "10 Community Way, Singapore 123456",
    status: "active",
  },
  {
    scheme_id: "daily-needs-grant",
    scheme: "Daily Needs Grant",
    agency: "Community Assistance Network",
    scheme_type: ["Financial Assistance"],
    summary: "Short-term support for groceries and household essentials.",
    link: "https://support.example.test/daily-needs",
    status: "active",
  },
  {
    scheme_id: "family-care-fund",
    scheme: "Family Care Fund",
    agency: "Care Partnership Office",
    scheme_type: ["Financial Assistance", "Family & Children"],
    summary: "Practical support for households with ongoing care needs.",
    link: "https://support.example.test/family-care",
    status: "active",
  },
];

const schemes = [buildScheme, ...e2eSchemes];

/** Every scheme the fixture publishes, so callers can assert on the build. */
export const PUBLIC_FIXTURE_SCHEME_IDS = schemes.map(
  (scheme) => scheme.scheme_id,
);

const sendJson = (response, status, payload) => {
  response.writeHead(status, { "Content-Type": "application/json" });
  response.end(JSON.stringify(payload));
};

/**
 * Label who made a request, so a spec can tell a server render apart from a
 * refetch in the page. Both arrive anonymously, and the User-Agent is the only
 * header that separates them: browsers send `Mozilla/5.0`, Node sends `node`.
 */
const initiatorOf = (request) =>
  /^mozilla\//i.test(request.headers["user-agent"] ?? "")
    ? "browser"
    : "server";

export function createPublicBuildFixtureServer() {
  // Every public request is recorded so E2E specs can assert the anonymous
  // contract on the requests Next.js actually made, rather than on requests a
  // browser-side interceptor swallowed before they left the page.
  const requests = [];

  return createServer((request, response) => {
    const url = new URL(request.url ?? "/", "http://127.0.0.1");

    if (request.method === "GET" && url.pathname === "/health") {
      return sendJson(response, 200, { status: "ok" });
    }

    if (url.pathname === "/__fixture/requests") {
      if (request.method === "GET") {
        return sendJson(response, 200, { requests });
      }
      if (request.method === "DELETE") {
        requests.length = 0;
        return sendJson(response, 200, { requests });
      }
    }

    if (request.method === "GET" && url.pathname === "/catalog") {
      requests.push({
        resource: "catalog",
        method: request.method,
        authorization: request.headers.authorization ?? null,
        initiator: initiatorOf(request),
        category: url.searchParams.get("category"),
        cursor: url.searchParams.get("cursor"),
        limit: url.searchParams.get("limit"),
      });
      if (request.headers.authorization) {
        return sendJson(response, 400, {
          error: "Public catalog requests must not send authorization",
        });
      }
      const category = url.searchParams.get("category")?.toLowerCase();
      const matchingSchemes = category
        ? schemes.filter((item) =>
            item.scheme_type.some((type) => type.toLowerCase() === category),
          )
        : schemes;
      return sendJson(response, 200, {
        data: matchingSchemes,
        total_count: matchingSchemes.length,
        has_more: false,
      });
    }

    if (request.method === "GET" && url.pathname.startsWith("/schemes/")) {
      const schemeId = decodeURIComponent(
        url.pathname.slice("/schemes/".length),
      );
      requests.push({
        resource: "scheme",
        method: request.method,
        authorization: request.headers.authorization ?? null,
        initiator: initiatorOf(request),
        schemeId,
      });
      if (request.headers.authorization) {
        return sendJson(response, 400, {
          error: "Public scheme requests must not send authorization",
        });
      }
      const scheme = schemes.find((item) => item.scheme_id === schemeId);
      if (scheme) return sendJson(response, 200, { data: scheme });
    }

    return sendJson(response, 404, { error: "Fixture route not found" });
  });
}

const isCli =
  process.argv[1] && pathToFileURL(process.argv[1]).href === import.meta.url;

if (isCli) {
  const port = Number.parseInt(
    process.env.PUBLIC_BUILD_FIXTURE_PORT ?? "4174",
    10,
  );
  const server = createPublicBuildFixtureServer();

  server.listen(port, "127.0.0.1", () => {
    process.stdout.write(
      `Public build fixture listening on 127.0.0.1:${port}\n`,
    );
  });

  const close = () => server.close(() => process.exit(0));
  process.once("SIGINT", close);
  process.once("SIGTERM", close);
}
