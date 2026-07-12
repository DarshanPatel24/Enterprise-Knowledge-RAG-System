import { AlertCircle } from "lucide-react";

import { AgentActivity } from "@/components/AgentActivity";
import { CitationCard } from "@/components/CitationCard";
import { MarkdownContent } from "@/components/MarkdownContent";
import { cn } from "@/lib/utils";
import { classifyResponseType } from "@/lib/responseType";
import type { ChatMessage as ChatMessageModel, ResponseType } from "@/lib/api/types";

const RESPONSE_TYPE_LABELS: Record<ResponseType, string> = {
  conversational: "Conversational",
  structured: "Structured",
  markdown: "Markdown",
  table: "Table",
  list: "List",
};

/** Right-aligned user message bubble (plain text). */
function UserBubble({ content }: { content: string }): React.JSX.Element {
  return (
    <div className="flex w-full justify-end">
      <div className="max-w-[80%] whitespace-pre-wrap break-words rounded-lg bg-primary px-4 py-2 text-sm text-primary-foreground">
        {content}
      </div>
    </div>
  );
}

/**
 * Left-aligned assistant message: a reasoning indicator before the first token,
 * Markdown-rendered content, a response-type label, and source citation cards.
 */
function AssistantBubble({
  message,
}: {
  message: ChatMessageModel;
}): React.JSX.Element {
  const isThinking = message.status === "streaming" && message.content.length === 0;
  const responseType = classifyResponseType(message.content);

  return (
    <div className="flex w-full flex-col gap-2">
      <div
        className={cn(
          "max-w-[90%] break-words rounded-lg bg-muted px-4 py-2 text-foreground",
          message.status === "error" && "border border-destructive",
        )}
      >
        {isThinking ? (
          <AgentActivity label={message.stage} />
        ) : (
          <MarkdownContent content={message.content} />
        )}
        {message.status === "error" && (
          <span className="mt-1 flex items-center gap-1 text-xs text-destructive">
            <AlertCircle className="h-3.5 w-3.5" aria-hidden />
            Response failed
          </span>
        )}
      </div>

      {message.status === "complete" && message.content.length > 0 && (
        <span className="ml-1 w-fit rounded-full border px-2 py-0.5 text-xs text-muted-foreground">
          {RESPONSE_TYPE_LABELS[responseType]}
        </span>
      )}

      {message.citations.length > 0 && (
        <div className="flex flex-col gap-2">
          <span className="ml-1 text-xs font-medium text-muted-foreground">
            Sources ({message.citations.length})
          </span>
          <div className="grid gap-2 sm:grid-cols-2">
            {message.citations.map((citation) => (
              <CitationCard
                key={`${citation.documentId}:${citation.chunkId}`}
                citation={citation}
              />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

/** Render a single chat message according to its author role. */
export function ChatMessage({
  message,
}: {
  message: ChatMessageModel;
}): React.JSX.Element {
  return (
    <div data-role={message.role} data-status={message.status}>
      {message.role === "user" ? (
        <UserBubble content={message.content} />
      ) : (
        <AssistantBubble message={message} />
      )}
    </div>
  );
}
