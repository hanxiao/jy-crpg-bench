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

def check_screen():
    path = get_screen()
    im = Image.open(path).convert("RGB")
    w, h = im.size
    
    # Check bottom 60 rows for dialogue box
    bottom = im.crop((10, 130, 310, 195))
    bottom_large = bottom.resize((bottom.width * 4, bottom.height * 4), Image.Resampling.NEAREST)
    bottom_large.save("/private/tmp/bottom.png")
    
    res_bottom = subprocess.run(
        ['tesseract', '/private/tmp/bottom.png', 'stdout', '--tessdata-dir', '/tmp', '-l', 'chi_tra+chi_sim+eng', '--psm', '6'],
        capture_output=True, text=True
    ).stdout.strip()
    
    # Check whole screen text
    large = im.resize((w * 4, h * 4), Image.Resampling.NEAREST)
    large.save("/private/tmp/screen_large.png")
    res_all = subprocess.run(
        ['tesseract', '/private/tmp/screen_large.png', 'stdout', '--tessdata-dir', '/tmp', '-l', 'chi_tra+chi_sim+eng', '--psm', '6'],
        capture_output=True, text=True
    ).stdout.strip()

    return res_bottom, res_all

def act_and_check(key, times=1, hold=None):
    res = post_key(key, times, hold)
    bot, all_txt = check_screen()
    print(f"Action: {key} (x{times}) -> changed: {res.get('changed')}")
    if bot:
        print(f"Bottom Text: {bot}")
    return res, bot, all_txt

if __name__ == "__main__":
    bot, all_txt = check_screen()
    print("Current Bottom:", bot)
    print("Current All:", all_txt)
