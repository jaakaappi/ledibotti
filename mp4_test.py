import time
import sys

from PIL import Image
import cv2

from showimage import show_mp4

if len(sys.argv) < 2:
    sys.exit("Require an image argument")
else:
    mp4_file = sys.argv[1]

capture = cv2.VideoCapture(mp4_file)
frames = []

while capture.isOpened():
    return_value, image = capture.read()
    if return_value:
        converted = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        pil_image = Image.fromarray(converted)
        pil_image.thumbnail((64, 64), Image.Resampling.LANCZOS)
        frames.append(pil_image.convert("RGB"))
    elif not return_value:
        break

capture.release()

# Make image fit our screen.
show_mp4(frames)
