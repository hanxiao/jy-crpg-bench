import pathlib
import sys
import unittest


BENCH_DIR = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(BENCH_DIR))

import broker


class PublicSessionRouteTests(unittest.TestCase):
    def test_only_visual_benchmark_routes_are_public(self):
        allowed = {
            ("GET", "api/screen"),
            ("GET", "api/help"),
            ("GET", "api/keys"),
            ("OPTIONS", "api/keys"),
            ("OPTIONS", "api/screen"),
            ("POST", "api/key"),
            ("POST", "api/keys"),
            ("POST", "api/wait"),
        }
        for method, path in allowed:
            self.assertTrue(broker.public_session_route(method, path))

        for method, path in {
            ("GET", "status"),
            ("GET", "api/history"),
            ("GET", "api/recording"),
            ("POST", "api/reset"),
            ("POST", "api/snapshot"),
            ("GET", ""),
            ("OPTIONS", "status"),
            ("OPTIONS", "api/history"),
        }:
            self.assertFalse(broker.public_session_route(method, path))

    def test_public_preflight_and_proxy_responses_allow_cross_origin_reads(self):
        preflight = broker.proxy_preflight("api/keys")
        self.assertEqual(preflight.status, 204)
        self.assertEqual(preflight.headers["Access-Control-Allow-Origin"], "*")
        self.assertEqual(preflight.headers["Access-Control-Allow-Methods"], "GET, OPTIONS, POST")
        self.assertIn("X-Agent", preflight.headers["Access-Control-Allow-Headers"])

        screen_preflight = broker.proxy_preflight("api/screen")
        self.assertEqual(screen_preflight.headers["Access-Control-Allow-Methods"], "GET, OPTIONS")

        headers = broker.proxy_cors_headers("application/json")
        self.assertEqual(headers["Access-Control-Allow-Origin"], "*")
        self.assertEqual(headers["Content-Type"], "application/json")
        self.assertEqual(headers["Access-Control-Expose-Headers"], "X-Bench-Remaining")

    def test_only_the_spectator_socket_is_public(self):
        self.assertTrue(broker.public_session_route("GET", "ws", websocket=True))
        self.assertFalse(broker.public_session_route("GET", "status", websocket=True))
        self.assertFalse(broker.public_session_route("POST", "ws", websocket=True))


if __name__ == "__main__":
    unittest.main()
