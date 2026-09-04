import pathlib
import sys
import unittest


BENCH_DIR = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(BENCH_DIR))

import broker


class LivePayloadTests(unittest.TestCase):
    def test_live_hero_preserves_inventory_progress(self):
        summary = {key: index for index, key in enumerate(broker.LIVE_HERO_FIELDS)}
        live = broker.live_hero(summary)
        self.assertEqual(set(live), set(broker.LIVE_HERO_FIELDS))
        self.assertEqual(live["inventory_distinct"], summary["inventory_distinct"])
        self.assertEqual(live["picked_item"], summary["picked_item"])

    def test_live_timing_contract_includes_submitted_input_totals(self):
        summary = {key: index for index, key in enumerate(broker.LIVE_TIMING_FIELDS)}
        live = broker.live_timing(summary)
        for field in ("decision_calls", "key_events", "input_frames", "wait_calls"):
            self.assertEqual(live[field], summary[field])


if __name__ == "__main__":
    unittest.main()
