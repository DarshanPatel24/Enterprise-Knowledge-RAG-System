import { defineConfig, devices } from "@playwright/test";

/**
 * Playwright browser E2E for the EK-RAG web UI.
 *
 * Validates real in-browser rendering of the streaming chat contract (token,
 * citation, and done SSE frames) by intercepting the EKCP gateway at the network
 * layer, so no backend is required. Local-first: the dev server and browser run
 * entirely on localhost.
 */
export default defineConfig({
  testDir: "./e2e",
  timeout: 45_000,
  expect: { timeout: 10_000 },
  fullyParallel: false,
  reporter: [["list"]],
  use: {
    baseURL: "http://localhost:3100",
    trace: "retain-on-failure",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
  webServer: {
    command: "npm run dev -- --port 3100",
    url: "http://localhost:3100",
    reuseExistingServer: true,
    timeout: 120_000,
    env: {
      NEXT_PUBLIC_EKCP_URL: "http://localhost:8003",
    },
  },
});
