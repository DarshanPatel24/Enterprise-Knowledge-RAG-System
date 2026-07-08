"use client";

import { useState, type FormEvent, type KeyboardEvent } from "react";
import { Send, Square } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";

/**
 * Chat composer with submit-on-Enter (Shift+Enter inserts a newline) and a
 * send button. While a response is streaming, the send action switches to a
 * stop control and the textarea is disabled.
 */
export function ChatInput({
  onSend,
  onStop,
  isStreaming,
  disabled = false,
}: {
  onSend: (text: string) => void;
  onStop: () => void;
  isStreaming: boolean;
  disabled?: boolean;
}): React.JSX.Element {
  const [value, setValue] = useState("");

  const submit = (): void => {
    const text = value.trim();
    if (!text || isStreaming || disabled) {
      return;
    }
    onSend(text);
    setValue("");
  };

  const handleSubmit = (event: FormEvent): void => {
    event.preventDefault();
    submit();
  };

  const handleKeyDown = (event: KeyboardEvent<HTMLTextAreaElement>): void => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      submit();
    }
  };

  return (
    <form onSubmit={handleSubmit} className="flex items-end gap-2 border-t p-4">
      <Textarea
        value={value}
        onChange={(event) => setValue(event.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={disabled ? "Configure a tenant to start chatting…" : "Send a message…"}
        rows={1}
        disabled={isStreaming || disabled}
        aria-label="Message"
        className="max-h-40 resize-none"
      />
      {isStreaming ? (
        <Button type="button" variant="secondary" onClick={onStop} aria-label="Stop">
          <Square className="h-4 w-4" aria-hidden />
          Stop
        </Button>
      ) : (
        <Button type="submit" disabled={!value.trim() || disabled} aria-label="Send">
          <Send className="h-4 w-4" aria-hidden />
          Send
        </Button>
      )}
    </form>
  );
}
