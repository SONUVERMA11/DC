"""
DC v2.0 — YouTube MP3 Downloader Android App
Built with KivyMD 1.1.1 (safe API only).
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
    ColorProperty,
)
from kivy.utils import platform
from kivy.core.clipboard import Clipboard
from kivy.uix.boxlayout import BoxLayout

from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.card import MDCard
from kivymd.uix.button import MDRaisedButton, MDFlatButton, MDIconButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.snackbar import Snackbar
from kivymd.uix.list import OneLineListItem
from kivymd.uix.progressbar import MDProgressBar
from kivymd.uix.toolbar import MDTopAppBar

from downloader import MusicDownloader, DownloadTask, DownloadStatus

# ─────────────────────── Constants ───────────────────────

MAX_CONCURRENT = 3
QUALITY_OPTIONS = ["320kbps (Best)", "256kbps", "192kbps", "128kbps"]
QUALITY_MAP = {
    "320kbps (Best)": "320",
    "256kbps": "256",
    "192kbps": "192",
    "128kbps": "128",
}

# ─────────────────────── KV Layout ───────────────────────
# IMPORTANT: Only uses KivyMD 1.1.1 safe properties.
# No line_color, no material_style M3, no fill_color on MDTextField.

KV = '''
#:import dp kivy.metrics.dp
#:import sp kivy.metrics.sp

<DownloadCard>:
    orientation: "vertical"
    size_hint_y: None
    height: dp(112)
    padding: [dp(14), dp(10), dp(14), dp(8)]
    spacing: dp(4)
    radius: [dp(14)]
    elevation: 1
    md_bg_color: app.card_bg

    BoxLayout:
        size_hint_y: None
        height: dp(40)
        spacing: dp(10)

        MDIconButton:
            icon: root.status_icon
            theme_text_color: "Custom"
            text_color: root.bar_color
            size_hint: None, None
            size: dp(38), dp(38)
            pos_hint: {"center_y": 0.5}

        BoxLayout:
            orientation: "vertical"
            spacing: dp(1)

            Label:
                text: root.title
                font_size: sp(13)
                bold: True
                color: app.text_primary
                text_size: self.size
                halign: "left"
                valign: "center"
                shorten: True
                shorten_from: "right"
                size_hint_y: None
                height: dp(20)

            Label:
                text: root.artist + "  ·  " + root.duration
                font_size: sp(11)
                color: app.text_sub
                text_size: self.size
                halign: "left"
                valign: "center"
                shorten: True
                shorten_from: "right"
                size_hint_y: None
                height: dp(16)

        MDIconButton:
            icon: "close"
            theme_text_color: "Custom"
            text_color: app.text_sub
            size_hint: None, None
            size: dp(30), dp(30)
            pos_hint: {"center_y": 0.5}
            on_release: app.cancel_download(root.task_id)

    MDProgressBar:
        value: root.progress_value
        color: root.bar_color
        size_hint_y: None
        height: dp(4)

    BoxLayout:
        size_hint_y: None
        height: dp(18)

        Label:
            text: root.status_text
            font_size: sp(10)
            bold: True
            color: root.status_color
            text_size: self.size
            halign: "left"
            valign: "center"

        Label:
            text: root.speed_text
            font_size: sp(10)
            color: app.text_sub
            text_size: self.size
            halign: "right"
            valign: "center"


<RootScreen>:
    md_bg_color: app.bg

    BoxLayout:
        orientation: "vertical"

        MDTopAppBar:
            title: "DC"
            md_bg_color: app.bar_bg
            specific_text_color: app.text_primary
            elevation: 2
            left_action_items: [["music-note-eighth", lambda x: None]]
            right_action_items: [["theme-light-dark", lambda x: app.toggle_theme()], ["information-outline", lambda x: app.show_about()]]

        # URL Input
        BoxLayout:
            size_hint_y: None
            height: dp(56)
            padding: [dp(12), dp(8), dp(12), dp(4)]

            MDTextField:
                id: url_input
                hint_text: "Paste YouTube URL or playlist..."
                mode: "rectangle"
                size_hint_x: 1
                on_text_validate: app.add_url()

        # Action Buttons
        BoxLayout:
            size_hint_y: None
            height: dp(48)
            padding: [dp(12), dp(2), dp(12), dp(6)]
            spacing: dp(8)

            MDRaisedButton:
                id: quality_btn
                text: "320k"
                elevation: 0
                size_hint_x: 0.22
                on_release: app.open_quality_menu(self)

            MDRaisedButton:
                text: "Paste"
                elevation: 0
                size_hint_x: 0.22
                on_release: app.paste_url()

            MDRaisedButton:
                id: add_btn
                text: "+ Add"
                md_bg_color: app.theme_cls.primary_color
                elevation: 1
                size_hint_x: 0.56
                on_release: app.add_url()

        # Queue Header
        BoxLayout:
            size_hint_y: None
            height: dp(44)
            padding: [dp(16), dp(6), dp(12), dp(2)]

            Label:
                id: queue_count
                text: "Downloads (0)"
                font_size: sp(15)
                bold: True
                color: app.text_primary
                text_size: self.size
                halign: "left"
                valign: "center"

            Widget:

            MDRaisedButton:
                id: download_all_btn
                text: "Download All"
                md_bg_color: app.theme_cls.primary_color
                size_hint: None, None
                size: dp(120), dp(36)
                pos_hint: {"center_y": 0.5}
                on_release: app.download_all()

            MDIconButton:
                icon: "delete-sweep-outline"
                theme_text_color: "Custom"
                text_color: app.text_sub
                size_hint: None, None
                size: dp(36), dp(36)
                pos_hint: {"center_y": 0.5}
                on_release: app.clear_queue()

        # Download List
        ScrollView:
            do_scroll_x: False

            BoxLayout:
                id: download_list
                orientation: "vertical"
                size_hint_y: None
                height: self.minimum_height
                padding: [dp(10), dp(4)]
                spacing: dp(8)

                Label:
                    id: empty_label
                    text: "Paste a YouTube URL above to start downloading"
                    font_size: sp(13)
                    color: app.text_sub
                    halign: "center"
                    size_hint_y: None
                    height: dp(100)
                    opacity: 1

        # Status Bar
        BoxLayout:
            size_hint_y: None
            height: dp(28)
            padding: [dp(16), dp(4)]
            md_bg_color: app.bar_bg

            Label:
                id: status_label
                text: "Ready  ·  v2.0"
                font_size: sp(10)
                color: app.text_sub
                text_size: self.size
                halign: "left"
                valign: "center"
'''


# ─────────────────── Widgets ─────────────────────────────

class DownloadCard(MDCard):
    task_id = StringProperty("")
    title = StringProperty("Unknown")
    artist = StringProperty("Unknown")
    duration = StringProperty("0:00")
    status_text = StringProperty("Queued")
    progress_value = NumericProperty(0)
    speed_text = StringProperty("")
    status_color = ColorProperty([0.5, 0.55, 0.65, 1])
    bar_color = ColorProperty([0.45, 0.22, 0.9, 1])
    status_icon = StringProperty("clock-outline")


class RootScreen(MDScreen):
    pass


# ─────────────────── Application ─────────────────────────

class YouTubeMP3App(MDApp):

    # Theme properties — safe names, no conflicts
    bg = ColorProperty([0.06, 0.06, 0.09, 1])
    card_bg = ColorProperty([0.1, 0.1, 0.15, 1])
    bar_bg = ColorProperty([0.05, 0.05, 0.08, 1])
    text_primary = ColorProperty([0.94, 0.95, 0.97, 1])
    text_sub = ColorProperty([0.5, 0.54, 0.62, 1])

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
        # Do NOT use material_style M3 — can cause crashes in 1.1.1
        self._apply_dark()
        return Builder.load_string(KV)

    def _apply_dark(self):
        self.bg = [0.06, 0.06, 0.09, 1]
        self.card_bg = [0.1, 0.1, 0.15, 1]
        self.bar_bg = [0.05, 0.05, 0.08, 1]
        self.text_primary = [0.94, 0.95, 0.97, 1]
        self.text_sub = [0.5, 0.54, 0.62, 1]

    def _apply_light(self):
        self.bg = [0.96, 0.96, 0.98, 1]
        self.card_bg = [1, 1, 1, 1]
        self.bar_bg = [0.94, 0.94, 0.96, 1]
        self.text_primary = [0.1, 0.1, 0.16, 1]
        self.text_sub = [0.45, 0.48, 0.56, 1]

    def toggle_theme(self):
        self._is_dark = not self._is_dark
        if self._is_dark:
            self.theme_cls.theme_style = "Dark"
            self._apply_dark()
        else:
            self.theme_cls.theme_style = "Light"
            self._apply_light()

    # ─── Quality ───

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
            self.quality_menu = MDDropdownMenu(
                caller=caller, items=items, width_mult=3
            )
        self.quality_menu.caller = caller
        self.quality_menu.open()

    def _set_quality(self, text):
        self.quality = QUALITY_MAP.get(text, "320")
        self.root.ids.quality_btn.text = text.split(" ")[0].replace("kbps", "k")
        self.quality_menu.dismiss()

    # ─── URL ───

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
            Clock.schedule_once(lambda dt: self._set_status("Error: " + str(e)[:50]))
        finally:
            Clock.schedule_once(lambda dt: self._reset_add_btn())

    def _resolve_single(self, url):
        try:
            if self.downloader.is_playlist(url):
                entries = self.downloader.get_playlist_entries(url)
                Clock.schedule_once(
                    lambda dt: self._set_status("Found " + str(len(entries)) + " tracks")
                )
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
            Clock.schedule_once(lambda dt: self._set_status("Error: " + str(e)[:50]))

    def _fmt_dur(self, seconds):
        try:
            s = int(seconds)
            return str(s // 60) + ":" + str(s % 60).zfill(2)
        except (TypeError, ValueError):
            return "0:00"

    def _get_output_dir(self):
        if platform == "android":
            from android.storage import primary_external_storage_path
            return os.path.join(primary_external_storage_path(), "Music", "YT Downloads")
        return os.path.join(os.path.expanduser("~"), "Music", "YT Downloads")

    def _reset_add_btn(self):
        self.root.ids.add_btn.text = "+ Add"
        self.root.ids.add_btn.disabled = False

    # ─── Queue ───

    def _add_to_queue(self, task):
        self.root.ids.empty_label.opacity = 0
        self.root.ids.empty_label.height = 0

        self.tasks[task.task_id] = task
        card = DownloadCard(
            task_id=task.task_id,
            title=task.title,
            artist=task.artist,
            duration=task.duration,
        )
        self.widgets[task.task_id] = card
        self.root.ids.download_list.add_widget(card)
        self._update_count()
        self._set_status("Added: " + task.title[:40])

    def _update_count(self):
        self.root.ids.queue_count.text = "Downloads (" + str(len(self.tasks)) + ")"

    def cancel_download(self, task_id):
        task = self.tasks.get(task_id)
        if task and task.status not in (DownloadStatus.COMPLETE, DownloadStatus.CANCELLED):
            task.cancel()
            self._update_card(task)
            self._set_status("Cancelled: " + task.title[:40])

    def clear_queue(self):
        for task in self.tasks.values():
            if task.status not in (DownloadStatus.COMPLETE, DownloadStatus.ERROR, DownloadStatus.CANCELLED):
                task.cancel()
        for widget in self.widgets.values():
            self.root.ids.download_list.remove_widget(widget)
        self.tasks.clear()
        self.widgets.clear()
        self.root.ids.empty_label.opacity = 1
        self.root.ids.empty_label.height = dp(100)
        self._update_count()
        self._set_status("Queue cleared")

    # ─── Download ───

    def download_all(self):
        queued = [t for t in self.tasks.values() if t.status == DownloadStatus.QUEUED]
        if not queued:
            Snackbar(text="No queued items").open()
            return
        self.root.ids.download_all_btn.disabled = True
        self.root.ids.download_all_btn.text = "Working..."
        self._set_status("Starting " + str(len(queued)) + " downloads...")
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

        styles = {
            DownloadStatus.QUEUED:        ([0.5, 0.55, 0.65, 1], [0.45, 0.22, 0.9, 1], "clock-outline"),
            DownloadStatus.FETCHING_INFO: ([0.96, 0.68, 0.12, 1], [0.96, 0.68, 0.12, 1], "magnify"),
            DownloadStatus.DOWNLOADING:   ([0.25, 0.58, 1.0, 1], [0.25, 0.58, 1.0, 1], "download"),
            DownloadStatus.CONVERTING:    ([0.96, 0.68, 0.12, 1], [0.96, 0.68, 0.12, 1], "cog"),
            DownloadStatus.COMPLETE:      ([0.18, 0.8, 0.44, 1], [0.18, 0.8, 0.44, 1], "check-circle"),
            DownloadStatus.ERROR:         ([0.95, 0.3, 0.3, 1], [0.95, 0.3, 0.3, 1], "alert-circle"),
            DownloadStatus.CANCELLED:     ([0.5, 0.55, 0.65, 1], [0.5, 0.55, 0.65, 1], "close-circle"),
        }
        s = styles.get(task.status, styles[DownloadStatus.QUEUED])
        card.status_color = s[0]
        card.bar_color = s[1]
        card.status_icon = s[2]

        if task.status == DownloadStatus.DOWNLOADING:
            speed = task.speed or ""
            eta = (" ETA " + task.eta) if task.eta else ""
            card.speed_text = speed + eta + " " + str(int(task.progress)) + "%"
        elif task.status == DownloadStatus.COMPLETE:
            card.speed_text = "Done"
        elif task.status == DownloadStatus.ERROR:
            card.speed_text = task.error_message[:30]
        elif task.status == DownloadStatus.CONVERTING:
            card.speed_text = "Converting..."
        elif task.status == DownloadStatus.CANCELLED:
            card.speed_text = "Cancelled"
        else:
            card.speed_text = ""

    def _update_status_bar(self):
        active = sum(
            1 for t in self.tasks.values()
            if t.status in (DownloadStatus.DOWNLOADING, DownloadStatus.CONVERTING, DownloadStatus.FETCHING_INFO)
        )
        done = sum(1 for t in self.tasks.values() if t.status == DownloadStatus.COMPLETE)
        self._set_status("Active: " + str(active) + "  Done: " + str(done) + "/" + str(len(self.tasks)))

    def _check_all_done(self):
        self._update_status_bar()
        active = sum(
            1 for t in self.tasks.values()
            if t.status in (DownloadStatus.DOWNLOADING, DownloadStatus.CONVERTING, DownloadStatus.FETCHING_INFO, DownloadStatus.QUEUED)
        )
        if active == 0:
            self.root.ids.download_all_btn.disabled = False
            self.root.ids.download_all_btn.text = "Download All"
            done = sum(1 for t in self.tasks.values() if t.status == DownloadStatus.COMPLETE)
            self._set_status("All done! " + str(done) + " files downloaded")

    def _set_status(self, text):
        self.root.ids.status_label.text = text

    def show_about(self):
        dialog = MDDialog(
            title="DC v2.0",
            text="YouTube MP3 Downloader\n\nPlaylists, batch URLs, 320kbps\nDark and light themes\n\nPowered by yt-dlp",
            buttons=[MDFlatButton(text="OK", on_release=lambda x: dialog.dismiss())],
        )
        dialog.open()

    def on_stop(self):
        for task in self.tasks.values():
            task.cancel()
        self.executor.shutdown(wait=False, cancel_futures=True)


if __name__ == "__main__":
    YouTubeMP3App().run()
