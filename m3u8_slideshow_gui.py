import os
import sys
import subprocess
import requests
from pathlib import Path
import tkinter as tk
from tkinter import messagebox, filedialog, ttk
from tkinter.scrolledtext import ScrolledText

THEME = "dark"  # options: "dark", "light"

if THEME == "dark":
    BG = "#1e1e1e"
    FG = "#ffffff"
    ACCENT = "#1793d1"
    ENTRY_BG = "#111111"
    ENTRY_FG = "#00ff00"
    LOG_FG = "#00ff00"
    BUTTON_BG = "#333333"
    CREDIT = "#777777"
else:
    BG = "#f0f0f0"
    FG = "#000000"
    ACCENT = "#0066cc"
    ENTRY_BG = "#ffffff"
    ENTRY_FG = "#000000"
    LOG_FG = "#003300"
    BUTTON_BG = "#dddddd"
    CREDIT = "#555555"

ARCH_ASCII = r"""
                -`
               .o+`
              `ooo/
             `+oooo:
            `+oooooo:
            -+oooooo+:
          `/:-:++oooo+:
         `/++++/+++++++:
        `/++++++++++++++:
       `/+++ooooooooooooo/`
      ./ooosssso++osssssso+`
     .oossssso-````/ossssss+`
    -osssssso.      :ssssssso.
   :osssssss/        osssso+++.
  /ossssssss/        +ssssooo/-
 /ossssso+/:-        -:/+osssso+-
`+sso+:-`                 `.-/+oso:
`:/`                           `.///
"""

def parse_m3u8(url, log):
    log("Parsing M3U8 playlist...")
    try:
        resp = requests.get(url)
        resp.raise_for_status()
    except Exception as e:
        raise RuntimeError(f"Failed to download .m3u8 playlist: {e}")
    lines = resp.text.strip().splitlines()
    segments = [line for line in lines if line and not line.startswith("#")]
    if not segments:
        raise RuntimeError("No media segments found in playlist.")
    log(f"Found {len(segments)} segments.")
    return segments

def download_images(segments, base_url, output_dir, log, progress_callback=None):
    output_dir.mkdir(parents=True, exist_ok=True)
    total = len(segments)
    for i, seg in enumerate(segments):
        seg_url = base_url + seg
        local_path = output_dir / seg
        if local_path.exists():
            if progress_callback:
                progress_callback(i + 1, total)
            continue
        try:
            r = requests.get(seg_url)
            r.raise_for_status()
            local_path.write_bytes(r.content)
            log(f"Downloaded {seg}")
            if progress_callback:
                progress_callback(i + 1, total)
        except Exception as e:
            raise RuntimeError(f"Failed to download segment {seg}: {e}")

def build_input_txt(segments, output_dir, log):
    input_txt = output_dir / "input.txt"
    log("Building ffmpeg input file...")
    with open(input_txt, "w") as f:
        for seg in segments:
            f.write(f"file '{seg}'\n")
            f.write("duration 10\n")
        f.write(f"file '{segments[-1]}'\n")
    return input_txt

def run_ffmpeg(input_txt_path, output_path, output_format, log):
    if output_format == "mp4":
        cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(input_txt_path),
               "-vsync", "vfr", "-pix_fmt", "yuv420p", str(output_path) + ".mp4"]
    elif output_format == "webm":
        cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(input_txt_path),
               "-vsync", "vfr", "-pix_fmt", "yuv420p", "-c:v", "libvpx-vp9", str(output_path) + ".webm"]
    elif output_format == "gif":
        cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(input_txt_path),
               "-vf", "fps=10,scale=320:-1:flags=lanczos", "-loop", "0", str(output_path) + ".gif"]
    else:
        raise ValueError("Unsupported output format")

    log("Running ffmpeg...")
    log("> " + ' '.join(cmd))
    result = subprocess.run(cmd, capture_output=True, text=True)
    log(result.stdout)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg error:\n{result.stderr}")
    return output_path.with_suffix(f".{output_format}")

def cleanup_images(segments, output_dir, log):
    log("Cleaning up downloaded segments...")
    for seg in segments:
        try:
            (output_dir / seg).unlink()
        except Exception as e:
            log(f"Could not delete {seg}: {e}")

def show_gui():
    def log(msg):
        log_box.config(state=tk.NORMAL)
        log_box.insert(tk.END, msg.strip() + "\n")
        log_box.see(tk.END)
        log_box.config(state=tk.DISABLED)

    def update_progress(text="", current=0, total=100):
        if text:
            progress_label.config(text=text)
        progress_bar["value"] = (current / total) * 100 if total else 0
        root.update_idletasks()

    def on_browse():
        folder = filedialog.askdirectory()
        if folder:
            folder_entry.delete(0, tk.END)
            folder_entry.insert(0, folder)

    def on_submit():
        url = url_entry.get().strip()
        fmt = format_var.get().strip().lower()
        folder = folder_entry.get().strip()

        if not url.endswith(".m3u8"):
            messagebox.showerror("Error", "URL must end with .m3u8")
            return
        if fmt not in ("mp4", "webm", "gif"):
            messagebox.showerror("Error", "Choose mp4, webm, or gif")
            return
        if not folder or not Path(folder).is_dir():
            messagebox.showerror("Error", "Choose valid folder")
            return

        submit_btn.config(state=tk.DISABLED)
        log_box.config(state=tk.NORMAL)
        log_box.delete(1.0, tk.END)
        log_box.config(state=tk.DISABLED)
        update_progress("Starting...", 0)

        def progress_callback(i, total):
            update_progress(f"Downloading {i}/{total}", i, total)

        try:
            base_url = url.rsplit('/', 1)[0] + '/'
            output_dir = Path(folder) / "slideshow_temp"
            output_dir.mkdir(parents=True, exist_ok=True)

            segments = parse_m3u8(url, log)
            download_images(segments, base_url, output_dir, log, progress_callback)
            input_txt = build_input_txt(segments, output_dir, log)
            output_video = run_ffmpeg(input_txt, Path(folder) / "output", fmt, log)
            cleanup_images(segments, output_dir, log)

            try:
                output_dir.rmdir()
            except:
                pass

            update_progress("Done!", 100)
            messagebox.showinfo("Done", f"Video created:\n{output_video}")
        except Exception as e:
            update_progress("Error", 0)
            log(f"[ERROR] {e}")
            messagebox.showerror("Error", str(e))
        finally:
            submit_btn.config(state=tk.NORMAL)

    root = tk.Tk()
    root.title("M3U8 Creator and Exporter")
    root.geometry("660x690")
    root.configure(bg=BG)

    mono = ("Consolas", 11)
    header = ("Consolas", 14, "bold")
    credit = ("Consolas", 9, "italic")

    ascii_label = tk.Label(root, text=ARCH_ASCII, font=("Courier New", 8),
                           fg=ACCENT, bg=BG, justify="left", anchor="nw")
    ascii_label.place(x=20, y=5)

    title_label = tk.Label(root, text="M3U8 Creator and Exporter", font=header, fg=FG, bg=BG)
    title_label.place(x=330, y=20)

    version_label = tk.Label(root, text="Alpha version 1.2", font=credit, fg=CREDIT, bg=BG)
    version_label.place(x=330, y=50)

    tk.Label(root, text="Playlist .m3u8 URL:", font=mono, fg=FG, bg=BG).place(x=30, y=130)
    url_entry = tk.Entry(root, width=75, font=mono, bg=ENTRY_BG, fg=ENTRY_FG, insertbackground=FG)
    url_entry.place(x=30, y=155)
    url_entry.bind("<Return>", lambda e: on_submit())

    tk.Label(root, text="Output Format:", font=mono, fg=FG, bg=BG).place(x=30, y=190)
    format_var = tk.StringVar(value="mp4")
    format_menu = ttk.OptionMenu(root, format_var, "mp4", "mp4", "webm", "gif")
    format_menu.place(x=150, y=185)

    tk.Label(root, text="Output Folder:", font=mono, fg=FG, bg=BG).place(x=30, y=230)
    folder_entry = tk.Entry(root, width=60, font=mono, bg=ENTRY_BG, fg=ENTRY_FG, insertbackground=FG)
    folder_entry.place(x=30, y=255)

    browse_btn = tk.Button(root, text="Browse", command=on_browse, font=("Consolas", 10),
                           bg=BUTTON_BG, fg=FG, relief="flat", padx=10)
    browse_btn.place(x=500, y=250)

    submit_btn = tk.Button(root, text="Generate Video", command=on_submit,
                           font=("Consolas", 11, "bold"), bg=ACCENT, fg="white", padx=10, pady=5)
    submit_btn.place(x=240, y=300)

    progress_label = tk.Label(root, text="", font=mono, fg=CREDIT, bg=BG)
    progress_label.place(x=30, y=350)

    progress_bar = ttk.Progressbar(root, length=580, mode="determinate")
    progress_bar.place(x=30, y=375)

    tk.Label(root, text="Log Output:", font=mono, fg=FG, bg=BG).place(x=30, y=410)
    log_box = ScrolledText(root, width=75, height=12, font=mono, bg=ENTRY_BG, fg=LOG_FG, insertbackground=FG)
    log_box.place(x=30, y=435)
    log_box.config(state=tk.DISABLED)

    tk.Label(root, text="z3niith", font=credit, fg=CREDIT, bg=BG).place(x=30, y=660)

    root.mainloop()

def main():
    try:
        show_gui()
    except Exception as e:
        print(f"[Fatal Error] {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
