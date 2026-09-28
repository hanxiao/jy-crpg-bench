"""The world map of the game at native scale, rendered from its data files.

    python worldmap.py            # writes worldmap.png and worldmap.json

The map is 480 x 480 tiles. EARTH, SURFACE and BUILDING hold one 16-bit picture
number per tile (twice the index into MMAP.GRP), BUILDX and BUILDY name the
anchor tile of the building that covers a tile, and MMAP.COL is the 6-bit
palette. A tile (x, y) is drawn with its centre at ((y - x) * 18, (x + y) * 9)
from the map origin, as the game draws it, ground and surface first and then
the buildings from the back row to the front. Each picture is run-length
coded: width, height, x and y offset, then per row a byte count followed by
(skip, n, n palette indices) runs. worldmap.json records the pixel of tile
(0, 0) so that a pixel converts back to a tile.
"""
import json
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
GAME = os.path.join(HERE, "..", "..", "..", "game")
sys.path.insert(0, os.path.join(HERE, "..", "..", "..", "server"))
from measure.worldmap import render, TW, TH  # noqa: E402  the service renders the same map


def to_tile(px, py, meta):
    """Pixel on worldmap.png to the tile (x, y) whose centre is nearest."""
    u = (px - meta["origin"][0]) / TW       # y - x
    v = (py - meta["origin"][1]) / TH       # x + y
    return (v - u) / 2, (v + u) / 2


def main():
    img, meta = render(GAME)
    Image.fromarray(img).save(os.path.join(HERE, "worldmap.png"))
    json.dump(meta, open(os.path.join(HERE, "worldmap.json"), "w"), indent=1)
    print("wrote worldmap.png", img.shape)


if __name__ == "__main__":
    main()
