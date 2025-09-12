# OpenCV_Project

This tool downloads `.jpeg` frames listed in a `.m3u8` file and turns them into a video (MP4, WebM, or GIF).

## Features

- GUI prompt (via `tkinter`)
- CLI fallback (if GUI not available)
- Automatically cleans up images after rendering
- Supports MP4, WebM, and GIF output

## Requirements

- Python 3.7+
- `ffmpeg` must be installed and available in your system PATH

## Install

```bash
pip install -r requirements.txt
