"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import { chatStream, readSseStream } from "@/lib/api/ekcp";
import type { ChatMessage, Citation } from "@/lib/api/types";
import { loadMessages, saveMessages } from "@/lib/conversations";
import { generateUuid } from "@/lib/utils";

/** Live runtime state for a single conversation. */
export type ConversationRuntime = {
  messages: ChatMessage[];
  isStreaming: boolean;
  error: string | null;
};

/** Public surface of the multi-conversation chat store. */
export type UseChatSessions = {
  /** Seed a conversation's runtime from persisted storage if not already loaded. */
  ensure: (id: string) => void;
  /** Return the live runtime for a conversation (empty when unknown). */
  getRuntime: (id: string) => ConversationRuntime;
  /** Send a message and stream the response into the given conversation. */
  sendMessage: (id: string, text: string) => Promise<void>;
  /** Abort the in-flight stream for a conversation, if any. */
  stop: (id: string) => void;
};

/** Options controlling the chat sessions store. */
export type UseChatSessionsOptions = {
  /** Called after a conversation's settled transcript is persisted. */
  onPersisted?: (id: string) => void;
};

const EMPTY_RUNTIME: ConversationRuntime = {
  messages: [],
  isStreaming: false,
  error: null,
};

/**
 * Workspace-level store that owns streaming for every conversation at once.
 *
 * Streams live here, above the conversation switcher, so selecting another
 * conversation never aborts or discards an in-flight response: the request keeps
 * running in the background and its partial transcript is preserved in memory.
 * Returning to a conversation renders its current live state. Each conversation
 * has an independent stream, abort controller, and EKCP session id, so several
 * responses can generate concurrently. Settled transcripts are persisted to
 * ``localStorage`` for durability across reloads.
 */
export function useChatSessions(
  options: UseChatSessionsOptions = {},
): UseChatSessions {
  const { onPersisted } = options;
  const [runtimes, setRuntimes] = useState<Record<string, ConversationRuntime>>(
    {},
  );

  // Non-render state, keyed by conversation id.
  const abortsRef = useRef<Record<string, AbortController>>({});
  const sessionIdsRef = useRef<Record<string, string>>({});
  const streamingRef = useRef<Record<string, boolean>>({});
  const prevStreamingRef = useRef<Record<string, boolean>>({});
  const persistedRef = useRef(onPersisted);
  // Mirror of the latest runtimes so sendMessage can read the current transcript
  // (for conversation history) without depending on it and going stale.
  const runtimesRef = useRef(runtimes);

  useEffect(() => {
    runtimesRef.current = runtimes;
  }, [runtimes]);

  useEffect(() => {
    persistedRef.current = onPersisted;
  });

  // Persist a conversation only as it settles (streaming -> idle), mirroring the
  // "save on turn completion" contract and keeping token appends out of storage.
  useEffect(() => {
    for (const [id, runtime] of Object.entries(runtimes)) {
      const wasStreaming = prevStreamingRef.current[id] ?? false;
      if (wasStreaming && !runtime.isStreaming && runtime.messages.length > 0) {
        saveMessages(id, runtime.messages);
        persistedRef.current?.(id);
      }
      prevStreamingRef.current[id] = runtime.isStreaming;
    }
  }, [runtimes]);

  const patch = useCallback(
    (
      id: string,
      updater: (runtime: ConversationRuntime) => ConversationRuntime,
    ): void => {
      setRuntimes((prev) => ({
        ...prev,
        [id]: updater(prev[id] ?? EMPTY_RUNTIME),
      }));
    },
    [],
  );

  const mapMessages = useCallback(
    (
      id: string,
      assistantId: string,
      updater: (message: ChatMessage) => ChatMessage,
    ): void => {
      patch(id, (runtime) => ({
        ...runtime,
        messages: runtime.messages.map((message) =>
          message.id === assistantId ? updater(message) : message,
        ),
      }));
    },
    [patch],
  );

  const ensure = useCallback((id: string): void => {
    setRuntimes((prev) =>
      prev[id]
        ? prev
        : {
            ...prev,
            [id]: {
              messages: loadMessages(id),
              isStreaming: false,
              error: null,
            },
          },
    );
  }, []);

  const getRuntime = useCallback(
    (id: string): ConversationRuntime => runtimes[id] ?? EMPTY_RUNTIME,
    [runtimes],
  );

  const sendMessage = useCallback(
    async (id: string, text: string): Promise<void> => {
      const trimmed = text.trim();
      if (!trimmed || streamingRef.current[id]) {
        return;
      }
      streamingRef.current[id] = true;

      // Build the conversation history (settled prior turns) so EKCP can answer
      // follow-up questions in context. Read from the live transcript, falling
      // back to persisted storage for a conversation not yet in memory.
      const priorMessages =
        runtimesRef.current[id]?.messages ?? loadMessages(id);
      const history = priorMessages
        .filter(
          (message) =>
            (message.role === "user" || message.role === "assistant") &&
            message.status !== "streaming" &&
            message.content.trim().length > 0,
        )
        .slice(-8)
        .map((message) => ({
          role: message.role as "user" | "assistant",
          content: message.content,
        }));

      const assistantId = generateUuid();
      const userMessage: ChatMessage = {
        id: generateUuid(),
        role: "user",
        content: trimmed,
        status: "complete",
        citations: [],
      };
      const assistantMessage: ChatMessage = {
        id: assistantId,
        role: "assistant",
        content: "",
        status: "streaming",
        citations: [],
      };

      // Seed from storage if this conversation has not been loaded yet, then
      // append the new turn and mark the conversation as streaming.
      setRuntimes((prev) => {
        const base = prev[id] ?? {
          messages: loadMessages(id),
          isStreaming: false,
          error: null,
        };
        return {
          ...prev,
          [id]: {
            messages: [...base.messages, userMessage, assistantMessage],
            isStreaming: true,
            error: null,
          },
        };
      });

      const controller = new AbortController();
      abortsRef.current[id] = controller;
      const citationBuffer: Citation[] = [];

      try {
        const response = await chatStream(trimmed, {
          sessionId: sessionIdsRef.current[id],
          signal: controller.signal,
          history,
        });
        if (!response.ok) {
          const detail = await response.text().catch(() => "");
          throw new Error(
            detail || `EKCP chat stream failed with HTTP ${response.status}`,
          );
        }

        for await (const event of readSseStream(response)) {
          if (event.type === "token") {
            mapMessages(id, assistantId, (message) => ({
              ...message,
              content: message.content + event.text,
            }));
          } else if (event.type === "citation") {
            citationBuffer.push(event.citation);
          } else if (event.type === "stage") {
            mapMessages(id, assistantId, (message) => ({
              ...message,
              stage: event.label,
            }));
          } else if (event.type === "done") {
            if (event.done.sessionId) {
              sessionIdsRef.current[id] = event.done.sessionId;
            }
            mapMessages(id, assistantId, (message) => ({
              ...message,
              status: "complete",
              stage: undefined,
              citations: [...citationBuffer],
            }));
          } else if (event.type === "error") {
            patch(id, (runtime) => ({ ...runtime, error: event.message }));
            mapMessages(id, assistantId, (message) => ({
              ...message,
              status: "error",
              stage: undefined,
            }));
          }
        }
      } catch (cause) {
        if (cause instanceof DOMException && cause.name === "AbortError") {
          mapMessages(id, assistantId, (message) => ({
            ...message,
            status: "complete",
            stage: undefined,
          }));
        } else {
          const message =
            cause instanceof Error ? cause.message : "Unknown streaming error";
          patch(id, (runtime) => ({ ...runtime, error: message }));
          mapMessages(id, assistantId, (msg) => ({
            ...msg,
            status: "error",
            stage: undefined,
          }));
        }
      } finally {
        streamingRef.current[id] = false;
        delete abortsRef.current[id];
        patch(id, (runtime) => ({ ...runtime, isStreaming: false }));
      }
    },
    [mapMessages, patch],
  );

  const stop = useCallback((id: string): void => {
    abortsRef.current[id]?.abort();
  }, []);

  return { ensure, getRuntime, sendMessage, stop };
}
