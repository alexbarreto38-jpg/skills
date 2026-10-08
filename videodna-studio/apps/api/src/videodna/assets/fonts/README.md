# Bundled font

`DejaVuSans-Bold.ttf` comes from the DejaVu fonts 2.37 release
(https://github.com/dejavu-fonts/dejavu-fonts/releases/tag/version_2_37), unchanged.
Its license is in `LICENSE-DejaVu.txt` and allows redistribution with that notice.

FFmpeg's `drawtext` needs a font file, and neither the Docker image (no apt, no
fontconfig) nor Windows has one at a predictable path. Without it, the captions of the
sample video and the labels of mock outputs silently disappear — and the sample video's
shots become harder to tell apart. `media/ffmpeg.py:find_font_file` uses this file
unless `MOCK_FONT_FILE` points elsewhere.
