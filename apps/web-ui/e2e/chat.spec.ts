import { test, expect } from "@playwright/test";

/**
 * End-to-end browser validation of the streaming chat + citation rendering.
 *
 * The EKCP gateway is intercepted at the network layer: `/chat/stream` returns a
 * canned Server-Sent Events body (a citation frame, token frames, then done).
 * This proves the browser renders streamed tokens and a citation card with the
 * clearance badge from the exact contract the app consumes — no backend needed.
 */

type UiSettings = {
  apiBaseUrl: string;
  apiKey: string;
  tenantId: string;
  userId: string;
  clearance: string;
};

const SETTINGS: UiSettings = {
  apiBaseUrl: "http://localhost:8003",
  apiKey: "test-gateway-token",
  tenantId: "tenant-a",
  userId: "u-1",
  clearance: "internal",
};

const SSE_BODY = [
  "event: citation",
  'data: {"document_id":"doc-9","chunk_id":"chunk-1","source_path":"/enterprise/retention.md","confidence":0.91,"explanation":"policy match"}',
  "",
  "event: token",
  'data: {"text":"Enterprise "}',
  "",
  "event: token",
  'data: {"text":"retention "}',
  "",
  "event: token",
  'data: {"text":"is seven years."}',
  "",
  "event: done",
  'data: {"session_id":"s-1","correlation_id":"c-1","finish_reason":"stop","total_tokens":5,"cost_estimate":0}',
  "",
  "",
].join("\n");

test.beforeEach(async ({ page }) => {
  await page.addInitScript((settings: UiSettings) => {
    window.localStorage.setItem("ekrag.settings.v1", JSON.stringify(settings));
  }, SETTINGS);

  await page.route("**/health/live", (route) =>
    route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ status: "ok", service: "ekcp" }),
    }),
  );

  await page.route("**/chat/stream", (route) =>
    route.fulfill({
      status: 200,
      headers: { "content-type": "text/event-stream" },
      body: SSE_BODY,
    }),
  );
});

test("streams a grounded answer and renders a citation card", async ({ page }) => {
  await page.goto("/chat");

  const input = page.getByRole("textbox", { name: "Message" });
  await expect(input).toBeEnabled();
  await input.fill("What is the data retention policy?");
  await input.press("Enter");

  // Streamed assistant answer renders as Markdown text.
  await expect(
    page.getByText("Enterprise retention is seven years."),
  ).toBeVisible();

  // Citation card renders with source path, clearance badge, and a Sources header.
  await expect(page.getByText("/enterprise/retention.md")).toBeVisible();
  await expect(page.getByText("Internal", { exact: true })).toBeVisible();
  await expect(page.getByText(/Sources \(1\)/)).toBeVisible();
});

test("blocks chat until configuration is present", async ({ page }) => {
  await page.addInitScript(() => {
    window.localStorage.removeItem("ekrag.settings.v1");
  });
  await page.goto("/chat");

  await expect(page.getByRole("alert")).toContainText("Configuration required");
  await expect(page.getByRole("textbox", { name: "Message" })).toBeDisabled();
});
