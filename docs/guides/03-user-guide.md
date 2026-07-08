# EK-RAG User Guide

> Audience: the people who use the product day-to-day — asking questions and (optionally) adding documents. No technical setup here; that's the [Installation Guide](02-installation-guide.md).

---

## 1. What you can do with EK-RAG

- **Ask questions in plain language** and get answers grounded in your organization's documents.
- **See where every answer comes from** — each response can include **citation cards** (source file, confidence, and a classification badge).
- **Have real conversations** — the assistant remembers context within a conversation.
- **Keep multiple conversations** — start new ones, switch between them; they're saved in your browser.
- **(If permitted) Add documents** so the assistant can answer about new material.

Everything runs inside your organization. Your questions and documents stay private.

---

## 2. First-time setup in the browser

When you open the Web UI for the first time, you must tell it how to reach the assistant and who you are. You only do this once per browser.

1. Open the app (your admin will give you the URL, e.g., `http://localhost:3001`).
2. The **home page** shows an **EKCP Connectivity** card:
   - **Online** (green) — good, the assistant is reachable.
   - **Offline** (red) — the backend isn't reachable; tell your admin.
3. Click **Settings** (in the sidebar) and fill in:
   | Field | What to enter | Example |
   |---|---|---|
   | **EKCP API URL** | The assistant's address (from your admin) | `http://localhost:8003` |
   | **API key** | The access token from your admin | *(provided by admin)* |
   | **Tenant ID** | Your organization/workspace identifier | `tenant-a` |
   | **User ID** | Your user identifier | `jane.doe` |
   | **Classification clearance** | Your access level | `internal` |
4. Click **Save settings**. You'll see a green "Saved" confirmation.

> These values are stored **only in your browser** (local storage) and are never sent anywhere except the assistant you configured. Nothing is written to a server.

**If chat is disabled:** a banner says "Configuration required: … not set." Return to Settings and fill in the missing fields (you need at least Tenant ID, API key, and User ID).

---

## 3. Having a conversation

1. Click **New conversation** (or use the default one) in the left sidebar.
2. Type your question in the box at the bottom.
3. Press **Enter** to send (use **Shift+Enter** for a new line without sending).
4. Watch the answer **stream in** word by word.
5. While the assistant is thinking, you'll see an **"Agent is reasoning…"** indicator; you can press **Stop** to cancel a response.

### Understanding the answer
- The assistant's reply is rendered with formatting (headings, lists, tables, code).
- A small **response-type label** (e.g., *Conversational*, *Markdown*, *Table*, *List*) appears under the answer.
- If the answer used your documents, **citation cards** appear beneath it.

---

## 4. Reading citation cards

Each citation card shows:

| Element | Meaning |
|---|---|
| **Title** | The source document (usually the file name). |
| **Source path** | Where the passage came from — your proof/trace. |
| **Confidence** | How relevant the system judged that source (as a percentage). |
| **Clearance badge** | The source's classification, colour-coded: **Public** (green), **Internal** (blue), **Confidential** (amber), **Restricted** (red). |

Use citations to **verify** answers. If a card cites a document you recognize, you can open that source to confirm. A "**Sources (N)**" header tells you how many sources supported the answer.

> If an answer has **no** citation cards, it was answered conversationally (from general reasoning or memory), not from your indexed documents.

---

## 5. Managing conversations

- **Start fresh:** click **New conversation**. Each conversation is independent.
- **Switch:** click any conversation in the sidebar to reopen it; its full transcript reloads.
- **Titles:** a conversation is automatically titled from your first message.
- **Persistence:** conversations and their messages are saved **in your browser**. They survive page reloads and browser restarts on the same machine.
- **Privacy:** because they're stored locally, clearing your browser data removes them. They are not shared between machines or users.

---

## 6. Adding documents (if you have permission)

Whether you can add documents depends on your organization's setup. There are two common ways material gets in:

1. **Drop-folder (EKDC):** an administrator configures a watched folder. Anyone with access to that folder can drop files (PDF, Word, PowerPoint, images, audio, video). The system converts and ingests them automatically. Ask your admin where that folder is.
2. **Managed ingestion (EKIE):** an administrator or an automated job ingests approved documents. In this model you request that a document be added rather than adding it yourself.

After a document is ingested (this can take from seconds to a few minutes depending on size), ask a question about it — you should see citation cards pointing to it.

> You do **not** add documents through the chat window. Adding documents is a separate ingestion step handled by EKDC/EKIE.

---

## 7. Tips for better answers

- **Be specific.** "What is our data retention period for customer records?" beats "retention?".
- **Reference the topic, not the file.** The system searches by meaning; you don't need to name the exact document.
- **Follow up.** The assistant keeps context within a conversation — you can say "and for employees?" after a first question.
- **Check citations for anything important.** Grounded answers include sources; verify high-stakes answers against them.
- **Start a new conversation for a new topic** so context doesn't blur across unrelated questions.

---

## 8. What to do when something looks wrong

| You see… | What it means / what to do |
|---|---|
| "Configuration required" banner, input disabled | Fill in Tenant ID, API key, and User ID in **Settings**. |
| "Offline" on the home page | The assistant backend is down or the URL is wrong — contact your admin. |
| A red error banner in chat | The request failed (often auth or a backend hiccup). Re-check Settings; retry. |
| Answer with no citations, but you expected some | The relevant documents may not be ingested yet, or knowledge retrieval is off — ask your admin. |
| A "Response failed" marker on a message | The backend errored mid-answer; send the message again. |
| Wrong or stale answer | The source may be outdated; check the citation and report it to your admin so the document can be re-ingested. |

For anything beyond these, contact whoever administers your EK-RAG instance — the [Admin Guide](04-admin-guide.md) covers their side.
