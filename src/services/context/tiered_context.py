from __future__ import annotations
import asyncio
import logging
import time
from typing import Any, Optional
from bson import ObjectId

from langchain_text_splitters import RecursiveCharacterTextSplitter

from src.core.configs import (
    CHAT_CHUNK_SIZE,
    CHAT_CHUNK_OVERLAP,
    DEFAULT_VECTORDB_N,
    DEFAULT_BM25_N,
)
from src.services.vectordb.memory import Memory
from src.services.bm25.bm25 import BM25
from src.services.db.db import get_db
from src.utils.utils import get_datetime
from src.services.retrieval.chat_retriever import reciprocal_rank_fusion

logger = logging.getLogger(__name__)

ALL_REGISTERED_FRUITS = ["banana", "plum", "kiwi", "quince", "lemon", "cherry"]


class TieredContextManager:
    """
    Tiered Context & Knowledge Engine for Basket and the Fruits Ecosystem:
    1. Volatile Chat Tier: Short-term conversation context (volatile ChromaDB & BM25 pair).
       - Automatically purges and re-indexes once when chat_id switches.
       - Progressively appends (O(1)) during ongoing chat turns.
       - Ranked with highest priority.
    2. Persistent Notes Tier: Long-term knowledge base (persistent ChromaDB & BM25 pair).
       - Loaded from MongoDB <fruit>.notes on startup and synced on mutations.
       - Partitioned by fruit metadata.
    3. Commands Tier: Hardcoded system prompt instructions (in-memory cache).
       - Synced from MongoDB <fruit>.commands.
       - Always stitched verbatim into system prompt (never ranked away).
    """

    def __init__(self) -> None:
        # Volatile Store Pair (Short-term conversation chats)
        self.volatile_vectordb = Memory(application="", collection_name="volatile_chats")
        self.volatile_bm25 = BM25()

        # Persistent Store Pair (Long-term notes and knowledge base)
        self.persistent_vectordb = Memory(application="", collection_name="persistent_notes")
        self.persistent_bm25 = BM25()

        # In-memory tracking
        self._active_fruit_chats: dict[str, str | None] = {}
        self._commands_cache: dict[str, list[dict[str, Any]]] = {}
        self._splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHAT_CHUNK_SIZE,
            chunk_overlap=CHAT_CHUNK_OVERLAP,
            separators=["\n\n", "\n", ". ", "? ", "! ", ", ", " ", ""],
        )

    # =========================================================================
    # TIER 1: VOLATILE CHAT CONTEXT
    # =========================================================================

    async def ensure_chat_indexed(self, application: str, chat_id: str) -> None:
        """
        Ensures the volatile vector and BM25 stores hold only the active chat_id for this fruit.
        If chat_id changes or is newly initialized:
          1. Purges prior chat candidates of this fruit.
          2. Bootstraps and indexes historical messages from MongoDB <fruit>.chats ONCE.
        If chat_id is unchanged:
          Zero-overhead early exit (no re-indexing).
        """
        if not chat_id:
            return

        str_chat_id = str(chat_id)
        current_active = self._active_fruit_chats.get(application)
        if current_active == str_chat_id:
            return

        logger.info(
            "Switching volatile chat context for app='%s': '%s' -> '%s'",
            application,
            current_active,
            str_chat_id,
        )

        # 1. Purge volatile index for this application
        try:
            self.volatile_vectordb.delete_by_filter({"application": application})
        except Exception as exc:
            logger.warning("Error purging volatile vectordb for %s: %s", application, exc)

        try:
            self.volatile_bm25.delete_by_filter(metadata_filter={"application": application})
        except Exception as exc:
            logger.warning("Error purging volatile BM25 for %s: %s", application, exc)

        # 2. Fetch existing messages from MongoDB <fruit>.chats
        try:
            db = get_db(application)
            query_filter: dict[str, Any] = {}
            if ObjectId.is_valid(str_chat_id):
                query_filter = {
                    "$or": [
                        {"_id": ObjectId(str_chat_id)},
                        {"session_id": str_chat_id},
                        {"id": str_chat_id},
                    ]
                }
            else:
                query_filter = {
                    "$or": [
                        {"session_id": str_chat_id},
                        {"id": str_chat_id},
                        {"_id": str_chat_id},
                    ]
                }

            chat_doc = db["chats"].find_one(query_filter)
            if chat_doc:
                messages = chat_doc.get("messages") or chat_doc.get("chats") or []
                if messages:
                    ids: list[str] = []
                    docs: list[str] = []
                    metas: list[dict[str, Any]] = []
                    now = get_datetime()

                    for m_idx, msg in enumerate(messages):
                        content = msg.get("content", "")
                        if not content or not str(content).strip():
                            continue
                        role = msg.get("role", "user")
                        chunks = self._splitter.split_text(str(content))
                        for c_idx, chunk in enumerate(chunks):
                            cid = f"{str_chat_id}:{m_idx}:{c_idx}"
                            ids.append(cid)
                            docs.append(chunk)
                            metas.append({
                                "application": application,
                                "chat_id": str_chat_id,
                                "role": role,
                                "source": role,
                                "tier": "chat",
                                "message_index": m_idx,
                                "chunk_index": c_idx,
                                "created_at": msg.get("created_at", now),
                            })

                    if ids:
                        self.volatile_vectordb.bulk_add_memories(
                            memory_ids=ids,
                            documents=docs,
                            metadatas=metas,
                            session_id=str_chat_id,
                        )
                        self.volatile_bm25.bulk_upsert(
                            ids=ids,
                            documents=docs,
                            metadatas=metas,
                        )
                        logger.info(
                            "Indexed %d historical chunks for app='%s', chat_id='%s'",
                            len(ids),
                            application,
                            str_chat_id,
                        )
        except Exception as exc:
            logger.exception("Failed to bootstrap chat history from MongoDB for %s: %s", application, exc)

        self._active_fruit_chats[application] = str_chat_id

    def append_chat_turn(
        self,
        application: str,
        chat_id: str,
        user_text: str,
        assistant_text: str,
    ) -> None:
        """
        Progressively appends a completed chat turn to MongoDB <fruit>.chats
        and performs an O(1) batch append to the active volatile VectorDB & BM25 index.
        """
        if not chat_id:
            return

        str_chat_id = str(chat_id)
        now = get_datetime()
        user_msg = {"role": "user", "content": user_text, "created_at": now}
        asst_msg = {"role": "assistant", "content": assistant_text, "created_at": now}

        # 1. Update MongoDB <fruit>.chats
        try:
            db = get_db(application)
            query_filter: dict[str, Any] = {}
            if ObjectId.is_valid(str_chat_id):
                query_filter = {
                    "$or": [
                        {"_id": ObjectId(str_chat_id)},
                        {"session_id": str_chat_id},
                    ]
                }
            else:
                query_filter = {
                    "$or": [
                        {"session_id": str_chat_id},
                        {"_id": str_chat_id},
                    ]
                }

            update_res = db["chats"].update_one(
                query_filter,
                {
                    "$push": {"messages": {"$each": [user_msg, asst_msg]}},
                    "$set": {"updated_at": now},
                },
                upsert=False,
            )

            # If document did not exist yet, initialize it
            if update_res.matched_count == 0:
                new_doc: dict[str, Any] = {
                    "session_id": str_chat_id,
                    "title": user_text[:60].strip() or "New Chat",
                    "messages": [user_msg, asst_msg],
                    "application": application,
                    "created_at": now,
                    "updated_at": now,
                }
                if ObjectId.is_valid(str_chat_id):
                    new_doc["_id"] = ObjectId(str_chat_id)
                db["chats"].insert_one(new_doc)
        except Exception as exc:
            logger.warning("Failed to persist chat turn to %s.chats: %s", application, exc)

        # 2. Append chunks to volatile VectorDB and BM25
        ids: list[str] = []
        docs: list[str] = []
        metas: list[dict[str, Any]] = []

        ts = time.time_ns()
        if user_text and user_text.strip():
            u_chunks = self._splitter.split_text(user_text)
            for i, chunk in enumerate(u_chunks):
                cid = f"{str_chat_id}:u:{ts}:{i}"
                ids.append(cid)
                docs.append(chunk)
                metas.append({
                    "application": application,
                    "chat_id": str_chat_id,
                    "role": "user",
                    "source": "user",
                    "tier": "chat",
                    "created_at": now,
                })

        if assistant_text and assistant_text.strip():
            a_chunks = self._splitter.split_text(assistant_text)
            for i, chunk in enumerate(a_chunks):
                cid = f"{str_chat_id}:a:{ts}:{i}"
                ids.append(cid)
                docs.append(chunk)
                metas.append({
                    "application": application,
                    "chat_id": str_chat_id,
                    "role": "assistant",
                    "source": "assistant",
                    "tier": "chat",
                    "created_at": now,
                })

        if ids:
            try:
                self.volatile_vectordb.bulk_add_memories(
                    memory_ids=ids,
                    documents=docs,
                    metadatas=metas,
                    session_id=str_chat_id,
                )
                self.volatile_bm25.bulk_upsert(
                    ids=ids,
                    documents=docs,
                    metadatas=metas,
                )
            except Exception as exc:
                logger.warning("Failed to append volatile chunks for %s: %s", application, exc)

    # =========================================================================
    # TIER 2: PERSISTENT NOTES CONTEXT
    # =========================================================================

    def sync_fruit_notes(self, application: str) -> int:
        """
        Synchronizes all notes from MongoDB <fruit>.notes into the persistent VectorDB & BM25 stores.
        """
        try:
            db = get_db(application)
            notes_cursor = db["notes"].find({})
            notes_list = list(notes_cursor)
        except Exception as exc:
            logger.warning("Unable to fetch notes from %s.notes: %s", application, exc)
            return 0

        # Purge existing notes for this application in persistent stores
        try:
            self.persistent_vectordb.delete_by_filter({"application": application})
        except Exception:
            pass
        try:
            self.persistent_bm25.delete_by_filter(metadata_filter={"application": application})
        except Exception:
            pass

        if not notes_list:
            return 0

        ids: list[str] = []
        docs: list[str] = []
        metas: list[dict[str, Any]] = []
        now = get_datetime()

        for note in notes_list:
            nid = str(note.get("_id", ""))
            title = note.get("title", "")
            content = note.get("content") or note.get("text") or ""
            if not content and not title:
                continue

            full_text = f"{title}\n\n{content}".strip() if title else str(content).strip()
            chunks = self._splitter.split_text(full_text)
            for c_idx, chunk in enumerate(chunks):
                cid = f"note:{nid}:{c_idx}"
                ids.append(cid)
                docs.append(chunk)
                meta: dict[str, Any] = {
                    "application": application,
                    "note_id": nid,
                    "title": title,
                    "tier": "notes",
                    "chunk_index": c_idx,
                    "created_at": str(note.get("created_at", now)),
                    "updated_at": str(note.get("updated_at", now)),
                }
                if note.get("metadata") and isinstance(note["metadata"], dict):
                    meta.update({f"meta_{k}": v for k, v in note["metadata"].items()})
                metas.append(meta)

        if ids:
            self.persistent_vectordb.bulk_add_memories(
                memory_ids=ids,
                documents=docs,
                metadatas=metas,
                memory_type="long_term",
            )
            self.persistent_bm25.bulk_upsert(
                ids=ids,
                documents=docs,
                metadatas=metas,
            )
            logger.info("Synced %d note chunks into persistent stores for app='%s'", len(ids), application)

        return len(notes_list)

    def upsert_note(
        self,
        application: str,
        note_id: str,
        title: str,
        content: str,
        metadata: dict[str, Any] | None = None,
    ) -> int:
        """
        Incrementally updates a single note in the persistent VectorDB and BM25 stores.
        """
        str_nid = str(note_id)
        # Delete existing chunks for this note
        self.delete_note(application=application, note_id=str_nid)

        full_text = f"{title}\n\n{content}".strip() if title else str(content).strip()
        if not full_text:
            return 0

        chunks = self._splitter.split_text(full_text)
        ids: list[str] = []
        docs: list[str] = []
        metas: list[dict[str, Any]] = []
        now = get_datetime()

        for c_idx, chunk in enumerate(chunks):
            cid = f"note:{str_nid}:{c_idx}"
            ids.append(cid)
            docs.append(chunk)
            meta: dict[str, Any] = {
                "application": application,
                "note_id": str_nid,
                "title": title,
                "tier": "notes",
                "chunk_index": c_idx,
                "updated_at": now,
            }
            if metadata:
                meta.update(metadata)
            metas.append(meta)

        if ids:
            self.persistent_vectordb.bulk_add_memories(
                memory_ids=ids,
                documents=docs,
                metadatas=metas,
                memory_type="long_term",
            )
            self.persistent_bm25.bulk_upsert(ids=ids, documents=docs, metadatas=metas)

        return len(ids)

    def delete_note(self, application: str, note_id: str) -> None:
        """Deletes all chunks of a note from the persistent VectorDB and BM25 stores."""
        str_nid = str(note_id)
        filt = {"application": application, "note_id": str_nid}
        try:
            self.persistent_vectordb.delete_by_filter(filt)
        except Exception:
            pass
        try:
            self.persistent_bm25.delete_by_filter(metadata_filter=filt)
        except Exception:
            pass

    # =========================================================================
    # TIER 3: COMMANDS CONTEXT (STITCHED IN-MEMORY SYSTEM PROMPT)
    # =========================================================================

    def sync_fruit_commands(self, application: str) -> int:
        """
        Loads all active commands from MongoDB <fruit>.commands into the fast in-memory cache.
        """
        try:
            db = get_db(application)
            cursor = db["commands"].find({})
            cmds = list(cursor)
        except Exception as exc:
            logger.warning("Unable to fetch commands from %s.commands: %s", application, exc)
            cmds = []

        active_commands: list[dict[str, Any]] = []
        for doc in cmds:
            is_active = doc.get("is_active", True)
            if not is_active:
                continue
            cmd_text = doc.get("command") or doc.get("text") or doc.get("name") or ""
            if cmd_text and str(cmd_text).strip():
                active_commands.append({
                    "id": str(doc.get("_id", "")),
                    "command": str(cmd_text).strip(),
                })

        self._commands_cache[application] = active_commands
        logger.info("Loaded %d active commands into memory cache for app='%s'", len(active_commands), application)
        return len(active_commands)

    def upsert_command(self, application: str, command_id: str, command: str) -> None:
        """Incrementally upserts a command into memory cache and updates MongoDB."""
        str_cid = str(command_id)
        str_cmd = str(command).strip()
        now = get_datetime()

        # Update MongoDB
        try:
            db = get_db(application)
            q: dict[str, Any] = {}
            if ObjectId.is_valid(str_cid):
                q = {"_id": ObjectId(str_cid)}
            else:
                q = {"_id": str_cid}
            db["commands"].update_one(
                q,
                {"$set": {"command": str_cmd, "is_active": True, "updated_at": now}},
                upsert=True,
            )
        except Exception as exc:
            logger.warning("Error saving command to %s.commands: %s", application, exc)

        # Update in-memory cache
        cmds = self._commands_cache.setdefault(application, [])
        for item in cmds:
            if item.get("id") == str_cid:
                item["command"] = str_cmd
                return
        cmds.append({"id": str_cid, "command": str_cmd})

    def delete_command(self, application: str, command_id: str) -> None:
        """Deletes a command from memory cache and MongoDB."""
        str_cid = str(command_id)
        try:
            db = get_db(application)
            q = {"_id": ObjectId(str_cid)} if ObjectId.is_valid(str_cid) else {"_id": str_cid}
            db["commands"].delete_one(q)
        except Exception:
            pass

        cmds = self._commands_cache.get(application, [])
        self._commands_cache[application] = [c for c in cmds if c.get("id") != str_cid]

    def get_formatted_commands(self, application: str) -> str:
        """
        Produces the unconditional system instructions block stitched directly into system prompt.
        """
        cmds = self._commands_cache.get(application)
        if cmds is None:
            self.sync_fruit_commands(application)
            cmds = self._commands_cache.get(application, [])

        if not cmds:
            return ""

        lines = [
            "<SYSTEM_COMMANDS>",
            "The following behavioural guidelines and system commands are active for this application and MUST be obeyed at all times:",
        ]
        for c in cmds:
            lines.append(f"- {c.get('command')}")
        lines.append("</SYSTEM_COMMANDS>")
        return "\n".join(lines)

    # =========================================================================
    # TIERED HYBRID RETRIEVAL & FUSION
    # =========================================================================

    async def retrieve_tiered_context(
        self,
        query: str,
        application: str,
        chat_id: str | None = None,
        retrieve_chat: bool = True,
        retrieve_notes: bool = True,
        top_k_chat: int = 4,
        top_k_notes: int = 3,
        metadata_filter: dict[str, Any] | None = None,
    ) -> dict[str, list[dict[str, Any]]]:
        """
        Executes hybrid retrieval across both stores:
        1. Volatile Chat: Filtered by application and chat_id (higher rank priority).
        2. Persistent Notes: Filtered by application and optional metadata.
        Returns:
          {"chat_chunks": [...], "notes_chunks": [...], "all_fused": [...]}
        """
        chat_candidates: list[dict[str, Any]] = []
        notes_candidates: list[dict[str, Any]] = []

        # 1. Retrieve from Volatile Chat Store (Ranked Higher)
        if retrieve_chat and chat_id:
            await self.ensure_chat_indexed(application, chat_id)
            c_filter = {"application": application, "chat_id": str(chat_id)}

            v_chat = self.volatile_vectordb.query_memory(
                query=query,
                n_result=top_k_chat * 2,
                metadata_filter=c_filter,
            )
            bm_chat = self.volatile_bm25.search(
                query=query,
                n_result=top_k_chat * 2,
                metadata_filter=c_filter,
            )
            chat_candidates = reciprocal_rank_fusion(
                vector_candidates=v_chat,
                bm25_candidates=bm_chat,
                rrf_k=60,
                vector_weight=0.6,
                bm25_weight=0.4,
            )[:top_k_chat]

            for c in chat_candidates:
                c["tier"] = "chat"

        # 2. Retrieve from Persistent Notes Store
        if retrieve_notes:
            n_filter: dict[str, Any] = {"application": application}
            if metadata_filter:
                n_filter.update(metadata_filter)

            v_notes = self.persistent_vectordb.query_memory(
                query=query,
                n_result=top_k_notes * 2,
                metadata_filter=n_filter,
            )
            bm_notes = self.persistent_bm25.search(
                query=query,
                n_result=top_k_notes * 2,
                metadata_filter=n_filter,
            )
            notes_candidates = reciprocal_rank_fusion(
                vector_candidates=v_notes,
                bm25_candidates=bm_notes,
                rrf_k=60,
                vector_weight=0.5,
                bm25_weight=0.5,
            )[:top_k_notes]

            for n in notes_candidates:
                n["tier"] = "notes"

        # 3. Blended fused pool where volatile chat chunks are ranked ahead
        all_fused = list(chat_candidates) + list(notes_candidates)

        return {
            "chat_chunks": chat_candidates,
            "notes_chunks": notes_candidates,
            "all_fused": all_fused,
        }

    # =========================================================================
    # STARTUP INITIALIZATION FOR ALL FRUITS
    # =========================================================================

    async def sync_all_fruits_startup(self) -> None:
        """
        Background startup job: Populates persistent notes and commands cache
        for all registered fruits in the ecosystem.
        """
        logger.info("Initializing Tiered Context Engine for all fruits: %s", ALL_REGISTERED_FRUITS)
        for fruit in ALL_REGISTERED_FRUITS:
            try:
                c_count = self.sync_fruit_commands(fruit)
                n_count = self.sync_fruit_notes(fruit)
                logger.info("Fruit '%s' initialized: %d commands, %d notes synced.", fruit, c_count, n_count)
            except Exception as exc:
                logger.warning("Startup sync skipped or failed for fruit '%s': %s", fruit, exc)


# Global singleton instance
tiered_context = TieredContextManager()
