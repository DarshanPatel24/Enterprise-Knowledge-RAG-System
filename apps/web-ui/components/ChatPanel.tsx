"use client";

import { AlertCircle } from "lucide-react";

import { ChatInput } from "@/components/ChatInput";
import { MessageList } from "@/components/MessageList";
import { useChatStream } from "@/lib/hooks/useChatStream";
import type { ChatMessage } from "@/lib/api/types";

/**
 * Core streaming chat experience: transcript, composer, and error banner.
 *
 * Streaming state lives entirely in the `useChatStream` hook; this component
 * renders it, forwards user actions, and persists settled turns via
 * `onMessagesChange`. Remount it (via a `key`) to switch conversations.
 */
export function ChatPanel({
  initialMessages,
  onMessagesChange,
  disabled = false,
}: {
  initialMessages: ChatMessage[];
  onMessagesChange: (messages: ChatMessage[]) => void;
  disabled?: boolean;
}): React.JSX.Element {
  const { messages, isStreaming, error, sendMessage, stop } = useChatStream({
    initialMessages,
    onMessagesChange,
  });

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
        onSend={(text) => void sendMessage(text)}
        onStop={stop}
        isStreaming={isStreaming}
        disabled={disabled}
      />
    </div>
  );
}
