import sys
from PIL import Image
from PIL import ImageDraw
import time
from rgbmatrix import RGBMatrix, RGBMatrixOptions


def show_image(image):
    # Configuration for the matrix
    options = RGBMatrixOptions()
    options.rows = 32
    options.cols = 64
    options.chain_length = 2
    options.parallel = 1
    options.hardware_mapping = 'adafruit-hat'
    options.gpio_slowdown = 4
    options.pixel_mapper_config = "U-mapper"

    matrix = RGBMatrix(options=options)

    matrix.Clear()
    matrix.SetImage(image, 0, 0)

    # image = Image.new("RGB", (64, 64))  # Can be larger than matrix if wanted!!
    # draw = ImageDraw.Draw(image)  # Declare Draw instance before prims
    # # Draw some shapes into image (no immediate effect on matrix)...
    # draw.rectangle((0, 0, 63, 63), fill=(0, 0, 0), outline=(0, 0, 255))
    # draw.line((0, 0, 63, 63), fill=(255, 0, 0))
    # draw.line((0, 63, 63, 0), fill=(0, 255, 0))
    # matrix.SetImage(image)
    try:
        while True:
            time.sleep(100)
    except KeyboardInterrupt:
        sys.exit(0)
