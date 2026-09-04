"""Pure decoders for game data embedded in a DOSBox Pure savestate."""

import struct


# R*.GRP stores the public bag immediately before the character array: 200
# pairs of little-endian int16 values (item id, amount).
INVENTORY_SLOTS = 200
INVENTORY_BYTES = INVENTORY_SLOTS * 4
MAX_ITEM_ID = 199


def decode_inventory(mem: bytes, character_base: int):
    """Return ``{item_id: amount}``, or None when the block is implausible."""
    start = character_base - INVENTORY_BYTES
    if start < 0 or character_base > len(mem):
        return None

    values = struct.unpack_from(f"<{INVENTORY_SLOTS * 2}h", mem, start)
    inventory = {}
    empty_seen = False
    for slot in range(INVENTORY_SLOTS):
        item_id, amount = values[slot * 2:slot * 2 + 2]
        if item_id == -1 and amount == 0:
            empty_seen = True
            continue
        # The original game keeps occupied slots packed at the front.  These
        # checks prevent an unrelated 800-byte region being accepted as a bag.
        if (empty_seen or not 0 <= item_id <= MAX_ITEM_ID
                or not 0 < amount <= 32767 or item_id in inventory):
            return None
        inventory[item_id] = amount
    return inventory


def inventory_gained(baseline, current):
    """Return whether any item count exceeds the run's opening state."""
    return any(amount > baseline.get(item_id, 0)
               for item_id, amount in current.items())
