"""
DC v2.0 — YouTube MP3 Downloader
Built with Flet (Flutter-powered Python framework).
"""

import os
import sys
import uuid
import threading
from concurrent.futures import ThreadPoolExecutor

import flet as ft

from downloader import MusicDownloader, DownloadTask, DownloadStatus

MAX_CONCURRENT = 3
QUALITY_OPTIONS = ["320", "256", "192", "128"]


def main(page: ft.Page):

    # ── Page config ──
    page.title = "DC — YouTube MP3 Downloader"
    page.theme_mode = ft.ThemeMode.DARK
    page.theme = ft.Theme(
        color_scheme_seed=ft.Colors.DEEP_PURPLE,
        visual_density=ft.VisualDensity.COMPACT,
    )
    page.padding = 0
    page.spacing = 0

    # ── State ──
    downloader = MusicDownloader()
    tasks: dict[str, DownloadTask] = {}
    cards: dict[str, ft.Container] = {}
    executor = ThreadPoolExecutor(max_workers=MAX_CONCURRENT)
    quality = "320"
    lock = threading.Lock()

    # ── Helpers ──

    def get_output_dir():
        if hasattr(sys, "getandroidapilevel"):
            return "/storage/emulated/0/Music/YT Downloads"
        return os.path.join(os.path.expanduser("~"), "Music", "YT Downloads")

    def fmt_dur(seconds):
        try:
            s = int(seconds)
            return f"{s // 60}:{s % 60:02d}"
        except (TypeError, ValueError):
            return "0:00"

    def status_color(status: DownloadStatus) -> str:
        return {
            DownloadStatus.QUEUED: ft.Colors.GREY_500,
            DownloadStatus.FETCHING_INFO: ft.Colors.AMBER_600,
            DownloadStatus.DOWNLOADING: ft.Colors.BLUE_500,
            DownloadStatus.CONVERTING: ft.Colors.ORANGE_500,
            DownloadStatus.COMPLETE: ft.Colors.GREEN_500,
            DownloadStatus.ERROR: ft.Colors.RED_500,
            DownloadStatus.CANCELLED: ft.Colors.GREY_500,
        }.get(status, ft.Colors.GREY_500)

    def status_icon(status: DownloadStatus) -> str:
        return {
            DownloadStatus.QUEUED: ft.Icons.SCHEDULE,
            DownloadStatus.FETCHING_INFO: ft.Icons.SEARCH,
            DownloadStatus.DOWNLOADING: ft.Icons.DOWNLOAD,
            DownloadStatus.CONVERTING: ft.Icons.SETTINGS,
            DownloadStatus.COMPLETE: ft.Icons.CHECK_CIRCLE,
            DownloadStatus.ERROR: ft.Icons.ERROR,
            DownloadStatus.CANCELLED: ft.Icons.CANCEL,
        }.get(status, ft.Icons.SCHEDULE)

    # ── Status bar ──
    status_text = ft.Text("Ready", size=11, color=ft.Colors.GREY_500)
    queue_count_text = ft.Text("0 items", size=12, color=ft.Colors.GREY_500)

    def set_status(msg: str):
        status_text.value = msg
        try:
            page.update()
        except Exception:
            pass

    # ── Download card builder ──

    def build_card(task: DownloadTask) -> ft.Container:
        title_text = ft.Text(
            task.title, size=13, weight=ft.FontWeight.W_600,
            max_lines=1, overflow=ft.TextOverflow.ELLIPSIS,
        )
        subtitle_text = ft.Text(
            f"{task.artist}  ·  {task.duration}",
            size=11, color=ft.Colors.GREY_500, max_lines=1,
        )
        progress_bar = ft.ProgressBar(
            value=0, height=4, border_radius=2,
            color=ft.Colors.DEEP_PURPLE_400,
            bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.WHITE),
        )
        status_chip = ft.Text(
            task.status.value, size=10, weight=ft.FontWeight.W_600,
            color=ft.Colors.GREY_500,
        )
        speed_text = ft.Text("", size=10, color=ft.Colors.GREY_500)
        icon_widget = ft.Icon(ft.Icons.SCHEDULE, size=20, color=ft.Colors.GREY_500)

        def cancel_click(e):
            cancel_download(task.task_id)

        card = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Container(
                        content=icon_widget,
                        width=36, height=36, border_radius=10,
                        bgcolor=ft.Colors.with_opacity(0.08, ft.Colors.DEEP_PURPLE_400),
                        alignment=ft.alignment.center,
                    ),
                    ft.Column([title_text, subtitle_text], spacing=2, expand=True),
                    ft.IconButton(
                        ft.Icons.CLOSE, icon_size=18,
                        icon_color=ft.Colors.GREY_600,
                        on_click=cancel_click,
                    ),
                ], spacing=10, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                progress_bar,
                ft.Row([
                    status_chip,
                    ft.Container(expand=True),
                    speed_text,
                ]),
            ], spacing=6),
            padding=ft.padding.all(14),
            border_radius=16,
            bgcolor=ft.Colors.with_opacity(0.04, ft.Colors.WHITE),
            border=ft.border.all(1, ft.Colors.with_opacity(0.06, ft.Colors.WHITE)),
            animate=ft.Animation(200, ft.AnimationCurve.EASE_OUT),
        )

        # Store refs for updates
        card.data = {
            "title": title_text,
            "subtitle": subtitle_text,
            "progress": progress_bar,
            "status": status_chip,
            "speed": speed_text,
            "icon": icon_widget,
        }
        return card

    def update_card(task: DownloadTask):
        card = cards.get(task.task_id)
        if not card:
            return
        refs = card.data
        refs["title"].value = task.title
        refs["subtitle"].value = f"{task.artist}  ·  {task.duration}"
        refs["progress"].value = task.progress / 100 if task.progress > 0 else 0
        refs["progress"].color = status_color(task.status)
        refs["status"].value = task.status.value
        refs["status"].color = status_color(task.status)
        refs["icon"].name = status_icon(task.status)
        refs["icon"].color = status_color(task.status)

        if task.status == DownloadStatus.DOWNLOADING:
            sp = task.speed or ""
            eta = f" ETA {task.eta}" if task.eta else ""
            refs["speed"].value = f"{sp}{eta} · {int(task.progress)}%"
        elif task.status == DownloadStatus.COMPLETE:
            refs["speed"].value = "✓ Done"
        elif task.status == DownloadStatus.ERROR:
            refs["speed"].value = task.error_message[:35]
        elif task.status == DownloadStatus.CONVERTING:
            refs["speed"].value = "Converting..."
        elif task.status == DownloadStatus.CANCELLED:
            refs["speed"].value = "Cancelled"
        else:
            refs["speed"].value = ""

        try:
            page.update()
        except Exception:
            pass

    # ── Download list ──
    download_list = ft.Column(spacing=8)

    empty_state = ft.Container(
        content=ft.Column([
            ft.Icon(ft.Icons.MUSIC_NOTE, size=48, color=ft.Colors.GREY_700),
            ft.Text("No downloads yet", size=15, weight=ft.FontWeight.W_600, color=ft.Colors.GREY_600),
            ft.Text("Paste a YouTube URL above to start", size=12, color=ft.Colors.GREY_700),
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=8),
        padding=ft.padding.symmetric(vertical=40),
        alignment=ft.alignment.center,
    )
    download_list.controls.append(empty_state)

    # ── URL input ──
    url_input = ft.TextField(
        hint_text="Paste YouTube URL or playlist...",
        border_radius=12,
        filled=True,
        height=48,
        text_size=13,
        content_padding=ft.padding.symmetric(horizontal=16, vertical=12),
        on_submit=lambda e: add_url(e),
    )

    # ── Quality dropdown ──
    quality_dropdown = ft.Dropdown(
        value="320",
        width=90,
        height=42,
        text_size=12,
        border_radius=10,
        options=[ft.dropdown.Option(q, f"{q}k") for q in QUALITY_OPTIONS],
        on_change=lambda e: set_quality(e),
    )

    def set_quality(e):
        nonlocal quality
        quality = e.control.value

    # ── Buttons ──
    add_btn = ft.ElevatedButton(
        text="+ Add",
        bgcolor=ft.Colors.DEEP_PURPLE_500,
        color=ft.Colors.WHITE,
        height=42,
        expand=True,
        on_click=lambda e: add_url(e),
    )

    download_all_btn = ft.ElevatedButton(
        text="Download All",
        bgcolor=ft.Colors.DEEP_PURPLE_500,
        color=ft.Colors.WHITE,
        height=36,
        on_click=lambda e: download_all(e),
    )

    # ── Actions ──

    def paste_url(e):
        try:
            text = page.get_clipboard()
            if text:
                url_input.value = text.strip()
                page.update()
        except Exception:
            page.open(ft.SnackBar(ft.Text("Could not paste")))

    def add_url(e):
        url = url_input.value.strip() if url_input.value else ""
        if not url:
            page.open(ft.SnackBar(ft.Text("Please enter a YouTube URL")))
            return

        url_input.value = ""
        add_btn.text = "Adding..."
        add_btn.disabled = True
        page.update()
        set_status("Resolving URL...")
        threading.Thread(target=_resolve_url, args=(url,), daemon=True).start()

    def _resolve_url(url):
        try:
            urls = [u.strip() for u in url.replace(",", "\n").split("\n") if u.strip()]
            for u in urls:
                _resolve_single(u)
        except Exception as ex:
            set_status(f"Error: {str(ex)[:50]}")
        finally:
            add_btn.text = "+ Add"
            add_btn.disabled = False
            try:
                page.update()
            except Exception:
                pass

    def _resolve_single(url):
        try:
            if downloader.is_playlist(url):
                entries = downloader.get_playlist_entries(url)
                set_status(f"Found {len(entries)} tracks")
                for entry in entries:
                    task = DownloadTask(
                        url=entry["url"],
                        output_dir=get_output_dir(),
                        task_id=str(uuid.uuid4())[:8],
                        title=entry.get("title", "Unknown"),
                        duration=fmt_dur(entry.get("duration", 0)),
                    )
                    _add_to_queue(task)
            else:
                info = downloader.get_video_info(url)
                task = DownloadTask(
                    url=url,
                    output_dir=get_output_dir(),
                    task_id=str(uuid.uuid4())[:8],
                    title=info.get("title", "Unknown"),
                    artist=info.get("artist", "Unknown"),
                    duration=info.get("duration", "0:00"),
                    thumbnail_url=info.get("thumbnail", ""),
                )
                _add_to_queue(task)
        except Exception as ex:
            set_status(f"Error: {str(ex)[:50]}")

    def _add_to_queue(task):
        if empty_state in download_list.controls:
            download_list.controls.remove(empty_state)

        tasks[task.task_id] = task
        card = build_card(task)
        cards[task.task_id] = card
        download_list.controls.append(card)
        queue_count_text.value = f"{len(tasks)} item{'s' if len(tasks) != 1 else ''}"
        set_status(f"Added: {task.title[:40]}")

    def cancel_download(task_id):
        task = tasks.get(task_id)
        if task and task.status not in (DownloadStatus.COMPLETE, DownloadStatus.CANCELLED):
            task.cancel()
            update_card(task)
            set_status(f"Cancelled: {task.title[:40]}")

    def clear_queue(e):
        for task in tasks.values():
            if task.status not in (DownloadStatus.COMPLETE, DownloadStatus.ERROR, DownloadStatus.CANCELLED):
                task.cancel()
        tasks.clear()
        cards.clear()
        download_list.controls.clear()
        download_list.controls.append(empty_state)
        queue_count_text.value = "0 items"
        set_status("Queue cleared")
        page.update()

    def download_all(e):
        queued = [t for t in tasks.values() if t.status == DownloadStatus.QUEUED]
        if not queued:
            page.open(ft.SnackBar(ft.Text("No queued items")))
            return

        download_all_btn.disabled = True
        download_all_btn.text = "Downloading..."
        page.update()
        set_status(f"Starting {len(queued)} downloads...")

        for task in queued:
            executor.submit(_run_download, task)

    def _run_download(task):
        def on_progress(t):
            update_card(t)
            _update_status_bar()

        try:
            if task.artist == "Unknown" and not task.thumbnail_url:
                try:
                    info = downloader.get_video_info(task.url)
                    task.title = info.get("title", task.title)
                    task.artist = info.get("artist", "Unknown")
                    task.duration = info.get("duration", task.duration)
                except Exception:
                    pass
            downloader.download(task, quality=quality, progress_callback=on_progress)
        except Exception as ex:
            task.status = DownloadStatus.ERROR
            task.error_message = str(ex)
            on_progress(task)
        finally:
            _check_all_done()

    def _update_status_bar():
        active = sum(1 for t in tasks.values()
                     if t.status in (DownloadStatus.DOWNLOADING, DownloadStatus.CONVERTING, DownloadStatus.FETCHING_INFO))
        done = sum(1 for t in tasks.values() if t.status == DownloadStatus.COMPLETE)
        set_status(f"Active: {active}  ·  Done: {done}/{len(tasks)}")

    def _check_all_done():
        active = sum(1 for t in tasks.values()
                     if t.status in (DownloadStatus.DOWNLOADING, DownloadStatus.CONVERTING,
                                     DownloadStatus.FETCHING_INFO, DownloadStatus.QUEUED))
        if active == 0:
            download_all_btn.disabled = False
            download_all_btn.text = "Download All"
            done = sum(1 for t in tasks.values() if t.status == DownloadStatus.COMPLETE)
            set_status(f"All done! {done} files downloaded ✓")
            try:
                page.update()
            except Exception:
                pass

    def toggle_theme(e):
        page.theme_mode = (
            ft.ThemeMode.LIGHT if page.theme_mode == ft.ThemeMode.DARK
            else ft.ThemeMode.DARK
        )
        page.update()

    def show_about(e):
        page.open(ft.AlertDialog(
            title=ft.Text("DC v2.0"),
            content=ft.Text(
                "YouTube MP3 Downloader\n\n"
                "· Playlists & batch URLs\n"
                "· Up to 320kbps quality\n"
                "· Dark & light themes\n\n"
                "Powered by yt-dlp & Flet"
            ),
        ))

    # ═══════════════ BUILD UI ═══════════════

    page.add(
        # ── Header ──
        ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.MUSIC_NOTE, color=ft.Colors.DEEP_PURPLE_400, size=28),
                    ft.Text("DC", size=22, weight=ft.FontWeight.BOLD),
                    ft.Container(expand=True),
                    ft.IconButton(ft.Icons.BRIGHTNESS_6, on_click=toggle_theme, icon_size=20),
                    ft.IconButton(ft.Icons.INFO_OUTLINE, on_click=show_about, icon_size=20),
                ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
                ft.Text("YouTube MP3 Downloader", size=12, color=ft.Colors.GREY_500),
            ], spacing=2),
            padding=ft.padding.only(left=20, right=12, top=12, bottom=8),
        ),

        # ── URL Input ──
        ft.Container(
            content=url_input,
            padding=ft.padding.symmetric(horizontal=14, vertical=4),
        ),

        # ── Action row ──
        ft.Container(
            content=ft.Row([
                quality_dropdown,
                ft.ElevatedButton("Paste", height=42, on_click=paste_url),
                add_btn,
            ], spacing=8),
            padding=ft.padding.only(left=14, right=14, top=4, bottom=8),
        ),

        # ── Queue header ──
        ft.Container(
            content=ft.Row([
                ft.Text("Queue", size=16, weight=ft.FontWeight.BOLD),
                queue_count_text,
                ft.Container(expand=True),
                download_all_btn,
                ft.IconButton(ft.Icons.DELETE_SWEEP, on_click=clear_queue, icon_size=20),
            ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
            padding=ft.padding.symmetric(horizontal=16, vertical=4),
        ),

        ft.Divider(height=1, thickness=0.5),

        # ── Download list ──
        ft.Container(
            content=download_list,
            padding=ft.padding.symmetric(horizontal=12, vertical=4),
            expand=True,
        ),

        # ── Status bar ──
        ft.Container(
            content=ft.Row([
                status_text,
                ft.Container(expand=True),
                ft.Text("v2.0", size=10, color=ft.Colors.GREY_600),
            ]),
            padding=ft.padding.symmetric(horizontal=16, vertical=6),
            bgcolor=ft.Colors.with_opacity(0.03, ft.Colors.WHITE),
        ),
    )


ft.app(target=main)
