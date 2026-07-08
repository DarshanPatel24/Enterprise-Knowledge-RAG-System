"use client";

import { useSyncExternalStore } from "react";

import {
  getSettingsServerSnapshot,
  getSettingsSnapshot,
  subscribeSettings,
  type AppSettings,
} from "@/lib/settings";

/** Reactive access to the runtime settings store (localStorage-backed). */
export function useSettings(): AppSettings {
  return useSyncExternalStore(
    subscribeSettings,
    getSettingsSnapshot,
    getSettingsServerSnapshot,
  );
}
