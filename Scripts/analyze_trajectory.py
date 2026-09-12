#!/usr/bin/env python3
"""Analyze action timing and optional position samples in a saved recording."""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "server"))
from trajectory import analyze  # noqa: E402


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("recording", type=Path)
parser.add_argument("--window", type=int, default=25)
args = parser.parse_args()
if args.window < 1:
    parser.error("--window must be positive")
print(json.dumps(analyze(args.recording, window_size=args.window),
                 ensure_ascii=False, indent=2))
