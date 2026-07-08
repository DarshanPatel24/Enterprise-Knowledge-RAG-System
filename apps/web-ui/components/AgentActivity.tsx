import { Sparkles } from "lucide-react";

/**
 * Reasoning-in-progress indicator shown while EKCP is executing a reasoning
 * step before the first response token arrives.
 */
export function AgentActivity(): React.JSX.Element {
  return (
    <span className="flex items-center gap-2 text-muted-foreground" role="status">
      <Sparkles className="h-4 w-4 animate-pulse text-primary" aria-hidden />
      <span>Agent is reasoning…</span>
    </span>
  );
}
