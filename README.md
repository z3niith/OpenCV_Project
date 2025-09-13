# .M3U8 Downloader and Converter

This tool downloads `.jpeg` frames listed in a `.m3u8` playlist and converts them into a video (`MP4`, `WebM`, or `GIF`).  

I built it because I couldn’t find a simple, open-source solution for handling image-based `.m3u8` playlists.  

It’s open source — fork it, tweak it, and adapt it to your needs.  

> **Note:** This only works for `.m3u8` playlists that reference image frames (commonly in the “network” section), not standard video streams.

---

## Features

- Graphical user interface (via `tkinter`)
- Command-line fallback if GUI is unavailable
- Automatic cleanup of downloaded frames after rendering
- Output formats: **MP4**, **WebM**, and **GIF**

---

## Requirements

- Python 3.7 or higher  
- [FFmpeg](https://ffmpeg.org/download.html) installed and available in your system `PATH`

---

## Installation

Clone the repository and install dependencies:

```bash
git clone https://github.com/z3niith/M3U8-Downloader-and-Converter.git
cd M3U8-Downloader-and-Converter
pip install -r requirements.txt

## Usage

GUI Mode (default)

Run the main script to launch the GUI: 
python m3u8_slideshow_gui.py

CLI Mode

If no GUI is available (e.g., running on a server), you can use the CLI version: 
python m3u8_slideshow_cli.py <playlist.m3u8> -o output.mp4

## License

This project is licensed under the MIT License — feel free to use, modify, and share.
