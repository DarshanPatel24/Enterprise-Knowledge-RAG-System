import type { ResponseType } from "@/lib/api/types";

const TABLE_SEPARATOR = /^\s*\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)+\|?\s*$/m;
const CODE_FENCE = /```/;
const LIST_ITEM = /^\s*([-*+]|\d+\.)\s+/gm;
const MARKDOWN_MARKS = /(^|\n)#{1,6}\s|\*\*[^*]+\*\*|\[[^\]]+\]\([^)]+\)/;

/**
 * Classify an assistant response into a display label from its content.
 *
 * EKCP does not carry a response type on the chat stream, so the label is
 * derived client-side. Precedence: table, structured (code), list, markdown,
 * then conversational as the default.
 */
export function classifyResponseType(content: string): ResponseType {
  if (TABLE_SEPARATOR.test(content)) {
    return "table";
  }
  if (CODE_FENCE.test(content)) {
    return "structured";
  }
  const listMatches = content.match(LIST_ITEM);
  if (listMatches && listMatches.length >= 2) {
    return "list";
  }
  if (MARKDOWN_MARKS.test(content)) {
    return "markdown";
  }
  return "conversational";
}
