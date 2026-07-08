import { cn } from "@/lib/utils";
import type { ClassificationClearance } from "@/lib/api/types";

/**
 * Colour-coded classification clearance badge.
 *
 * Colours are semantically distinct and WCAG 2.1 AA compliant against white
 * text: public (green), internal (blue), confidential (amber), restricted (red).
 * Colours come from design tokens in `tailwind.config.ts`, never inline styles.
 */
const CLEARANCE_STYLES: Record<ClassificationClearance, string> = {
  public: "bg-clearance-public text-white",
  internal: "bg-clearance-internal text-white",
  confidential: "bg-clearance-confidential text-white",
  restricted: "bg-clearance-restricted text-white",
};

const CLEARANCE_LABELS: Record<ClassificationClearance, string> = {
  public: "Public",
  internal: "Internal",
  confidential: "Confidential",
  restricted: "Restricted",
};

export function ClearanceBadge({
  clearance,
  className,
}: {
  clearance: ClassificationClearance;
  className?: string;
}): React.JSX.Element {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2 py-0.5 text-xs font-semibold",
        CLEARANCE_STYLES[clearance],
        className,
      )}
      aria-label={`Classification: ${CLEARANCE_LABELS[clearance]}`}
    >
      {CLEARANCE_LABELS[clearance]}
    </span>
  );
}
