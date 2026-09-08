import json
import urllib.request
import subprocess
from PIL import Image

BASE_URL = "http://34.66.39.184:8080"
AGENT = "gemini-3.7-flash"

def post_key(key, times=1, hold=None):
    payload = {"key": key}
    if times > 1:
        payload["times"] = times
    if hold is not None:
        payload["hold"] = hold
    req = urllib.request.Request(
        f"{BASE_URL}/api/key",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "X-Agent": AGENT}
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))

def get_screen(save_path="/private/tmp/screen.png"):
    req = urllib.request.Request(
        f"{BASE_URL}/api/screen?format=png",
        headers={"X-Agent": AGENT}
    )
    with urllib.request.urlopen(req) as resp:
        data = resp.read()
    with open(save_path, "wb") as f:
        f.write(data)
    return save_path

def move_and_diff(key, times=1, hold=None):
    get_screen("/private/tmp/before.png")
    im_before = Image.open("/private/tmp/before.png").convert("L")
    
    res = post_key(key, times, hold)
    
    get_screen("/private/tmp/after.png")
    im_after = Image.open("/private/tmp/after.png").convert("L")
    
    # Simple pixel difference in scenery area (e.g. top half y=0..120)
    w, h = im_before.size
    diff = 0
    p1 = im_before.load()
    p2 = im_after.load()
    for y in range(0, 140):
        for x in range(0, w):
            diff += abs(p1[x, y] - p2[x, y])
    avg_diff = diff / (w * 140)
    print(f"KEY: {key:4s} x{times} (hold={hold}) -> changed: {res.get('changed')}, Scenery Diff: {avg_diff:.2f}")
    return avg_diff

if __name__ == "__main__":
    import sys
    k = sys.argv[1] if len(sys.argv) > 1 else 'kp1'
    t = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    h = int(sys.argv[3]) if len(sys.argv) > 3 else None
    move_and_diff(k, t, h)
