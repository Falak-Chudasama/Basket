# Fruit Application Developer Guide (`Fruits.md`)

This guide serves as the authoritative, comprehensive manual and zero-step foundation for developing, integrating, and running Fruit applications within the Basket ecosystem. It covers the 3-tiered context architecture, exposed APIs, MongoDB database standards, multi-chat lifecycles, asset sharing, reverse proxy routing, and central authentication.

---

## 1. Architecture and Ecosystem Topology

Basket acts as the central control plane, AI engine hub, and reverse proxy coordinator for all fruit applications. Each fruit is an autonomous service with its own frontend and backend, integrating with Basket for intelligence, authentication, and database storage.

```
                           +------------------------+
                           |  Browser / Client Apps  |
                           +-----------+------------+
                                       |
                   HTTPS (*.jam) / WSS | Port 80, 443
                                       v
               +------------------------------------------------+
               |            Nginx Edge Reverse Proxy            |
               +---+--------------+--------------+------------+-+
                   |              |              |            |
+------------------v---+ +--------v-------+ +----v----+ +-----v-------+
|        Basket        | |      Plum      | |  Kiwi   | |   Banana    |
| Core API: 127.0.0.1  | | API: 127.0.0.2 | |  API:   | |    API:     |
|   Port: 10010 (API)  | |  Port: 10000   | |127.0.0.3| |  127.0.0.4  |
|   Port: 10020 (Ctrl) | |  WS:   10010   | |Port:10000|Port: 10000   |
+----------+-----------+ +--------+-------+ +----+----+ +-----+-------+
           |                      |              |            |
           +----------------------+--------------+------------+
                                  |
                                  v
                +------------------------------------+
                |       Central MongoDB Server       |
                |       127.0.0.1:10000              |
                | Databases: basket, plum, kiwi...   |
                +------------------------------------+
```

### 1.1 Local Subnet & Port Convention

All services run locally on specific loopback IP aliases (`127.0.0.X`) to avoid port collisions and provide clean process isolation:

| Fruit / Service | Frontend URL | API / Gateway URL | Loopback IP & Port | Tech Stack |
| :--- | :--- | :--- | :--- | :--- |
| **Basket (AI Core)** | `https://basket.jam` | `https://api.basket.jam` | `127.0.0.1:10010` | FastAPI |
| **Basket (Control)** | — | `http://127.0.0.1:10020` | `127.0.0.1:10020` | FastAPI |
| **Plum** | `https://plum.jam` | `https://api.plum.jam` | `127.0.0.2:10000` (WS: `10010`) | Node / Express / React |
| **Kiwi** | `https://kiwi.jam` | `https://api.kiwi.jam` | `127.0.0.3:10000` | Python / FastAPI / React |
| **Banana** | `https://banana.jam` | `https://api.banana.jam` | `127.0.0.4:10000` | Python / FastAPI / React |
| **Quince** | `https://quince.jam` | `https://api.quince.jam` | `127.0.0.5:10000` (MCP: `10010`) | Python / FastAPI / Chrome Ext |
| **Lemon** | `https://lemon.jam` | `https://api.lemon.jam` | `127.0.0.6:10000` (DNS: `53`) | Python / FastAPI / React |
| **Cherry** | `https://cherry.jam` | `https://api.cherry.jam` | `127.0.0.7:10000` | Python / FastAPI / Vite |

### 1.2 Underlying AI Model Endpoints (Managed by Basket)

- **LLM Engine (llama.cpp / LM Studio / Groq)**: `http://127.0.0.1:10030`
- **STT Engine (Qwen3-ASR)**: `http://127.0.0.1:10040`
- **TTS Engine (PocketTTS / Kokoro)**: `http://127.0.0.1:10050`
- **Vector DB (ChromaDB)**: Embedded `/chromadb` managed by Basket

### 1.3 Central Shared Ecosystem Assets (`Basket/assets`)

> [!IMPORTANT]
> **Asset Sharing Rule**: All branding assets, SVG icons, logos, sound effects, and shared graphic media MUST be fetched from Basket's central asset repository (`Basket/assets` or `client/public/icons/`).
> Fruit applications MUST NEVER reinvent, generate disparate icon styles, or bundle disconnected copies. 

Static assets are served via Nginx across all subdomains:
- **Ecosystem Base URL**: `https://basket.jam/assets/` or `/icons/`
- **Standard Fruit Icons**:
  - Plum: `/icons/plum-icon.svg`
  - Cherry: `/icons/cherry-icon.svg`
  - Kiwi: `/icons/kiwi-icon.svg`
  - Banana: `/icons/banana-icon.svg`
  - Lemon: `/icons/lemon-icon.svg`
  - Quince: `/icons/quince-icon.svg`
  - Basket: `/icons/basket-icon.svg`

---

## 2. Standard 3-Tier Database Architecture for Fruits

Basket manages a centralized, high-performance MongoDB instance listening on:
```
mongodb://127.0.0.1:10000/
```

### 2.1 Database Namespace Isolation
Every fruit application owns its dedicated database namespace:
- **Plum**: `mongodb://127.0.0.1:10000/plum`
- **Cherry**: `mongodb://127.0.0.1:10000/cherry`
- **Kiwi**: `mongodb://127.0.0.1:10000/kiwi`
- **Banana**: `mongodb://127.0.0.1:10000/banana`
- **Quince**: `mongodb://127.0.0.1:10000/quince`
- **Lemon**: `mongodb://127.0.0.1:10000/lemon`
- **Basket**: `mongodb://127.0.0.1:10000/basket` (internal orchestrator state)

### 2.2 Mandatory Collections for Chattable Fruits
Every chattable fruit (Plum, Cherry, Quince, etc.) MUST strictly maintain three collections:

```
mongodb://127.0.0.1:10000/<fruit_name>/
├── chats       <-- Volatile Short-Term Multi-Chat Sessions
├── notes       <-- Persistent Long-Term Knowledge Base
└── commands    <-- Fixed Behavioral Guidelines Stitched into System Prompt
```

---

### Collection 1: `chats` (Multi-Chat Conversation Store)

Stores conversation sessions. Each document represents a complete chat thread containing an ordered list of messages.

#### MongoDB Document Schema:
```json
{
  "_id": ObjectId("6737a9f8b4c21e001234abcd"),
  "session_id": "6737a9f8b4c21e001234abcd",
  "title": "Meeting Preparation with Sarah",
  "application": "plum",
  "messages": [
    {
      "role": "user",
      "content": "Can you summarize Sarah's email regarding the Q3 roadmap?",
      "created_at": "2026-11-16 10:15:00"
    },
    {
      "role": "assistant",
      "content": "Sarah highlighted three key priorities for Q3: 1) Performance optimization...",
      "created_at": "2026-11-16 10:15:03"
    }
  ],
  "created_at": "2026-11-16 10:15:00",
  "updated_at": "2026-11-16 10:15:03"
}
```

#### Multi-Chat Client Architecture & Lifecycle:
1. **Creating a New Chat**: Client generates a new thread or sends an initial message with no `chat_id`. The backend inserts a new document in `chats`, generates a new `ObjectId`, and assigns a default title based on the first prompt (`user_prompt.slice(0, 50)`).
2. **Switching Chats**: When the user clicks a different chat thread in the sidebar, the client sends that thread's `chat_id` on subsequent calls. Basket **automatically detects the switch**, purges the volatile VectorDB/BM25 store for that fruit, and loads the new chat's history in one go.
3. **Updating a Chat Turn**: After every assistant response, the turn is appended to `messages` via `$push` and `updated_at` is refreshed. Basket handles the progressive $O(1)$ indexing automatically.

---

### Collection 2: `notes` (Persistent Knowledge Base)

Stores long-term user notes, documents, facts, and reference material.

#### MongoDB Document Schema:
```json
{
  "_id": ObjectId("6737b019b4c21e005678efaa"),
  "title": "Quarterly Budget & Travel Guidelines",
  "content": "All team offsite flights must be booked at least 14 days in advance via corporate card...",
  "tags": ["finance", "policy"],
  "metadata": {
    "category": "policy",
    "author": "Operations"
  },
  "application": "plum",
  "created_at": "2026-11-16 09:00:00",
  "updated_at": "2026-11-16 09:00:00"
}
```

#### Sync Rule:
Whenever a user creates, edits, or deletes a note, the fruit backend updates its MongoDB `notes` collection AND notifies Basket via `POST /context/notes/sync`. Basket updates the persistent VectorDB and BM25 index incrementally with zero rebuild lag.

---

### Collection 3: `commands` (Stitched System Prompt Rules)

Stores high-priority behavioral guidelines, macros, and personality instructions.

#### MongoDB Document Schema:
```json
{
  "_id": ObjectId("6737b11fb4c21e009012bbcc"),
  "command": "Always format calendar dates in ISO 8601 (YYYY-MM-DD) and assume IST timezone.",
  "is_active": true,
  "application": "plum",
  "created_at": "2026-11-16 08:30:00",
  "updated_at": "2026-11-16 08:30:00"
}
```

#### Ingestion & Execution Rule:
- Commands require **NO VectorDB or BM25 indexing**.
- Basket loads all active commands into an in-memory cache on startup (`_commands_cache[fruit]`).
- Basket **unconditionally stitches all commands into the system prompt** on every `/chat` and `/completion` turn. Commands are never ranked away or dropped by relevance filters.

---

## 3. Basket APIs Exposed for Fruits

All requests to Basket APIs (`https://api.basket.jam`) should include the standard identification header:
```http
X-Basket-Application: <fruit_name>
```

---

### 3.1 Fast Stateful/Stateless Inference (`POST /completion`)

The `/completion` endpoint provides lightning-fast LLM responses for categorization, summaries, JSON extraction, or one-off tasks. It can be used **statelessly** (with custom inline context) or **optionally stateful** (leveraging volatile chat or persistent notes).

#### Endpoint:
- `POST https://api.basket.jam/completion` (or `POST https://api.basket.jam/llm/completion`)

#### Request Schema:
```json
{
  "prompt": "Extract the meeting action items and assignees.",
  "application": "cherry",
  "system_prompt": "You are a professional project manager. Be direct and concise.",
  "grammar": null,
  "context": [
    {
      "content": "Alex agreed to finish the database migrations by Wednesday.",
      "metadata": { "source": "meeting_transcript", "timestamp": "10:30" }
    },
    {
      "content": "Priya will verify the API integration with Basket.",
      "metadata": { "source": "meeting_transcript", "timestamp": "10:35" }
    }
  ],
  "chat_id": null,
  "retrieve_chat": false,
  "retrieve_notes": false,
  "temperature": 0.2,
  "stream": false
}
```

#### Request Attributes:
| Field | Type | Description |
| :--- | :--- | :--- |
| `prompt` / `text` | `string` | The user instruction or input prompt. |
| `application` | `string` | The fruit namespace (`plum`, `cherry`, `kiwi`, etc.). |
| `system_prompt` | `string?` | Optional system instruction prepended to system context. |
| `grammar` | `string?` | Optional GBNF grammar or JSON schema rule for structured output. |
| `context` | `array?` | Array of `[{content: string, metadata: object}]`. Basket JSONifies this and injects it under `<INLINE_CONTEXT>`. |
| `chat_id` | `string?` | Optional active chat session ID. |
| `retrieve_chat` | `boolean` | If `true` and `chat_id` provided, retrieves top chunks from volatile chat. |
| `retrieve_notes` | `boolean` | If `true`, retrieves top chunks from persistent notes. |
| `temperature` | `float?` | Sampling temperature (default: `0.7`). |
| `stream` | `boolean` | Set `true` to receive a Server-Sent Events (SSE) stream. |

#### Response (Non-Streaming):
```json
{
  "status": "success",
  "content": "1. Alex: Complete database migrations by Wednesday.\n2. Priya: Verify API integration with Basket.",
  "application": "cherry",
  "model": "llama-3.2-3b-instruct",
  "usage": { "prompt_tokens": 142, "completion_tokens": 31 }
}
```

---

### 3.2 Conversational Multi-Chat Pipeline (`POST /chat/text`)

The unified multi-modal chat pipeline that powers the primary interactive assistant interface for fruits.

#### Endpoint:
- `POST https://api.basket.jam/chat/text` (or `POST https://api.basket.jam/chat`)

#### Request Schema:
```json
{
  "text": "What was the vacation policy we agreed on, and what did I mention 2 minutes ago?",
  "application": "plum",
  "chat_id": "6737a9f8b4c21e001234abcd",
  "retrieve_chat": true,
  "retrieve_notes": true,
  "synthesize_speech": false,
  "llm": {
    "system_prompt": "You are Plum, the intelligent personal assistant.",
    "temperature": 0.7
  }
}
```

#### Under the Hood Execution:
1. **Volatile Chat Check**:
   - If `chat_id` matches current active: Basket proceeds directly ($O(1)$).
   - If `chat_id` switched: Basket purges Plum's volatile memory and indexes the new chat from `plum.chats` in MongoDB.
2. **Commands Injection**: Unconditionally stitches active rules from `plum.commands` into system prompt.
3. **Tiered Hybrid Search**:
   - Searches volatile chat (ChromaDB + BM25) $\rightarrow$ Ranked with **highest priority** ($W=0.7$).
   - Searches persistent notes (ChromaDB + BM25) $\rightarrow$ Ranked with **secondary priority** ($W=0.3$).
4. **LLM Generation**: Streams tokens back via Server-Sent Events (`event: delta`).
5. **Progressive Append**: Automatically appends the user prompt and final assistant response to `plum.chats` and the volatile VectorDB/BM25 index.

#### Response Stream (Server-Sent Events):
```
event: delta
data: {"content": "Based on "}

event: delta
data: {"content": "your policy notes..."}

event: done
data: {"finish_reason": "stop"}
```

---

### 3.3 Mutation Sync Endpoints for Notes and Commands

Fruits must call these endpoints whenever a user creates, updates, or deletes a note or command.

#### A. Sync Note (`POST /context/notes/sync`)
```http
POST https://api.basket.jam/context/notes/sync HTTP/1.1
Content-Type: application/json

{
  "application": "plum",
  "action": "upsert",
  "note_id": "6737b019b4c21e005678efaa",
  "title": "Quarterly Budget & Travel Guidelines",
  "content": "All team offsite flights must be booked at least 14 days in advance...",
  "metadata": { "category": "policy" }
}
```
*To delete:* Set `"action": "delete"` with `"note_id": "..."`.

#### B. Sync Command (`POST /context/commands/sync`)
```http
POST https://api.basket.jam/context/commands/sync HTTP/1.1
Content-Type: application/json

{
  "application": "plum",
  "action": "upsert",
  "command_id": "6737b11fb4c21e009012bbcc",
  "command": "Always format calendar dates in ISO 8601 (YYYY-MM-DD)."
}
```
*To delete:* Set `"action": "delete"` with `"command_id": "..."`.

---

## 4. Blueprint: Building a New Fruit from Scratch

Follow this exact blueprint when constructing a new Fruit application (e.g., `Mango`):

```
┌────────────────────────────────────────────────────────┐
│ STEP 1: Assets & Icons                                 │
│   Fetch official icon from Basket/assets               │
│   e.g. /icons/mango-icon.svg                           │
└──────────────────────────┬─────────────────────────────┘
                           │
┌──────────────────────────▼─────────────────────────────┐
│ STEP 2: Database Setup                                 │
│   Connect to: mongodb://127.0.0.1:10000/mango          │
│   Ensure collections exist:                            │
│     - chats (session_id, title, messages: [])          │
│     - notes (title, content, metadata, updated_at)     │
│     - commands (command, is_active)                    │
└──────────────────────────┬─────────────────────────────┘
                           │
┌──────────────────────────▼─────────────────────────────┐
│ STEP 3: Multi-Chat Client Flow                         │
│   1. Fetch user's chats list from mango.chats          │
│   2. On select chat: set active chat_id                │
│   3. Send prompt to POST /chat/text with:              │
│      { text, application: "mango", chat_id }           │
│   4. Display streaming SSE response                    │
└──────────────────────────┬─────────────────────────────┘
                           │
┌──────────────────────────▼─────────────────────────────┐
│ STEP 4: Fast Tasks with /completion                    │
│   For tag extraction, categorization, or summary:      │
│   Call POST /completion with inline context & grammar   │
└────────────────────────────────────────────────────────┘
```

---

## 5. Summary Matrix of Context Tiers

| Tier | Collection | Basket Store | Retention | Priority / Weight |
| :--- | :--- | :--- | :--- | :--- |
| **Tier 1: Chat** | `<fruit>.chats` | Volatile ChromaDB & BM25 pair (`volatile_chats`) | Active session only (purged on chat switch) | **Highest** ($W=0.7$) |
| **Tier 2: Notes** | `<fruit>.notes` | Persistent ChromaDB & BM25 pair (`persistent_notes`) | Long-term across all chats | **Secondary** ($W=0.3$) |
| **Tier 3: Commands** | `<fruit>.commands` | In-memory cache (`_commands_cache`) | Permanent | **Absolute** (Stitched into system prompt) |
