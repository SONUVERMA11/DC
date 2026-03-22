"""
YouTube Music Downloader Engine — Android Compatible
Downloads high-quality MP3 audio from YouTube with metadata.
Works on both desktop and Android (via Buildozer/python-for-android).
"""

import os
import re
import shutil
import threading
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Optional

from kivy.utils import platform

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
    """Core download engine wrapping yt-dlp with Android support."""

    QUALITY_MAP = {
        "320kbps (Best)": "320",
        "256kbps": "256",
        "192kbps": "192",
        "128kbps": "128",
    }

    def __init__(self):
        self._ffmpeg_path = self._find_ffmpeg()

    def _find_ffmpeg(self) -> Optional[str]:
        """Find ffmpeg binary — checks standard paths and Android bundle."""
        # Standard system PATH
        ffmpeg = shutil.which("ffmpeg")
        if ffmpeg:
            return ffmpeg

        # Android: check bundled location
        if platform == "android":
            from android import mActivity
            app_dir = mActivity.getFilesDir().getAbsolutePath()
            bundled = os.path.join(app_dir, "ffmpeg")
            if os.path.isfile(bundled) and os.access(bundled, os.X_OK):
                return bundled

        return None

    @staticmethod
    def is_ffmpeg_available() -> bool:
        return shutil.which("ffmpeg") is not None

    @staticmethod
    def sanitize_filename(name: str) -> str:
        return re.sub(r'[<>:"/\\|?*]', '', name).strip()

    def get_info(self, url: str) -> dict:
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': 'in_playlist',
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            return ydl.extract_info(url, download=False)

    def is_playlist(self, url: str) -> bool:
        try:
            info = self.get_info(url)
            return info.get('_type') == 'playlist'
        except Exception:
            return False

    def get_playlist_entries(self, url: str) -> list:
        try:
            info = self.get_info(url)
            if info.get('_type') == 'playlist':
                result = []
                for entry in info.get('entries', []):
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
        ydl_opts = {'quiet': True, 'no_warnings': True}
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                dur = info.get('duration', 0) or 0
                return {
                    'title': info.get('title', 'Unknown'),
                    'artist': info.get('artist') or info.get('uploader', 'Unknown'),
                    'duration': f"{int(dur) // 60}:{int(dur) % 60:02d}",
                    'thumbnail': info.get('thumbnail', ''),
                    'id': info.get('id', ''),
                    'url': url,
                }
        except Exception as e:
            return {
                'title': 'Unknown', 'artist': 'Unknown',
                'duration': '0:00', 'thumbnail': '',
                'id': '', 'url': url, 'error': str(e),
            }

    def download(
        self,
        task: DownloadTask,
        quality: str = "320",
        progress_callback: Optional[Callable] = None,
    ) -> bool:
        if task.cancelled:
            return False

        task.status = DownloadStatus.FETCHING_INFO
        if progress_callback:
            progress_callback(task)

        output_template = os.path.join(task.output_dir, '%(title)s.%(ext)s')

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
                    fi = d.get('fragment_index', 0)
                    fc = d.get('fragment_count', 0)
                    if fc > 0:
                        task.progress = (fi / fc) * 100

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
                    task.eta = f"{int(eta) // 60}:{int(eta) % 60:02d}"

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

        # Build yt-dlp options
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': output_template,
            'quiet': True,
            'no_warnings': True,
            'progress_hooks': [progress_hook],
            'postprocessor_hooks': [postprocessor_hook],
        }

        # Add ffmpeg postprocessors if available
        if self._ffmpeg_path:
            ydl_opts['ffmpeg_location'] = os.path.dirname(self._ffmpeg_path)
            ydl_opts['writethumbnail'] = True
            ydl_opts['postprocessors'] = [
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
            ]
            ydl_opts['parse_metadata'] = [
                '%(uploader)s:%(artist)s',
                '%(title)s:%(title)s',
            ]
        else:
            # No ffmpeg: download best audio in native format (m4a/opus/webm)
            ydl_opts['format'] = 'bestaudio[ext=m4a]/bestaudio/best'

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
