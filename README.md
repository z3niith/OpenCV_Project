# .M3U8 Downloader and Converter
Check "Mac" branch for mac
For Linux (Arch):

I created this because I was annoyed that their are no others that I could easily find out their. 

This is open source; fork it, and tweak it to your liking.

This tool downloads `.jpeg` frames listed in a `.m3u8` file and turns them into a video (MP4, WebM, or GIF).

`Note:` This is only for .M3U8 files that use pictures in the "network" section. 

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
