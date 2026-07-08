/**
 * Runtime application settings, persisted to `localStorage` only.
 *
 * These user-configurable values (API base URL, API key, tenant id, user id,
 * clearance) override the build-time `NEXT_PUBLIC_*` environment defaults. They
 * are never sent to any server other than the configured EKCP gateway, and are
 * never persisted anywhere but the browser's `localStorage`.
 */

import {
  getApiBaseUrl as envApiBaseUrl,
  getApiKey as envApiKey,
  getClearance as envClearance,
  getTenantId as envTenantId,
  getUserId as envUserId,
} from "@/lib/config";
import type { ClassificationClearance } from "@/lib/api/types";

export type AppSettings = {
  apiBaseUrl: string;
  apiKey: string;
  tenantId: string;
  userId: string;
  clearance: ClassificationClearance;
};

const STORAGE_KEY = "ekrag.settings.v1";

function envDefaults(): AppSettings {
  const clearance = envClearance();
  return {
    apiBaseUrl: envApiBaseUrl(),
    apiKey: envApiKey(),
    tenantId: envTenantId(),
    userId: envUserId(),
    clearance: (clearance as ClassificationClearance) ?? "public",
  };
}

function readFromStorage(): AppSettings {
  const defaults = envDefaults();
  if (typeof window === "undefined") {
    return defaults;
  }
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) {
      return defaults;
    }
    const parsed = JSON.parse(raw) as Partial<AppSettings>;
    return { ...defaults, ...parsed };
  } catch {
    return defaults;
  }
}

let cache: AppSettings | null = null;
let serverCache: AppSettings | null = null;
const listeners = new Set<() => void>();

function emit(): void {
  for (const listener of listeners) {
    listener();
  }
}

/** External-store subscribe for `useSyncExternalStore`. */
export function subscribeSettings(listener: () => void): () => void {
  listeners.add(listener);
  return () => {
    listeners.delete(listener);
  };
}

/** Current settings snapshot (client), reading from `localStorage` once and caching. */
export function getSettingsSnapshot(): AppSettings {
  if (!cache) {
    cache = readFromStorage();
  }
  return cache;
}

/** Server snapshot: environment defaults only (no `localStorage` on the server).
 *
 * Returns a stable cached reference so `useSyncExternalStore` does not loop.
 */
export function getSettingsServerSnapshot(): AppSettings {
  if (!serverCache) {
    serverCache = envDefaults();
  }
  return serverCache;
}

/** Persist a partial settings update and notify subscribers. */
export function updateSettings(patch: Partial<AppSettings>): AppSettings {
  const next = { ...getSettingsSnapshot(), ...patch };
  cache = next;
  if (typeof window !== "undefined") {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
  }
  emit();
  return next;
}

/** The configuration values required before chat is permitted. */
export function missingRequiredFields(settings: AppSettings): string[] {
  const missing: string[] = [];
  if (!settings.tenantId.trim()) {
    missing.push("Tenant ID");
  }
  if (!settings.apiKey.trim()) {
    missing.push("API key");
  }
  if (!settings.userId.trim()) {
    missing.push("User ID");
  }
  return missing;
}

/** Whether the app is sufficiently configured to start a chat. */
export function isConfigured(settings: AppSettings): boolean {
  return missingRequiredFields(settings).length === 0;
}
