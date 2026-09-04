import struct
import unittest

from server.state_reader import (
    INVENTORY_BYTES,
    INVENTORY_SLOTS,
    decode_inventory,
    inventory_gained,
)


def memory_with_inventory(entries):
    values = []
    for item_id, amount in entries:
        values.extend((item_id, amount))
    values.extend((-1, 0) * (INVENTORY_SLOTS - len(entries)))
    bag = struct.pack(f"<{len(values)}h", *values)
    prefix = b"prefix"
    return prefix + bag + b"character records", len(prefix) + INVENTORY_BYTES


class InventoryDecoderTests(unittest.TestCase):
    def test_reads_item_zero_and_public_bag(self):
        mem, base = memory_with_inventory([(0, 3), (2, 3), (174, 160), (182, 1)])
        self.assertEqual(decode_inventory(mem, base),
                         {0: 3, 2: 3, 174: 160, 182: 1})

    def test_detects_a_new_item_or_increased_amount(self):
        opening = {0: 3, 2: 3}
        self.assertFalse(inventory_gained(opening, dict(opening)))
        self.assertTrue(inventory_gained(opening, {0: 3, 2: 4}))
        self.assertTrue(inventory_gained(opening, {0: 3, 2: 3, 182: 1}))

    def test_rejects_non_inventory_blocks(self):
        mem, base = memory_with_inventory([(0, 3)])
        broken = bytearray(mem)
        struct.pack_into("<hh", broken, len(b"prefix") + 8, 182, 1)
        self.assertIsNone(decode_inventory(bytes(broken), base))


if __name__ == "__main__":
    unittest.main()
