// Vendors the dotLottie player's wasm runtime into public/ so the chat spinner
// never needs jsdelivr or unpkg. Without this the player fetches 1.7MB from a
// CDN on first paint and renders nothing at all when that CDN is blocked — the
// same corporate-network failure mode as issue #367.
//
// Runs from postinstall, so the copy tracks whatever version is in the lockfile
// rather than a binary committed to the repo.
import { copyFileSync, mkdirSync } from "node:fs";
import { createRequire } from "node:module";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

// dotlottie-web is deliberately not a direct dependency: dotlottie-react pins it
// to an exact version, and a second declaration could resolve a copy whose wasm
// does not match the player that loads it. Resolved through its own exports map,
// so hoisting and dist-layout changes cannot silently break this.
const source = createRequire(import.meta.url).resolve(
  "@lottiefiles/dotlottie-web/dotlottie-player.wasm",
);
const target = resolve(
  dirname(fileURLToPath(import.meta.url)),
  "../public/dotlottie-player.wasm",
);

mkdirSync(dirname(target), { recursive: true });
copyFileSync(source, target);
console.log(`copied ${source} -> ${target}`);
