#!/usr/bin/env python3
import urllib.request, json, base64, time
from PIL import Image, ImageChops
import io

AGENT = "pi-agent"
API_BASE = "http://34.66.39.184:8080"

OPP = {"kp7": "kp3", "kp3": "kp7", "kp9": "kp1", "kp1": "kp9"}

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

def try_step(k, times=1):
    im1 = get_screen()
    res = call("/api/key", {"key": k, "times": times})
    time.sleep(0.05)
    im2 = get_screen()
    d = ImageChops.difference(im1, im2).getbbox()
    moved = d is not None and (d[2]-d[0])*(d[3]-d[1]) > 5000
    return moved, im2

def check_scene_transition(im):
    colors = im.getcolors(320*200)
    top_c = sorted(colors, key=lambda x: x[0], reverse=True)[0]
    if top_c[1] == (0, 0, 0) and top_c[0] > 50000:
        return True
    return False

def check_inside_building(im):
    # Check if menu has 4 options instead of 6 or indoor colors
    pass

def navigate(preferred_order=["kp9", "kp7", "kp3", "kp1"], steps=40):
    last_dir = None
    for step in range(steps):
        im = get_screen()
        if check_scene_transition(im):
            print("Scene transition! Waiting 1500ms...")
            time.sleep(1.5)
            im = get_screen()
            im.save(f"transition_{step}.png")
            print("Saved transition screen!")
            return True
        
        # Order directions: preferred first, but put opposite of last_dir at the very end!
        dirs = [d for d in preferred_order if d != OPP.get(last_dir)]
        if last_dir and OPP.get(last_dir) in preferred_order:
            dirs.append(OPP[last_dir])
        
        moved = False
        for k in dirs:
            ok, im2 = try_step(k, 1)
            if ok:
                print(f"Step {step:2d}: moved {k}")
                last_dir = k
                moved = True
                break
        
        if not moved:
            print(f"Step {step:2d}: completely blocked!")
            break
    
    im = get_screen()
    im.save("nav_final.png")
    return False

if __name__ == "__main__":
    navigate()
