"use client";

import { MessageSquare, Plus } from "lucide-react";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import type { StoredConversation } from "@/lib/conversations";

/** Format a timestamp as a short local date-time. */
function formatTimestamp(value: number): string {
  return new Date(value).toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

/**
 * Sidebar list of stored conversations with a "new conversation" action.
 *
 * The active conversation is highlighted; selecting an entry loads its stored
 * transcript. The list is passed in already sorted (newest first).
 */
export function ConversationList({
  conversations,
  activeId,
  onSelect,
  onNew,
}: {
  conversations: StoredConversation[];
  activeId: string | null;
  onSelect: (id: string) => void;
  onNew: () => void;
}): React.JSX.Element {
  return (
    <div className="flex h-full flex-col gap-2 p-2">
      <Button onClick={onNew} className="w-full justify-start">
        <Plus className="h-4 w-4" aria-hidden />
        New conversation
      </Button>
      <nav className="flex-1 space-y-1 overflow-y-auto" aria-label="Conversations">
        {conversations.length === 0 ? (
          <p className="px-2 py-4 text-center text-xs text-muted-foreground">
            No conversations yet.
          </p>
        ) : (
          conversations.map((conversation) => (
            <button
              key={conversation.id}
              type="button"
              onClick={() => onSelect(conversation.id)}
              className={cn(
                "flex w-full flex-col gap-0.5 rounded-md px-2 py-2 text-left text-sm transition-colors hover:bg-accent",
                conversation.id === activeId && "bg-accent",
              )}
              aria-current={conversation.id === activeId}
            >
              <span className="flex items-center gap-2 truncate font-medium">
                <MessageSquare
                  className="h-3.5 w-3.5 shrink-0 text-muted-foreground"
                  aria-hidden
                />
                <span className="truncate">{conversation.title}</span>
              </span>
              <span className="pl-5 text-xs text-muted-foreground">
                {formatTimestamp(conversation.updatedAt)}
              </span>
            </button>
          ))
        )}
      </nav>
    </div>
  );
}
