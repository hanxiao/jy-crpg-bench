import sys
import os
import subprocess
from PIL import Image

def analyze_screen(img_path="/private/tmp/screen.png"):
    im = Image.open(img_path).convert("RGB")
    w, h = im.size
    
    # 1. Print small ANSI preview
    pw, ph = 80, 40
    pim = im.resize((pw, ph), Image.Resampling.BILINEAR)
    pix = pim.load()
    print("--- SCREEN VIEW ---")
    for y in range(0, ph, 2):
        row = []
        for x in range(pw):
            r1, g1, b1 = pix[x, y]
            r2, g2, b2 = pix[x, y+1] if y+1 < ph else (0,0,0)
            row.append(f"\033[38;2;{r1};{g1};{b1}m\033[48;2;{r2};{g2};{b2}m▀")
        row.append("\033[0m")
        print("".join(row))

    # 2. Text extraction via color filtering
    # Pure PIL
    text_img = Image.new("L", (w, h), 0)
    text_pix = text_img.load()
    raw_pix = im.load()
    for y in range(h):
        for x in range(w):
            r, g, b = raw_pix[x, y]
            # White or yellow or light cyan text
            if (r > 160 and g > 160 and b > 160) or (r > 180 and g > 180 and b < 100) or (r < 100 and g > 180 and b > 180):
                text_pix[x, y] = 255
            else:
                text_pix[x, y] = 0

    text_img_large = text_img.resize((w * 4, h * 4), Image.Resampling.NEAREST)
    text_img_large.save("/private/tmp/screen_text.png")

    # OCR on text mask
    res_mask = subprocess.run(
        ['tesseract', '/private/tmp/screen_text.png', 'stdout', '--tessdata-dir', '/tmp', '-l', 'chi_tra+eng', '--psm', '6'],
        capture_output=True, text=True
    ).stdout.strip()

    print("--- TEXT MASK OCR ---")
    print(res_mask if res_mask else "(none)")

if __name__ == "__main__":
    analyze_screen()
