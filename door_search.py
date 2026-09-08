#!/usr/bin/env python3
import urllib.request, json, base64, time
from PIL import Image, ImageChops
import io

AGENT = "pi-agent"
API_BASE = "http://34.66.39.184:8080"

def call(endpoint, data=None):
    url = f"{API_BASE}{endpoint}"
    headers = {"X-Agent": AGENT, "Content-Type": "application/json"}
    req_data = json.dumps(data).encode("utf-8") if data is not None else None
    req = urllib.request.Request(url, data=req_data, headers=headers)
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))

def get_screen():
    res = call("/api/screen")
    b64 = res["image"].split(",", 1)[1] if "," in res["image"] else res["image"]
    return Image.open(io.BytesIO(base64.b64decode(b64))).convert("RGB")

def is_transition(im):
    colors = im.getcolors(320*200)
    top_c = sorted(colors, key=lambda x: x[0], reverse=True)[0]
    return top_c[1] == (0, 0, 0) and top_c[0] > 50000

def check_inside(im):
    # If menu has only 4 options (medical, detox, item, status) instead of 6 (party, system)
    call("/api/key", {"key": "esc"})
    time.sleep(0.1)
    im_menu = get_screen()
    crop = im_menu.crop((20, 18, 62, 110))
    # Height of menu border: world map is ~90px (6 items), indoor is ~60px (4 items)
    # Close menu
    call("/api/key", {"key": "esc"})
    time.sleep(0.1)
    return im_menu

def probe_perimeter():
    print("Starting systematic perimeter probe around building...")
    # Test perimeter walk sequence:
    # Walk along kp9, testing kp3 / kp1 inward at each step
    # Walk along kp3, testing kp7 / kp1 inward at each step
    # Walk along kp1, testing kp9 / kp7 inward at each step
    # Walk along kp7, testing kp3 / kp9 inward at each step
    
    for side_name, walk_dir, test_dirs in [
        ("Side 1 (moving kp9)", "kp9", ["kp3", "kp1", "kp7"]),
        ("Side 2 (moving kp3)", "kp3", ["kp7", "kp9", "kp1"]),
        ("Side 3 (moving kp1)", "kp1", ["kp9", "kp3", "kp7"]),
        ("Side 4 (moving kp7)", "kp7", ["kp3", "kp9", "kp1"]),
    ]:
        print(f"\n--- {side_name} ---")
        for step in range(8):
            im1 = get_screen()
            call("/api/key", {"key": walk_dir, "times": 1})
            time.sleep(0.08)
            im2 = get_screen()
            diff = ImageChops.difference(im1, im2).getbbox()
            moved = diff is not None and (diff[2]-diff[0])*(diff[3]-diff[1]) > 5000
            print(f"  Step {step} along {walk_dir}: moved={moved}")
            
            # Test inward dirs
            for test_dir in test_dirs:
                im_before = get_screen()
                call("/api/key", {"key": test_dir, "times": 1})
                time.sleep(0.08)
                im_after = get_screen()
                if is_transition(im_after):
                    print(f"*** SCENE TRANSITION via {test_dir} at {side_name} step {step}! ***")
                    time.sleep(1.5)
                    im_room = get_screen()
                    im_room.save("entered_room_success.png")
                    return True
                # If moved inward, step back
                d_in = ImageChops.difference(im_before, im_after).getbbox()
                if d_in and (d_in[2]-d_in[0])*(d_in[3]-d_in[1]) > 5000:
                    print(f"    Tested inward {test_dir}: moved into tile! Testing enter...")
                    call("/api/key", {"key": "enter", "times": 1})
                    time.sleep(0.08)
                    if is_transition(get_screen()):
                        print("*** ENTERED VIA ENTER! ***")
                        time.sleep(1.5)
                        get_screen().save("entered_room_success.png")
                        return True
                    opp = {"kp7": "kp3", "kp3": "kp7", "kp9": "kp1", "kp1": "kp9"}[test_dir]
                    call("/api/key", {"key": opp, "times": 1})
                    time.sleep(0.08)
    return False

if __name__ == "__main__":
    probe_perimeter()
