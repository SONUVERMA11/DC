"""
DC v2.0 — YouTube MP3 Downloader Android App
Premium Material Design 3 app built with KivyMD.
"""

import os
import uuid
import threading
from concurrent.futures import ThreadPoolExecutor

from kivy.clock import Clock
from kivy.lang import Builder
from kivy.metrics import dp
from kivy.properties import (
    StringProperty, NumericProperty, BooleanProperty,
    ListProperty, ColorProperty,
)
from kivy.utils import platform
from kivy.core.clipboard import Clipboard
from kivy.uix.boxlayout import BoxLayout
from kivy.animation import Animation
from kivy.graphics import Color, RoundedRectangle, Rectangle, Line, Ellipse

from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.card import MDCard
from kivymd.uix.button import MDRaisedButton, MDFlatButton, MDIconButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.snackbar import Snackbar
from kivymd.uix.list import OneLineListItem

from downloader import MusicDownloader, DownloadTask, DownloadStatus

# ─────────────────────── Constants ───────────────────────

MAX_CONCURRENT = 3
QUALITY_OPTIONS = ["320kbps (Best)", "256kbps", "192kbps", "128kbps"]
QUALITY_MAP = {"320kbps (Best)": "320", "256kbps": "256", "192kbps": "192", "128kbps": "128"}

# ─────────────────────── KV Layout ───────────────────────

KV = '''
#:import dp kivy.metrics.dp
#:import sp kivy.metrics.sp
#:import Window kivy.core.window.Window
#:import Animation kivy.animation.Animation

# ══════════════════════ Download Card ══════════════════════

<DownloadCard>:
    orientation: "vertical"
    size_hint_y: None
    height: dp(136)
    padding: [dp(16), dp(14), dp(16), dp(12)]
    spacing: dp(6)
    radius: dp(20), dp(20), dp(20), dp(20)
    elevation: 0
    md_bg_color: app.card_color

    canvas.before:
        # Accent stripe on left
        Color:
            rgba: root.bar_color
        RoundedRectangle:
            pos: self.x, self.y
            size: dp(4), self.height
            radius: [dp(20), 0, 0, dp(20)]

    # ── Title row ──
    BoxLayout:
        size_hint_y: None
        height: dp(46)
        spacing: dp(12)

        # Music icon with colored bg
        BoxLayout:
            size_hint: None, None
            size: dp(42), dp(42)
            pos_hint: {"center_y": 0.5}
            canvas.before:
                Color:
                    rgba: root.bar_color[0], root.bar_color[1], root.bar_color[2], 0.15
                RoundedRectangle:
                    pos: self.pos
                    size: self.size
                    radius: [dp(12)]

            MDIconButton:
                icon: root.status_icon
                theme_icon_color: "Custom"
                icon_color: root.bar_color
                size_hint: None, None
                size: dp(42), dp(42)

        # Title + artist
        BoxLayout:
            orientation: "vertical"
            spacing: dp(2)

            Label:
                text: root.title
                font_size: sp(14)
                bold: True
                color: app.text_color
                text_size: self.size
                halign: "left"
                valign: "center"
                shorten: True
                shorten_from: "right"
                size_hint_y: None
                height: dp(22)

            Label:
                text: f"{root.artist}  ·  {root.duration}"
                font_size: sp(11.5)
                color: app.text_secondary
                text_size: self.size
                halign: "left"
                valign: "center"
                shorten: True
                shorten_from: "right"
                size_hint_y: None
                height: dp(18)

        MDIconButton:
            icon: "close"
            theme_icon_color: "Custom"
            icon_color: app.text_muted
            size_hint: None, None
            size: dp(34), dp(34)
            pos_hint: {"center_y": 0.5}
            on_release: app.cancel_download(root.task_id)

    # ── Progress bar ──
    BoxLayout:
        size_hint_y: None
        height: dp(8)
        padding: [0, dp(2)]

        canvas.before:
            Color:
                rgba: app.progress_bg
            RoundedRectangle:
                pos: self.pos
                size: self.size
                radius: [dp(4)]

        Widget:
            size_hint_x: root.progress_value / 100 if root.progress_value > 0 else 0.001
            canvas.before:
                Color:
                    rgba: root.bar_color
                RoundedRectangle:
                    pos: self.pos
                    size: self.size
                    radius: [dp(4)]

    # ── Status row ──
    BoxLayout:
        size_hint_y: None
        height: dp(24)
        spacing: dp(6)

        # Status chip
        BoxLayout:
            size_hint: None, None
            size: self.minimum_width + dp(16), dp(22)
            pos_hint: {"center_y": 0.5}
            canvas.before:
                Color:
                    rgba: root.status_color[0], root.status_color[1], root.status_color[2], 0.12
                RoundedRectangle:
                    pos: self.pos
                    size: self.size
                    radius: [dp(11)]

            Label:
                text: root.status_text
                font_size: sp(10.5)
                bold: True
                color: root.status_color
                size_hint_x: None
                width: self.texture_size[0]
                padding: [dp(8), 0]
                text_size: None, self.height
                valign: "center"

        Widget:

        Label:
            text: root.speed_text
            font_size: sp(10.5)
            color: app.text_secondary
            text_size: self.size
            halign: "right"
            valign: "center"
            size_hint_x: 0.5


# ══════════════════════ Root Screen ══════════════════════

<RootScreen>:
    md_bg_color: app.bg_color

    BoxLayout:
        orientation: "vertical"

        # ── Gradient Header ──
        BoxLayout:
            size_hint_y: None
            height: dp(110)
            padding: [dp(22), dp(16), dp(22), dp(12)]
            orientation: "vertical"

            canvas.before:
                Color:
                    rgba: app.header_grad_start
                Rectangle:
                    pos: self.pos
                    size: self.size

            # Top row: logo + actions
            BoxLayout:
                size_hint_y: None
                height: dp(42)

                BoxLayout:
                    spacing: dp(8)
                    size_hint_x: None
                    width: self.minimum_width

                    MDIconButton:
                        icon: "music-note-eighth"
                        theme_icon_color: "Custom"
                        icon_color: app.accent_color
                        size_hint: None, None
                        size: dp(38), dp(38)
                        pos_hint: {"center_y": 0.5}

                    Label:
                        text: "DC"
                        font_size: sp(24)
                        bold: True
                        color: app.text_color
                        size_hint: None, None
                        size: self.texture_size
                        pos_hint: {"center_y": 0.5}

                Widget:

                MDIconButton:
                    icon: "theme-light-dark"
                    theme_icon_color: "Custom"
                    icon_color: app.text_secondary
                    size_hint: None, None
                    size: dp(38), dp(38)
                    pos_hint: {"center_y": 0.5}
                    on_release: app.toggle_theme()

                MDIconButton:
                    icon: "information-outline"
                    theme_icon_color: "Custom"
                    icon_color: app.text_secondary
                    size_hint: None, None
                    size: dp(38), dp(38)
                    pos_hint: {"center_y": 0.5}
                    on_release: app.show_about()

            # Subtitle
            Label:
                text: "YouTube MP3 Downloader"
                font_size: sp(13)
                color: app.text_secondary
                text_size: self.size
                halign: "left"
                valign: "top"
                size_hint_y: None
                height: dp(20)
                padding: [dp(2), 0]

        # ── URL Input Area ──
        BoxLayout:
            size_hint_y: None
            height: dp(56)
            padding: [dp(16), dp(8), dp(16), dp(4)]
            spacing: dp(8)

            MDTextField:
                id: url_input
                hint_text: "Paste YouTube URL or playlist link..."
                mode: "round"
                size_hint_x: 1
                fill_color_normal: app.input_bg_color
                fill_color_focus: app.input_bg_color
                line_color_focus: app.accent_color
                hint_text_color_normal: app.text_muted
                text_color_normal: app.text_color
                text_color_focus: app.text_color
                on_text_validate: app.add_url()

        # ── Action Buttons Row ──
        BoxLayout:
            size_hint_y: None
            height: dp(46)
            padding: [dp(16), dp(2), dp(16), dp(6)]
            spacing: dp(8)

            MDRaisedButton:
                id: quality_btn
                text: "320k"
                md_bg_color: app.chip_bg_color
                text_color: app.text_color
                elevation: 0
                size_hint_x: 0.22
                font_size: sp(12)
                on_release: app.open_quality_menu(self)

            MDRaisedButton:
                text: "Paste"
                md_bg_color: app.chip_bg_color
                text_color: app.text_color
                elevation: 0
                size_hint_x: 0.22
                font_size: sp(12)
                on_release: app.paste_url()

            MDRaisedButton:
                id: add_btn
                text: "+  Add"
                md_bg_color: app.accent_color
                text_color: [1, 1, 1, 1]
                elevation: 0
                size_hint_x: 0.56
                font_size: sp(13)
                on_release: app.add_url()

        # ── Queue Section Header ──
        BoxLayout:
            size_hint_y: None
            height: dp(44)
            padding: [dp(20), dp(6), dp(16), dp(2)]
            spacing: dp(8)

            Label:
                id: queue_label
                text: "Queue"
                font_size: sp(17)
                bold: True
                color: app.text_color
                text_size: self.size
                halign: "left"
                valign: "center"

            Label:
                id: queue_count
                text: "0 items"
                font_size: sp(12)
                color: app.text_muted
                text_size: self.size
                halign: "left"
                valign: "center"
                size_hint_x: 0.3

            Widget:

            MDIconButton:
                icon: "delete-sweep-outline"
                theme_icon_color: "Custom"
                icon_color: app.text_muted
                size_hint: None, None
                size: dp(36), dp(36)
                pos_hint: {"center_y": 0.5}
                on_release: app.clear_queue()

        # ── DOWNLOAD LIST ──
        ScrollView:
            do_scroll_x: False
            bar_width: dp(3)
            bar_color: app.accent_color

            BoxLayout:
                id: download_list
                orientation: "vertical"
                size_hint_y: None
                height: self.minimum_height
                padding: [dp(12), dp(4), dp(12), dp(80)]
                spacing: dp(10)

                # Empty state
                BoxLayout:
                    id: empty_state
                    orientation: "vertical"
                    size_hint_y: None
                    height: dp(200)
                    spacing: dp(8)
                    opacity: 1

                    Widget:
                        size_hint_y: 0.3

                    MDIconButton:
                        icon: "music-note-plus"
                        theme_icon_color: "Custom"
                        icon_color: app.text_muted
                        size_hint: None, None
                        size: dp(64), dp(64)
                        pos_hint: {"center_x": 0.5}
                        disabled: True

                    Label:
                        text: "No downloads yet"
                        font_size: sp(16)
                        bold: True
                        color: app.text_muted
                        halign: "center"
                        size_hint_y: None
                        height: dp(24)

                    Label:
                        text: "Paste a YouTube URL above to get started"
                        font_size: sp(12)
                        color: app.text_muted
                        halign: "center"
                        size_hint_y: None
                        height: dp(20)

                    Widget:
                        size_hint_y: 0.3

        # ── Floating Download Button ──
        BoxLayout:
            size_hint_y: None
            height: dp(64)
            padding: [dp(16), dp(8), dp(16), dp(8)]

            canvas.before:
                Color:
                    rgba: app.bg_color
                Rectangle:
                    pos: self.pos
                    size: self.size

            MDRaisedButton:
                id: download_all_btn
                text: "▶  Download All"
                md_bg_color: app.accent_color
                text_color: [1, 1, 1, 1]
                elevation: 0
                size_hint_x: 1
                font_size: sp(15)
                on_release: app.download_all()

        # ── Status Bar ──
        BoxLayout:
            size_hint_y: None
            height: dp(30)
            padding: [dp(20), dp(4)]
            canvas.before:
                Color:
                    rgba: app.status_bar_color
                Rectangle:
                    pos: self.pos
                    size: self.size

            Label:
                id: status_label
                text: "Ready"
                font_size: sp(10.5)
                color: app.text_muted
                text_size: self.size
                halign: "left"
                valign: "center"

            Label:
                text: "v2.0"
                font_size: sp(10)
                color: app.text_muted
                text_size: self.size
                halign: "right"
                valign: "center"
                size_hint_x: 0.2
'''


# ─────────────────── Download Card Widget ────────────────

class DownloadCard(MDCard):
    """Card widget for a single download item."""
    task_id = StringProperty("")
    title = StringProperty("Unknown")
    artist = StringProperty("Unknown")
    duration = StringProperty("0:00")
    status_text = StringProperty("Queued")
    progress_value = NumericProperty(0)
    speed_text = StringProperty("")
    status_color = ColorProperty([0.5, 0.55, 0.65, 1])
    bar_color = ColorProperty([0.47, 0.26, 0.95, 1])  # Electric violet
    status_icon = StringProperty("music-note")


# ─────────────────── Root Screen ─────────────────────────

class RootScreen(MDScreen):
    pass


# ─────────────────── Main Application ────────────────────

class YouTubeMP3App(MDApp):
    """Main KivyMD application — DC v2.0."""

    # ── Theme colors (reactive properties) ──
    bg_color = ColorProperty([0.05, 0.05, 0.08, 1])
    card_color = ColorProperty([0.09, 0.09, 0.14, 1])
    header_grad_start = ColorProperty([0.07, 0.06, 0.14, 1])
    input_bg_color = ColorProperty([0.11, 0.11, 0.18, 1])
    chip_bg_color = ColorProperty([0.13, 0.13, 0.2, 1])
    border_color = ColorProperty([0.16, 0.17, 0.25, 1])
    text_color = ColorProperty([0.95, 0.96, 0.98, 1])
    text_secondary = ColorProperty([0.55, 0.58, 0.68, 1])
    text_muted = ColorProperty([0.38, 0.42, 0.52, 1])
    progress_bg = ColorProperty([0.12, 0.12, 0.2, 1])
    accent_color = ColorProperty([0.47, 0.26, 0.95, 1])   # #7842F2
    status_bar_color = ColorProperty([0.04, 0.04, 0.07, 1])

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.downloader = MusicDownloader()
        self.tasks = {}
        self.widgets = {}
        self.executor = ThreadPoolExecutor(max_workers=MAX_CONCURRENT)
        self.quality = "320"
        self.active_count = 0
        self._lock = threading.Lock()
        self.quality_menu = None
        self._is_dark = True

    def build(self):
        self.title = "DC"
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "DeepPurple"
        self.theme_cls.material_style = "M3"
        self._apply_dark_theme()
        return Builder.load_string(KV)

    # ─────────── Theme Management ───────────

    def _apply_dark_theme(self):
        self.bg_color = [0.05, 0.05, 0.08, 1]
        self.card_color = [0.09, 0.09, 0.14, 1]
        self.header_grad_start = [0.07, 0.06, 0.14, 1]
        self.input_bg_color = [0.11, 0.11, 0.18, 1]
        self.chip_bg_color = [0.13, 0.13, 0.2, 1]
        self.border_color = [0.16, 0.17, 0.25, 1]
        self.text_color = [0.95, 0.96, 0.98, 1]
        self.text_secondary = [0.55, 0.58, 0.68, 1]
        self.text_muted = [0.38, 0.42, 0.52, 1]
        self.progress_bg = [0.12, 0.12, 0.2, 1]
        self.accent_color = [0.47, 0.26, 0.95, 1]
        self.status_bar_color = [0.04, 0.04, 0.07, 1]

    def _apply_light_theme(self):
        self.bg_color = [0.97, 0.97, 0.98, 1]
        self.card_color = [1, 1, 1, 1]
        self.header_grad_start = [0.95, 0.94, 0.98, 1]
        self.input_bg_color = [0.93, 0.93, 0.96, 1]
        self.chip_bg_color = [0.91, 0.91, 0.95, 1]
        self.border_color = [0.86, 0.87, 0.9, 1]
        self.text_color = [0.1, 0.1, 0.15, 1]
        self.text_secondary = [0.42, 0.44, 0.52, 1]
        self.text_muted = [0.58, 0.6, 0.66, 1]
        self.progress_bg = [0.88, 0.88, 0.92, 1]
        self.accent_color = [0.42, 0.2, 0.88, 1]
        self.status_bar_color = [0.94, 0.94, 0.96, 1]

    def toggle_theme(self):
        self._is_dark = not self._is_dark
        if self._is_dark:
            self.theme_cls.theme_style = "Dark"
            self._apply_dark_theme()
        else:
            self.theme_cls.theme_style = "Light"
            self._apply_light_theme()

    # ─────────── Quality Menu ───────────

    def open_quality_menu(self, caller):
        if not self.quality_menu:
            items = []
            for q in QUALITY_OPTIONS:
                items.append({
                    "text": q,
                    "viewclass": "OneLineListItem",
                    "height": dp(48),
                    "on_release": lambda x=q: self._set_quality(x),
                })
            self.quality_menu = MDDropdownMenu(caller=caller, items=items, width_mult=3)
        self.quality_menu.caller = caller
        self.quality_menu.open()

    def _set_quality(self, quality_text):
        self.quality = QUALITY_MAP.get(quality_text, "320")
        self.root.ids.quality_btn.text = quality_text.split(" ")[0].replace("bps", "k")
        self.quality_menu.dismiss()

    # ─────────── URL Actions ───────────

    def paste_url(self):
        try:
            text = Clipboard.paste()
            if text:
                self.root.ids.url_input.text = text.strip()
        except Exception:
            Snackbar(text="Could not paste from clipboard").open()

    def add_url(self):
        url = self.root.ids.url_input.text.strip()
        if not url:
            Snackbar(text="Please enter a YouTube URL").open()
            return

        self.root.ids.url_input.text = ""
        self.root.ids.add_btn.text = "Adding..."
        self.root.ids.add_btn.disabled = True
        self._set_status("Resolving URL...")

        threading.Thread(target=self._resolve_url, args=(url,), daemon=True).start()

    def _resolve_url(self, url):
        try:
            urls = [u.strip() for u in url.replace(",", "\n").split("\n") if u.strip()]
            for u in urls:
                self._resolve_single(u)
        except Exception as e:
            Clock.schedule_once(lambda dt: self._set_status(f"Error: {str(e)[:50]}"))
        finally:
            Clock.schedule_once(lambda dt: self._reset_add_btn())

    def _resolve_single(self, url):
        try:
            if self.downloader.is_playlist(url):
                entries = self.downloader.get_playlist_entries(url)
                Clock.schedule_once(lambda dt: self._set_status(f"Found {len(entries)} tracks"))
                for entry in entries:
                    task = DownloadTask(
                        url=entry["url"],
                        output_dir=self._get_output_dir(),
                        task_id=str(uuid.uuid4())[:8],
                        title=entry.get("title", "Unknown"),
                        duration=self._fmt_dur(entry.get("duration", 0)),
                    )
                    Clock.schedule_once(lambda dt, t=task: self._add_to_queue(t))
            else:
                info = self.downloader.get_video_info(url)
                task = DownloadTask(
                    url=url,
                    output_dir=self._get_output_dir(),
                    task_id=str(uuid.uuid4())[:8],
                    title=info.get("title", "Unknown"),
                    artist=info.get("artist", "Unknown"),
                    duration=info.get("duration", "0:00"),
                    thumbnail_url=info.get("thumbnail", ""),
                )
                Clock.schedule_once(lambda dt: self._add_to_queue(task))
        except Exception as e:
            Clock.schedule_once(lambda dt: self._set_status(f"Error: {str(e)[:50]}"))

    def _fmt_dur(self, seconds):
        try:
            s = int(seconds)
            return f"{s // 60}:{s % 60:02d}"
        except (TypeError, ValueError):
            return "0:00"

    def _get_output_dir(self):
        if platform == "android":
            from android.storage import primary_external_storage_path
            return os.path.join(primary_external_storage_path(), "Music", "YT Downloads")
        return os.path.join(os.path.expanduser("~"), "Music", "YT Downloads")

    def _reset_add_btn(self):
        self.root.ids.add_btn.text = "+  Add"
        self.root.ids.add_btn.disabled = False

    # ─────────── Queue Management ───────────

    def _add_to_queue(self, task):
        # Hide empty state
        empty = self.root.ids.empty_state
        empty.opacity = 0
        empty.height = 0

        self.tasks[task.task_id] = task
        card = DownloadCard(
            task_id=task.task_id,
            title=task.title,
            artist=task.artist,
            duration=task.duration,
        )
        self.widgets[task.task_id] = card
        self.root.ids.download_list.add_widget(card)
        self._update_queue_label()
        self._set_status(f"Added: {task.title[:40]}")

    def _update_queue_label(self):
        count = len(self.tasks)
        self.root.ids.queue_count.text = f"{count} item{'s' if count != 1 else ''}"

    def cancel_download(self, task_id):
        task = self.tasks.get(task_id)
        if task and task.status not in (DownloadStatus.COMPLETE, DownloadStatus.CANCELLED):
            task.cancel()
            self._update_card(task)
            self._set_status(f"Cancelled: {task.title[:40]}")

    def clear_queue(self):
        for task in self.tasks.values():
            if task.status not in (DownloadStatus.COMPLETE, DownloadStatus.ERROR, DownloadStatus.CANCELLED):
                task.cancel()
        for widget in self.widgets.values():
            self.root.ids.download_list.remove_widget(widget)
        self.tasks.clear()
        self.widgets.clear()

        # Show empty state
        empty = self.root.ids.empty_state
        empty.opacity = 1
        empty.height = dp(200)

        self._update_queue_label()
        self._set_status("Queue cleared")

    # ─────────── Download Execution ───────────

    def download_all(self):
        queued = [t for t in self.tasks.values() if t.status == DownloadStatus.QUEUED]
        if not queued:
            Snackbar(text="No queued items to download").open()
            return

        self.root.ids.download_all_btn.disabled = True
        self.root.ids.download_all_btn.text = "⏳  Downloading..."
        self._set_status(f"Starting {len(queued)} downloads...")

        for task in queued:
            self.executor.submit(self._run_download, task)

    def _run_download(self, task):
        with self._lock:
            self.active_count += 1

        def on_progress(t):
            Clock.schedule_once(lambda dt: self._update_card(t))
            Clock.schedule_once(lambda dt: self._update_status_bar())

        try:
            if task.artist == "Unknown" and not task.thumbnail_url:
                try:
                    info = self.downloader.get_video_info(task.url)
                    task.title = info.get("title", task.title)
                    task.artist = info.get("artist", "Unknown")
                    task.duration = info.get("duration", task.duration)
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
            Clock.schedule_once(lambda dt: self._check_all_done())

    def _update_card(self, task):
        card = self.widgets.get(task.task_id)
        if not card:
            return

        card.title = task.title
        card.artist = task.artist
        card.duration = task.duration
        card.progress_value = task.progress
        card.status_text = task.status.value

        # Status-specific styling
        style_map = {
            DownloadStatus.QUEUED: {
                "color": [0.5, 0.55, 0.65, 1],
                "bar": [0.47, 0.26, 0.95, 1],
                "icon": "clock-outline",
            },
            DownloadStatus.FETCHING_INFO: {
                "color": [0.96, 0.68, 0.12, 1],
                "bar": [0.96, 0.68, 0.12, 1],
                "icon": "magnify",
            },
            DownloadStatus.DOWNLOADING: {
                "color": [0.25, 0.58, 1.0, 1],
                "bar": [0.25, 0.58, 1.0, 1],
                "icon": "download",
            },
            DownloadStatus.CONVERTING: {
                "color": [0.96, 0.68, 0.12, 1],
                "bar": [0.96, 0.68, 0.12, 1],
                "icon": "cog",
            },
            DownloadStatus.COMPLETE: {
                "color": [0.18, 0.8, 0.44, 1],
                "bar": [0.18, 0.8, 0.44, 1],
                "icon": "check-circle",
            },
            DownloadStatus.ERROR: {
                "color": [0.95, 0.3, 0.3, 1],
                "bar": [0.95, 0.3, 0.3, 1],
                "icon": "alert-circle",
            },
            DownloadStatus.CANCELLED: {
                "color": [0.5, 0.55, 0.65, 1],
                "bar": [0.5, 0.55, 0.65, 1],
                "icon": "close-circle",
            },
        }

        style = style_map.get(task.status, style_map[DownloadStatus.QUEUED])
        card.status_color = style["color"]
        card.bar_color = style["bar"]
        card.status_icon = style["icon"]

        # Speed / info text
        if task.status == DownloadStatus.DOWNLOADING:
            speed = task.speed or ""
            eta = f"  ETA {task.eta}" if task.eta else ""
            card.speed_text = f"{speed}{eta}  ·  {int(task.progress)}%"
        elif task.status == DownloadStatus.COMPLETE:
            card.speed_text = "✓ Done"
        elif task.status == DownloadStatus.ERROR:
            card.speed_text = task.error_message[:35]
        elif task.status == DownloadStatus.CONVERTING:
            card.speed_text = "Converting to MP3..."
        elif task.status == DownloadStatus.CANCELLED:
            card.speed_text = "Cancelled"
        else:
            card.speed_text = ""

    def _update_status_bar(self):
        active = sum(1 for t in self.tasks.values()
                     if t.status in (DownloadStatus.DOWNLOADING, DownloadStatus.CONVERTING,
                                     DownloadStatus.FETCHING_INFO))
        done = sum(1 for t in self.tasks.values() if t.status == DownloadStatus.COMPLETE)
        self._set_status(f"Active: {active}  ·  Complete: {done}/{len(self.tasks)}")

    def _check_all_done(self):
        self._update_status_bar()
        active = sum(1 for t in self.tasks.values()
                     if t.status in (DownloadStatus.DOWNLOADING, DownloadStatus.CONVERTING,
                                     DownloadStatus.FETCHING_INFO, DownloadStatus.QUEUED))
        if active == 0:
            self.root.ids.download_all_btn.disabled = False
            self.root.ids.download_all_btn.text = "▶  Download All"
            done = sum(1 for t in self.tasks.values() if t.status == DownloadStatus.COMPLETE)
            self._set_status(f"All done! {done} files downloaded ✓")

    # ─────────── Helpers ───────────

    def _set_status(self, text):
        self.root.ids.status_label.text = text

    def show_about(self):
        dialog = MDDialog(
            title="DC v2.0",
            text=(
                "Download high-quality MP3 audio from YouTube\n"
                "with embedded metadata and artwork.\n\n"
                "• Supports playlists & batch URLs\n"
                "• Quality: up to 320kbps\n"
                "• Preserves thumbnails & metadata\n"
                "• Dark & light themes\n\n"
                "Powered by yt-dlp"
            ),
            buttons=[MDFlatButton(text="CLOSE", on_release=lambda x: dialog.dismiss())],
        )
        dialog.open()

    def on_stop(self):
        for task in self.tasks.values():
            task.cancel()
        self.executor.shutdown(wait=False, cancel_futures=True)


# ─────────────────── Entry Point ─────────────────────────

if __name__ == "__main__":
    YouTubeMP3App().run()
