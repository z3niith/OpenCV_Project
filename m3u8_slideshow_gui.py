import os
import sys
import subprocess
import requests
from pathlib import Path
import tkinter as tk
from tkinter import messagebox, filedialog

# --- Core functions ---

def parse_m3u8(url):
    try:
        resp = requests.get(url)
        resp.raise_for_status()
    except Exception as e:
        raise RuntimeError(f"Failed to download .m3u8 playlist: {e}")

    lines = resp.text.strip().splitlines()
    segments = [line for line in lines if line and not line.startswith("#")]
    if not segments:
        raise RuntimeError("No media segments found in playlist.")
    return segments

def download_images(segments, base_url, output_dir):
    output_dir.mkdir(parents=True, exist_ok=True)
    for seg in segments:
        seg_url = base_url + seg
        local_path = output_dir / seg
        if local_path.exists():
            continue
        try:
            r = requests.get(seg_url)
            r.raise_for_status()
            local_path.write_bytes(r.content)
            print(f"Downloaded {seg}")
        except Exception as e:
            raise RuntimeError(f"Failed to download segment {seg}: {e}")

def build_input_txt(segments, output_dir):
    input_txt = output_dir / "input.txt"
    with open(input_txt, "w") as f:
        for seg in segments:
            f.write(f"file '{seg}'\n")
            f.write("duration 10\n")
        f.write(f"file '{segments[-1]}'\n")
    return input_txt

def run_ffmpeg(input_txt_path, output_path, output_format):
    if output_format == "mp4":
        cmd = [
            "ffmpeg", "-y", "-f", "concat", "-safe", "0",
            "-i", str(input_txt_path), "-vsync", "vfr",
            "-pix_fmt", "yuv420p", str(output_path) + ".mp4"
        ]
    elif output_format == "webm":
        cmd = [
            "ffmpeg", "-y", "-f", "concat", "-safe", "0",
            "-i", str(input_txt_path), "-vsync", "vfr",
            "-pix_fmt", "yuv420p", "-c:v", "libvpx-vp9",
            str(output_path) + ".webm"
        ]
    elif output_format == "gif":
        cmd = [
            "ffmpeg", "-y", "-f", "concat", "-safe", "0",
            "-i", str(input_txt_path),
            "-vf", "fps=10,scale=320:-1:flags=lanczos",
            "-loop", "0", str(output_path) + ".gif"
        ]
    else:
        raise ValueError("Unsupported output format")

    print(f"Running ffmpeg: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg error:\n{result.stderr}")
    return output_path.with_suffix(f".{output_format}")

def cleanup_images(segments, output_dir):
    for seg in segments:
        try:
            (output_dir / seg).unlink()
        except Exception as e:
            print(f"Warning: Could not delete {seg}: {e}")

# --- GUI ---

def run_processing(m3u8_url, output_format, folder_path):
    base_url = m3u8_url.rsplit('/', 1)[0] + '/'
    output_dir = Path(folder_path) / "slideshow_temp"
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        segments = parse_m3u8(m3u8_url)
        download_images(segments, base_url, output_dir)
        input_txt = build_input_txt(segments, output_dir)
        output_video = run_ffmpeg(input_txt, Path(folder_path) / "output", output_format)
        cleanup_images(segments, output_dir)
        # Remove temp folder
        try:
            output_dir.rmdir()
        except:
            pass

        messagebox.showinfo("Success", f"Video created successfully:\n{output_video}")
    except Exception as e:
        messagebox.showerror("Error", str(e))
        sys.exit(1)

def show_gui():
    def on_browse():
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            folder_entry.delete(0, tk.END)
            folder_entry.insert(0, folder_selected)

    def on_submit():
        url = url_entry.get().strip()
        fmt = format_var.get().strip().lower()
        folder = folder_entry.get().strip()

        if not url.endswith(".m3u8"):
            messagebox.showerror("Invalid Input", "URL must end with .m3u8")
            return
        if fmt not in ("mp4", "webm", "gif"):
            messagebox.showerror("Invalid Format", "Choose mp4, webm, or gif")
            return
        if not folder or not Path(folder).is_dir():
            messagebox.showerror("Invalid Folder", "Please select a valid folder to save the output")
            return

        root.destroy()
        run_processing(url, fmt, folder)

    root = tk.Tk()
    root.title("🎞️ M3U8 Slideshow Creator")
    root.geometry("520x320")
    root.resizable(False, False)

    # Center window
    ws = root.winfo_screenwidth()
    hs = root.winfo_screenheight()
    x = (ws // 2) - (520 // 2)
    y = (hs // 2) - (320 // 2)
    root.geometry(f"+{x}+{y}")

    label_font = ("Segoe UI", 14, "bold")
    normal_font = ("Segoe UI", 11)

    tk.Label(root, text="🎞️ M3U8 Slideshow Creator", font=label_font).pack(pady=15)
    tk.Label(root, text="Paste your .m3u8 playlist URL:", font=normal_font).pack(pady=(5, 0))

    url_entry = tk.Entry(root, width=65, font=("Consolas", 11))
    url_entry.pack(pady=8)
    url_entry.focus()

    tk.Label(root, text="Select output format:", font=normal_font).pack(pady=(10, 0))
    format_var = tk.StringVar(value="mp4")
    format_menu = tk.OptionMenu(root, format_var, "mp4", "webm", "gif")
    format_menu.config(font=normal_font)
    format_menu.pack()

    tk.Label(root, text="Choose output folder:", font=normal_font).pack(pady=(15, 0))
    folder_frame = tk.Frame(root)
    folder_frame.pack(pady=5)

    folder_entry = tk.Entry(folder_frame, width=52, font=("Consolas", 11))
    folder_entry.pack(side=tk.LEFT, padx=(0,5))
    browse_btn = tk.Button(folder_frame, text="Browse", command=on_browse, font=("Segoe UI", 10, "bold"))
    browse_btn.pack(side=tk.LEFT)

    submit_btn = tk.Button(root, text="Generate Video", font=("Segoe UI", 12, "bold"),
                           bg="#28a745", fg="white", command=on_submit)
    submit_btn.pack(pady=25, ipadx=10, ipady=5)

    root.mainloop()

def main():
    try:
        show_gui()
    except Exception as e:
        print(f"Fatal error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
