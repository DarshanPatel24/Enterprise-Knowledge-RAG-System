/**
 * TypeScript shapes mirroring the EKCP API response models.
 *
 * These replicate the relevant `packages/contracts` Pydantic shapes. Python
 * runtime code is never imported; only the wire shape is mirrored here.
 */

/** Response from the EKCP `/health/live` and `/health/ready` endpoints. */
export type HealthResponse = {
  status: string;
  service: string;
};

/** Classification clearance levels recognised across EK-RAG. */
export type ClassificationClearance =
  | "public"
  | "internal"
  | "confidential"
  | "restricted";

/** Security context carried on governed EKCP requests (ingress gate). */
export type SecurityContext = {
  user_id: string;
  tenant_id: string;
  classification_clearance: ClassificationClearance;
};

/** Result of a client-side connectivity probe against the EKCP gateway. */
export type ConnectivityStatus =
  | { state: "ok"; service: string; status: string }
  | { state: "error"; message: string };

/** A prior conversation turn sent to EKCP so follow-up questions have context. */
export type ChatHistoryTurn = {
  role: "user" | "assistant";
  content: string;
};

/** Request body for the EKCP `POST /chat/stream` endpoint. */
export type ChatStreamRequest = {
  message: string;
  security_context: SecurityContext;
  session_id?: string;
  history?: ChatHistoryTurn[];
};

/** Terminal `done` payload carried on a successful chat stream completion. */
export type StreamDone = {
  sessionId: string;
  correlationId: string;
  finishReason: string;
  totalTokens: number;
  costEstimate: number;
};

/**
 * A source citation attached to an assistant response.
 *
 * Mirrors the EKRE citation contract (`source_path`, `document_id`, `chunk_id`)
 * enriched with the confidence score and classification clearance the card
 * renders. Python runtime code is never imported; only the wire shape is mirrored.
 */
export type Citation = {
  sourcePath: string;
  documentId: string;
  chunkId: string;
  title: string;
  sectionTitle: string;
  snippet: string;
  confidence: number;
  clearance: ClassificationClearance;
  explanation: string;
};

/**
 * A parsed Server-Sent Event frame from the EKCP chat stream.
 *
 * `token`/`done`/`error` drive the streaming response; `citation` frames are
 * buffered during the stream and attached to the assistant message on `done`.
 */
export type SseEvent =
  | { type: "token"; text: string }
  | { type: "citation"; citation: Citation }
  | { type: "stage"; key: string; label: string }
  | { type: "done"; done: StreamDone }
  | { type: "error"; errorType: string; message: string };

/** Role of a chat message author. */
export type ChatRole = "user" | "assistant";

/** Lifecycle status of a rendered chat message. */
export type ChatMessageStatus = "streaming" | "complete" | "error";

/**
 * Heuristic response-type label for an assistant message, derived client-side
 * from the rendered content (EKCP does not carry a response type on the stream).
 */
export type ResponseType =
  | "conversational"
  | "structured"
  | "markdown"
  | "table"
  | "list";

/** A message rendered in the chat transcript. */
export type ChatMessage = {
  id: string;
  role: ChatRole;
  content: string;
  status: ChatMessageStatus;
  citations: Citation[];
  /** Current pipeline stage label shown while the assistant is thinking. */
  stage?: string;
};
