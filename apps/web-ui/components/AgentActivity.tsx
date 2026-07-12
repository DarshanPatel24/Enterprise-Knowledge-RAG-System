import { Sparkles } from "lucide-react";

/**
 * Reasoning-in-progress indicator shown while EKCP is executing a pipeline
 * step before the first response token arrives. When a ``label`` is supplied it
 * shows the live stage (e.g. "Retrieving relevant documents").
 */
export function AgentActivity({ label }: { label?: string }): React.JSX.Element {
  return (
    <span className="flex items-center gap-2 text-muted-foreground" role="status">
      <Sparkles className="h-4 w-4 animate-pulse text-primary" aria-hidden />
      <span>{label ?? "Agent is reasoning\u2026"}</span>
    </span>
  );
}
