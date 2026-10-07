"""A harness withdraws a session its model should not have opened."""
import asyncio
from copy import deepcopy
import unittest
from unittest.mock import patch

from aiohttp import web
from aiohttp.test_utils import AioHTTPTestCase

import warden
with patch('ctypes.CDLL'):
    import server


class WithdrawTests(unittest.TestCase):
    def setUp(self):
        self.old = deepcopy(warden.run)
        self.addCleanup(lambda: (warden.run.clear(), warden.run.update(self.old)))
        warden.run.update(done=None, result=None)

    def test_a_running_run_is_withdrawn_once(self):
        self.assertTrue(warden.withdraw("a second session\n"))
        self.assertEqual(warden.run["done"], "withdrawn")
        self.assertEqual(warden.why_text(),
                         "withdrawn by the agent's harness: a second session")
        self.assertFalse(warden.withdraw("again"))

    def test_an_ended_run_is_not_withdrawn(self):
        warden.run["done"] = "time"
        self.assertFalse(warden.withdraw("late"))
        self.assertEqual(warden.run["done"], "time")


class WithdrawEndpointTests(AioHTTPTestCase):
    async def get_application(self):
        app = web.Application()
        app.router.add_post("/bench/withdraw", server.bench_withdraw)
        return app

    def setUp(self):
        super().setUp()
        self.old = deepcopy(warden.run)
        self.addCleanup(lambda: (warden.run.clear(), warden.run.update(self.old)))
        warden.run.update(done=None, result=None)
        for p in (patch.object(warden, "ON", True),
                  patch.dict("os.environ", {"QUNXIA_RESET_TOKEN": "op"})):
            p.start()
            self.addCleanup(p.stop)

    async def test_only_the_operator_withdraws(self):
        r = await self.client.post("/bench/withdraw", json={"why": "x"})
        self.assertEqual(r.status, 403)
        self.assertIsNone(warden.run["done"])

    async def test_the_operator_withdraws_and_a_second_call_is_refused(self):
        r = await self.client.post("/bench/withdraw", json={"why": "x"},
                                   headers={"X-Reset-Token": "op"})
        self.assertEqual(r.status, 200)
        self.assertEqual(warden.run["done"], "withdrawn")
        r = await self.client.post("/bench/withdraw", json={},
                                   headers={"X-Reset-Token": "op"})
        self.assertEqual(r.status, 409)


if __name__ == "__main__":
    unittest.main()
