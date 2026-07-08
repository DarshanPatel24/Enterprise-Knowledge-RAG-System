"use client";

import { useEffect, useRef } from "react";

import { ChatMessage } from "@/components/ChatMessage";
import type { ChatMessage as ChatMessageModel } from "@/lib/api/types";

/**
 * Scrollable transcript of chat messages with auto-scroll to the latest entry.
 *
 * Auto-scroll re-runs whenever the message list changes (including streaming
 * token appends), keeping the newest content in view.
 */
export function MessageList({
  messages,
}: {
  messages: ChatMessageModel[];
}): React.JSX.Element {
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages]);

  if (messages.length === 0) {
    return (
      <div className="flex flex-1 items-center justify-center text-center text-muted-foreground">
        <p>Ask a question to start the conversation.</p>
      </div>
    );
  }

  return (
    <div className="flex flex-1 flex-col gap-3 overflow-y-auto p-4">
      {messages.map((message) => (
        <ChatMessage key={message.id} message={message} />
      ))}
      <div ref={endRef} />
    </div>
  );
}
