import asyncio
import json
import unittest
from unittest.mock import AsyncMock, MagicMock, patch
from starlette.testclient import TestClient

from src.main import app
from src.schemas.VoiceSchema import TextInputRequest, VoiceStartRequest
from src.services.chat.chat_pipeline import PipelineEvent


class TestBasketCoreDashboardAPIs(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    # -------------------------------------------------------------------------
    # 1. CORS Headers on Basket Core
    # -------------------------------------------------------------------------
    def test_cors_preflight_for_dashboard_clients(self):
        origins = [
            "http://127.0.0.1:10020",
            "http://localhost:10020",
            "http://127.0.0.1:10010",
            "http://localhost:10010",
            "http://basket.jam",
            "https://basket.jam",
            "http://api.basket.jam",
            "https://api.basket.jam",
        ]
        for origin in origins:
            with self.subTest(origin=origin):
                resp = self.client.options(
                    "/chat",
                    headers={
                        "Origin": origin,
                        "Access-Control-Request-Method": "POST",
                        "Access-Control-Request-Headers": "Content-Type,X-Basket-Application",
                    },
                )
                self.assertEqual(
                    resp.headers.get("access-control-allow-origin"),
                    origin,
                    f"CORS preflight failed for origin {origin}",
                )

    # -------------------------------------------------------------------------
    # 2. POST /chat and POST /chat/text (SSE Streaming)
    # -------------------------------------------------------------------------
    def test_chat_empty_text_rejected(self):
        # Empty string
        r1 = self.client.post("/chat", json={"text": ""})
        self.assertEqual(r1.status_code, 422)  # Pydantic validator min_length=1

        # Whitespace-only string
        r2 = self.client.post("/chat", json={"text": "   "})
        self.assertEqual(r2.status_code, 422)  # field_validator rejects whitespace

    @patch("src.apis.chat.chat_pipeline")
    def test_chat_stream_success(self, mock_pipeline):
        async def mock_event_gen(*args, **kwargs):
            yield PipelineEvent(type="pipeline.started", data={"mode": "text_to_voice"})
            yield PipelineEvent(type="llm.token", data="Hello")
            yield PipelineEvent(type="llm.token", data=" world!")
            yield PipelineEvent(type="llm.final", data="Hello world!")
            yield PipelineEvent(type="pipeline.completed", data={"mode": "text_to_voice"})

        mock_pipeline.side_effect = mock_event_gen

        resp = self.client.post(
            "/chat",
            json={
                "text": "What is Basket?",
                "application": "quince",
                "synthesize_speech": False,
            },
        )
        self.assertEqual(resp.status_code, 200)
        self.assertIn("text/event-stream", resp.headers.get("content-type", ""))

        lines = [line.strip() for line in resp.text.split("\n") if line.startswith("data:")]
        self.assertEqual(len(lines), 5)

        first_event = json.loads(lines[0].replace("data:", "").strip())
        self.assertEqual(first_event["type"], "pipeline.started")

        last_event = json.loads(lines[-1].replace("data:", "").strip())
        self.assertEqual(last_event["type"], "pipeline.completed")

    @patch("src.apis.chat.chat_pipeline")
    def test_chat_text_alias_endpoint(self, mock_pipeline):
        async def mock_event_gen(*args, **kwargs):
            yield PipelineEvent(type="llm.final", data="Response from alias")

        mock_pipeline.side_effect = mock_event_gen

        resp = self.client.post("/chat/text", json={"text": "Hello"})
        self.assertEqual(resp.status_code, 200)
        self.assertIn("Response from alias", resp.text)

    # -------------------------------------------------------------------------
    # 3. POST /llm/embeddings
    # -------------------------------------------------------------------------
    @patch("src.apis.llm.create_embedding")
    def test_llm_embeddings_single_string(self, mock_create):
        mock_create.return_value = [0.123, 0.456, 0.789]
        resp = self.client.post(
            "/llm/embeddings",
            json={"input": "Embed this string"},
            headers={"X-Basket-Application": "quince", "X-Request-ID": "req-101"},
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.headers.get("x-basket-application"), "quince")
        self.assertEqual(resp.headers.get("x-request-id"), "req-101")
        data = resp.json()
        self.assertEqual(data["object"], "list")
        self.assertEqual(len(data["data"]), 1)
        self.assertEqual(data["data"][0]["embedding"], [0.123, 0.456, 0.789])

    @patch("src.apis.llm.batch_encode")
    def test_llm_embeddings_batch_list(self, mock_batch):
        mock_batch.return_value = [[0.1, 0.2], [0.3, 0.4]]
        resp = self.client.post(
            "/llm/embeddings",
            json={"input": ["First sentence", "Second sentence"]},
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(len(data["data"]), 2)
        self.assertEqual(data["data"][0]["index"], 0)
        self.assertEqual(data["data"][1]["index"], 1)

    def test_llm_embeddings_invalid_input_type(self):
        resp = self.client.post("/llm/embeddings", json={"input": 42})
        self.assertEqual(resp.status_code, 422)

    # -------------------------------------------------------------------------
    # 4. POST /llm/chat & Grammar Compatibility
    # -------------------------------------------------------------------------
    def test_llm_chat_grammar_conflict_with_tools(self):
        payload = {
            "messages": [{"role": "user", "content": "Choose"}],
            "grammar": 'root ::= "yes" | "no"',
            "tools": [{"type": "function", "function": {"name": "test_func"}}],
        }
        resp = self.client.post("/llm/chat", json=payload)
        self.assertEqual(resp.status_code, 422)
        self.assertIn("conflict", resp.json()["detail"].lower())

    @patch("src.clients.llama_llm._chat_completion_non_streaming")
    def test_llm_chat_custom_headers_propagation(self, mock_chat_non_stream):
        mock_chat_non_stream.return_value = {
            "id": "chatcmpl-1",
            "choices": [{"message": {"role": "assistant", "content": "Done"}}],
        }
        resp = self.client.post(
            "/llm/chat",
            json={"messages": [{"role": "user", "content": "Hello"}]},
            headers={"X-Basket-Application": "quince-dashboard", "X-Request-ID": "test-req-999"},
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.headers.get("x-basket-application"), "quince-dashboard")
        self.assertEqual(resp.headers.get("x-request-id"), "test-req-999")

    # -------------------------------------------------------------------------
    # 5. LLM Model Management Endpoints
    # -------------------------------------------------------------------------
    @patch("src.apis.llm._load_model")
    def test_llm_load_model_endpoint(self, mock_load):
        mock_load.return_value = {"status": "already_loaded", "model": "test-model"}
        resp = self.client.post("/llm/load?model_id=test-model")
        self.assertEqual(resp.status_code, 200)

    def test_llm_unload_not_implemented(self):
        resp = self.client.post("/llm/unload?instance_id=dummy")
        self.assertEqual(resp.status_code, 501)

        resp_all = self.client.post("/llm/unload-all")
        self.assertEqual(resp_all.status_code, 501)


if __name__ == "__main__":
    unittest.main()
