---
description: 'LangChain, LangGraph, and Langfuse coding standards for EK-RAG engines. Use when writing prompt templates, LLM calls, output parsers, graphs, or tracing.'
applyTo: 'services/**/*.py'
---

# LangChain, LangGraph & Langfuse Standards

Apply these conventions whenever writing LLM orchestration code so behavior is consistent, testable, and easy to trace. Keep all orchestration behind engine-owned abstractions to preserve model independence.

## Prompt Templates
- Use `ChatPromptTemplate.from_messages` with explicit `("system", ...)` and `("human", ...)` messages.
- Declare `input_variables` explicitly; never rely on implicit variable discovery.
- Use `partial_variables` for constants such as output format instructions, policy text, or tenant-invariant context.
- Store templates in a dedicated `prompts/` module per engine; give each template a stable name and version.
- Never inline secrets or environment-specific values in prompts; inject via variables sourced from settings.

## LLM Construction
- Build chat models through a single provider-abstracted factory (for example `build_chat_model(settings)`); never instantiate provider clients directly in business logic.
- Source model name, temperature, timeouts, and limits from the engine settings module; no hardcoded values.
- Import base types from `langchain_core` and concrete models from the relevant `langchain` integration module; keep the core model-agnostic.

## Output Parsing
- Always parse model output with a `langchain_core.output_parsers` parser (`PydanticOutputParser`, `JsonOutputParser`, or `StrOutputParser`).
- For structured output, validate against Pydantic v2 models; reuse `packages/contracts` models for any cross-engine payload.
- Bind parser format instructions into the prompt via `partial_variables` (for example `format_instructions=parser.get_format_instructions()`).

## Chains (LCEL)
- Compose with LCEL: `prompt | llm | parser`.
- Keep chains small, typed, and independently testable; avoid hidden side effects.

## Streaming And Execution
- For user-facing responses, prefer streaming (`.stream()` / `.astream()`, or `.astream_events()` for token-level UX) instead of `.invoke()` to improve perceived latency and experience.
- Use `.invoke()` / `.ainvoke()` for internal, deterministic, or non-interactive steps where the full result is required before proceeding.
- Preserve tracing and parsing when streaming: attach the Langfuse callback and reconcile streamed chunks against the output parser before returning a final validated result.
- Expose streaming through the API layer (for example server-sent events) only for interactive endpoints; keep batch and pipeline paths on `.invoke()`.

## LangGraph
- Define graph state as a typed structure (TypedDict or Pydantic model); no untyped dicts.
- Implement nodes as pure functions of state; keep transitions explicit and deterministic.
- Use a checkpointer for recovery; never store execution state in module-level globals.
- Name nodes and edges clearly for traceability.

## Langfuse (Self-Hosted Only)
- Instrument chains and graphs with the Langfuse callback handler.
- Attach `tenant_id`, `correlation_id`, and `session_id` as trace metadata or tags on every run.
- Configure the Langfuse host from settings; it must point to the local self-hosted instance only. Never send traces to a managed cloud endpoint.

## Tracking And Standardization
- One prompt registry per engine; typed inputs and outputs everywhere.
- Every LLM and graph invocation must be traceable end to end via Langfuse plus structured logs carrying `tenant_id` and `correlation_id`.