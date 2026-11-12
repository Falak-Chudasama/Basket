import asyncio
import json
import unittest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException
from fastapi.testclient import TestClient

from src.main import app
from src.schemas.ChatSchema import ChatRequest, Message
from src.clients.llama_llm import (
    _build_request,
    _validate_grammar_compatibility,
    validate_gbnf,
    _chat,
    _chat_completion_non_streaming,
    _chat_completion_streaming,
    _get_tool_call_grammar,
    _parse_grammar_tool_call,
)
from src.clients.quince_mcp import QuinceMCPClient


class TestGrammarValidationAndCompatibility(unittest.TestCase):
    """Test GBNF validation and tool-call compatibility rules."""

    def test_valid_gbnf_grammars(self):
        valid_examples = [
            'root ::= "yes" | "no"',
            'root ::= "urgent" | "normal" | "low"',
            '# Email classification grammar\nroot ::= "spam" | "ham"\n',
            'root ::=\n  "billing" |\n  "support" |\n  "general"',
            (
                'root ::= "{" ws "\\"category\\":" ws category ws "}"\n'
                'category ::= "\\"work\\"" | "\\"personal\\""\n'
                'ws ::= [ \\t\\n]*\n'
            ),
            'root ::= [0-9]+ ("." [0-9]+)?',
            'root ::= ("A" | "B")+ [a-z]*',
            'subrule ::= "ok"\nroot ::= subrule',
        ]
        for grammar in valid_examples:
            with self.subTest(grammar=grammar[:30]):
                try:
                    validate_gbnf(grammar)
                except Exception as exc:
                    self.fail(f"validate_gbnf raised unexpectedly on valid grammar: {exc}")

    def test_invalid_gbnf_rejected(self):
        invalid_cases = [
            ("", "empty or blank"),
            ("   \n\t  ", "empty or blank"),
            ("category ::= \"work\" | \"personal\"", "missing required 'root' rule"),
            ("subroot ::= \"work\"", "missing required 'root' rule"),
            ("root_rule ::= \"work\"", "missing required 'root' rule"),
            ("root ::= \"unclosed string", "unclosed string literal"),
            ("root ::= [0-9", "unclosed character class"),
            ("root ::= (\"a\" | \"b\"", "unclosed parenthesis"),
            ("root ::= \"a\" )", "unexpected closing parenthesis"),
            ("root ::= " + "a" * 70000, "exceeds maximum limit"),
        ]
        for grammar, expected_msg in invalid_cases:
            with self.subTest(grammar=grammar[:30], expected=expected_msg):
                with self.assertRaises(HTTPException) as ctx:
                    validate_gbnf(grammar)
                self.assertEqual(ctx.exception.status_code, 422)
                self.assertIn(expected_msg.lower(), ctx.exception.detail.lower())

    def test_non_string_grammar_rejected(self):
        with self.assertRaises(HTTPException) as ctx:
            validate_gbnf(12345)  # type: ignore
        self.assertEqual(ctx.exception.status_code, 422)
        self.assertIn("must be a string", ctx.exception.detail.lower())

    def test_tool_call_compatibility_rejection(self):
        grammar = 'root ::= "urgent" | "normal"'
        sample_tools = [{
            "type": "function",
            "function": {"name": "test_tool", "parameters": {"type": "object"}}
        }]

        # 1. Grammar + non-empty tools -> 422
        req = ChatRequest(
            messages=[Message(role="user", content="Classify")],
            grammar=grammar,
            tools=sample_tools,
        )
        with self.assertRaises(HTTPException) as ctx:
            _validate_grammar_compatibility(req)
        self.assertEqual(ctx.exception.status_code, 422)
        self.assertIn("cannot provide both 'grammar' and 'tools'", ctx.exception.detail)

        # 2. Grammar + tool_choice="required" -> 422
        req = ChatRequest(
            messages=[Message(role="user", content="Classify")],
            grammar=grammar,
            tool_choice="required",
        )
        with self.assertRaises(HTTPException) as ctx:
            _validate_grammar_compatibility(req)
        self.assertEqual(ctx.exception.status_code, 422)
        self.assertIn("tool_choice", ctx.exception.detail)

        # 3. Grammar + tool_choice="auto" -> 422
        req = ChatRequest(
            messages=[Message(role="user", content="Classify")],
            grammar=grammar,
            tool_choice="auto",
        )
        with self.assertRaises(HTTPException) as ctx:
            _validate_grammar_compatibility(req)
        self.assertEqual(ctx.exception.status_code, 422)
        self.assertIn("tool_choice", ctx.exception.detail)

        # 4. Grammar + is_tool_call_request=True -> 422
        req = ChatRequest(
            messages=[Message(role="user", content="Classify")],
            grammar=grammar,
            is_tool_call_request=True,
        )
        with self.assertRaises(HTTPException) as ctx:
            _validate_grammar_compatibility(req)
        self.assertEqual(ctx.exception.status_code, 422)
        self.assertIn("is_tool_call_request", ctx.exception.detail)

        # 5. Grammar + abstract_tool_use=True -> 422
        req = ChatRequest(
            messages=[Message(role="user", content="Classify")],
            grammar=grammar,
            abstract_tool_use=True,
        )
        with self.assertRaises(HTTPException) as ctx:
            _validate_grammar_compatibility(req)
        self.assertEqual(ctx.exception.status_code, 422)
        self.assertIn("abstract_tool_use", ctx.exception.detail)

    def test_compatible_grammar_configuration(self):
        # Generic grammar with empty tools and tool_choice="none" -> OK!
        req = ChatRequest(
            messages=[Message(role="user", content="Classify")],
            grammar='root ::= "urgent" | "normal"',
            tools=[],
            tool_choice="none",
            abstract_tool_use=False,
        )
        try:
            _validate_grammar_compatibility(req)
        except Exception as exc:
            self.fail(f"Compatibility validation raised unexpectedly: {exc}")


class TestPayloadConstruction(unittest.TestCase):
    """Test _build_request with and without grammar."""

    def test_build_request_with_generic_grammar(self):
        grammar = 'root ::= "spam" | "ham"'
        req = ChatRequest(
            model="quince-llm",
            messages=[
                Message(role="system", content="Classify email."),
                Message(role="user", content="Subject: Buy now!"),
            ],
            grammar=grammar,
            stream=False,
            temperature=0.0,
            repeat_penalty=1.1,
            max_tokens=256,
        )
        payload = _build_request(req, stream=False)

        self.assertEqual(payload["model"], "quince-llm")
        self.assertEqual(payload["grammar"], grammar)
        self.assertEqual(payload["temperature"], 0.0)
        self.assertEqual(payload["repeat_penalty"], 1.1)
        self.assertEqual(payload["max_tokens"], 256)
        self.assertFalse(payload["stream"])

    def test_build_request_without_grammar(self):
        req = ChatRequest(
            messages=[Message(role="user", content="Hello")],
            stream=False,
            temperature=0.7,
        )
        payload = _build_request(req, stream=False)

        self.assertNotIn("grammar", payload)
        self.assertEqual(payload["temperature"], 0.7)

    def test_build_request_tool_call_grammar_preserved(self):
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "lookup_user",
                    "description": "Look up user info",
                    "parameters": {
                        "type": "object",
                        "properties": {"user_id": {"type": "string"}},
                        "required": ["user_id"],
                    },
                },
            }
        ]
        req = ChatRequest(
            messages=[Message(role="user", content="Find Alice")],
            tools=tools,
            tool_choice="required",
        )
        payload = _build_request(req, stream=False)

        self.assertIn("grammar", payload)
        self.assertIn("lookup_user", payload["grammar"])
        self.assertIn("<tool_call>", payload["grammar"])
        self.assertEqual(payload["temperature"], 0)
        self.assertEqual(payload["repeat_penalty"], 1.0)


class TestInferenceAndMultiFruitIntegration(unittest.IsolatedAsyncioTestCase):
    """Test inference workflows and Multi-Fruit metadata."""

    @patch("src.clients.llama_llm._ensure_model_loaded", new_callable=AsyncMock)
    @patch("httpx.AsyncClient.post")
    async def test_non_streaming_grammar_inference_abstracted(self, mock_post, mock_ensure):
        mock_ensure.return_value = True

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "id": "chatcmpl-123",
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": "<thinking>Analyzing...</thinking>urgent",
                    },
                    "finish_reason": "stop",
                }
            ],
        }
        mock_post.return_value = mock_resp

        req = ChatRequest(
            messages=[Message(role="user", content="Analyze priority")],
            grammar='root ::= "urgent" | "normal"',
            abstracted=True,
        )

        response_obj = MagicMock()
        response_obj.headers = {}
        result = await _chat(
            req,
            application="plum",
            request_id="req-plum-001",
            response=response_obj,
        )

        self.assertEqual(result, "urgent")
        self.assertEqual(response_obj.headers.get("X-Basket-Application"), "plum")
        self.assertEqual(response_obj.headers.get("X-Request-ID"), "req-plum-001")

        # Verify payload sent to llama.cpp
        call_kwargs = mock_post.call_args[1]
        sent_payload = call_kwargs["json"]
        self.assertEqual(sent_payload["grammar"], 'root ::= "urgent" | "normal"')

    @patch("src.clients.llama_llm._ensure_model_loaded", new_callable=AsyncMock)
    @patch("httpx.AsyncClient.post")
    async def test_non_streaming_grammar_inference_raw(self, mock_post, mock_ensure):
        mock_ensure.return_value = True

        raw_data = {
            "id": "chatcmpl-456",
            "choices": [
                {
                    "message": {"role": "assistant", "content": '{"category": "work"}'},
                    "finish_reason": "stop",
                }
            ],
        }
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = raw_data
        mock_post.return_value = mock_resp

        req = ChatRequest(
            messages=[Message(role="user", content="Get JSON")],
            grammar='root ::= "{\\"category\\": \\"work\\"}"',
            abstracted=False,
        )

        result = await _chat(req, application="plum")
        self.assertEqual(result, raw_data)

    @patch("src.clients.llama_llm._ensure_model_loaded", new_callable=AsyncMock)
    @patch("httpx.AsyncClient.send")
    @patch("httpx.AsyncClient.build_request")
    async def test_streaming_grammar_inference(self, mock_build, mock_send, mock_ensure):
        mock_ensure.return_value = True

        mock_response = AsyncMock()
        mock_response.status_code = 200

        async def fake_aiter_lines():
            yield "data: {\"choices\": [{\"delta\": {\"content\": \"urg\"}}]}"
            yield "data: {\"choices\": [{\"delta\": {\"content\": \"ent\"}}]}"
            yield "data: [DONE]"

        mock_response.aiter_lines = fake_aiter_lines
        mock_send.return_value = mock_response

        req = ChatRequest(
            messages=[Message(role="user", content="Stream priority")],
            grammar='root ::= "urgent" | "normal"',
            stream=True,
        )

        streaming_response = await _chat(
            req,
            application="plum",
            request_id="stream-req-002",
        )

        self.assertEqual(streaming_response.headers.get("X-Basket-Application"), "plum")
        self.assertEqual(streaming_response.headers.get("X-Request-ID"), "stream-req-002")

        tokens = []
        async for token in streaming_response.body_iterator:
            tokens.append(token)
        self.assertEqual("".join(tokens), "urgent")

    @patch("src.clients.llama_llm._ensure_model_loaded", new_callable=AsyncMock)
    @patch("httpx.AsyncClient.post")
    async def test_concurrent_multi_fruit_requests(self, mock_post, mock_ensure):
        """Simulate concurrent requests from Plum and Quince."""
        mock_ensure.return_value = True

        async def fake_post(url, **kwargs):
            payload = kwargs.get("json", {})
            grammar = payload.get("grammar")
            resp = MagicMock()
            resp.status_code = 200
            if grammar == 'root ::= "plum_output"':
                content = "plum_output"
            else:
                content = "quince_output"
            resp.json.return_value = {
                "id": f"chatcmpl-{id(payload)}",
                "choices": [{"message": {"role": "assistant", "content": content}}],
            }
            await asyncio.sleep(0.01)
            return resp

        mock_post.side_effect = fake_post

        req_plum = ChatRequest(
            messages=[Message(role="user", content="Plum task")],
            grammar='root ::= "plum_output"',
            abstracted=True,
        )
        req_quince = ChatRequest(
            messages=[Message(role="user", content="Quince task")],
            abstracted=True,
        )

        resp_plum = MagicMock()
        resp_plum.headers = {}
        resp_quince = MagicMock()
        resp_quince.headers = {}

        task_plum = _chat(req_plum, application="plum", request_id="id-plum", response=resp_plum)
        task_quince = _chat(req_quince, application="quince", request_id="id-quince", response=resp_quince)

        res_plum, res_quince = await asyncio.gather(task_plum, task_quince)

        self.assertEqual(res_plum, "plum_output")
        self.assertEqual(res_quince, "quince_output")
        self.assertEqual(resp_plum.headers.get("X-Basket-Application"), "plum")
        self.assertEqual(resp_plum.headers.get("X-Request-ID"), "id-plum")
        self.assertEqual(resp_quince.headers.get("X-Basket-Application"), "quince")
        self.assertEqual(resp_quince.headers.get("X-Request-ID"), "id-quince")


class TestQuinceMCPPreservation(unittest.TestCase):
    """Test Quince MCP integration preservation."""

    def test_quince_mcp_client_defaults(self):
        client = QuinceMCPClient()
        self.assertIn("quince", str(client._stdio_server.command).lower())
        self.assertIn("run_mcp.py", str(client._stdio_server.args[0]))
        self.assertEqual(client._stdio_server.args[1:], ["--transport", "stdio"])

    def test_to_openai_tool_conversion(self):
        client = QuinceMCPClient()
        tool_spec = {
            "tool_id": "test_mcp_tool",
            "description": "Performs testing",
            "arguments": {
                "param1": {"type": "string", "description": "A param"},
            },
            "required_arguments": ["param1"],
        }
        converted = client._to_openai_tool(tool_spec)
        self.assertEqual(converted["type"], "function")
        self.assertEqual(converted["function"]["name"], "test_mcp_tool")
        self.assertEqual(converted["function"]["description"], "Performs testing")
        self.assertIn("param1", converted["function"]["parameters"]["properties"])
        self.assertEqual(converted["function"]["parameters"]["required"], ["param1"])

    def test_existing_tool_grammar_and_parse(self):
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "root--chat--reply",
                    "description": "Reply in chat",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "response": {"type": "string", "description": "Message"},
                        },
                        "required": ["response"],
                    },
                },
            }
        ]
        grammar = _get_tool_call_grammar(tools)
        self.assertIn("root--chat--reply", grammar)
        self.assertIn("root ::=", grammar)

        raw_llm_output = (
            "<tool_call>\n"
            "<function=root--chat--reply>\n"
            "<parameter=response>\n"
            "Hello from Quince!\n"
            "</parameter>\n"
            "</function>\n"
            "</tool_call>"
        )
        parsed = _parse_grammar_tool_call(raw_llm_output, tools)
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed["name"], "root--chat--reply")
        args = json.loads(parsed["arguments"])
        self.assertEqual(args["response"], "Hello from Quince!")


class TestFastAPIRoutes(unittest.TestCase):
    """Test HTTP routes on the FastAPI router with TestClient."""

    def setUp(self):
        # Create a fresh client for the app without invoking lifespan jobs
        self.client = TestClient(app, raise_server_exceptions=False)

    @patch("src.apis.llm._chat", new_callable=AsyncMock)
    def test_post_chat_success_with_plum_headers(self, mock_chat):
        mock_chat.return_value = "classified_email"

        payload = {
            "model": "quince-llm",
            "messages": [
                {"role": "system", "content": "Classify email"},
                {"role": "user", "content": "Order #1234"},
            ],
            "grammar": 'root ::= "order" | "inquiry"',
            "tools": [],
            "tool_choice": "none",
        }
        headers = {
            "X-Basket-Application": "plum",
            "X-Request-ID": "plum-test-request-42",
        }

        # Simulate _chat setting response headers
        async def fake_chat(req, application=None, request_id=None, response=None):
            if response is not None:
                response.headers["X-Request-ID"] = request_id or "auto-id"
                if application:
                    response.headers["X-Basket-Application"] = application
            return "order"

        mock_chat.side_effect = fake_chat

        response = self.client.post("/llm/chat", json=payload, headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), "order")
        self.assertEqual(response.headers.get("x-basket-application"), "plum")
        self.assertEqual(response.headers.get("x-request-id"), "plum-test-request-42")

    def test_post_chat_invalid_grammar_returns_422(self):
        payload = {
            "messages": [{"role": "user", "content": "Hi"}],
            "grammar": "invalid_grammar_no_root",
        }
        response = self.client.post("/llm/chat", json=payload)
        self.assertEqual(response.status_code, 422)
        self.assertIn("missing required 'root' rule", response.text)

    def test_post_chat_conflict_returns_422(self):
        payload = {
            "messages": [{"role": "user", "content": "Hi"}],
            "grammar": 'root ::= "yes"',
            "tools": [
                {"type": "function", "function": {"name": "test"}}
            ],
        }
        response = self.client.post("/llm/chat", json=payload)
        self.assertEqual(response.status_code, 422)
        self.assertIn("cannot provide both 'grammar' and 'tools'", response.text)

    @patch("src.apis.llm._get_models", new_callable=AsyncMock)
    def test_get_models_with_metadata_headers(self, mock_get_models):
        mock_get_models.return_value = {"data": [{"id": "quince-llm"}]}

        headers = {
            "X-Basket-Application": "plum",
            "X-Request-ID": "plum-models-01",
        }
        response = self.client.get("/llm/models", headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers.get("x-basket-application"), "plum")
        self.assertEqual(response.headers.get("x-request-id"), "plum-models-01")
        self.assertEqual(response.json(), {"data": [{"id": "quince-llm"}]})

    @patch("src.apis.llm._load_model", new_callable=AsyncMock)
    def test_load_model_with_metadata_headers(self, mock_load):
        mock_load.return_value = {"status": "already_loaded", "model": "quince-llm"}

        headers = {
            "X-Basket-Application": "plum",
            "X-Request-ID": "plum-load-01",
        }
        response = self.client.post("/llm/load?model_id=quince-llm", headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers.get("x-basket-application"), "plum")
        self.assertEqual(response.headers.get("x-request-id"), "plum-load-01")

    @patch("src.apis.llm._unload_model", new_callable=AsyncMock)
    def test_unload_model_with_metadata_headers(self, mock_unload):
        mock_unload.side_effect = HTTPException(status_code=501, detail="Model unloading is not supported.")

        headers = {
            "X-Basket-Application": "plum",
            "X-Request-ID": "plum-unload-01",
        }
        response = self.client.post("/llm/unload?instance_id=quince-llm", headers=headers)
        self.assertEqual(response.status_code, 501)
        self.assertEqual(response.headers.get("x-basket-application"), "plum")
        self.assertEqual(response.headers.get("x-request-id"), "plum-unload-01")


if __name__ == "__main__":
    unittest.main()
