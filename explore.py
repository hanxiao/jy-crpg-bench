import time
import room
from PIL import Image
import subprocess

def talk_until_done():
    while True:
        res, bot, all_txt = room.act_and_check('space')
        # Check if dialog box exists
        # In dialog box, bottom crop usually has meaningful Chinese text
        im = Image.open('/private/tmp/screen.png')
        # Check if bottom has text box border or text
        bot, _ = room.check_screen()
        # If no meaningful dialogue, break
        # Let's filter out noise
        clean = "".join([c for c in bot if '\u4e00' <= c <= '\u9fff'])
        if len(clean) < 3:
            break
        print(f"DIALOG: {bot}")
        time.sleep(0.3)

def try_interact(key, times=1):
    room.post_key(key, times)
    room.post_key('space')
    bot, _ = room.check_screen()
    clean = "".join([c for c in bot if '\u4e00' <= c <= '\u9fff'])
    if len(clean) >= 3:
        print(f"Found interaction at {key} x{times}: {bot}")
        talk_until_done()
        return True
    return False

if __name__ == "__main__":
    print("Testing surrounding interactions...")
    for d in ['kp7', 'kp9', 'kp1', 'kp3']:
        for step in [1, 2]:
            print(f"Testing direction {d} step {step}")
            try_interact(d, step)
