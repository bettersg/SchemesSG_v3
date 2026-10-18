// Vendors the dotLottie player's wasm runtime into public/ so the chat spinner
// never needs jsdelivr or unpkg: without this the player pulls 1.7MB from a
// third-party CDN on first paint before it renders anything.
//
// Runs from postinstall, so the copy tracks whatever version is in the lockfile
// rather than a binary committed to the repo.
import { copyFileSync, mkdirSync } from "node:fs";
import { createRequire } from "node:module";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

// dotlottie-web is deliberately not a direct dependency: dotlottie-react pins
// it to an exact version, and a second declaration could resolve a copy whose
// wasm does not match the player that loads it. So resolve it through
// dotlottie-react, which also survives a strict (non-hoisting) node_modules.
const require = createRequire(import.meta.url);
const source = createRequire(
  require.resolve("@lottiefiles/dotlottie-react"),
).resolve("@lottiefiles/dotlottie-web/dotlottie-player.wasm");
const target = resolve(
  dirname(fileURLToPath(import.meta.url)),
  "../public/dotlottie-player.wasm",
);

mkdirSync(dirname(target), { recursive: true });
copyFileSync(source, target);
console.log(`copied ${source} -> ${target}`);
