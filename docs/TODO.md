TODO:
1. Memory Management & Session Scoping (Short-term/session vs Long-term memory, commands, protocols, modes):
   - Scope default `/chat` retrieval to active `session_id` and/or `memory_type == "long_term"` to prevent cross-chat context bleed across distinct conversation sessions.
   - Provide clean "New Chat" lifecycle hooks (auto-clear short-term memory partition or switch active session).
2. RAG (Dynamic hybrid fusion, BM25 incremental cache, neural cross-encoder reranker)
3. MCP
4. RTSI
5. Event Env
6. Text-in client
7. Standardized Traceable Logging System:
   - Define and enforce a uniform, traceable log format across Basket and every Fruit application (consistent timestamps, log levels, service/fruit tags, and request/trace context) so `LogViewer` highlights and parses all services consistently.
