"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { AlertTriangle, Settings } from "lucide-react";

import { ChatPanel } from "@/components/ChatPanel";
import { ConversationList } from "@/components/ConversationList";
import { Button } from "@/components/ui/button";
import { useSettings } from "@/lib/hooks/useSettings";
import { isConfigured, missingRequiredFields } from "@/lib/settings";
import {
  createConversation,
  listConversations,
  loadMessages,
  saveMessages,
  type StoredConversation,
} from "@/lib/conversations";
import type { ChatMessage } from "@/lib/api/types";

/**
 * Full chat workspace: conversation sidebar, configuration gate, and the keyed
 * streaming chat panel.
 *
 * Conversations and their transcripts are persisted to `localStorage`; the panel
 * is remounted on conversation switch to seed the stored transcript. Chat is
 * disabled until the required settings (tenant, API key, user) are present.
 */
export function ChatWorkspace(): React.JSX.Element {
  const settings = useSettings();
  const configured = isConfigured(settings);
  const missing = missingRequiredFields(settings);

  const [mounted, setMounted] = useState(false);
  const [conversations, setConversations] = useState<StoredConversation[]>([]);
  const [activeId, setActiveId] = useState<string | null>(null);

  useEffect(() => {
    const existing = listConversations();
    if (existing.length === 0) {
      const created = createConversation();
      setConversations([created]);
      setActiveId(created.id);
    } else {
      setConversations(existing);
      setActiveId(existing[0]?.id ?? null);
    }
    setMounted(true);
  }, []);

  const handleNew = useCallback((): void => {
    const created = createConversation();
    setConversations(listConversations());
    setActiveId(created.id);
  }, []);

  const handleSelect = useCallback((id: string): void => {
    setActiveId(id);
  }, []);

  const handlePersist = useCallback(
    (id: string, messages: ChatMessage[]): void => {
      if (messages.length === 0) {
        return;
      }
      setConversations(saveMessages(id, messages));
    },
    [],
  );

  return (
    <div className="flex h-screen">
      <aside className="flex w-64 shrink-0 flex-col border-r">
        <div className="border-b px-3 py-3">
          <Link href="/" className="text-sm font-semibold tracking-tight">
            EK-RAG Console
          </Link>
        </div>
        <ConversationList
          conversations={conversations}
          activeId={activeId}
          onSelect={handleSelect}
          onNew={handleNew}
        />
        <div className="border-t p-2">
          <Button asChild variant="ghost" size="sm" className="w-full justify-start">
            <Link href="/settings">
              <Settings className="h-4 w-4" aria-hidden />
              Settings
            </Link>
          </Button>
        </div>
      </aside>

      <main className="flex min-w-0 flex-1 flex-col">
        {!configured && (
          <div
            role="alert"
            className="flex items-center gap-2 border-b border-clearance-confidential/40 bg-clearance-confidential/10 px-4 py-2 text-sm"
          >
            <AlertTriangle
              className="h-4 w-4 shrink-0 text-clearance-confidential"
              aria-hidden
            />
            <span>
              Configuration required: {missing.join(", ")} not set.{" "}
              <Link href="/settings" className="font-medium underline underline-offset-2">
                Open settings
              </Link>
              .
            </span>
          </div>
        )}

        {mounted && activeId ? (
          <ChatPanel
            key={activeId}
            initialMessages={loadMessages(activeId)}
            onMessagesChange={(messages) => handlePersist(activeId, messages)}
            disabled={!configured}
          />
        ) : (
          <div className="flex flex-1 items-center justify-center text-sm text-muted-foreground">
            Loading conversations…
          </div>
        )}
      </main>
    </div>
  );
}
