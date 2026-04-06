import type { NextConfig } from "next";
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

/**
 * Next.js only auto-loads `apps/web/.env*`. The API uses the monorepo root `.env`;
 * lift `NEXT_PUBLIC_*` from there (and root `.env.local`) so one file is enough for local dev.
 */
function mergeRootNextPublicEnv(): void {
  const repoRoot = path.resolve(__dirname, "../..");

  const applyFile = (filename: string, overrideExisting: boolean) => {
    const full = path.join(repoRoot, filename);
    if (!fs.existsSync(full)) return;
    const raw = fs.readFileSync(full, "utf8");
    for (const line of raw.split("\n")) {
      const trimmed = line.trim();
      if (!trimmed || trimmed.startsWith("#")) continue;
      const eq = trimmed.indexOf("=");
      if (eq <= 0) continue;
      const key = trimmed.slice(0, eq).trim();
      if (!key.startsWith("NEXT_PUBLIC_")) continue;
      const current = process.env[key];
      if (!overrideExisting && current != null && current !== "") continue;
      let value = trimmed.slice(eq + 1).trim();
      if (
        (value.startsWith('"') && value.endsWith('"')) ||
        (value.startsWith("'") && value.endsWith("'"))
      ) {
        value = value.slice(1, -1);
      }
      if (value === "" && overrideExisting) continue;
      process.env[key] = value;
    }
  };

  applyFile(".env", false);
  applyFile(".env.local", true);
}

mergeRootNextPublicEnv();

const nextConfig: NextConfig = {
  turbopack: {
    root: __dirname,
  },
};

export default nextConfig;
