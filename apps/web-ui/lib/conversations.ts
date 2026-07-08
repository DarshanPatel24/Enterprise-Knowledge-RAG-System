/**
 * Local-first conversation store, persisted to `localStorage` only.
 *
 * Holds the conversation index (id, title, timestamps) and each conversation's
 * message transcript. This is the source of truth for the session list and for
 * loading past conversations across page reloads. No conversation data leaves
 * the browser.
 *
 * When EKCP exposes a conversation history endpoint, the index can be hydrated
 * from it; until then this local store keeps the UI self-sufficient.
 */

import type { ChatMessage } from "@/lib/api/types";
import { generateUuid } from "@/lib/utils";

export type StoredConversation = {
  id: string;
  title: string;
  createdAt: number;
  updatedAt: number;
};

const INDEX_KEY = "ekrag.conversations.v1";
const MESSAGES_PREFIX = "ekrag.conversation.";
const DEFAULT_TITLE = "New conversation";
const TITLE_MAX_LENGTH = 60;

function hasStorage(): boolean {
  return typeof window !== "undefined";
}

function messagesKey(id: string): string {
  return `${MESSAGES_PREFIX}${id}.messages.v1`;
}

/** Load the conversation index, newest first. */
export function listConversations(): StoredConversation[] {
  if (!hasStorage()) {
    return [];
  }
  try {
    const raw = window.localStorage.getItem(INDEX_KEY);
    if (!raw) {
      return [];
    }
    const parsed = JSON.parse(raw) as StoredConversation[];
    return [...parsed].sort((a, b) => b.updatedAt - a.updatedAt);
  } catch {
    return [];
  }
}

function writeIndex(conversations: StoredConversation[]): void {
  if (hasStorage()) {
    window.localStorage.setItem(INDEX_KEY, JSON.stringify(conversations));
  }
}

/** Create a new empty conversation and persist it to the index. */
export function createConversation(): StoredConversation {
  const now = Date.now();
  const conversation: StoredConversation = {
    id: generateUuid(),
    title: DEFAULT_TITLE,
    createdAt: now,
    updatedAt: now,
  };
  writeIndex([conversation, ...listConversations()]);
  return conversation;
}

/** Load the transcript for a conversation. */
export function loadMessages(id: string): ChatMessage[] {
  if (!hasStorage()) {
    return [];
  }
  try {
    const raw = window.localStorage.getItem(messagesKey(id));
    return raw ? (JSON.parse(raw) as ChatMessage[]) : [];
  } catch {
    return [];
  }
}

/** Derive a conversation title from the first user message. */
export function deriveTitle(messages: ChatMessage[]): string {
  const firstUser = messages.find((message) => message.role === "user");
  if (!firstUser) {
    return DEFAULT_TITLE;
  }
  const text = firstUser.content.trim().replace(/\s+/g, " ");
  return text.length > TITLE_MAX_LENGTH
    ? `${text.slice(0, TITLE_MAX_LENGTH)}…`
    : text;
}

/**
 * Persist a conversation's transcript and update its index entry (title from the
 * first user message, `updatedAt` timestamp). Returns the refreshed index.
 */
export function saveMessages(
  id: string,
  messages: ChatMessage[],
): StoredConversation[] {
  if (hasStorage()) {
    window.localStorage.setItem(messagesKey(id), JSON.stringify(messages));
  }
  const conversations = listConversations();
  const existing = conversations.find((conversation) => conversation.id === id);
  const title = deriveTitle(messages);
  const now = Date.now();
  const updated: StoredConversation = existing
    ? { ...existing, title, updatedAt: now }
    : { id, title, createdAt: now, updatedAt: now };
  const next = [updated, ...conversations.filter((c) => c.id !== id)];
  writeIndex(next);
  return next.sort((a, b) => b.updatedAt - a.updatedAt);
}

/** Remove a conversation and its transcript. */
export function deleteConversation(id: string): StoredConversation[] {
  if (hasStorage()) {
    window.localStorage.removeItem(messagesKey(id));
  }
  const next = listConversations().filter((conversation) => conversation.id !== id);
  writeIndex(next);
  return next;
}
