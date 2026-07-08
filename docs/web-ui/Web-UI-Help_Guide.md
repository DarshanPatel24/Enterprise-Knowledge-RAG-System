# Web UI Help Guide

**Audience:** End users of the EK-RAG chat interface, and operators supporting them.
**Component:** `apps/web-ui/` — EK-RAG local-first enterprise chat UI.
**Last updated:** 2026-07-08

---

## Table of Contents

1. [What This App Does](#1-what-this-app-does)
2. [First-Time Setup](#2-first-time-setup)
3. [The Connectivity Indicator](#3-the-connectivity-indicator)
4. [Having a Conversation](#4-having-a-conversation)
5. [Understanding Citations and Clearance Badges](#5-understanding-citations-and-clearance-badges)
6. [Managing Conversations](#6-managing-conversations)
7. [Settings and Privacy](#7-settings-and-privacy)
8. [Security Model in Plain Terms](#8-security-model-in-plain-terms)
9. [Troubleshooting](#9-troubleshooting)
10. [Frequently Asked Questions](#10-frequently-asked-questions)

---

## 1. What This App Does

The EK-RAG web UI lets you ask questions in natural language and get answers grounded in your organization's knowledge base. Answers **stream in live**, are formatted with rich text and code, and — when the answer draws on source documents — come with **citations** showing exactly where the information came from and how sensitive it is.

Everything runs locally. The app talks to a single local service (the EKCP gateway); it makes no external internet calls, and your conversations and settings stay in your own browser.

### Main screens

| Route | Screen | Purpose |
|---|---|---|
| `/` | Home | Confirms the app can reach the backend. |
| `/chat` | Chat workspace | Ask questions, read streamed answers, browse citations, switch conversations. |
| `/settings` | Settings | Configure the connection, identity, and clearance. |

---

## 2. First-Time Setup

Before you can chat, open **Settings** (`/settings`) and provide:

1. **API base URL** — where the EKCP gateway is running (default `http://localhost:8003`). Usually leave the default unless your operator tells you otherwise.
2. **Tenant ID** — your organization/workspace identifier. *(Required.)*
3. **User ID** — your user identifier. *(Required.)*
4. **API key** — the access key issued for the gateway. *(Required.)* It is sent as a bearer token on each request.
5. **Clearance** — your access level: `public`, `internal`, `confidential`, or `restricted`. Defaults to `public`.

Save. The chat input stays disabled until **Tenant ID**, **User ID**, and **API key** are all set. These values are stored only in your browser and can be changed at any time.

---

## 3. The Connectivity Indicator

The home page shows a **connectivity card**:

- **Connected (green):** the app reached the gateway; it displays the service name and status.
- **Error (red):** the app could not reach the gateway. Check that the backend is running and that the API base URL in Settings is correct.

The card is a quick health check — if it is red, chat will not work until the connection is restored.

---

## 4. Having a Conversation

1. Go to **Chat** (`/chat`).
2. Type your question in the input at the bottom and send it (Enter to send).
3. The answer **streams in token by token** — you see it being written in real time, with no page refresh.
4. Answers render **Markdown**: headings, lists, tables, and syntax-highlighted code blocks.
5. You can send a follow-up once the current answer finishes; the conversation keeps its context.

If something goes wrong mid-answer, an inline error message explains what happened; you can retry your question.

---

## 5. Understanding Citations and Clearance Badges

When an answer is grounded in source documents, **citation cards** appear with the response. Each card shows:

- **Source path** — the document (and chunk) the information came from.
- **Relevance score** — how strongly that source matched your question.
- **Clearance badge** — the classification of that source, colour-coded:

| Badge | Meaning |
|---|---|
| `public` | Freely shareable. |
| `internal` | Internal use only. |
| `confidential` | Sensitive; restricted distribution. |
| `restricted` | Highest sensitivity. |

Badges are colour-coded and meet WCAG AA contrast so they are readable at a glance. You will only ever see sources at or below your own clearance — the backend filters out anything above your level before it reaches you.

> Not every answer has citations. General or conversational replies may carry none.

---

## 6. Managing Conversations

The chat workspace has a **sidebar** listing your conversations:

- **New conversation** — starts a fresh session. The title is taken from your first message.
- **Load a conversation** — click any item in the list to reopen it.
- **Persistence** — conversations are saved in your browser's `localStorage`, so they survive page reloads and browser restarts on the same machine.

Because conversations live in your browser, they are private to that browser profile and are not visible on other devices or to other users.

---

## 7. Settings and Privacy

- All settings and conversations are stored **only in your browser** (`localStorage`, key `ekrag.settings.v1` for settings).
- Nothing is sent to any server except the configured EKCP gateway.
- There is **no analytics, no telemetry, and no external tracking** — by design.
- To reset the app, clear the site's `localStorage`; this removes your settings and saved conversations from that browser.

---

## 8. Security Model in Plain Terms

- The app only ever talks to **one** backend: the EKCP gateway you configure. It never touches databases or internal services directly.
- Every request carries your **tenant**, a unique **correlation id** (for traceability), and your **API key**.
- Your **clearance and tenant** are enforced by the backend, not the browser. The clearance selector tells the backend what to *request*; the backend decides what you are actually *allowed* to see. Selecting a higher clearance than you are entitled to does not grant access.
- Keep your **API key** private. If it is compromised, ask your operator to rotate it.

---

## 9. Troubleshooting

| Problem | What to try |
|---|---|
| Connectivity card is red | Confirm the backend (EKCP) is running; verify the API base URL in Settings. |
| Chat box is greyed out | Open Settings and fill Tenant ID, User ID, and API key. |
| "Unauthorized" / access errors | Re-enter your API key; confirm your Tenant ID is correct. |
| Answer appears all at once instead of streaming | Usually a network/proxy issue between the app and the gateway — tell your operator (see the Deployment Guide, reverse-proxy section). |
| No citations on answers | The answer may not use documents, or the knowledge base has no matching sources — this is normal for some questions. |
| Lost my conversations | Conversations are per-browser; clearing browser data or switching devices/profiles removes them. |
| Wrong or unreachable server | Reset the API base URL in Settings, or clear `localStorage` to return to defaults. |

---

## 10. Frequently Asked Questions

**Does my data leave my machine?**
No. The app calls only the local EKCP gateway and makes no external internet requests. Your settings and conversations stay in your browser.

**Where are my conversations stored?**
In your browser's `localStorage`. They are private to that browser profile and are not synced anywhere.

**Can I change which backend I connect to?**
Yes — set the API base URL in Settings. It defaults to `http://localhost:8003`.

**Why can't I see a document another colleague can?**
Access is filtered by clearance and tenant on the backend. You see only what your clearance and tenant permit.

**Why is a citation showing a `restricted` badge?**
That source is highly sensitive. You are seeing it because your clearance permits it; handle its contents accordingly.

**The app says it's connected but chat won't send — why?**
Connectivity only checks that the gateway is reachable. You still need Tenant ID, User ID, and API key set in Settings before chat is enabled.

---

## References

- [Web-UI-Deployment-Guide.md](Web-UI-Deployment-Guide.md)
- [../../apps/web-ui/README.md](../../apps/web-ui/README.md)
- [../master-architecture.md](../master-architecture.md) — Section 13 (Web UI Layer)
