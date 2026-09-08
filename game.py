import sys
import json
import urllib.request
import subprocess
from PIL import Image

BASE_URL = "http://34.66.39.184:8080"
AGENT = "gemini-3.7-flash"

def post_json(endpoint, data):
    url = f"{BASE_URL}{endpoint}"
    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "X-Agent": AGENT
        }
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

def ocr_screen(img_path="/private/tmp/screen.png"):
    # Upscale 4x nearest
    im = Image.open(img_path)
    im_large = im.resize((im.width * 4, im.height * 4), Image.Resampling.NEAREST)
    large_path = "/private/tmp/screen_large.png"
    im_large.save(large_path)

    # Run tesseract
    res = subprocess.run(
        ['tesseract', large_path, 'stdout', '--tessdata-dir', '/tmp', '-l', 'chi_tra+chi_sim+eng', '--psm', '6'],
        capture_output=True, text=True
    )
    ocr_psm6 = res.stdout.strip()

    res11 = subprocess.run(
        ['tesseract', large_path, 'stdout', '--tessdata-dir', '/tmp', '-l', 'chi_tra+chi_sim+eng', '--psm', '11'],
        capture_output=True, text=True
    )
    ocr_psm11 = res11.stdout.strip()
    return ocr_psm6, ocr_psm11

def render_ansi(img_path="/private/tmp/screen.png", width=80):
    im = Image.open(img_path).convert("RGB")
    aspect = im.height / im.width
    height = int(width * aspect / 2) * 2
    im = im.resize((width, height), Image.Resampling.BILINEAR)
    pixels = im.load()
    
    lines = []
    for y in range(0, height, 2):
        line = []
        for x in range(width):
            r1, g1, b1 = pixels[x, y]
            r2, g2, b2 = pixels[x, y + 1] if y + 1 < height else (0, 0, 0)
            line.append(f"\033[38;2;{r1};{g1};{b1}m\033[48;2;{r2};{g2};{b2}m▀")
        line.append("\033[0m")
        lines.append("".join(line))
    return "\n".join(lines)

def cmd_screen():
    path = get_screen()
    p6, p11 = ocr_screen(path)
    print("=== OCR PSM 6 ===")
    print(p6)
    print("=== OCR PSM 11 ===")
    print(p11)

def cmd_view(width=80):
    path = get_screen()
    print(render_ansi(path, width=width))
    p6, p11 = ocr_screen(path)
    print("=== OCR PSM 6 ===")
    print(p6)

def cmd_key(key, times=1, hold=None):
    payload = {"key": key}
    if times > 1:
        payload["times"] = times
    if hold is not None:
        payload["hold"] = hold
    res = post_json("/api/key", payload)
    print(f"KEY '{key}' -> {res}")
    return res

def cmd_keys(keys):
    res = post_json("/api/keys", {"keys": keys})
    print(f"KEYS {keys} -> {res}")
    return res

def cmd_wait(ms=1000):
    res = post_json("/api/wait", {"ms": ms})
    print(f"WAIT {ms}ms -> {res}")
    return res

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 game.py [screen|view|key <k>|keys <k1> <k2>...|wait <ms>|hold <k> <ms>]")
        sys.exit(1)
    
    cmd = sys.argv[1]
    if cmd == "screen":
        cmd_screen()
    elif cmd == "view":
        w = int(sys.argv[2]) if len(sys.argv) > 2 else 80
        cmd_view(w)
    elif cmd == "key":
        k = sys.argv[2]
        times = int(sys.argv[3]) if len(sys.argv) > 3 else 1
        cmd_key(k, times)
        cmd_screen()
    elif cmd == "hold":
        k = sys.argv[2]
        ms = int(sys.argv[3]) if len(sys.argv) > 3 else 120
        cmd_key(k, hold=ms)
        cmd_screen()
    elif cmd == "keys":
        keys = sys.argv[2:]
        cmd_keys(keys)
        cmd_screen()
    elif cmd == "wait":
        ms = int(sys.argv[2]) if len(sys.argv) > 2 else 1000
        cmd_wait(ms)
        cmd_screen()
    else:
        print(f"Unknown command {cmd}")
