import { FileText } from "lucide-react";

import { ClearanceBadge } from "@/components/ClearanceBadge";
import type { Citation } from "@/lib/api/types";

/** Format a 0..1 confidence score as a whole-number percentage. */
function formatConfidence(confidence: number): string {
  const bounded = Math.max(0, Math.min(1, confidence));
  return `${Math.round(bounded * 100)}%`;
}

/**
 * Source citation card showing the document name, the section it came from, a
 * readable snippet of the cited text, the relevance score, and the
 * classification clearance badge for a single retrieved source.
 */
export function CitationCard({ citation }: { citation: Citation }): React.JSX.Element {
  return (
    <div className="rounded-md border bg-card p-3 text-card-foreground shadow-sm">
      <div className="flex items-start justify-between gap-2">
        <div className="flex min-w-0 items-center gap-2">
          <FileText className="h-4 w-4 shrink-0 text-muted-foreground" aria-hidden />
          <span className="truncate text-sm font-medium" title={citation.sourcePath || citation.title}>
            {citation.title}
          </span>
        </div>
        <ClearanceBadge clearance={citation.clearance} />
      </div>
      {citation.sectionTitle && (
        <p className="mt-1 truncate text-xs font-medium text-foreground/80" title={citation.sectionTitle}>
          Section: {citation.sectionTitle}
        </p>
      )}
      {citation.snippet && (
        <p className="mt-1 line-clamp-3 text-xs text-muted-foreground">{citation.snippet}</p>
      )}
      <div
        className="mt-2 flex items-center gap-1 text-xs text-muted-foreground"
        title={citation.explanation || undefined}
      >
        <span className="font-medium text-foreground">
          {formatConfidence(citation.confidence)}
        </span>
        <span>relevance</span>
      </div>
    </div>
  );
}
