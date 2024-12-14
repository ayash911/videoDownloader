import os
import tkinter as tk
from tkinter import filedialog, messagebox
import yt_dlp
import csv
import threading
import requests
import zipfile
import json

# Function to check for FFmpeg installation and install it if missing
def check_and_install_ffmpeg():
    """Check for FFmpeg and install it if not available."""
    try:
        if os.system("ffmpeg -version") == 0:
            return True  # FFmpeg is already installed

        update_status("FFmpeg not found. Installing...")
        url = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
        response = requests.get(url, stream=True)
        ffmpeg_zip = os.path.join(os.getcwd(), "ffmpeg.zip")

        # Download FFmpeg zip file
        with open(ffmpeg_zip, "wb") as f:
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)

        # Extract FFmpeg zip file
        with zipfile.ZipFile(ffmpeg_zip, "r") as zip_ref:
            zip_ref.extractall(os.getcwd())

        # Locate FFmpeg binaries and add to PATH
        ffmpeg_dir = [d for d in os.listdir(os.getcwd()) if "ffmpeg" in d.lower()]
        if ffmpeg_dir:
            ffmpeg_bin = os.path.join(os.getcwd(), ffmpeg_dir[0], "bin")
            os.environ["PATH"] += os.pathsep + ffmpeg_bin
            update_status("FFmpeg installed and added to PATH.")
        else:
            raise Exception("Failed to locate FFmpeg binaries.")

        os.remove(ffmpeg_zip)  # Clean up downloaded zip file
        return True
    except Exception as e:
        messagebox.showerror("Error", f"Failed to install FFmpeg: {e}")
        return False

# Function to select the folder for downloads
def select_folder():
    folder = filedialog.askdirectory()
    if folder:
        download_path.set(folder)

# Function to update the status label
def update_status(message):
    status_var.set(message)
    root.update_idletasks()

# Function to download media from the provided URL
def download_media():
    media_url = url_entry.get()
    if not media_url:
        messagebox.showerror("Error", "Please enter a valid URL.")
        return

    options = {
        'outtmpl': f'{download_path.get()}/%(title)s.%(ext)s',
        'format': 'bestvideo+bestaudio/best',
    }

    # Check for audio-only mode
    if audio_only.get():
        options['format'] = 'bestaudio/best'
        options['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }]

    # Check for subtitles
    if subtitles.get():
        options['writesubtitles'] = True
        options['subtitleslangs'] = ['en']

    # Check for thumbnail download
    if thumbnail.get():
        options['writethumbnail'] = True

    # Check for archive mode
    if archive.get():
        options['download_archive'] = f'{download_path.get()}/archive.txt'

    try:
        update_status("Downloading...")
        with yt_dlp.YoutubeDL(options) as ydl:
            ydl.download([media_url])
        update_status("Download completed!")
        messagebox.showinfo("Success", "Download completed!")
    except Exception as e:
        update_status("Error occurred!")
        messagebox.showerror("Error", f"An error occurred: {e}")

# Function to save metadata in both JSON and CSV formats
def save_metadata():
    media_url = url_entry.get()
    if not media_url:
        messagebox.showerror("Error", "Please enter a valid URL.")
        return

    options = {
        'extract_flat': True,
        'quiet': True,
    }

    try:
        update_status("Generating Metadata...")
        with yt_dlp.YoutubeDL(options) as ydl:
            info = ydl.extract_info(media_url, download=False)

        # Save metadata as JSON
        metadata_file_json = f'{download_path.get()}/metadata.json'
        with open(metadata_file_json, 'w', encoding='utf-8') as file:
            json.dump(info, file, ensure_ascii=False, indent=4)

        # Save metadata as CSV
        headers = [
            "id", "title", "fulltitle", "ext", "alt_title", "description", "display_id",
            "uploader", "uploader_id", "uploader_url", "license", "creators", "creator",
            "timestamp", "upload_date", "release_timestamp", "release_date", "release_year",
            "modified_timestamp", "modified_date", "channel", "channel_id", "channel_url",
            "channel_follower_count", "channel_is_verified", "location", "duration",
            "duration_string", "view_count", "like_count", "dislike_count", "comment_count",
            "age_limit", "live_status", "is_live", "was_live", "categories", "tags",
            "webpage_url"
        ]

        metadata_file_csv = f'{download_path.get()}/metadata.csv'
        with open(metadata_file_csv, 'w', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=headers)
            writer.writeheader()

            if 'entries' in info:
                for video in info['entries']:
                    metadata = {key: video.get(key, "N/A") for key in headers}
                    writer.writerow(metadata)
            else:
                metadata = {key: info.get(key, "N/A") for key in headers}
                writer.writerow(metadata)

        update_status("Metadata saved!")
        messagebox.showinfo("Success", f"Metadata saved to {metadata_file_json} and {metadata_file_csv}!")
    except Exception as e:
        update_status("Error occurred!")
        messagebox.showerror("Error", f"An error occurred: {e}")

# Function to record live streams
def stream_record():
    media_url = url_entry.get()
    if not media_url:
        messagebox.showerror("Error", "Please enter a valid URL.")
        return

    options = {
        'outtmpl': f'{download_path.get()}/livestreams/%(title)s.%(ext)s',
        'format': 'best',
        'live_from_start': True,
    }

    try:
        update_status("Recording livestream...")
        with yt_dlp.YoutubeDL(options) as ydl:
            update_status("Recording started! This may take some time.")
            ydl.download([media_url])
        update_status("Livestream recording completed!")
        messagebox.showinfo("Success", "Livestream recording completed!")
    except Exception as e:
        update_status("Error occurred!")
        messagebox.showerror("Error", f"An error occurred: {e}")

# Function to start download in a separate thread
def start_download():
    threading.Thread(target=download_media, daemon=True).start()

# Function to start recording live streams in a separate thread
def record_live():
    threading.Thread(target=stream_record, daemon=True).start()

# Function to generate metadata in a separate thread
def generate_metadata():
    threading.Thread(target=save_metadata, daemon=True).start()

# GUI setup
root = tk.Tk()
root.title("YouTube Downloader")
root.geometry("1150x350")
root.configure(bg="#121212")

font_style = ("Poppins", 16)
highlight_color = "#00bcd4"
button_color = "#1e1e1e"
button_fg = "white"
entry_bg = "#333333"
entry_fg = "white"
label_fg = "#cccccc"
status_color = "#f1c40f"

# URL input field
url_label = tk.Label(root, text="Video/Playlist URL:", font=font_style, fg=label_fg, bg="#121212")
url_label.grid(row=0, column=0, padx=15, pady=10, sticky="w")

url_entry = tk.Entry(root, width=50, font=font_style, bg=entry_bg, fg=entry_fg)
url_entry.grid(row=0, column=1, padx=15, pady=10, sticky="w")

download_path = tk.StringVar(value=os.getcwd())

# Folder selection
folder_label = tk.Label(root, text="Download Folder:", font=font_style, fg=label_fg, bg="#121212")
folder_label.grid(row=1, column=0, padx=15, pady=10, sticky="w")

folder_entry = tk.Entry(root, textvariable=download_path, width=50, font=font_style, bg=entry_bg, fg=entry_fg)
folder_entry.grid(row=1, column=1, padx=15, pady=10, sticky="w")

folder_button = tk.Button(root, text="Browse", command=select_folder, font=font_style, bg=button_color, fg=button_fg, cursor="hand2")
folder_button.grid(row=1, column=2, padx=15, pady=10)

# Checkboxes for download options
audio_only = tk.BooleanVar()
subtitles = tk.BooleanVar()
thumbnail = tk.BooleanVar()
archive = tk.BooleanVar()

audio_check = tk.Checkbutton(root, text="Audio Only (MP3)", variable=audio_only, font=font_style, fg=label_fg, bg="#121212", activebackground="#121212", activeforeground=highlight_color)
subtitles_check = tk.Checkbutton(root, text="Download Subtitles", variable=subtitles, font=font_style, fg=label_fg, bg="#121212", activebackground="#121212", activeforeground=highlight_color)
thumbnail_check = tk.Checkbutton(root, text="Download Thumbnail", variable=thumbnail, font=font_style, fg=label_fg, bg="#121212", activebackground="#121212", activeforeground=highlight_color)
archive_check = tk.Checkbutton(root, text="Archive Mode (No Redownload)", variable=archive, font=font_style, fg=label_fg, bg="#121212", activebackground="#121212", activeforeground=highlight_color)

audio_check.grid(row=2, column=0, padx=15, pady=10, sticky="w")
subtitles_check.grid(row=2, column=1, padx=15, pady=10, sticky="w")
thumbnail_check.grid(row=3, column=0, padx=15, pady=10, sticky="w")
archive_check.grid(row=3, column=1, padx=15, pady=10, sticky="w")

# Status label
status_var = tk.StringVar(value="")
status_label = tk.Label(root, textvariable=status_var, fg=status_color, bg="#121212", font=("Helvetica", 12, "italic"))
status_label.grid(row=6, column=0, columnspan=3, padx=15, pady=10, sticky="w")

# Buttons for download and metadata generation
download_btn = tk.Button(root, text="Start Download", command=start_download, font=font_style, bg=highlight_color, fg=button_fg, cursor="hand2")
metadata_btn = tk.Button(root, text="Generate Metadata (CSV & JSON)", command=generate_metadata, font=font_style, bg=highlight_color, fg=button_fg, cursor="hand2")
record_btn = tk.Button(root, text="Record Live Stream", command=record_live, font=font_style, bg=highlight_color, fg=button_fg, cursor="hand2")

download_btn.grid(row=5, column=0, padx=15, pady=15)
metadata_btn.grid(row=5, column=1, padx=15, pady=15)
record_btn.grid(row=5, column=2, padx=15, pady=15)

# Check for FFmpeg installation at startup
if not check_and_install_ffmpeg():
    root.destroy()

root.mainloop()
