# ledibotti

## Hardware
* 2x [Adafruit 64x32 RGB LED Matrix - 5mm pitch](https://www.printables.com/model/1095162-64x64-p5-rgb-led-matrix-frame-and-feet-with-rasper)
* [Adafruit RGB Matrix HAT + RTC for Raspberry Pi - Mini Kit](https://www.adafruit.com/product/2345)
* At least one, preferably two [GPIO Ribbon Cable 2x8 IDC Cable - 16 pins 12" long](https://www.adafruit.com/product/4170)
* 3D-printed frame, files available [here](https://www.printables.com/model/1095162-64x64-p5-rgb-led-matrix-frame-and-feet-with-rasper)

## Dev notes

No special venv due to how the rgbmatrix library is installed

```
sudo -H pip install python-telegram-bot[job-queue] --break-system-packages
sudo -H pip install opencv-contrib-python-headless --break-system-packages -v
sudo -H pip install ffmpeg-python --break-system-packages
sudo apt-get install libheif-dev
# Raspbian libheif was something like 1.15.1
sudo -H pip install pillow-heif==0.10.1 --break-system-packages

sudo python image_test.py iu.png

sudo python main.py
```

In case of something like `[swscaler @ 0x204e5e0] Slice parameters 0, 89 are invalid`

```
# first resize the video
ffmpeg -i yeet.mp4 -vf "scale=50:88" -c:v libx264 -crf 23 -preset fast -c:a aac output.mp4

# then re-encode it just to make sure
ffmpeg -i input.mp4 -vf "scale=50:88" -c:v libx264 -crf 23 -preset fast -c:a aac output.mp4
```

IF `.heic` files give problems, install libheif deps from (here)[https://www.thedigitalpictureframe.com/the-heic-photo-format-now-works-with-the-pi3d-digital-picture-frame-image-viewer/
]
