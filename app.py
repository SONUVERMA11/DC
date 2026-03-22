"""
YouTube MP3 Downloader — GUI Application
A modern, dark-themed desktop app for downloading YouTube audio as high-quality MP3.
"""

import os
import sys
import uuid
import threading
import webbrowser
from io import BytesIO
from concurrent.futures import ThreadPoolExecutor
from tkinter import filedialog, messagebox
from typing import Optional

import customtkinter as ctk
from PIL import Image
import requests

from downloader import MusicDownloader, DownloadTask, DownloadStatus


# ──────────────────────────── Theme & Constants ─────────────────────────────

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

COLORS = {
    "bg_dark": "#0d0f1a",
    "bg_card": "#151829",
    "bg_card_hover": "#1c2040",
    "bg_input": "#1a1e35",
    "accent": "#7c3aed",
    "accent_hover": "#9461fb",
    "accent_glow": "#6d28d9",
    "success": "#22c55e",
    "error": "#ef4444",
    "warning": "#f59e0b",
    "text": "#f1f5f9",
    "text_secondary": "#94a3b8",
    "text_muted": "#64748b",
    "border": "#2a2f4a",
    "progress_bg": "#1e2340",
    "progress_fill": "#7c3aed",
    "cancel_bg": "#dc2626",
    "cancel_hover": "#b91c1c",
}

DEFAULT_OUTPUT_DIR = os.path.join(os.path.expanduser("~"), "Music", "YouTube Downloads")
MAX_CONCURRENT = 3


# ──────────────────────────── Download Item Widget ──────────────────────────

class DownloadItemWidget(ctk.CTkFrame):
    """A card widget representing one download in the queue."""

    def __init__(self, master, task: DownloadTask, on_cancel=None, **kwargs):
        super().__init__(
            master,
            fg_color=COLORS["bg_card"],
            corner_radius=12,
            border_width=1,
            border_color=COLORS["border"],
            **kwargs,
        )
        self.task = task
        self.on_cancel = on_cancel
        self._thumbnail_image = None

        self.grid_columnconfigure(1, weight=1)

        # ── Thumbnail placeholder ──
        self.thumb_label = ctk.CTkLabel(
            self, text="♫", width=64, height=64,
            fg_color=COLORS["bg_input"], corner_radius=8,
            font=ctk.CTkFont(size=28),
            text_color=COLORS["accent"],
        )
        self.thumb_label.grid(row=0, column=0, rowspan=3, padx=(12, 10), pady=12, sticky="nsw")

        # ── Title ──
        self.title_label = ctk.CTkLabel(
            self, text=task.title,
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=COLORS["text"],
            anchor="w",
        )
        self.title_label.grid(row=0, column=1, padx=(0, 10), pady=(12, 0), sticky="ew")

        # ── Artist & Duration ──
        meta_text = f"{task.artist}  •  {task.duration}"
        self.meta_label = ctk.CTkLabel(
            self, text=meta_text,
            font=ctk.CTkFont(size=11),
            text_color=COLORS["text_secondary"],
            anchor="w",
        )
        self.meta_label.grid(row=1, column=1, padx=(0, 10), pady=0, sticky="ew")

        # ── Progress bar ──
        self.progress_bar = ctk.CTkProgressBar(
            self, height=6, corner_radius=3,
            fg_color=COLORS["progress_bg"],
            progress_color=COLORS["progress_fill"],
        )
        self.progress_bar.set(0)
        self.progress_bar.grid(row=2, column=1, padx=(0, 10), pady=(4, 12), sticky="ew")

        # ── Right side: status + cancel ──
        right_frame = ctk.CTkFrame(self, fg_color="transparent")
        right_frame.grid(row=0, column=2, rowspan=3, padx=(0, 12), pady=12, sticky="nse")

        self.status_label = ctk.CTkLabel(
            right_frame, text=task.status.value,
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=COLORS["text_muted"],
            width=100,
        )
        self.status_label.pack(pady=(0, 4))

        self.speed_label = ctk.CTkLabel(
            right_frame, text="",
            font=ctk.CTkFont(size=10),
            text_color=COLORS["text_muted"],
        )
        self.speed_label.pack()

        self.cancel_btn = ctk.CTkButton(
            right_frame, text="✕", width=30, height=30,
            corner_radius=8,
            fg_color=COLORS["cancel_bg"],
            hover_color=COLORS["cancel_hover"],
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._on_cancel,
        )
        self.cancel_btn.pack(pady=(6, 0))

    def _on_cancel(self):
        self.task.cancel()
        self.update_ui(self.task)
        if self.on_cancel:
            self.on_cancel(self.task)

    def set_thumbnail(self, image: Image.Image):
        """Set the thumbnail from a PIL Image."""
        try:
            img = image.resize((64, 64), Image.LANCZOS)
            self._thumbnail_image = ctk.CTkImage(light_image=img, dark_image=img, size=(64, 64))
            self.thumb_label.configure(image=self._thumbnail_image, text="")
        except Exception:
            pass

    def update_ui(self, task: DownloadTask):
        """Update widgets to reflect current task state."""
        self.task = task

        # Status color
        color_map = {
            DownloadStatus.QUEUED: COLORS["text_muted"],
            DownloadStatus.FETCHING_INFO: COLORS["warning"],
            DownloadStatus.DOWNLOADING: COLORS["accent"],
            DownloadStatus.CONVERTING: COLORS["warning"],
            DownloadStatus.COMPLETE: COLORS["success"],
            DownloadStatus.ERROR: COLORS["error"],
            DownloadStatus.CANCELLED: COLORS["text_muted"],
        }

        self.status_label.configure(
            text=task.status.value,
            text_color=color_map.get(task.status, COLORS["text_muted"]),
        )

        self.progress_bar.set(task.progress / 100)

        if task.status == DownloadStatus.COMPLETE:
            self.progress_bar.configure(progress_color=COLORS["success"])
            self.cancel_btn.configure(state="disabled", fg_color=COLORS["border"])
            self.speed_label.configure(text="✓ Done")
        elif task.status == DownloadStatus.ERROR:
            self.progress_bar.configure(progress_color=COLORS["error"])
            self.cancel_btn.configure(state="disabled", fg_color=COLORS["border"])
            self.speed_label.configure(text=task.error_message[:30])
        elif task.status == DownloadStatus.CANCELLED:
            self.cancel_btn.configure(state="disabled", fg_color=COLORS["border"])
            self.speed_label.configure(text="Cancelled")
        elif task.status == DownloadStatus.DOWNLOADING:
            speed_text = task.speed
            if task.eta:
                speed_text += f"  ETA {task.eta}"
            self.speed_label.configure(text=speed_text)
        elif task.status == DownloadStatus.CONVERTING:
            self.speed_label.configure(text="Converting to MP3...")

        self.title_label.configure(text=task.title)
        meta = f"{task.artist}  •  {task.duration}"
        self.meta_label.configure(text=meta)


# ──────────────────────────── Main Application ──────────────────────────────

class App(ctk.CTk):
    """Main application window."""

    def __init__(self):
        super().__init__()

        self.title("YouTube MP3 Downloader")
        self.geometry("900x720")
        self.minsize(750, 600)
        self.configure(fg_color=COLORS["bg_dark"])

        # State
        self.downloader = MusicDownloader()
        self.tasks: dict[str, DownloadTask] = {}
        self.widgets: dict[str, DownloadItemWidget] = {}
        self.executor = ThreadPoolExecutor(max_workers=MAX_CONCURRENT)
        self.output_dir = DEFAULT_OUTPUT_DIR
        self.quality = "320"
        self.active_count = 0
        self._lock = threading.Lock()

        self._build_ui()

    # ──────────────── UI Construction ────────────────

    def _build_ui(self):
        self.grid_rowconfigure(3, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # ── Header ──
        header = ctk.CTkFrame(self, fg_color=COLORS["bg_card"], corner_radius=0, height=70)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(1, weight=1)

        icon_label = ctk.CTkLabel(
            header, text="🎵",
            font=ctk.CTkFont(size=32),
        )
        icon_label.grid(row=0, column=0, padx=(20, 10), pady=15)

        title_frame = ctk.CTkFrame(header, fg_color="transparent")
        title_frame.grid(row=0, column=1, sticky="w")

        ctk.CTkLabel(
            title_frame, text="YouTube MP3 Downloader",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=COLORS["text"],
        ).pack(anchor="w")

        ctk.CTkLabel(
            title_frame, text="Download high-quality music with metadata & artwork",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_secondary"],
        ).pack(anchor="w")

        # ── Input Section ──
        input_frame = ctk.CTkFrame(self, fg_color=COLORS["bg_card"], corner_radius=14)
        input_frame.grid(row=1, column=0, padx=20, pady=(15, 8), sticky="ew")
        input_frame.grid_columnconfigure(0, weight=1)

        # URL entry row
        url_row = ctk.CTkFrame(input_frame, fg_color="transparent")
        url_row.grid(row=0, column=0, padx=16, pady=(16, 8), sticky="ew")
        url_row.grid_columnconfigure(0, weight=1)

        self.url_entry = ctk.CTkEntry(
            url_row,
            placeholder_text="Paste YouTube URL or playlist link here...",
            height=44,
            corner_radius=10,
            fg_color=COLORS["bg_input"],
            border_color=COLORS["border"],
            text_color=COLORS["text"],
            font=ctk.CTkFont(size=13),
        )
        self.url_entry.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        self.url_entry.bind("<Return>", lambda e: self._add_url())

        self.add_btn = ctk.CTkButton(
            url_row, text="＋  Add", width=100, height=44,
            corner_radius=10,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self._add_url,
        )
        self.add_btn.grid(row=0, column=1)

        # Settings row
        settings_row = ctk.CTkFrame(input_frame, fg_color="transparent")
        settings_row.grid(row=1, column=0, padx=16, pady=(0, 16), sticky="ew")
        settings_row.grid_columnconfigure(1, weight=1)

        # Quality
        ctk.CTkLabel(
            settings_row, text="Quality:",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_secondary"],
        ).grid(row=0, column=0, padx=(0, 6))

        self.quality_var = ctk.StringVar(value="320kbps (Best)")
        quality_menu = ctk.CTkOptionMenu(
            settings_row,
            variable=self.quality_var,
            values=list(MusicDownloader.QUALITY_MAP.keys()),
            width=160, height=34,
            corner_radius=8,
            fg_color=COLORS["bg_input"],
            button_color=COLORS["accent"],
            button_hover_color=COLORS["accent_hover"],
            font=ctk.CTkFont(size=12),
            command=self._on_quality_change,
        )
        quality_menu.grid(row=0, column=1, sticky="w", padx=(0, 20))

        # Output dir
        ctk.CTkLabel(
            settings_row, text="Save to:",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_secondary"],
        ).grid(row=0, column=2, padx=(0, 6))

        self.dir_label = ctk.CTkLabel(
            settings_row,
            text=self._truncate_path(self.output_dir),
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_muted"],
            anchor="w",
        )
        self.dir_label.grid(row=0, column=3, sticky="w", padx=(0, 6))

        ctk.CTkButton(
            settings_row, text="Browse", width=80, height=34,
            corner_radius=8,
            fg_color=COLORS["bg_input"],
            hover_color=COLORS["bg_card_hover"],
            border_width=1, border_color=COLORS["border"],
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text"],
            command=self._browse_output,
        ).grid(row=0, column=4)

        # ── Control Bar ──
        control_bar = ctk.CTkFrame(self, fg_color="transparent")
        control_bar.grid(row=2, column=0, padx=20, pady=(4, 4), sticky="ew")
        control_bar.grid_columnconfigure(0, weight=1)

        left_controls = ctk.CTkFrame(control_bar, fg_color="transparent")
        left_controls.grid(row=0, column=0, sticky="w")

        self.queue_label = ctk.CTkLabel(
            left_controls, text="Download Queue (0)",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color=COLORS["text"],
        )
        self.queue_label.pack(side="left")

        right_controls = ctk.CTkFrame(control_bar, fg_color="transparent")
        right_controls.grid(row=0, column=1, sticky="e")

        self.download_all_btn = ctk.CTkButton(
            right_controls, text="▶  Download All", height=36,
            corner_radius=8,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._download_all,
        )
        self.download_all_btn.pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            right_controls, text="🗁  Open Folder", height=36,
            corner_radius=8,
            fg_color=COLORS["bg_input"],
            hover_color=COLORS["bg_card_hover"],
            border_width=1, border_color=COLORS["border"],
            font=ctk.CTkFont(size=13),
            text_color=COLORS["text"],
            command=self._open_folder,
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            right_controls, text="Clear All", height=36,
            corner_radius=8,
            fg_color=COLORS["bg_input"],
            hover_color=COLORS["cancel_bg"],
            border_width=1, border_color=COLORS["border"],
            font=ctk.CTkFont(size=13),
            text_color=COLORS["text"],
            command=self._clear_queue,
        ).pack(side="left")

        # ── Queue Scroll Area ──
        self.queue_frame = ctk.CTkScrollableFrame(
            self,
            fg_color=COLORS["bg_dark"],
            corner_radius=0,
            scrollbar_button_color=COLORS["border"],
            scrollbar_button_hover_color=COLORS["accent"],
        )
        self.queue_frame.grid(row=3, column=0, padx=20, pady=(4, 8), sticky="nsew")
        self.queue_frame.grid_columnconfigure(0, weight=1)

        # Placeholder
        self.placeholder = ctk.CTkLabel(
            self.queue_frame,
            text="🎧  Paste a YouTube URL above to get started",
            font=ctk.CTkFont(size=15),
            text_color=COLORS["text_muted"],
        )
        self.placeholder.grid(row=0, column=0, pady=80)

        # ── Status Bar ──
        self.status_bar = ctk.CTkFrame(self, fg_color=COLORS["bg_card"], corner_radius=0, height=36)
        self.status_bar.grid(row=4, column=0, sticky="ew")
        self.status_bar.grid_columnconfigure(0, weight=1)

        self.status_label = ctk.CTkLabel(
            self.status_bar, text="Ready",
            font=ctk.CTkFont(size=11),
            text_color=COLORS["text_muted"],
            anchor="w",
        )
        self.status_label.grid(row=0, column=0, padx=20, pady=6, sticky="w")

        # Check ffmpeg
        if not MusicDownloader.is_ffmpeg_available():
            self.after(500, self._show_ffmpeg_warning)

    # ──────────────── Actions ────────────────

    def _show_ffmpeg_warning(self):
        messagebox.showwarning(
            "FFmpeg Not Found",
            "FFmpeg is required for MP3 conversion and thumbnail embedding.\n\n"
            "Please install FFmpeg and add it to your system PATH.\n"
            "Download: https://ffmpeg.org/download.html"
        )

    def _on_quality_change(self, value):
        self.quality = MusicDownloader.QUALITY_MAP.get(value, "320")

    def _browse_output(self):
        path = filedialog.askdirectory(initialdir=self.output_dir)
        if path:
            self.output_dir = path
            self.dir_label.configure(text=self._truncate_path(path))

    def _truncate_path(self, path: str, max_len: int = 35) -> str:
        if len(path) <= max_len:
            return path
        return "..." + path[-(max_len - 3):]

    def _open_folder(self):
        os.makedirs(self.output_dir, exist_ok=True)
        if sys.platform == "win32":
            os.startfile(self.output_dir)
        elif sys.platform == "darwin":
            os.system(f'open "{self.output_dir}"')
        else:
            os.system(f'xdg-open "{self.output_dir}"')

    def _add_url(self):
        url = self.url_entry.get().strip()
        if not url:
            return

        self.url_entry.delete(0, "end")
        self.add_btn.configure(state="disabled", text="Adding...")
        self.status_label.configure(text="Resolving URL...")

        threading.Thread(target=self._resolve_url, args=(url,), daemon=True).start()

    def _resolve_url(self, url: str):
        """Resolve URL in background thread — may be a single video or playlist."""
        try:
            # Handle multiple URLs (newline or space separated)
            urls = [u.strip() for u in url.replace(',', '\n').split('\n') if u.strip()]
            if len(urls) > 1:
                for u in urls:
                    self._resolve_single_or_playlist(u)
            else:
                self._resolve_single_or_playlist(urls[0])
        except Exception as e:
            self.after(0, lambda: self.status_label.configure(text=f"Error: {str(e)[:60]}"))
        finally:
            self.after(0, lambda: self.add_btn.configure(state="normal", text="＋  Add"))

    def _resolve_single_or_playlist(self, url: str):
        try:
            if self.downloader.is_playlist(url):
                entries = self.downloader.get_playlist_entries(url)
                self.after(0, lambda: self.status_label.configure(
                    text=f"Found playlist with {len(entries)} tracks"
                ))
                for entry in entries:
                    task_id = str(uuid.uuid4())[:8]
                    task = DownloadTask(
                        url=entry['url'],
                        output_dir=self.output_dir,
                        task_id=task_id,
                        title=entry.get('title', 'Unknown'),
                        duration=self._format_duration(entry.get('duration', 0)),
                    )
                    self.after(0, lambda t=task: self._add_task_to_queue(t))
            else:
                info = self.downloader.get_video_info(url)
                task_id = str(uuid.uuid4())[:8]
                task = DownloadTask(
                    url=url,
                    output_dir=self.output_dir,
                    task_id=task_id,
                    title=info.get('title', 'Unknown'),
                    artist=info.get('artist', 'Unknown'),
                    duration=info.get('duration', '0:00'),
                    thumbnail_url=info.get('thumbnail', ''),
                )
                self.after(0, lambda: self._add_task_to_queue(task))
        except Exception as e:
            self.after(0, lambda: self.status_label.configure(
                text=f"Error: {str(e)[:60]}"
            ))

    def _format_duration(self, seconds) -> str:
        try:
            seconds = int(seconds)
            m, s = divmod(seconds, 60)
            return f"{m}:{s:02d}"
        except (TypeError, ValueError):
            return "0:00"

    def _add_task_to_queue(self, task: DownloadTask):
        """Add a task card to the queue (must be called from main thread)."""
        # Hide placeholder
        self.placeholder.grid_forget()

        self.tasks[task.task_id] = task

        widget = DownloadItemWidget(
            self.queue_frame, task,
            on_cancel=self._on_task_cancel,
        )
        widget.grid(row=len(self.widgets), column=0, sticky="ew", pady=(0, 8))
        self.widgets[task.task_id] = widget

        # Load thumbnail async
        if task.thumbnail_url:
            threading.Thread(
                target=self._load_thumbnail,
                args=(task.task_id, task.thumbnail_url),
                daemon=True,
            ).start()

        self._update_queue_label()
        self.status_label.configure(text=f"Added: {task.title[:50]}")

    def _load_thumbnail(self, task_id: str, url: str):
        """Download and set thumbnail image."""
        try:
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                img = Image.open(BytesIO(resp.content))
                widget = self.widgets.get(task_id)
                if widget:
                    self.after(0, lambda: widget.set_thumbnail(img))
        except Exception:
            pass

    def _on_task_cancel(self, task: DownloadTask):
        self.status_label.configure(text=f"Cancelled: {task.title[:50]}")

    def _download_all(self):
        """Start downloading all queued tasks."""
        queued = [t for t in self.tasks.values() if t.status == DownloadStatus.QUEUED]
        if not queued:
            self.status_label.configure(text="No queued items to download")
            return

        self.download_all_btn.configure(state="disabled", text="Downloading...")
        self.status_label.configure(text=f"Starting {len(queued)} downloads...")

        for task in queued:
            self.executor.submit(self._run_download, task)

    def _run_download(self, task: DownloadTask):
        """Run a single download in a worker thread."""
        with self._lock:
            self.active_count += 1

        def on_progress(t: DownloadTask):
            widget = self.widgets.get(t.task_id)
            if widget:
                self.after(0, lambda: widget.update_ui(t))
            self.after(0, self._update_status_bar)

        try:
            # Re-fetch info for playlist items that might lack details
            if task.artist == "Unknown" and task.thumbnail_url == "":
                try:
                    info = self.downloader.get_video_info(task.url)
                    task.title = info.get('title', task.title)
                    task.artist = info.get('artist', 'Unknown')
                    task.duration = info.get('duration', task.duration)
                    task.thumbnail_url = info.get('thumbnail', '')
                    if task.thumbnail_url:
                        self._load_thumbnail(task.task_id, task.thumbnail_url)
                except Exception:
                    pass

            self.downloader.download(task, quality=self.quality, progress_callback=on_progress)
        except Exception as e:
            task.status = DownloadStatus.ERROR
            task.error_message = str(e)
            on_progress(task)
        finally:
            with self._lock:
                self.active_count -= 1
            self.after(0, self._check_all_done)

    def _update_status_bar(self):
        active = sum(
            1 for t in self.tasks.values()
            if t.status in (DownloadStatus.DOWNLOADING, DownloadStatus.CONVERTING, DownloadStatus.FETCHING_INFO)
        )
        done = sum(1 for t in self.tasks.values() if t.status == DownloadStatus.COMPLETE)
        total = len(self.tasks)
        self.status_label.configure(
            text=f"Active: {active}  |  Completed: {done}/{total}"
        )

    def _check_all_done(self):
        self._update_status_bar()
        active = sum(
            1 for t in self.tasks.values()
            if t.status in (DownloadStatus.DOWNLOADING, DownloadStatus.CONVERTING,
                            DownloadStatus.FETCHING_INFO, DownloadStatus.QUEUED)
        )
        if active == 0:
            self.download_all_btn.configure(state="normal", text="▶  Download All")
            done = sum(1 for t in self.tasks.values() if t.status == DownloadStatus.COMPLETE)
            self.status_label.configure(text=f"All done! {done} files downloaded ✓")

    def _clear_queue(self):
        # Cancel any active downloads
        for task in self.tasks.values():
            if task.status not in (DownloadStatus.COMPLETE, DownloadStatus.ERROR, DownloadStatus.CANCELLED):
                task.cancel()

        for widget in self.widgets.values():
            widget.destroy()

        self.tasks.clear()
        self.widgets.clear()

        self.placeholder.grid(row=0, column=0, pady=80)
        self._update_queue_label()
        self.download_all_btn.configure(state="normal", text="▶  Download All")
        self.status_label.configure(text="Queue cleared")

    def _update_queue_label(self):
        self.queue_label.configure(text=f"Download Queue ({len(self.tasks)})")

    def on_closing(self):
        # Cancel active downloads
        for task in self.tasks.values():
            task.cancel()
        self.executor.shutdown(wait=False, cancel_futures=True)
        self.destroy()


# ──────────────────────────── Entry Point ───────────────────────────────────

def main():
    app = App()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()


if __name__ == "__main__":
    main()
