import { chromium } from "playwright-core";
import { spawnSync } from "node:child_process";
import { mkdir, writeFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";

const root = fileURLToPath(new URL("../../../", import.meta.url));
const artifacts = `${root}/.local/agent-workflow/browser`;
await mkdir(artifacts, { recursive: true });
const config = `${artifacts}/cli.config.json`;
await writeFile(
  config,
  JSON.stringify(
    {
      browser: {
        browserName: "chromium",
        launchOptions: { executablePath: chromium.executablePath(), headless: true },
      },
      outputDir: artifacts,
    },
    null,
    2,
  ),
);
const result = spawnSync(
  `${root}/node/tools/agent-workflow/node_modules/.bin/playwright-cli`,
  process.argv.slice(2),
  { stdio: "inherit", cwd: root, env: { ...process.env, PLAYWRIGHT_MCP_CONFIG: config } },
);
if (result.error) throw result.error;
process.exit(result.status ?? 1);
