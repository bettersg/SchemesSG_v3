import { spawn } from "node:child_process";
import { once } from "node:events";
import { readFile, rm } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import {
  PUBLIC_FIXTURE_SCHEME_IDS,
  createPublicBuildFixtureServer,
} from "./public-build-fixture.mjs";

const frontendRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const port = Number.parseInt(process.env.PUBLIC_BUILD_FIXTURE_PORT ?? "4174", 10);

// Next persists `revalidate` fetch results in .next/cache/fetch-cache across
// builds. Reusing them would let a previous run's catalog decide which scheme
// pages get generated, which is the opposite of what this gate checks.
await rm(path.join(frontendRoot, ".next/cache/fetch-cache"), {
  recursive: true,
  force: true,
});

const server = createPublicBuildFixtureServer();

await new Promise((resolve, reject) => {
  server.once("error", reject);
  server.listen(port, "127.0.0.1", resolve);
});

try {
  const build = spawn(process.execPath, ["node_modules/next/dist/bin/next", "build"], {
    env: {
      ...process.env,
      APP_ENV: "staging",
      NEXT_TELEMETRY_DISABLED: "1",
      NEXT_PUBLIC_API_BASE_URL: `http://127.0.0.1:${port}`,
    },
    stdio: "inherit",
  });

  const [code, signal] = await once(build, "exit");
  if (code !== 0) {
    throw new Error(
      `Public fixture build failed${signal ? ` with signal ${signal}` : ` with exit code ${code}`}`,
    );
  }
} finally {
  await new Promise((resolve, reject) =>
    server.close((error) => (error ? reject(error) : resolve())),
  );
}

// A build that silently generated no scheme pages still exits 0, so check the
// prerender manifest for the routes generateStaticParams was supposed to emit.
const manifest = JSON.parse(
  await readFile(
    path.join(frontendRoot, ".next/prerender-manifest.json"),
    "utf8",
  ),
);
const prerendered = new Set(Object.keys(manifest.routes ?? {}));
const missing = PUBLIC_FIXTURE_SCHEME_IDS.map((id) => `/schemes/${id}`).filter(
  (route) => !prerendered.has(route),
);

if (missing.length > 0) {
  throw new Error(
    `Public build did not prerender ${missing.length} scheme route(s): ${missing.join(", ")}`,
  );
}

process.stdout.write(
  `Prerendered ${PUBLIC_FIXTURE_SCHEME_IDS.length} public scheme routes\n`,
);
