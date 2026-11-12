import unittest
from unittest.mock import AsyncMock, MagicMock, patch
from pydantic import ValidationError

from src.schemas.VoiceSchema import TextInputRequest, VoiceStartRequest
from src.services.session import session
from src.services.chat.chat_pipeline import (
    PipelineEvent,
    VoicePipelineConfig,
    ChatPipelineConfig,
    text_to_voice,
    chat_pipeline,
)
from src.schemas.ChatSchema import Message


class TestTextPipeline(unittest.IsolatedAsyncioTestCase):
    def test_text_input_request_valid(self):
        req = TextInputRequest(text="Hello Basket")
        self.assertEqual(req.text, "Hello Basket")
        self.assertTrue(req.synthesize_speech)
        self.assertEqual(req.application, "quince")

    def test_text_input_request_empty_fails(self):
        with self.assertRaises(ValidationError):
            TextInputRequest(text="")

        with self.assertRaises(ValidationError):
            TextInputRequest(text="   ")

    def test_voice_start_request_with_text(self):
        req = VoiceStartRequest(text="Turn text prompt")
        self.assertEqual(req.text, "Turn text prompt")

    @patch("src.services.session.session.create_session")
    @patch("src.services.session.session._get_db_chats")
    @patch("src.services.session.session._get_vectordb_memory")
    @patch("src.services.session.session._get_bm25_memory")
    @patch("src.services.session.session._get_active_session_id")
    def test_session_auto_initialization(
        self,
        mock_get_active,
        mock_bm25,
        mock_vectordb,
        mock_db_chats,
        mock_create_session,
    ):
        # First call None, second call returns session-123
        mock_get_active.side_effect = [None, "session-123"]
        mock_chats = MagicMock()
        mock_chats.update_chat.return_value = "msg-1"
        mock_db_chats.return_value = mock_chats

        mock_vdb = MagicMock()
        mock_vectordb.return_value = mock_vdb

        mock_bm = MagicMock()
        mock_bm25.return_value = mock_bm

        session.append_chat_to_memory(application="quince", content="hi", source="user")
        mock_create_session.assert_called_once_with(application="quince")
        mock_chats.update_chat.assert_called_once_with(session_id="session-123", content="hi", role="user")

    @patch("src.services.chat.chat_pipeline.retrieve_context", new_callable=AsyncMock)
    @patch("src.services.chat.chat_pipeline.agent_loop", new_callable=AsyncMock)
    @patch("src.services.chat.chat_pipeline.append_chat_to_memory")
    @patch("src.services.chat.chat_pipeline.llm_to_speech")
    async def test_text_to_voice_execution(
        self,
        mock_llm_to_speech,
        mock_append_chat,
        mock_agent_loop,
        mock_retrieve_context,
    ):
        mock_retrieve_context.return_value = [Message(role="user", content="Hi assistant")]
        mock_agent_loop.return_value = []

        async def mock_speech_gen(*args, **kwargs):
            yield PipelineEvent(type="llm.token", data="Hello ")
            yield PipelineEvent(type="tts.started", data="Hello ")
            yield PipelineEvent(type="tts.audio", data=b"\x00\x01\x02\x03")
            yield PipelineEvent(type="llm.final", data="Hello there!")

        mock_llm_to_speech.side_effect = mock_speech_gen

        events = []
        config = VoicePipelineConfig(synthesize_speech=True)
        async for evt in text_to_voice(text="Hi assistant", config=config):
            events.append(evt)

        event_types = [e.type for e in events]
        self.assertIn("pipeline.started", event_types)
        self.assertIn("llm.token", event_types)
        self.assertIn("tts.audio", event_types)
        self.assertIn("llm.final", event_types)
        self.assertIn("pipeline.completed", event_types)

        # Check memory append was called with the assistant response
        mock_append_chat.assert_called_once_with(
            application="quince",
            content="Hello there!",
            source="assistant",
        )

    @patch("src.services.chat.chat_pipeline.retrieve_context", new_callable=AsyncMock)
    @patch("src.services.chat.chat_pipeline.agent_loop", new_callable=AsyncMock)
    @patch("src.services.chat.chat_pipeline.append_chat_to_memory")
    @patch("src.services.chat.chat_pipeline.get_llm_response_stream")
    async def test_text_to_voice_without_speech(
        self,
        mock_llm_stream,
        mock_append_chat,
        mock_agent_loop,
        mock_retrieve_context,
    ):
        mock_retrieve_context.return_value = [Message(role="user", content="Fast prompt")]
        mock_agent_loop.return_value = []

        async def mock_stream_gen(*args, **kwargs):
            yield "Fast "
            yield "response"

        mock_llm_stream.side_effect = mock_stream_gen

        events = []
        config = VoicePipelineConfig(synthesize_speech=False)
        async for evt in text_to_voice(text="Fast prompt", config=config):
            events.append(evt)

        event_types = [e.type for e in events]
        self.assertIn("pipeline.started", event_types)
        self.assertIn("llm.token", event_types)
        self.assertNotIn("tts.audio", event_types)
        self.assertIn("llm.final", event_types)
        self.assertIn("pipeline.completed", event_types)

        mock_append_chat.assert_called_once_with(
            application="quince",
            content="Fast response",
            source="assistant",
        )

    @patch("src.services.chat.chat_pipeline.text_to_voice")
    async def test_unified_chat_pipeline(self, mock_text_to_voice):
        async def mock_gen(*args, **kwargs):
            yield PipelineEvent(type="pipeline.completed")

        mock_text_to_voice.side_effect = mock_gen

        events = []
        async for evt in chat_pipeline(text="Hello world"):
            events.append(evt)

        self.assertEqual(len(events), 1)
        mock_text_to_voice.assert_called_once()

    def test_array_and_object_in_tool_grammar(self):
        import json
        from src.clients.llama_llm import _get_tool_call_grammar, _parse_grammar_tool_call

        tools = [
            {
                "type": "function",
                "function": {
                    "name": "root--browser--fill-form",
                    "description": "Fill multiple form fields",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "refs": {
                                "type": "array",
                                "items": {"type": "string"},
                            },
                            "values": {
                                "type": "array",
                                "items": {"type": "string"},
                            },
                        },
                        "required": ["refs", "values"],
                    },
                },
            }
        ]

        grammar = _get_tool_call_grammar(tools)
        self.assertIn("root--browser--fill-form", grammar)
        self.assertIn("array", grammar)

        call_text = (
            "<tool_call>\n"
            "<function=root--browser--fill-form>\n"
            "<parameter=refs>\n"
            '["e1", "e2"]\n'
            "</parameter>\n"
            "<parameter=values>\n"
            '["val1", "val2"]\n'
            "</parameter>\n"
            "</function>\n"
            "</tool_call>"
        )

        parsed = _parse_grammar_tool_call(call_text, tools)
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed["name"], "root--browser--fill-form")
        args = json.loads(parsed["arguments"])
        self.assertEqual(args["refs"], ["e1", "e2"])
        self.assertEqual(args["values"], ["val1", "val2"])

    def test_bm25_empty_and_punctuation_zero_division_safety(self):
        from src.services.bm25.bm25 import BM25

        bm = BM25()
        self.assertIsNone(bm.index)
        self.assertEqual(bm.search(query="test"), [])

        # Punctuation-only document (tokenizes to empty list)
        bm.upsert(document_id="doc1", document="???", metadata={"type": "test"})
        self.assertIsNone(bm.index)
        self.assertEqual(bm.search(query="test"), [])

        # Whitespace-only document
        bm.upsert(document_id="doc2", document="   ", metadata={"type": "test"})
        self.assertIsNone(bm.index)
        self.assertEqual(bm.search(query="test"), [])

        # Now add a valid document with words
        bm.upsert(document_id="doc3", document="Hello world from basket", metadata={"type": "test"})
        self.assertIsNotNone(bm.index)
        results = bm.search(query="hello")
        self.assertGreater(len(results), 0)
        self.assertEqual(results[0]["id"], "doc3")

        # Search with punctuation-only query
        self.assertEqual(bm.search(query="???"), [])

    def test_clean_tool_result_for_llm(self):
        import json
        from src.services.chat.chat_pipeline import _clean_tool_result_for_llm

        raw_result = {
            "success": True,
            "message": "Opened tab https://wikipedia.org",
            "result": {"effect": "navigated", "url": "https://wikipedia.org"},
            "was_category_call": True,
            "children": [
                {"tool_id": f"tool_{i}", "description": "a" * 500, "arguments": {}}
                for i in range(20)
            ],
            "terminate": False,
        }

        cleaned = _clean_tool_result_for_llm(raw_result)
        data = json.loads(cleaned)
        # Verify children was stripped
        self.assertNotIn("children", data)
        self.assertEqual(data["success"], True)
        self.assertEqual(data["message"], "Opened tab https://wikipedia.org")
        self.assertLess(len(cleaned), 1200)

    def test_prune_agent_messages(self):
        from src.services.chat.chat_pipeline import _prune_agent_messages

        messages = [
            Message(role="system", content="System prompt"),
            Message(role="user", content="User request"),
        ]
        # Add 10 tool call & tool result pairs with long content
        for i in range(10):
            messages.append(
                Message(
                    role="assistant",
                    content="",
                    tool_calls=[{"id": f"call_{i}", "function": {"name": f"tool_{i}"}}],
                )
            )
            messages.append(
                Message(
                    role="tool",
                    tool_call_id=f"call_{i}",
                    content="x" * 2000,
                )
            )

        pruned = _prune_agent_messages(messages, max_total_chars=10000)
        # Should preserve system and user prompt
        self.assertEqual(pruned[0].role, "system")
        self.assertEqual(pruned[1].role, "user")
        # Should have compacted earlier messages
        total_len = sum(len(str(m.content or "")) for m in pruned)
        self.assertLess(total_len, 10000)

    @patch("src.services.chat.chat_pipeline.retrieve_context", new_callable=AsyncMock)
    @patch("src.services.chat.chat_pipeline.agent_loop", new_callable=AsyncMock)
    @patch("src.services.chat.chat_pipeline.append_chat_to_memory")
    async def test_text_to_voice_graceful_error_fallback(
        self,
        mock_append_chat,
        mock_agent_loop,
        mock_retrieve_context,
    ):
        from fastapi import HTTPException

        mock_retrieve_context.return_value = [Message(role="user", content="Break test")]
        # Simulate an exceed_context_size_error
        mock_agent_loop.side_effect = HTTPException(
            status_code=400,
            detail='{"error":{"message":"request (17774 tokens) exceeds the available context size (16128 tokens)"}}',
        )

        events = []
        config = VoicePipelineConfig(synthesize_speech=False)
        async for evt in text_to_voice(text="Break test", config=config):
            events.append(evt)

        event_types = [e.type for e in events]
        self.assertIn("pipeline.started", event_types)
        self.assertIn("llm.token", event_types)
        self.assertIn("llm.final", event_types)
        self.assertIn("pipeline.completed", event_types)

        final_msg = [e.data for e in events if e.type == "llm.final"][0]
        self.assertIn("memory window", final_msg.lower())
        mock_append_chat.assert_called_once()


if __name__ == "__main__":
    unittest.main()
