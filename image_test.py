import time
import sys

from rgbmatrix import RGBMatrix, RGBMatrixOptions
from PIL import Image

from showimage import show_image

if len(sys.argv) < 2:
    sys.exit("Require an image argument")
else:
    image_file = sys.argv[1]

image = Image.open(image_file)

# Make image fit our screen.
image.thumbnail((64, 64), Image.ANTIALIAS)

show_image(image.convert("RGB"))
