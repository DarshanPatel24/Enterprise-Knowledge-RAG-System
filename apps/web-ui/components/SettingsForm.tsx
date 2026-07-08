"use client";

import { useState, type FormEvent } from "react";
import { CheckCircle2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { useSettings } from "@/lib/hooks/useSettings";
import { updateSettings } from "@/lib/settings";
import type { AppSettings } from "@/lib/settings";
import type { ClassificationClearance } from "@/lib/api/types";

const CLEARANCE_OPTIONS: ClassificationClearance[] = [
  "public",
  "internal",
  "confidential",
  "restricted",
];

/**
 * Local-first configuration screen.
 *
 * Persists the API base URL, API key, tenant id, user id, and clearance to
 * `localStorage` only. No value is ever transmitted to any server other than the
 * configured EKCP gateway.
 */
export function SettingsForm(): React.JSX.Element {
  const settings = useSettings();
  const [form, setForm] = useState<AppSettings>(settings);
  const [saved, setSaved] = useState(false);

  const setField = <K extends keyof AppSettings>(
    key: K,
    value: AppSettings[K],
  ): void => {
    setForm((prev) => ({ ...prev, [key]: value }));
    setSaved(false);
  };

  const handleSubmit = (event: FormEvent): void => {
    event.preventDefault();
    updateSettings({
      apiBaseUrl: form.apiBaseUrl.trim(),
      apiKey: form.apiKey.trim(),
      tenantId: form.tenantId.trim(),
      userId: form.userId.trim(),
      clearance: form.clearance,
    });
    setSaved(true);
  };

  return (
    <form onSubmit={handleSubmit}>
      <Card className="w-full max-w-xl">
        <CardHeader>
          <CardTitle>Settings</CardTitle>
          <CardDescription>
            Connection and identity values, stored only in this browser. Nothing is
            sent to any external service.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-1.5">
            <label htmlFor="apiBaseUrl" className="text-sm font-medium">
              EKCP API URL
            </label>
            <Input
              id="apiBaseUrl"
              value={form.apiBaseUrl}
              onChange={(event) => setField("apiBaseUrl", event.target.value)}
              placeholder="http://localhost:8003"
              autoComplete="off"
            />
          </div>
          <div className="space-y-1.5">
            <label htmlFor="apiKey" className="text-sm font-medium">
              API key
            </label>
            <Input
              id="apiKey"
              type="password"
              value={form.apiKey}
              onChange={(event) => setField("apiKey", event.target.value)}
              placeholder="Required"
              autoComplete="off"
            />
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-1.5">
              <label htmlFor="tenantId" className="text-sm font-medium">
                Tenant ID
              </label>
              <Input
                id="tenantId"
                value={form.tenantId}
                onChange={(event) => setField("tenantId", event.target.value)}
                placeholder="Required"
                autoComplete="off"
              />
            </div>
            <div className="space-y-1.5">
              <label htmlFor="userId" className="text-sm font-medium">
                User ID
              </label>
              <Input
                id="userId"
                value={form.userId}
                onChange={(event) => setField("userId", event.target.value)}
                placeholder="Required"
                autoComplete="off"
              />
            </div>
          </div>
          <div className="space-y-1.5">
            <label htmlFor="clearance" className="text-sm font-medium">
              Classification clearance
            </label>
            <select
              id="clearance"
              value={form.clearance}
              onChange={(event) =>
                setField("clearance", event.target.value as ClassificationClearance)
              }
              className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
            >
              {CLEARANCE_OPTIONS.map((option) => (
                <option key={option} value={option}>
                  {option}
                </option>
              ))}
            </select>
          </div>
        </CardContent>
        <CardFooter className="justify-between">
          <Button type="submit">Save settings</Button>
          {saved && (
            <span className="flex items-center gap-1 text-sm text-clearance-public">
              <CheckCircle2 className="h-4 w-4" aria-hidden />
              Saved
            </span>
          )}
        </CardFooter>
      </Card>
    </form>
  );
}
