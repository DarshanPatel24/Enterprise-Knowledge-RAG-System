"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";

import {
  useChatSessions,
  type ConversationRuntime,
} from "@/lib/hooks/useChatSessions";
import {
  createConversation,
  deleteConversation,
  listConversations,
  type StoredConversation,
} from "@/lib/conversations";

/** Value exposed by the app-wide chat sessions context. */
export type ChatSessionsContextValue = {
  conversations: StoredConversation[];
  activeId: string | null;
  mounted: boolean;
  getRuntime: (id: string) => ConversationRuntime;
  sendMessage: (id: string, text: string) => Promise<void>;
  stop: (id: string) => void;
  selectConversation: (id: string) => void;
  newConversation: () => void;
  removeConversation: (id: string) => void;
};

const ChatSessionsContext = createContext<ChatSessionsContextValue | null>(null);

/** localStorage key remembering the last-active conversation across navigations. */
const ACTIVE_KEY = "ekrag.activeConversation.v1";

/**
 * App-wide chat store mounted in the root layout, ABOVE every route.
 *
 * Because it lives above the router it is never unmounted by client navigation
 * (opening Settings, Home, or any other page), so in-flight streams keep running
 * in the background and their transcripts are preserved. The active conversation
 * is remembered in `localStorage` so returning to the chat restores the same
 * conversation and its live state.
 */
export function ChatSessionsProvider({
  children,
}: {
  children: ReactNode;
}): React.JSX.Element {
  const [conversations, setConversations] = useState<StoredConversation[]>([]);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [mounted, setMounted] = useState(false);

  const refreshConversations = useCallback((): void => {
    setConversations(listConversations());
  }, []);

  const { ensure, getRuntime, sendMessage, stop } = useChatSessions({
    onPersisted: refreshConversations,
  });

  useEffect(() => {
    const existing = listConversations();
    const savedActive =
      typeof window !== "undefined"
        ? window.localStorage.getItem(ACTIVE_KEY)
        : null;
    if (existing.length === 0) {
      const created = createConversation();
      setConversations([created]);
      setActiveId(created.id);
    } else {
      setConversations(existing);
      const active =
        savedActive && existing.some((c) => c.id === savedActive)
          ? savedActive
          : (existing[0]?.id ?? null);
      setActiveId(active);
    }
    setMounted(true);
  }, []);

  // Seed the active conversation's transcript into the store when it changes,
  // and remember it so navigation and reloads restore the same conversation.
  useEffect(() => {
    if (!activeId) {
      return;
    }
    ensure(activeId);
    if (typeof window !== "undefined") {
      window.localStorage.setItem(ACTIVE_KEY, activeId);
    }
  }, [activeId, ensure]);

  const selectConversation = useCallback((id: string): void => {
    setActiveId(id);
  }, []);

  const newConversation = useCallback((): void => {
    const created = createConversation();
    setConversations(listConversations());
    setActiveId(created.id);
  }, []);

  const removeConversation = useCallback(
    (id: string): void => {
      stop(id);
      const remaining = deleteConversation(id);
      const next = remaining[0];
      if (!next) {
        const created = createConversation();
        setConversations([created]);
        setActiveId(created.id);
        return;
      }
      setConversations(remaining);
      setActiveId((current) => (current === id ? next.id : current));
    },
    [stop],
  );

  const value: ChatSessionsContextValue = {
    conversations,
    activeId,
    mounted,
    getRuntime,
    sendMessage,
    stop,
    selectConversation,
    newConversation,
    removeConversation,
  };

  return (
    <ChatSessionsContext.Provider value={value}>
      {children}
    </ChatSessionsContext.Provider>
  );
}

/** Consume the app-wide chat sessions store. */
export function useChatSessionsContext(): ChatSessionsContextValue {
  const context = useContext(ChatSessionsContext);
  if (context === null) {
    throw new Error(
      "useChatSessionsContext must be used within a ChatSessionsProvider",
    );
  }
  return context;
}
