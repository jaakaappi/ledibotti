# ledibotti

No special venv due to how the rgbmatrix library is installed

```
sudo -H pip install python-telegram-bot --break-system-packages
sudo -H pip install opencv-contrib-python-headless --break-system-packages -v
sudo -H pip install ffmpeg-python --break-system-packages

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
