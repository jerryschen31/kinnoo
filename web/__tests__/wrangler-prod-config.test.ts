/**
 * task522 / test745: prod wrangler config targets prod domains.
 *
 * Pure config-parsing test (no wrangler runtime) so it works in CI without
 * any Cloudflare credentials.
 */
import { describe, it, expect } from "vitest";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";

function loadJsonc(path: string): unknown {
  const raw = readFileSync(path, "utf8");
  // Strip /* ... */ and // ... comments before parsing.
  const stripped = raw
    .replace(/\/\*[\s\S]*?\*\//g, "")
    .replace(/^\s*\/\/.*$/gm, "");
  return JSON.parse(stripped);
}

describe("feature121 / task522 wrangler prod config", () => {
  const prodPath = resolve(__dirname, "..", "wrangler.prod.jsonc");
  const devPath = resolve(__dirname, "..", "wrangler.jsonc");

  it("wrangler_prod_config_targets_prod_domains", () => {
    const prod = loadJsonc(prodPath) as Record<string, any>;

    expect(prod.name).toBe("kinnoo");
    expect(prod.vars?.BACKEND_URL).toBe("https://api.kinnoo.ai");

    const routes = prod.routes as Array<{ pattern: string }>;
    expect(routes).toBeDefined();
    const patterns = routes.map((r) => r.pattern);
    expect(patterns).toContain("kinnoo.ai");
    // Must contain at least one prod-scoped route.
    expect(patterns.some((p) => p === "kinnoo.ai" || p === "www.kinnoo.ai")).toBe(true);

    // Bindings preserved.
    const services = prod.services as Array<{ binding: string; service: string }>;
    expect(services?.[0]?.binding).toBe("WORKER_SELF_REFERENCE");
    expect(services?.[0]?.service).toBe("kinnoo");
    expect(prod.assets?.binding).toBe("ASSETS");

    // No dev references in prod config.
    const serialized = JSON.stringify(prod);
    expect(serialized).not.toContain("dev.kinnoo.ai");
    expect(serialized).not.toContain("dev-api.kinnoo.ai");

    // Dev wrangler config must remain dev-targeted (no prod drift).
    const dev = loadJsonc(devPath) as Record<string, any>;
    expect(dev.vars?.BACKEND_URL).toBe("https://dev-api.kinnoo.ai");
  });
});
