# Basket

Basket is the backend runtime for Quince, a local voice-first AI assistant. It handles the part of the system that sits between the user-facing client, model services, retrieval and memory, and Quince's MCP server.

The project started from a simple need: keep the assistant's reasoning and orchestration separate from the capabilities it can use. Basket is responsible for deciding what should happen during a turn. Quince exposes the capabilities that can actually be executed on the machine.

## At a glance

| Area | Responsibility |
| --- | --- |
| Conversation | Session state, history, context assembly |
| LLM | Response generation and agent reasoning |
| Retrieval | Semantic search, BM25, candidate reranking |
| Memory | Persistent memories, commands, conversation context |
| MCP | Capability discovery and tool execution through Quince |
| Voice | STT, TTS, WebSocket streaming |
| API | FastAPI endpoints for model, voice and context services |

## Architecture

At runtime, the request path looks like this:

```text
User
  |
  v
Quince Client
  |  WebSocket
  v
Basket
  |
  +-------------------------------+
  | Conversation Manager           |
  | LLM / Agent Runtime            |
  | Retrieval + Memory             |
  | MCP Client                     |
  +-------------------------------+
                 |
                 | MCP over stdio
                 v
        Quince MCP Server
                 |
                 v
        Hierarchical Tool Registry
          /    /      |      \
     System  Work   Knowledge  Memory  Chat
```

The important boundary is between Basket and the Quince MCP server.

Basket contains the agent runtime and the MCP client. The LLM does not connect to the MCP server on its own. A model can request an action, but Basket is responsible for interpreting that request, navigating the MCP tool tree, executing the selected capability, and putting the result back into the reasoning loop.

The client and backend communicate over WebSocket. Basket and the Quince MCP server communicate over MCP using JSON-RPC over stdio.

## MCP and tool discovery

Quince exposes its capabilities as a hierarchy instead of sending the complete tool set to the model at once.

```text
root
├── system
├── productivity
├── knowledge
├── memory
└── chat
```

A typical agent interaction is:

```text
1. Start at the MCP root
2. Navigate to a relevant category
3. Discover the capabilities available there
4. Read the selected capability schema
5. Execute the tool with validated arguments
6. Return the result to Basket
7. Continue reasoning or produce the final response
```

Two control operations are available at the root:

- `reset` clears the current MCP navigation state.
- `terminate` ends the MCP tool session.

This keeps the model's working tool set small and makes tool discovery an explicit part of the agent loop.

## Request and voice flow

For a text or voice turn, Basket brings together the same core pieces: context, retrieval, the model, tools, and the final response.

A voice turn follows this path:

```text
Audio input
    |
    v
Speech-to-text
    |
    v
Context + retrieval
    |
    v
LLM / agent loop
    |
    +---- MCP tool call ----> Quince MCP Server
    |                              |
    |<------- tool result ---------+
    |
    v
Response generation
    |
    v
Text-to-speech
    |
    v
Streaming audio
```

The WebSocket layer emits structured events during the pipeline, including STT, LLM and TTS stages. The client can therefore react to the turn while it is still running instead of waiting for a single final response.

## Retrieval

Conversation context uses hybrid retrieval. Basket combines semantic and lexical search before reranking the candidate set.

```text
                    Query
                      |
            +---------+---------+
            |                   |
            v                   v
      Semantic search        BM25 search
            |                   |
            +---------+---------+
                      |
                      v
             Candidate merge
                      |
                      v
              Cross-encoder
                 reranking
                      |
                      v
                  Top-K
```

Current retrieval components:

| Component | Implementation |
| --- | --- |
| Vector store | ChromaDB |
| Embeddings | `jinaai/jina-embeddings-v5-text-nano` |
| Lexical retrieval | `rank-bm25` |
| Reranker | `cross-encoder/ettin-reranker-32m-v1` |
| Chunking | Recursive character splitting |
| Chunk size | 600 characters |
| Chunk overlap | 80 characters |

The embedding and reranker models are managed centrally and currently run on CPU.

## Memory

Basket keeps several kinds of context because they serve different purposes.

### Conversation memory

Conversation messages are persisted and indexed for retrieval. MongoDB stores the underlying records, while ChromaDB and the BM25 index provide retrieval paths.

### Explicit memory

Quince can store persistent memories separately from ordinary conversation history. Basket exposes the APIs used to add, retrieve and delete those memories.

### Commands

Commands are stored separately from memories. They can be temporary or persistent and are exposed to the agent through the MCP layer.

The current data layout is:

```text
MongoDB
├── chats
├── memories
└── commands

ChromaDB
└── semantic conversation index

BM25
└── lexical conversation index
```

## Model integrations

Basket keeps model services behind small client interfaces so the orchestration code does not depend on one inference runtime.

### LLM

The codebase supports OpenAI-compatible model endpoints and includes clients for local and hosted runtimes, including llama.cpp, LM Studio, and Groq.

### Speech-to-text

Qwen3-ASR can be used through the configured STT service. The REST endpoint accepts uploaded audio, while the voice WebSocket path handles microphone sessions.

### Text-to-speech

Pocket TTS is integrated into the response pipeline. Audio is produced as PCM chunks and streamed back to the client.

## API

Basket runs as a FastAPI application.

### Voice

```text
WS /ws
```

### LLM

```text
POST /llm/chat
GET  /llm/models
POST /llm/load
POST /llm/unload
POST /llm/unload-all
```

### Speech-to-text

```text
POST /stt/transcribe
```

### Text-to-speech

```text
POST /tts/synthesize
```

### Memory

```text
POST   /context/memory/add
POST   /context/memory/get
POST   /context/memory/get_all
DELETE /context/memory/delete
POST   /context/memory/delete_all
```

### Commands

```text
POST   /context/command/add
POST   /context/command/get_all
POST   /context/command/delete
POST   /context/command/delete_all
```

FastAPI's interactive documentation is available when the server is running.

## Repository layout

```text
Basket/
├── infrastructure/
│   ├── config.bat
│   ├── start.bat
│   ├── stop.bat
│   ├── restart.bat
│   └── status.bat
│
├── src/
│   ├── apis/                  # FastAPI routes
│   ├── clients/               # LLM, STT, TTS and MCP clients
│   ├── core/                  # Runtime configuration and state
│   ├── jobs/                  # Startup and lifecycle jobs
│   ├── schemas/               # Pydantic and internal schemas
│   ├── services/
│   │   ├── bm25/              # Lexical retrieval
│   │   ├── chat/              # Agent and voice pipeline
│   │   ├── chunker/           # Conversation chunking
│   │   ├── db/                # MongoDB access
│   │   ├── embedding/         # Embedding generation
│   │   ├── models/            # Model loading and lifecycle
│   │   ├── retrieval/          # Retrieval and reranking
│   │   ├── session/            # Session and chat persistence
│   │   └── vectordb/           # ChromaDB integration
│   ├── socket/                # WebSocket handling
│   ├── utils/                 # Shared utilities
│   └── main.py                # FastAPI entry point
│
├── .env.example
├── requirements.txt
├── run.py
└── TODO.md
```

## Running Basket

Basket is primarily developed for a local Windows setup and expects the supporting services to be available on the configured hosts and ports.

### Requirements

- Python 3.11+
- MongoDB
- A compatible LLM server such as LM Studio or llama.cpp
- Qwen3-ASR for speech recognition when using voice input
- Pocket TTS for speech synthesis
- Quince with its MCP server

### 1. Create a virtual environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 2. Install dependencies

```powershell
pip install -r requirements.txt
```

### 3. Create the environment file

```powershell
copy .env.example .env
```

Then configure the service endpoints and model settings in `.env`.

A typical local setup uses values similar to:

```env
BASKET_HOST=127.0.0.1
BASKET_PORT=7000

MONGODB_URI=mongodb://localhost:7005/
BASKET_DB=basket

LLM_HOST=127.0.0.1
LLM_PORT=7001

STT_HOST=127.0.0.1
STT_PORT=7002

TTS_HOST=127.0.0.1
TTS_PORT=7003
```

### 4. Configure the Quince MCP server

Basket currently launches the Quince MCP server as a stdio child process. The Quince path is therefore environment-specific and must point to the local Quince checkout.

### 5. Start Basket

```powershell
python run.py
```

The default local endpoints are:

```text
http://127.0.0.1:7000
ws://127.0.0.1:7000/ws
```

The repository also includes Windows batch scripts under `infrastructure/` for the local development setup.

## Configuration

Most runtime settings are loaded from environment variables. The repository includes `.env.example` as the starting point.

The main groups are:

```text
Basket server
Database
LLM
STT
TTS
Retrieval
MCP / Quince
```

Keep machine-specific paths and service addresses out of source control when possible.

## Development notes

Basket is still under active development. The core runtime is already in place, but some areas are intentionally evolving, particularly realtime interaction, memory handling, MCP lifecycle behavior, and environment setup.

That is reflected in `TODO.md` and in the current separation between the orchestration code and the Quince capability layer.

## Project relationship

Basket is one part of the larger Quince system.

```text
Quince Client
    |
    | WebSocket
    v
Basket
    |
    | MCP over stdio
    v
Quince MCP Server
    |
    v
Windows capabilities
```

Quince owns the user-facing client and machine capabilities. Basket owns the reasoning pipeline, retrieval, memory, model communication, and agent orchestration.

Keeping those concerns separate makes it possible to change the model stack or retrieval system without moving operating-system logic into the backend, and to expand Quince's capabilities without putting Windows-specific code into Basket.

## License

Not yet specified.
