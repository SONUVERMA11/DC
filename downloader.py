"""
YouTube Music Downloader Engine
Downloads high-quality MP3 audio from YouTube with embedded thumbnails and metadata.
"""

import os
import re
import shutil
import threading
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Optional

import yt_dlp


class DownloadStatus(Enum):
    QUEUED = "Queued"
    FETCHING_INFO = "Fetching Info..."
    DOWNLOADING = "Downloading"
    CONVERTING = "Converting"
    COMPLETE = "Complete"
    ERROR = "Error"
    CANCELLED = "Cancelled"


@dataclass
class DownloadTask:
    """Represents a single download task."""
    url: str
    output_dir: str
    task_id: str = ""
    title: str = "Unknown"
    artist: str = "Unknown"
    duration: str = "0:00"
    thumbnail_url: str = ""
    status: DownloadStatus = DownloadStatus.QUEUED
    progress: float = 0.0
    speed: str = ""
    eta: str = ""
    error_message: str = ""
    file_path: str = ""
    cancelled: bool = False
    _cancel_event: threading.Event = field(default_factory=threading.Event)

    def cancel(self):
        self.cancelled = True
        self._cancel_event.set()
        self.status = DownloadStatus.CANCELLED


class MusicDownloader:
    """Core download engine wrapping yt-dlp."""

    QUALITY_MAP = {
        "320kbps (Best)": "320",
        "256kbps": "256",
        "192kbps": "192",
        "128kbps": "128",
    }

    def __init__(self):
        self._check_ffmpeg()

    @staticmethod
    def _check_ffmpeg() -> bool:
        """Check if ffmpeg is available on the system."""
        return shutil.which("ffmpeg") is not None

    @staticmethod
    def is_ffmpeg_available() -> bool:
        return shutil.which("ffmpeg") is not None

    @staticmethod
    def sanitize_filename(name: str) -> str:
        """Remove invalid characters from filenames."""
        return re.sub(r'[<>:"/\\|?*]', '', name).strip()

    def get_info(self, url: str) -> dict:
        """Fetch video/playlist metadata without downloading."""
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': 'in_playlist',
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return info

    def is_playlist(self, url: str) -> bool:
        """Check if a URL is a playlist."""
        try:
            info = self.get_info(url)
            return info.get('_type') == 'playlist'
        except Exception:
            return False

    def get_playlist_entries(self, url: str) -> list[dict]:
        """Get all video entries from a playlist URL."""
        try:
            info = self.get_info(url)
            if info.get('_type') == 'playlist':
                entries = info.get('entries', [])
                result = []
                for entry in entries:
                    if entry:
                        video_url = entry.get('url', '')
                        if not video_url.startswith('http'):
                            video_url = f"https://www.youtube.com/watch?v={entry.get('id', '')}"
                        result.append({
                            'url': video_url,
                            'title': entry.get('title', 'Unknown'),
                            'duration': entry.get('duration', 0),
                            'id': entry.get('id', ''),
                        })
                return result
            return []
        except Exception:
            return []

    def get_video_info(self, url: str) -> dict:
        """Get detailed info for a single video."""
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                duration_secs = info.get('duration', 0) or 0
                minutes = int(duration_secs) // 60
                seconds = int(duration_secs) % 60
                return {
                    'title': info.get('title', 'Unknown'),
                    'artist': info.get('artist') or info.get('uploader', 'Unknown'),
                    'duration': f"{minutes}:{seconds:02d}",
                    'thumbnail': info.get('thumbnail', ''),
                    'id': info.get('id', ''),
                    'url': url,
                }
        except Exception as e:
            return {
                'title': 'Unknown',
                'artist': 'Unknown',
                'duration': '0:00',
                'thumbnail': '',
                'id': '',
                'url': url,
                'error': str(e),
            }

    def download(
        self,
        task: DownloadTask,
        quality: str = "320",
        progress_callback: Optional[Callable] = None,
    ) -> bool:
        """
        Download a single video as MP3 with embedded thumbnail and metadata.
        Returns True on success, False on failure.
        """
        if task.cancelled:
            return False

        task.status = DownloadStatus.FETCHING_INFO
        if progress_callback:
            progress_callback(task)

        output_template = os.path.join(
            task.output_dir,
            '%(title)s.%(ext)s'
        )

        def progress_hook(d):
            if task.cancelled:
                raise Exception("Download cancelled by user")

            if d['status'] == 'downloading':
                task.status = DownloadStatus.DOWNLOADING
                total = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
                downloaded = d.get('downloaded_bytes', 0)
                if total > 0:
                    task.progress = (downloaded / total) * 100
                else:
                    # Use fragment index if available
                    frag_index = d.get('fragment_index', 0)
                    frag_count = d.get('fragment_count', 0)
                    if frag_count > 0:
                        task.progress = (frag_index / frag_count) * 100

                speed = d.get('speed')
                if speed:
                    if speed > 1024 * 1024:
                        task.speed = f"{speed / (1024 * 1024):.1f} MB/s"
                    elif speed > 1024:
                        task.speed = f"{speed / 1024:.1f} KB/s"
                    else:
                        task.speed = f"{speed:.0f} B/s"

                eta = d.get('eta')
                if eta:
                    eta_min = int(eta) // 60
                    eta_sec = int(eta) % 60
                    task.eta = f"{eta_min}:{eta_sec:02d}"

                if progress_callback:
                    progress_callback(task)

            elif d['status'] == 'finished':
                task.status = DownloadStatus.CONVERTING
                task.progress = 100
                task.speed = ""
                task.eta = ""
                if progress_callback:
                    progress_callback(task)

        def postprocessor_hook(d):
            if d['status'] == 'finished':
                task.file_path = d.get('filepath', '')

        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': output_template,
            'quiet': True,
            'no_warnings': True,
            'writethumbnail': True,
            'postprocessors': [
                {
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': quality,
                },
                {
                    'key': 'FFmpegMetadata',
                    'add_metadata': True,
                },
                {
                    'key': 'EmbedThumbnail',
                },
            ],
            'parse_metadata': [
                '%(uploader)s:%(artist)s',
                '%(title)s:%(title)s',
            ],
            'progress_hooks': [progress_hook],
            'postprocessor_hooks': [postprocessor_hook],
        }

        try:
            os.makedirs(task.output_dir, exist_ok=True)

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([task.url])

            if not task.cancelled:
                task.status = DownloadStatus.COMPLETE
                task.progress = 100
                if progress_callback:
                    progress_callback(task)
                return True
            return False

        except Exception as e:
            error_msg = str(e)
            if "cancelled" in error_msg.lower():
                task.status = DownloadStatus.CANCELLED
            else:
                task.status = DownloadStatus.ERROR
                task.error_message = error_msg
            if progress_callback:
                progress_callback(task)
            return False
