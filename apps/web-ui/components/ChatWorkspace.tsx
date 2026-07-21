"use client";

import { useCallback } from "react";
import Link from "next/link";
import { AlertTriangle, Settings } from "lucide-react";

import { ChatPanel } from "@/components/ChatPanel";
import { ConversationList } from "@/components/ConversationList";
import { Button } from "@/components/ui/button";
import { useSettings } from "@/lib/hooks/useSettings";
import { useChatSessionsContext } from "@/components/ChatSessionsProvider";
import { isConfigured, missingRequiredFields } from "@/lib/settings";

/**
 * Full chat workspace: conversation sidebar, configuration gate, and the chat
 * panel.
 *
 * Streaming is owned by the app-wide `ChatSessionsProvider` (mounted in the root
 * layout, above the router), so neither switching conversations NOR navigating
 * to another route (Settings, etc.) aborts or discards an in-flight response: it
 * keeps generating in the background and the transcript is preserved. This
 * component is a controlled view of that store. Chat is disabled until the
 * required settings (tenant, API key, user) are present.
 */
export function ChatWorkspace(): React.JSX.Element {
  const settings = useSettings();
  const configured = isConfigured(settings);
  const missing = missingRequiredFields(settings);

  const {
    conversations,
    activeId,
    mounted,
    getRuntime,
    sendMessage,
    stop,
    selectConversation,
    newConversation,
    removeConversation,
  } = useChatSessionsContext();

  const handleDelete = useCallback(
    (id: string): void => {
      if (
        typeof window !== "undefined" &&
        !window.confirm("Delete this conversation? This cannot be undone.")
      ) {
        return;
      }
      removeConversation(id);
    },
    [removeConversation],
  );

  const runtime = activeId ? getRuntime(activeId) : null;

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
          onSelect={selectConversation}
          onNew={newConversation}
          onDelete={handleDelete}
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

        {mounted && activeId && runtime ? (
          <ChatPanel
            messages={runtime.messages}
            isStreaming={runtime.isStreaming}
            error={runtime.error}
            onSend={(text) => void sendMessage(activeId, text)}
            onStop={() => stop(activeId)}
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
