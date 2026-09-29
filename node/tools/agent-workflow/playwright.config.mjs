import { defineConfig } from "@playwright/test";
import { fileURLToPath } from "node:url";

const root = fileURLToPath(new URL("../../../", import.meta.url));

export default defineConfig({
  testDir: "./tests",
  globalSetup: "./browser.setup.mjs",
  globalTeardown: "./browser.teardown.mjs",
  outputDir: `${root}/.local/agent-workflow/test-results`,
  workers: 1,
  retries: 0,
  timeout: 45_000,
  reporter: [
    ["list"],
    ["html", { outputFolder: `${root}/.local/agent-workflow/report`, open: "never" }],
  ],
  use: {
    browserName: "chromium",
    headless: true,
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },
});
