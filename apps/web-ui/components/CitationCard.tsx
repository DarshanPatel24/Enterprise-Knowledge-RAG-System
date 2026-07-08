import { FileText } from "lucide-react";

import { ClearanceBadge } from "@/components/ClearanceBadge";
import type { Citation } from "@/lib/api/types";

/** Format a 0..1 confidence score as a whole-number percentage. */
function formatConfidence(confidence: number): string {
  const bounded = Math.max(0, Math.min(1, confidence));
  return `${Math.round(bounded * 100)}%`;
}

/**
 * Source citation card showing title, source path, confidence, and the
 * classification clearance badge for a single retrieved source.
 */
export function CitationCard({ citation }: { citation: Citation }): React.JSX.Element {
  return (
    <div className="rounded-md border bg-card p-3 text-card-foreground shadow-sm">
      <div className="flex items-start justify-between gap-2">
        <div className="flex min-w-0 items-center gap-2">
          <FileText className="h-4 w-4 shrink-0 text-muted-foreground" aria-hidden />
          <span className="truncate text-sm font-medium">{citation.title}</span>
        </div>
        <ClearanceBadge clearance={citation.clearance} />
      </div>
      <p className="mt-1 truncate text-xs text-muted-foreground" title={citation.sourcePath}>
        {citation.sourcePath}
      </p>
      {citation.explanation && (
        <p className="mt-1 line-clamp-2 text-xs text-muted-foreground">
          {citation.explanation}
        </p>
      )}
      <div className="mt-2 flex items-center gap-1 text-xs text-muted-foreground">
        <span className="font-medium text-foreground">
          {formatConfidence(citation.confidence)}
        </span>
        <span>confidence</span>
      </div>
    </div>
  );
}
