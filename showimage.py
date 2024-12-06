import sys
import time

from rgbmatrix import RGBMatrix, RGBMatrixOptions


# Configuration for the matrix
options = RGBMatrixOptions()
options.rows = 32
options.cols = 64
options.chain_length = 2
options.parallel = 1
options.hardware_mapping = "adafruit-hat"
options.gpio_slowdown = 4
options.pixel_mapper_config = "U-mapper;Rotate:180"


def show_image(image):
    matrix = RGBMatrix(options=options)

    matrix.Clear()
    padding_x = int((64 - image.width) / 2)
    padding_y = int((64 - image.height) / 2)
    matrix.SetImage(image, padding_x, padding_y)

    try:
        while True:
            time.sleep(100)
    except KeyboardInterrupt:
        sys.exit(0)


def show_mp4(frames):
    print("Got " + str(len(frames)) + " frames")
    matrix = RGBMatrix(options=options)

    # Preprocess the gifs frames into canvases to improve playback performance
    canvases = []
    print(
        "Preprocessing gif, this may take a moment depending on the size of the gif..."
    )
    for frame in frames:
        canvas = matrix.CreateFrameCanvas()
        padding_x = int((64 - frame.width) / 2)
        padding_y = int((64 - frame.height) / 2)
        canvas.SetImage(frame, padding_x, padding_y)
        canvases.append(canvas)

    print("Completed Preprocessing, displaying gif")

    try:
        print("Press CTRL-C to stop.")

        # Infinitely loop through the gif
        cur_frame = 0
        while True:
            matrix.SwapOnVSync(canvases[cur_frame], framerate_fraction=10)
            if cur_frame == len(frames) - 1:
                cur_frame = 0
            else:
                cur_frame += 1
    except KeyboardInterrupt:
        sys.exit(0)
