"use client";

import { useCallback, useEffect, useState } from "react";
import { CheckCircle2, Loader2, RefreshCw, XCircle } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { checkLiveness } from "@/lib/api/ekcp";
import { useSettings } from "@/lib/hooks/useSettings";
import type { ConnectivityStatus } from "@/lib/api/types";

type ProbeState =
  | { phase: "loading" }
  | { phase: "resolved"; result: ConnectivityStatus };

/**
 * Client component that probes EKCP liveness and renders a connectivity status.
 *
 * The EKCP base URL is resolved from configuration and displayed for operator
 * transparency; it is never hardcoded in this component.
 */
export function HealthStatus(): React.JSX.Element {
  const settings = useSettings();
  const [state, setState] = useState<ProbeState>({ phase: "loading" });

  const probe = useCallback(async (): Promise<void> => {
    setState({ phase: "loading" });
    const result = await checkLiveness();
    setState({ phase: "resolved", result });
  }, []);

  useEffect(() => {
    void probe();
  }, [probe]);

  const isLoading = state.phase === "loading";
  const result = state.phase === "resolved" ? state.result : null;
  const isOk = result?.state === "ok";

  return (
    <Card className="w-full max-w-lg">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>EKCP Connectivity</CardTitle>
          {isLoading ? (
            <Badge variant="secondary">Checking…</Badge>
          ) : isOk ? (
            <Badge variant="success">Online</Badge>
          ) : (
            <Badge variant="destructive">Offline</Badge>
          )}
        </div>
        <CardDescription>Gateway: {settings.apiBaseUrl}</CardDescription>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="flex items-center gap-2 text-muted-foreground">
            <Loader2 className="h-5 w-5 animate-spin" aria-hidden />
            <span>Contacting EKCP liveness endpoint…</span>
          </div>
        ) : result?.state === "ok" ? (
          <div className="flex items-center gap-2 text-clearance-public">
            <CheckCircle2 className="h-5 w-5" aria-hidden />
            <span>
              Service <strong>{result.service}</strong> is {result.status}.
            </span>
          </div>
        ) : (
          <div className="flex items-center gap-2 text-destructive">
            <XCircle className="h-5 w-5" aria-hidden />
            <span>
              {result?.state === "error" ? result.message : "Unable to reach EKCP."}
            </span>
          </div>
        )}
      </CardContent>
      <CardFooter>
        <Button variant="outline" onClick={() => void probe()} disabled={isLoading}>
          <RefreshCw className="h-4 w-4" aria-hidden />
          Re-check
        </Button>
      </CardFooter>
    </Card>
  );
}
