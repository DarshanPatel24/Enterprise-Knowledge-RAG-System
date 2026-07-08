"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import { chatStream, readSseStream } from "@/lib/api/ekcp";
import type { ChatMessage, Citation } from "@/lib/api/types";
import { generateUuid } from "@/lib/utils";

/** Public surface of the chat streaming hook. */
export type UseChatStream = {
  messages: ChatMessage[];
  isStreaming: boolean;
  error: string | null;
  sendMessage: (text: string) => Promise<void>;
  stop: () => void;
};

/** Options controlling the chat stream hook. */
export type UseChatStreamOptions = {
  initialMessages?: ChatMessage[];
  onMessagesChange?: (messages: ChatMessage[]) => void;
};

function createId(): string {
  return generateUuid();
}

/**
 * Manage a single streaming chat conversation against EKCP.
 *
 * Owns transcript state, the streaming flag, and the terminal error. Consumes
 * the SSE stream via the centralised client, appending `token` fragments to the
 * in-flight assistant message and finalising on `done`. A new stream never
 * starts while one is active; unmounting aborts the current stream.
 *
 * `initialMessages` seeds a previously persisted transcript; `onMessagesChange`
 * fires when a turn settles (not on every token) so callers can persist state.
 */
export function useChatStream(options: UseChatStreamOptions = {}): UseChatStream {
  const { initialMessages, onMessagesChange } = options;
  const [messages, setMessages] = useState<ChatMessage[]>(initialMessages ?? []);
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const abortRef = useRef<AbortController | null>(null);
  const sessionIdRef = useRef<string | undefined>(undefined);
  const streamingRef = useRef(false);
  const changeRef = useRef(onMessagesChange);
  const initializedRef = useRef(false);

  // Keep the latest callback in a ref without touching refs during render.
  useEffect(() => {
    changeRef.current = onMessagesChange;
  });

  // Persist settled turns (not intermediate token appends) via the callback.
  // Skips the initial mount so seeding a stored transcript does not re-save it.
  useEffect(() => {
    if (!initializedRef.current) {
      initializedRef.current = true;
      return;
    }
    if (!isStreaming) {
      changeRef.current?.(messages);
    }
  }, [messages, isStreaming]);

  const finalizeAssistant = useCallback(
    (id: string, status: ChatMessage["status"]): void => {
      setMessages((prev) =>
        prev.map((message) =>
          message.id === id ? { ...message, status } : message,
        ),
      );
    },
    [],
  );

  const sendMessage = useCallback(
    async (text: string): Promise<void> => {
      const trimmed = text.trim();
      if (!trimmed || streamingRef.current) {
        return;
      }

      streamingRef.current = true;
      setIsStreaming(true);
      setError(null);

      const userMessage: ChatMessage = {
        id: createId(),
        role: "user",
        content: trimmed,
        status: "complete",
        citations: [],
      };
      const assistantId = createId();
      const assistantMessage: ChatMessage = {
        id: assistantId,
        role: "assistant",
        content: "",
        status: "streaming",
        citations: [],
      };
      setMessages((prev) => [...prev, userMessage, assistantMessage]);

      const controller = new AbortController();
      abortRef.current = controller;
      const citationBuffer: Citation[] = [];

      try {
        const response = await chatStream(trimmed, {
          sessionId: sessionIdRef.current,
          signal: controller.signal,
        });
        if (!response.ok) {
          const detail = await response.text().catch(() => "");
          throw new Error(
            detail || `EKCP chat stream failed with HTTP ${response.status}`,
          );
        }

        for await (const event of readSseStream(response)) {
          if (event.type === "token") {
            setMessages((prev) =>
              prev.map((message) =>
                message.id === assistantId
                  ? { ...message, content: message.content + event.text }
                  : message,
              ),
            );
          } else if (event.type === "citation") {
            citationBuffer.push(event.citation);
          } else if (event.type === "done") {
            sessionIdRef.current = event.done.sessionId || sessionIdRef.current;
            setMessages((prev) =>
              prev.map((message) =>
                message.id === assistantId
                  ? {
                      ...message,
                      status: "complete",
                      citations: [...citationBuffer],
                    }
                  : message,
              ),
            );
          } else {
            setError(event.message);
            finalizeAssistant(assistantId, "error");
          }
        }
      } catch (cause) {
        if (cause instanceof DOMException && cause.name === "AbortError") {
          finalizeAssistant(assistantId, "complete");
        } else {
          const message =
            cause instanceof Error ? cause.message : "Unknown streaming error";
          setError(message);
          finalizeAssistant(assistantId, "error");
        }
      } finally {
        streamingRef.current = false;
        setIsStreaming(false);
        abortRef.current = null;
      }
    },
    [finalizeAssistant],
  );

  const stop = useCallback((): void => {
    abortRef.current?.abort();
  }, []);

  useEffect(() => {
    return () => {
      abortRef.current?.abort();
    };
  }, []);

  return { messages, isStreaming, error, sendMessage, stop };
}
