import unittest
from unittest.mock import patch, MagicMock
from starlette.testclient import TestClient

from src.control.server import app, KNOWN_ROUTES
from src.control.registry import SERVICES, FRUITS


class TestControlAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_health_check(self):
        resp = self.client.get("/api/health")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "healthy")
        self.assertEqual(data["service"], "basket-control")
        self.assertEqual(data["port"], 10020)
        self.assertIn("timestamp", data)

    def test_overview_endpoint(self):
        resp = self.client.get("/api/overview")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("metrics", data)
        self.assertIn("services", data)
        self.assertIn("fruits", data)
        self.assertIn("recent_operations", data)

        metrics = data["metrics"]
        self.assertEqual(metrics["total_services"], len(SERVICES))
        self.assertEqual(metrics["total_routes"], len(KNOWN_ROUTES))
        self.assertIn("nginx_state", metrics)

    def test_services_list(self):
        resp = self.client.get("/api/services")
        self.assertEqual(resp.status_code, 200)
        services = resp.json()
        self.assertEqual(len(services), len(SERVICES))
        for svc in services:
            self.assertIn("id", svc)
            self.assertIn("name", svc)
            self.assertIn("status", svc)
            self.assertIn("is_running", svc)
            self.assertIn("is_healthy", svc)

    def test_single_service_found_and_not_found(self):
        # Existing service
        resp = self.client.get("/api/services/nginx")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["id"], "nginx")

        # Unknown service -> 404
        resp_404 = self.client.get("/api/services/non-existent-service")
        self.assertEqual(resp_404.status_code, 404)
        self.assertIn("not found", resp_404.json()["detail"].lower())

    def test_service_start_end_restart_endpoints(self):
        with patch("src.control.server.MANAGERS") as mock_managers:
            mock_mgr = MagicMock()
            mock_mgr.start.return_value = {"success": True, "action": "start"}
            mock_mgr.stop.return_value = {"success": True, "action": "end"}
            mock_mgr.restart.return_value = {"success": True, "action": "restart"}
            mock_managers.__contains__.side_effect = lambda key: key == "dummy-service"
            mock_managers.__getitem__.return_value = mock_mgr

            # Start
            r_start = self.client.post("/api/services/dummy-service/start")
            self.assertEqual(r_start.status_code, 200)
            self.assertTrue(r_start.json()["success"])

            # End
            r_end = self.client.post("/api/services/dummy-service/end")
            self.assertEqual(r_end.status_code, 200)
            self.assertTrue(r_end.json()["success"])

            # Restart
            r_restart = self.client.post("/api/services/dummy-service/restart")
            self.assertEqual(r_restart.status_code, 200)
            self.assertTrue(r_restart.json()["success"])

    def test_all_services_endpoints(self):
        with patch("src.control.server.start_all_services", return_value={"success": True, "action": "start_all"}), \
             patch("src.control.server.stop_all_services", return_value={"success": True, "action": "end_all"}), \
             patch("src.control.server.restart_all_services", return_value={"success": True, "action": "restart_all"}):

            r_start_all = self.client.post("/api/services/all/start")
            self.assertEqual(r_start_all.status_code, 200)
            self.assertTrue(r_start_all.json()["success"])

            r_end_all = self.client.post("/api/services/all/end")
            self.assertEqual(r_end_all.status_code, 200)
            self.assertTrue(r_end_all.json()["success"])

            r_restart_all = self.client.post("/api/services/all/restart")
            self.assertEqual(r_restart_all.status_code, 200)
            self.assertTrue(r_restart_all.json()["success"])

    def test_fruits_list_and_actions(self):
        resp = self.client.get("/api/fruits")
        self.assertEqual(resp.status_code, 200)
        fruits = resp.json()
        self.assertEqual(len(fruits), len(FRUITS))

        # Lemon is an Android client
        r_lemon_start = self.client.post("/api/fruits/lemon/start")
        self.assertEqual(r_lemon_start.status_code, 200)
        self.assertTrue(r_lemon_start.json()["success"])
        self.assertIn("android", r_lemon_start.json()["message"].lower())

        # Unknown fruit -> 404
        r_unknown = self.client.post("/api/fruits/unknown-fruit/start")
        self.assertEqual(r_unknown.status_code, 404)

    def test_logs_endpoint(self):
        resp = self.client.get("/api/logs/nginx?tail=20")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["service_id"], "nginx")
        self.assertIn("lines", data)

        # 404 for unknown service
        r_404 = self.client.get("/api/logs/non-existent")
        self.assertEqual(r_404.status_code, 404)

    def test_routes_endpoint(self):
        resp = self.client.get("/api/routes")
        self.assertEqual(resp.status_code, 200)
        routes = resp.json()
        self.assertEqual(len(routes), len(KNOWN_ROUTES))
        for r in routes:
            self.assertIn("id", r)
            self.assertIn("reverse_proxy_url", r)
            self.assertIn("is_live", r)

    def test_nginx_status_and_validate(self):
        resp = self.client.get("/api/nginx/status")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("status", data)
        self.assertIn("listening_80", data)
        self.assertIn("listening_443", data)

        r_val = self.client.post("/api/nginx/validate")
        self.assertEqual(r_val.status_code, 200)
        self.assertTrue(r_val.json()["valid"])

    def test_cors_headers_for_dashboard(self):
        allowed_origins = [
            "http://127.0.0.1:10020",
            "http://localhost:10020",
            "http://basket.jam",
            "https://basket.jam",
        ]
        for origin in allowed_origins:
            with self.subTest(origin=origin):
                resp = self.client.options(
                    "/api/health",
                    headers={
                        "Origin": origin,
                        "Access-Control-Request-Method": "GET",
                    },
                )
                self.assertEqual(
                    resp.headers.get("access-control-allow-origin"),
                    origin,
                    f"CORS origin {origin} was not allowed by server",
                )

    def test_spa_fallback(self):
        # Root GET /
        resp_root = self.client.get("/")
        self.assertEqual(resp_root.status_code, 200)

        # Arbitrary SPA client route
        resp_spa = self.client.get("/dashboard/services")
        self.assertEqual(resp_spa.status_code, 200)

        # API 404 should never fall back to SPA index
        resp_api = self.client.get("/api/non-existent-api-path")
        self.assertEqual(resp_api.status_code, 404)


if __name__ == "__main__":
    unittest.main()

