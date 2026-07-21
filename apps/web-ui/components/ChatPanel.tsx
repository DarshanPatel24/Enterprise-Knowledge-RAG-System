"use client";

import { AlertCircle } from "lucide-react";

import { ChatInput } from "@/components/ChatInput";
import { MessageList } from "@/components/MessageList";
import type { ChatMessage } from "@/lib/api/types";

/**
 * Core streaming chat experience: transcript, composer, and error banner.
 *
 * This is a controlled view. Streaming state is owned by the workspace-level
 * chat store (`useChatSessions`) so a response keeps generating even when the
 * user switches to another conversation; this component only renders the active
 * conversation's runtime and forwards user actions. It must NOT be remounted on
 * conversation switch (no `key`) — the store keeps the underlying stream alive.
 */
export function ChatPanel({
  messages,
  isStreaming,
  error,
  onSend,
  onStop,
  disabled = false,
}: {
  messages: ChatMessage[];
  isStreaming: boolean;
  error: string | null;
  onSend: (text: string) => void;
  onStop: () => void;
  disabled?: boolean;
}): React.JSX.Element {
  return (
    <div className="flex h-full min-h-0 flex-1 flex-col">
      {error && (
        <div
          role="alert"
          className="flex items-center gap-2 border-b border-destructive/40 bg-destructive/10 px-4 py-2 text-sm text-destructive"
        >
          <AlertCircle className="h-4 w-4" aria-hidden />
          <span>{error}</span>
        </div>
      )}
      <MessageList messages={messages} />
      <ChatInput
        onSend={onSend}
        onStop={onStop}
        isStreaming={isStreaming}
        disabled={disabled}
      />
    </div>
  );
}
