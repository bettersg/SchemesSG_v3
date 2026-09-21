import { describe, expect, it } from "vitest";
import packageLock from "../../package-lock.json";
import packageJson from "../../package.json";

type PackageRuntimeMetadata = {
  engines?: { node?: string };
  devEngines?: {
    runtime?: {
      name?: string;
      version?: string;
      onFail?: string;
    };
  };
};

const expectedRuntimeMetadata = {
  engines: { node: "20" },
  devEngines: {
    runtime: {
      name: "node",
      version: ">=20.19.0",
      onFail: "error",
    },
  },
};

describe("frontend package runtime metadata", () => {
  it("keeps Firebase runtime and source-development constraints separate", () => {
    const manifest = packageJson as PackageRuntimeMetadata;
    const lockRoot = packageLock.packages[""] as PackageRuntimeMetadata;

    expect(manifest).toMatchObject(expectedRuntimeMetadata);
    expect(lockRoot.engines).toEqual(manifest.engines);
  });
});
