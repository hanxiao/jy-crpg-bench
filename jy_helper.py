#!/usr/bin/env python3
import sys
import json
import base64
import urllib.request
import subprocess
from PIL import Image, ImageEnhance, ImageOps
import io

API_BASE = "http://34.66.39.184:8080"
AGENT = "pi-agent"

def call_api(endpoint, data=None):
    url = f"{API_BASE}{endpoint}"
    headers = {"X-Agent": AGENT}
    req_data = None
    if data is not None:
        headers["Content-Type"] = "application/json"
        req_data = json.dumps(data).encode("utf-8")
    req = urllib.request.Request(url, data=req_data, headers=headers)
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))

def get_screen():
    res = call_api("/api/screen")
    img_b64 = res["image"]
    if "," in img_b64:
        img_b64 = img_b64.split(",", 1)[1]
    raw = base64.b64decode(img_b64)
    im = Image.open(io.BytesIO(raw)).convert("RGB")
    return im, res.get("frame")

def send_key(key, times=1, hold=None):
    data = {"key": key}
    if times > 1:
        data["times"] = times
    if hold is not None:
        data["hold"] = hold
    return call_api("/api/key", data)

def send_keys(keys):
    return call_api("/api/keys", {"keys": keys})

def wait_ms(ms=1000):
    return call_api("/api/wait", {"ms": ms})

def ocr_image(img, psm=6, lang="chi_tra"):
    # Upscale 3x and save
    w, h = img.size
    img_scaled = img.resize((w * 3, h * 3), Image.Resampling.NEAREST)
    img_scaled.save("tmp_ocr.png")
    import os
    env = os.environ.copy()
    env["TESSDATA_PREFIX"] = "/tmp/tessdata"
    cmd = ["/opt/homebrew/bin/tesseract", "./tmp_ocr.png", "stdout", "-l", lang, "--psm", str(psm)]
    res = subprocess.run(cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return res.stdout.strip()

def analyze_screen():
    im, frame = get_screen()
    im.save("screen_latest.png")
    w, h = im.size
    print(f"Screen frame: {frame}, size: {w}x{h}")
    
    # Check if there is text in dialogue box (bottom: y=130..200 or top: y=0..60)
    # Check for white / light colored pixels (Chinese text in DOS JY is often white: RGB(255,255,255) or yellow: RGB(255,255,85))
    pixels = im.load()
    
    # Check regions
    # Bottom dialog box
    bottom_crop = im.crop((10, 130, 310, 195))
    top_crop = im.crop((10, 5, 310, 70))
    center_menu = im.crop((50, 40, 270, 160))
    right_menu = im.crop((230, 20, 315, 180))
    left_menu = im.crop((5, 20, 90, 180))
    
    # Try binarizing for OCR: text colors in JY:
    # High luminance text
    def binarize(crop, threshold=180):
        gray = crop.convert("L")
        return gray.point(lambda p: 255 if p > threshold else 0)

    # Let's OCR full screen, bottom, top, right, etc.
    full_text = ocr_image(im, psm=11)
    bottom_text = ocr_image(binarize(bottom_crop), psm=6)
    top_text = ocr_image(binarize(top_crop), psm=6)
    right_text = ocr_image(binarize(right_menu), psm=6)
    center_text = ocr_image(binarize(center_menu), psm=6)
    
    print("--- OCR Analysis ---")
    if bottom_text:
        print(f"Bottom Dialog OCR: {bottom_text}")
    if top_text:
        print(f"Top Dialog OCR: {top_text}")
    if right_text:
        print(f"Right Menu OCR: {right_text}")
    if center_text:
        print(f"Center Menu OCR: {center_text}")
    if full_text:
        print(f"Full Screen OCR:\n{full_text}")

if __name__ == "__main__":
    analyze_screen()
