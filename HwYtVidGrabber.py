import sys
import os
import re
import json
import yt_dlp
import time
import subprocess
import platform
from PyQt6.QtWidgets import (QApplication, QMainWindow, QLabel, QLineEdit,
                            QPushButton, QComboBox, QVBoxLayout, QHBoxLayout,
                            QWidget, QProgressBar, QMessageBox, QFileDialog,
                            QDialog, QFormLayout, QCheckBox, QSystemTrayIcon, QMenu,
                            QTabWidget, QSizePolicy, QScrollArea, QFrame)
from PyQt6.QtCore import (Qt, QThread, pyqtSignal, QTimer, QSettings, QEvent,
                          QPropertyAnimation, QRect)
from PyQt6.QtGui import QIcon, QFont, QAction, QColor, QPalette, QPixmap
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkRequest
from PyQt6.QtCore import QUrl
import eyed3
import screeninfo
import math
import io
import pytube
import logging

logging.basicConfig(level=logging.DEBUG, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                   filename='yt_downloader_debug.log')

def resource_path(relative_path):
    if getattr(sys, 'frozen', False):
        # When bundled with PyInstaller
        return os.path.join(sys._MEIPASS, relative_path)
    else:
        # When running from source
        return os.path.join(os.path.abspath("."), relative_path)



# Ensure ffmpeg is installed
def check_ffmpeg():
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
        return True
    except FileNotFoundError:
        return False

if not check_ffmpeg():
    QMessageBox.critical(None, "FFmpeg Not Found", "FFmpeg is not installed. Please install it to use this application.")
    sys.exit(1)

def get_default_paths():
    """Get default paths based on operating system"""
    user_home = os.path.expanduser("~")

    if sys.platform == 'win32':
        # Windows paths
        video_path = os.path.join(user_home, "Downloads", "Vids")
        audio_path = os.path.join(user_home, "Downloads", "Songs")
    elif sys.platform == 'darwin':
        # macOS paths
        video_path = os.path.join(user_home, "Downloads", "Vids")
        audio_path = os.path.join(user_home, "Downloads", "Songs")
    else:
        # Linux paths
        video_path = os.path.join(user_home, "Downloads", "Vids")
        audio_path = os.path.join(user_home, "Downloads", "Songs")

    # Create directories if they don't exist
    os.makedirs(video_path, exist_ok=True)
    os.makedirs(audio_path, exist_ok=True)

    return video_path, audio_path

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.initUI()
        self.load_settings()

    def initUI(self):
        self.setWindowTitle("Settings")
        self.setGeometry(200, 200, 400, 200)
        self.setWindowIcon(QIcon(resource_path("resources/icon.ico")))

        layout = QFormLayout()

        # Video save path
        self.video_path_input = QLineEdit()
        browse_video_btn = QPushButton("Browse...")
        browse_video_btn.clicked.connect(self.browse_video_path)

        video_path_layout = QHBoxLayout()
        video_path_layout.addWidget(self.video_path_input)
        video_path_layout.addWidget(browse_video_btn)

        # Audio save path
        self.audio_path_input = QLineEdit()
        browse_audio_btn = QPushButton("Browse...")
        browse_audio_btn.clicked.connect(self.browse_audio_path)

        audio_path_layout = QHBoxLayout()
        audio_path_layout.addWidget(self.audio_path_input)
        audio_path_layout.addWidget(browse_audio_btn)

        layout.addRow("Video Save Path:", video_path_layout)
        layout.addRow("Audio Save Path:", audio_path_layout)

        # Theme selection
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Light", "Dark"])
        layout.addRow("Theme:", self.theme_combo)

        # Post-download action
        self.post_action_combo = QComboBox()
        self.post_action_combo.addItems(["Nothing", "Sleep PC", "Terminate App", "Restart PC", "Shutdown PC"])
        layout.addRow("After Download:", self.post_action_combo)

        # Save button
        save_btn = QPushButton("Save Settings")
        save_btn.clicked.connect(self.save_settings)
        layout.addRow("", save_btn)

        self.setLayout(layout)

    def load_settings(self):
        self.video_path_input.setText(self.parent.settings.value("video_save_path", self.parent.default_video_path))
        self.audio_path_input.setText(self.parent.settings.value("audio_save_path", self.parent.default_audio_path))
        self.theme_combo.setCurrentText(self.parent.settings.value("theme", "Light"))
        self.post_action_combo.setCurrentText(self.parent.settings.value("post_download_action", "Nothing"))

    def browse_video_path(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Directory for Videos")
        if folder:
            self.video_path_input.setText(folder)

    def browse_audio_path(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Directory for Audio")
        if folder:
            self.audio_path_input.setText(folder)

    def save_settings(self):
        self.parent.settings.setValue("video_save_path", self.video_path_input.text())
        self.parent.settings.setValue("audio_save_path", self.audio_path_input.text())
        self.parent.settings.setValue("theme", self.theme_combo.currentText())
        self.parent.settings.setValue("post_download_action", self.post_action_combo.currentText())
        self.parent.load_settings() # Reload settings in main window
        self.accept()

class DownloadProgressHook:
    def __init__(self, progress_callback, info_callback, metadata_callback):
        self.progress_callback = progress_callback
        self.info_callback = info_callback
        self.metadata_callback = metadata_callback
        self.start_time = time.time()
        self.last_downloaded_bytes = 0
        self.last_update_time = self.start_time
        self.total_bytes = None
        self.filename = None
        self.metadata = None

    def __call__(self, d):
        if d['status'] == 'downloading':
            current_time = time.time()
            elapsed = current_time - self.last_update_time

            if elapsed < 0.5 and d.get('eta') is not None: # Update more frequently if eta is available
                return

            self.last_update_time = current_time

            downloaded = d.get('downloaded_bytes', 0)
            self.total_bytes = d.get('total_bytes', d.get('total_bytes_estimate', 0))
            speed = d.get('speed', 0)

            if self.total_bytes > 0:
                percentage = int((downloaded / self.total_bytes) * 100)
                self.progress_callback.emit(percentage)

                downloaded_str = self.format_size(downloaded)
                total_str = self.format_size(self.total_bytes)

                if speed:
                    speed_str = self.format_size(speed) + "/s"
                else:
                    elapsed_total = current_time - self.start_time
                    if elapsed_total > 0:
                        speed = downloaded / elapsed_total
                        speed_str = self.format_size(speed) + "/s"
                    else:
                        speed_str = "N/A"

                eta = d.get('eta')
                eta_str = f"ETA: {self.format_eta(eta)}" if eta is not None else ""

                self.info_callback.emit(f"{downloaded_str} of {total_str} ({speed_str}) {eta_str}")
            else:
                self.progress_callback.emit(-1) # Indeterminate progress

                downloaded_str = self.format_size(downloaded)

                if speed:
                    speed_str = self.format_size(speed) + "/s"
                else:
                    elapsed = current_time - self.last_update_time
                    if elapsed > 0 and downloaded > self.last_downloaded_bytes:
                         current_speed = (downloaded - self.last_downloaded_bytes) / elapsed
                         speed_str = self.format_size(current_speed) + "/s"
                    else:
                         speed_str = "N/A"

                self.info_callback.emit(f"{downloaded_str} downloaded ({speed_str})")

            self.last_downloaded_bytes = downloaded

        elif d['status'] == 'finished':
            self.progress_callback.emit(100)
            self.info_callback.emit("Processing completed file...")
            self.filename = d.get('filename') # Capture the final filename
            if self.metadata:
                 self.metadata_callback.emit(self.metadata, self.filename) # Pass metadata and filename

    def format_size(self, bytes):
        """Format bytes to human-readable size"""
        if bytes is None:
            return "N/A"
        if bytes < 1024:
            return f"{bytes} B"
        elif bytes < 1024 * 1024:
            return f"{bytes/1024:.1f} KB"
        elif bytes < 1024 * 1024 * 1024:
            return f"{bytes/(1024*1024):.1f} MB"
        else:
            return f"{bytes/(1024*1024*1024):.2f} GB"

    def format_eta(self, seconds):
        """Format eta from seconds to HH:MM:SS"""
        if seconds is None:
            return "N/A"
        m, s = divmod(seconds, 60)
        h, m = divmod(m, 60)
        return f"{int(h):02d}:{int(m):02d}:{int(s):02d}"

class MetadataFetchThread(QThread):
    metadata_fetched = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)

    def __init__(self, url):
        super().__init__()
        self.url = url

    def run(self):
        try:
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'skip_download': True,
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info_dict = ydl.extract_info(self.url, download=False)
                self.metadata_fetched.emit(info_dict)
        except Exception as e:
            self.error_occurred.emit(f"Error fetching metadata: {str(e)}")

class DownloadThread(QThread):
    progress_update = pyqtSignal(int)
    download_info = pyqtSignal(str)
    download_complete = pyqtSignal(str)
    download_error = pyqtSignal(str)
    metadata_download_finished = pyqtSignal(dict, str) # Signal to pass metadata and filename after download

    def __init__(self, url, format_options, save_path, ydl_extra_opts=None):
        super().__init__()
        self.url = url
        self.format_options = format_options
        self.save_path = save_path
        self.ydl_extra_opts = ydl_extra_opts if ydl_extra_opts is not None else {}

    def run(self):
        try:
            self.progress_update.emit(5)
            self.download_info.emit("Initializing download...")

            os.makedirs(self.save_path, exist_ok=True)

            ydl_opts = {
                'progress_hooks': [DownloadProgressHook(self.progress_update, self.download_info, self.metadata_download_finished)],
                'quiet': True,
                'no_warnings': True,
                'outtmpl': os.path.join(self.save_path, '%(uploader)s - %(title)s.%(ext)s'),
                **self.format_options,
                **self.ydl_extra_opts
            }

            # Fetch metadata before downloading for the hook
            metadata_ydl_opts = {
                 'quiet': True,
                 'no_warnings': True,
                 'skip_download': True,
             }
            with yt_dlp.YoutubeDL(metadata_ydl_opts) as ydl_meta:
                 info_dict = ydl_meta.extract_info(self.url, download=False)
                 # Pass metadata to the hook
                 for hook in ydl_opts['progress_hooks']:
                      hook.metadata = info_dict

            self.progress_update.emit(10)
            self.download_info.emit("Starting download...")

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(self.url, download=True)
                output_path = ydl.prepare_filename(info) # Get the actual output filename

            self.download_complete.emit(output_path)

        except Exception as e:
            self.download_error.emit(f"Error: {str(e)}")

class SearchResultWidget(QWidget):
    clicked = pyqtSignal(str)

    def __init__(self, video_info):
        super().__init__()
        self.video_info = video_info
        self.initUI()

    def initUI(self):
        layout = QHBoxLayout()
        self.setLayout(layout)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        # Thumbnail
        self.thumbnail_label = QLabel()
        self.thumbnail_label.setFixedSize(120, 90)
        self.thumbnail_label.setStyleSheet("border: 1px solid #ccc;")
        layout.addWidget(self.thumbnail_label)

        # Info
        info_layout = QVBoxLayout()
        self.title_label = QLabel(f"<b>{self.video_info.get('title', 'N/A')}</b>")
        self.title_label.setWordWrap(True)
        self.channel_label = QLabel(f"Channel: {self.video_info.get('channel', 'N/A')}")
        self.duration_label = QLabel(f"Duration: {self.format_duration(self.video_info.get('duration'))}")
        self.views_label = QLabel(f"Views: {self.format_views(self.video_info.get('view_count'))}")

        info_layout.addWidget(self.title_label)
        info_layout.addWidget(self.channel_label)
        info_layout.addWidget(self.duration_label)
        info_layout.addWidget(self.views_label)
        layout.addLayout(info_layout)

        layout.addStretch()

        # Fetch thumbnail
        if self.video_info.get('thumbnail'):
            self.fetch_thumbnail(self.video_info['thumbnail'])

    def fetch_thumbnail(self, url):
         self.manager = QNetworkAccessManager()
         self.manager.finished.connect(self.thumbnail_loaded)
         request = QNetworkRequest(QUrl(url))
         self.manager.get(request)

    def thumbnail_loaded(self, reply):
        if reply.error():
            print(f"Error loading thumbnail: {reply.errorString()}")
            return

        image_data = reply.readAll()
        pixmap = QPixmap()
        pixmap.loadFromData(image_data)
        self.thumbnail_label.setPixmap(pixmap.scaled(self.thumbnail_label.size(), aspectRatioMode=Qt.AspectRatioMode.KeepAspectRatio, transformMode=Qt.TransformationMode.SmoothTransformation))
        reply.deleteLater()


    def format_duration(self, seconds):
        if seconds is None:
            return "N/A"
        m, s = divmod(seconds, 60)
        h, m = divmod(m, 60)
        return f"{int(h):02d}:{int(m):02d}:{int(s):02d}"

    def format_views(self, views):
        if views is None:
            return "N/A"
        if views < 1000:
            return str(views)
        elif views < 1000000:
            return f"{views/1000:.1f}K"
        else:
            return f"{views/1000000:.1f}M"

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.video_info.get('webpage_url', ''))
            super().mousePressEvent(event)


class HwYtVidGrabber(QMainWindow):
    def __init__(self):
        super().__init__()
        self.settings = QSettings("MalikHw47", "HwYtVidGrabber")
        self.default_video_path, self.default_audio_path = get_default_paths()
        self.video_save_path = ""
        self.audio_save_path = ""
        self.title_click_count = 0
        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)
        self.current_theme = "Light"

        self.load_settings()
        self.apply_theme(self.current_theme)
        self.setup_tray()
        self.initUI()


    def load_settings(self):
        self.video_save_path = self.settings.value("video_save_path", self.default_video_path, type=str)
        self.audio_save_path = self.settings.value("audio_save_path", self.default_audio_path, type=str)
        self.current_theme = self.settings.value("theme", "Light", type=str)

        # Ensure directories exist
        os.makedirs(self.video_save_path, exist_ok=True)
        os.makedirs(self.audio_save_path, exist_ok=True)

    def apply_theme(self, theme):
        palette = QPalette()
        if theme == "Dark":
            palette.setColor(QPalette.ColorRole.Window, QColor(53, 53, 53))
            palette.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.white)
            palette.setColor(QPalette.ColorRole.Base, QColor(25, 25, 25))
            palette.setColor(QPalette.ColorRole.AlternateBase, QColor(53, 53, 53))
            palette.setColor(QPalette.ColorRole.ToolTipBase, Qt.GlobalColor.white)
            palette.setColor(QPalette.ColorRole.ToolTipText, Qt.GlobalColor.white)
            palette.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.white)
            palette.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53))
            palette.setColor(QPalette.ColorRole.ButtonText, Qt.GlobalColor.white)
            palette.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.red)
            palette.setColor(QPalette.ColorRole.Link, QColor(42, 130, 218))
            palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
            palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.black)
        else: # Light theme
            palette = QApplication.instance().style().standardPalette()

        QApplication.instance().setPalette(palette)
        self.current_theme = theme

    def setup_tray(self):
        self.tray_icon = QSystemTrayIcon(self)
        try:
            app_icon = QIcon.fromTheme("video-display")
            if app_icon.isNull():
                app_icon = QIcon.fromTheme("applications-multimedia")
                if app_icon.isNull():
                    app_icon = self.style().standardIcon(QApplication.style().StandardPixmap.SP_MediaPlay)
        except:
            app_icon = self.style().standardIcon(QApplication.style().StandardPixmap.SP_MediaPlay)

        self.tray_icon.setIcon(app_icon)
        self.setWindowIcon(app_icon)

        tray_menu = QMenu()
        show_action = QAction("Show", self)
        show_action.triggered.connect(self.show)

        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(self.close_application)

        tray_menu.addAction(show_action)
        tray_menu.addAction(quit_action)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self.tray_icon_activated)
        self.tray_icon.show()

    def tray_icon_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show()

    def hide_to_background(self):
        self.hide()
        self.tray_icon.showMessage(
            "HwYtVidGrabber",
            "Application is still running in the background",
            QSystemTrayIcon.MessageIcon.Information,
            2000
        )

    def close_application(self):
        self.tray_icon.hide()
        QApplication.quit()

    def closeEvent(self, event):
        if self.tray_icon.isVisible():
            QMessageBox.information(
                self,
                "HwYtVidGrabber",
                "The application will keep running in the system tray.\n"
                "To terminate the program, choose 'Quit' in the context menu "
                "of the system tray entry."
            )
            self.hide()
            event.ignore()
        else:
            event.accept()

    def initUI(self):
        self.setWindowTitle("HwYtVidGrabber v1.2 by MalikHw47")
        self.setGeometry(100, 100, 600, 600) # Increased height

        main_widget = QWidget()
        main_layout = QVBoxLayout()

        self.title_label = QLabel("HwYtVidGrabber v1.2")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        self.title_label.setFont(title_font)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.installEventFilter(self) # Install event filter
        main_layout.addWidget(self.title_label)

        author_label = QLabel("By: MalikHw47")
        author_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(author_label)

        donate_btn = QPushButton("Support Development ☕")
        donate_btn.setStyleSheet("background-color: #ff5f5f; color: white; font-weight: bold;")
        donate_btn.clicked.connect(self.open_donation_page)
        main_layout.addWidget(donate_btn)

        main_layout.addSpacing(10)

        # Use Tabs for different sections
        tab_widget = QTabWidget()
        main_layout.addWidget(tab_widget)

        # Download Tab
        download_widget = QWidget()
        download_layout = QVBoxLayout(download_widget)
        tab_widget.addTab(download_widget, "Download")

        url_layout = QHBoxLayout()
        url_label = QLabel("YouTube URL:")
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Paste YouTube URL here...")
        url_layout.addWidget(url_label)
        url_layout.addWidget(self.url_input)
        download_layout.addLayout(url_layout)

        # Display Metadata
        self.metadata_group = QFrame()
        self.metadata_group.setStyleSheet("border: 1px solid #ccc; padding: 10px; border-radius: 5px;")
        self.metadata_layout = QVBoxLayout(self.metadata_group)
        self.metadata_title = QLabel("<b>Video Information</b>")
        self.metadata_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.metadata_layout.addWidget(self.metadata_title)
        self.metadata_layout.addSpacing(5)

        self.metadata_labels = {}
        info_keys = ["Title", "Channel", "Duration", "Views"]
        for key in info_keys:
            label = QLabel(f"{key}: ")
            self.metadata_labels[key] = label
            self.metadata_layout.addWidget(label)

        download_layout.addWidget(self.metadata_group)
        self.metadata_group.setVisible(False) # Hide initially


        # Format Presets
        presets_layout = QHBoxLayout()
        presets_label = QLabel("Format Preset:")
        self.preset_combo = QComboBox()
        self.preset_combo.addItems(["Custom", "Best Quality", "Low Data (360p)", "Medium (480p)"])
        self.preset_combo.currentTextChanged.connect(self.apply_preset)
        presets_layout.addWidget(presets_label)
        presets_layout.addWidget(self.preset_combo)
        download_layout.addLayout(presets_layout)

        # Custom Format Options (initially visible for "Custom")
        self.custom_options_widget = QWidget()
        self.custom_options_layout = QVBoxLayout(self.custom_options_widget)

        resolution_layout = QHBoxLayout()
        resolution_label = QLabel("Resolution:")
        self.resolution_combo = QComboBox()
        self.resolution_combo.addItems(["144", "240", "360", "480", "720", "1080", "1440", "2160"])
        self.resolution_combo.setCurrentText("720")
        resolution_layout.addWidget(resolution_label)
        resolution_layout.addWidget(self.resolution_combo)
        self.custom_options_layout.addLayout(resolution_layout)

        format_layout = QHBoxLayout()
        format_label = QLabel("Format:")
        self.format_combo = QComboBox()
        self.format_combo.addItems(["mp4", "mp3", "muted_mp4"])
        format_layout.addWidget(format_label)
        format_layout.addWidget(self.format_combo)
        self.custom_options_layout.addLayout(format_layout)

        fps_layout = QHBoxLayout()
        self.fps_checkbox = QCheckBox("Prefer 60fps (for 720p and above)")
        self.fps_checkbox.setChecked(True)
        self.update_fps_checkbox_state()
        self.resolution_combo.currentTextChanged.connect(self.update_fps_checkbox_state)
        self.format_combo.currentTextChanged.connect(self.update_fps_checkbox_state)
        fps_layout.addWidget(self.fps_checkbox)
        self.custom_options_layout.addLayout(fps_layout)

        download_layout.addWidget(self.custom_options_widget)

        # Subtitle Options
        subtitle_layout = QHBoxLayout()
        self.subtitle_checkbox = QCheckBox("Download Subtitles")
        self.subtitle_language_input = QLineEdit()
        self.subtitle_language_input.setPlaceholderText("e.g., en, fr, auto (comma-separated)")
        self.subtitle_language_input.setEnabled(False) # Disabled by default
        self.subtitle_checkbox.toggled.connect(self.subtitle_language_input.setEnabled)
        subtitle_layout.addWidget(self.subtitle_checkbox)
        subtitle_layout.addWidget(QLabel("Language(s):"))
        subtitle_layout.addWidget(self.subtitle_language_input)
        download_layout.addLayout(subtitle_layout)

        download_layout.addSpacing(10)

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        download_layout.addWidget(self.progress_bar)

        self.status_label = QLabel("Ready to download")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        download_layout.addWidget(self.status_label)

        self.download_info_label = QLabel("")
        self.download_info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        download_layout.addWidget(self.download_info_label)

        save_path_frame = QFrame()
        save_path_frame.setStyleSheet("border: 1px solid #f0f0f0; background-color: #f0f0f0; border-radius: 5px; padding: 5px;")
        save_path_layout = QVBoxLayout(save_path_frame)

        save_path_heading = QLabel("Current Save Location:")
        save_path_heading.setStyleSheet("font-weight: bold;")

        self.save_path_label = QLabel("")
        self.save_path_label.setWordWrap(True)

        save_path_layout.addWidget(save_path_heading)
        save_path_layout.addWidget(self.save_path_label)

        download_layout.addWidget(save_path_frame)

        self.update_save_path_label() # Initial update
        self.format_combo.currentTextChanged.connect(self.update_save_path_label)
        self.preset_combo.currentTextChanged.connect(self.update_save_path_label) # Update on preset change

        buttons_layout = QHBoxLayout()

        self.download_btn = QPushButton("Download")
        self.download_btn.clicked.connect(self.start_download)
        buttons_layout.addWidget(self.download_btn)

        self.hide_btn = QPushButton("Hide to Background")
        self.hide_btn.clicked.connect(self.hide_to_background)
        buttons_layout.addWidget(self.hide_btn)

        self.settings_btn = QPushButton("Settings")
        self.settings_btn.clicked.connect(self.open_settings)
        buttons_layout.addWidget(self.settings_btn)

        download_layout.addLayout(buttons_layout)
        download_layout.addStretch()



        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

    def eventFilter(self, obj, event):
        if obj == self.title_label and event.type() == QEvent.Type.MouseButtonPress:
            if event.button() == Qt.MouseButton.LeftButton:
                self.title_click_count += 1
                if self.title_click_count >= 10:
                    self.trigger_easter_egg()
                    self.title_click_count = 0 # Reset count
            return True # Consume the event
        return super().eventFilter(obj, event)

    def trigger_easter_egg(self):
        # Play sound effect
        sound_file = os.path.join(os.path.dirname(__file__), "resources", "lol.wav")
        if os.path.exists(sound_file):
            self.player.setSource(QUrl.fromLocalFile(sound_file))
            self.player.play()
        else:
            print(f"Sound file not found: {sound_file}")


        original_text = self.title_label.text()
        original_font = self.title_label.font()
        original_palette = self.title_label.palette() # Store original palette

        # Sequence of text changes with timers
        QTimer.singleShot(200, lambda: self.title_label.setText("Miku"))
        QTimer.singleShot(400, lambda: self.title_label.setText("Miku Miku"))
        QTimer.singleShot(600, lambda: self.change_title_beam(original_font, original_palette)) # Change to BEEAAAAAAAM and shake
        QTimer.singleShot(3600, lambda: self.reset_title(original_text, original_font, original_palette)) # Revert after 3 seconds

    def change_title_beam(self, original_font, original_palette):
        self.title_label.setText("BEEAAAAAAAM")
        # Make text red and bold
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.red)
        self.title_label.setPalette(palette)

        font = self.title_label.font()
        font.setBold(True)
        font.setPointSize(20) # Make it bigger
        self.title_label.setFont(font)

        # Shake effect animation
        self.shake_animation = QPropertyAnimation(self.title_label, b"pos")
        self.shake_animation.setDuration(300)
        self.shake_animation.setLoopCount(2)
        initial_pos = self.title_label.pos()
        self.shake_animation.setKeyValueAt(0, initial_pos)
        self.shake_animation.setKeyValueAt(0.1, initial_pos + QPoint(5, 0))
        self.shake_animation.setKeyValueAt(0.3, initial_pos + QPoint(-5, 0))
        self.shake_animation.setKeyValueAt(0.5, initial_pos + QPoint(5, 0))
        self.shake_animation.setKeyValueAt(0.7, initial_pos + QPoint(-5, 0))
        self.shake_animation.setKeyValueAt(0.9, initial_pos + QPoint(5, 0))
        self.shake_animation.setKeyValueAt(1, initial_pos)
        self.shake_animation.start()


    def reset_title(self, original_text, original_font, original_palette):
        self.title_label.setText(original_text)
        self.title_label.setFont(original_font)
        self.title_label.setPalette(original_palette) # Restore original palette


    def get_screen_resolution(self):
        screen = QApplication.primaryScreen()
        return screen.geometry().height()

    def apply_preset(self, preset):
        if preset == "Custom":
            self.custom_options_widget.setVisible(True)
        else:
            self.custom_options_widget.setVisible(False)
            if preset == "Best Quality":
                screen_height = self.get_screen_resolution()
                if screen_height >= 2160:
                    self.resolution_combo.setCurrentText("2160")
                elif screen_height >= 1440:
                    self.resolution_combo.setCurrentText("1440")
                else:
                    self.resolution_combo.setCurrentText("1080")
                self.format_combo.setCurrentText("mp4")
                self.fps_checkbox.setChecked(True)
            elif preset == "Low Data (360p)":
                self.resolution_combo.setCurrentText("360")
                self.format_combo.setCurrentText("mp4")
                self.fps_checkbox.setChecked(False)
            elif preset == "Medium (480p)":
                self.resolution_combo.setCurrentText("480")
                self.format_combo.setCurrentText("mp4")
                self.fps_checkbox.setChecked(False)

        self.update_save_path_label() # Update save path display based on format

    def update_save_path_label(self):
        format_type = self.format_combo.currentText()
        save_path = self.audio_save_path if format_type == "mp3" else self.video_save_path
        os.makedirs(save_path, exist_ok=True) # Ensure directory exists
        self.save_path_label.setText(save_path)

    def open_donation_page(self):
        url = "https://ko-fi.com/MalikHw47"
        if platform.system() == 'Windows':
            os.startfile(url)
        elif platform.system() == 'Darwin':
            subprocess.call(['open', url])
        else:
            subprocess.call(['xdg-open', url])

    def update_fps_checkbox_state(self):
        resolution = int(self.resolution_combo.currentText())
        format_type = self.format_combo.currentText()
        self.fps_checkbox.setEnabled(resolution >= 720 and format_type != "mp3")
        if not self.fps_checkbox.isEnabled():
            self.fps_checkbox.setChecked(False)

    def open_settings(self):
        settings_dialog = SettingsDialog(self)
        settings_dialog.exec()
        self.update_save_path_label() # Update save path after settings change
        self.apply_theme(self.current_theme) # Apply theme after settings change

    def fetch_metadata(self):
        url = self.url_input.text().strip()
        if not url:
            QMessageBox.warning(self, "Error", "Please enter a YouTube URL")
            return

        self.status_label.setText("Fetching video information...")
        self.metadata_group.setVisible(False) # Hide previous metadata
        QApplication.processEvents() # Update UI

        self.metadata_thread = MetadataFetchThread(url)
        self.metadata_thread.metadata_fetched.connect(self.display_metadata)
        self.metadata_thread.error_occurred.connect(self.metadata_fetch_error)
        self.metadata_thread.start()

    def display_metadata(self, metadata):
        self.metadata_labels["Title"].setText(f"Title: {metadata.get('title', 'N/A')}")
        self.metadata_labels["Channel"].setText(f"Channel: {metadata.get('channel', 'N/A')}")
        self.metadata_labels["Duration"].setText(f"Duration: {self.format_duration(metadata.get('duration'))}")
        self.metadata_labels["Views"].setText(f"Views: {self.format_views(metadata.get('view_count'))}")
        self.metadata_group.setVisible(True)
        self.status_label.setText("Metadata fetched.")
        self.fetched_metadata = metadata # Store fetched metadata for download

    def metadata_fetch_error(self, error_msg):
        self.status_label.setText("Error fetching metadata.")
        self.metadata_group.setVisible(False)
        QMessageBox.critical(self, "Metadata Fetch Error", error_msg)

    def start_download(self):
        url = self.url_input.text().strip()
        if not url:
            QMessageBox.warning(self, "Error", "Please enter a YouTube URL")
            return

        resolution = self.resolution_combo.currentText()
        format_type = self.format_combo.currentText()
        prefer_60fps = self.fps_checkbox.isChecked()

        save_path = self.audio_save_path if format_type == "mp3" else self.video_save_path

        try:
            os.makedirs(save_path, exist_ok=True)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not create directory: {str(e)}")
            return

        self.update_save_path_label()

        self.download_btn.setEnabled(False)
        self.status_label.setText("Getting video information...")
        self.progress_bar.setValue(0)
        self.download_info_label.setText("Initializing...")

        ydl_format_options = {}
        ydl_extra_opts = {}

        if format_type == "mp3":
            ydl_format_options = {
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                 'extract_audio': True, # Ensure audio extraction is enabled
                 'audio_format': 'mp3',
            }
        elif format_type == "mp4":
            format_string = f'bestvideo[height<={resolution}]+bestaudio/best[height<={resolution}]'
            if prefer_60fps and int(resolution) >= 720:
                format_string = f'bestvideo[height<={resolution}][fps>=60]+bestaudio/best[height<={resolution}][fps<=60]' # Limit audio fps to prevent issues
            ydl_format_options = {
                'format': format_string,
                'merge_output_format': 'mp4',
            }
        elif format_type == "muted_mp4":
            format_string = f'bestvideo[height<={resolution}]'
            if prefer_60fps and int(resolution) >= 720:
                format_string = f'bestvideo[height<={resolution}][fps>=60]'
            ydl_format_options = {
                'format': format_string,
                'merge_output_format': 'mp4',
                'postprocessors': [{
                    'key': 'FFmpegVideoRemuxer',
                    'preferedformat': 'mp4',
                }],
                 'keepvideo': False, # Remove the original video file after remuxing
            }

        # Add subtitle options
        if self.subtitle_checkbox.isChecked():
            print(f"Attempting to download subtitles in languages: {self.subtitle_language_input.text()}")
            ydl_extra_opts['writesubtitles'] = True
            ydl_extra_opts['subtitlesformat'] = 'srt'  # Specify SRT format
    
            # Better language handling
            langs = [lang.strip() for lang in self.subtitle_language_input.text().split(',') if lang.strip()]
    
            if not langs:
                langs = ['en']  # Default to English if no language specified
    
            # Handle automatic subtitles
        if 'auto' in langs:
            ydl_extra_opts['writeautomaticsub'] = True
            langs.remove('auto')
        
        ydl_extra_opts['subtitleslangs'] = langs
    
        # Add subtitle conversion post-processor
        if 'postprocessors' not in ydl_extra_opts:
            ydl_extra_opts['postprocessors'] = []
    
        ydl_extra_opts['postprocessors'].append({
            'key': 'FFmpegSubtitlesConvertor',
            'format': 'srt',
        })

        self.download_thread = DownloadThread(url, ydl_format_options, save_path, ydl_extra_opts)
        self.download_thread.progress_update.connect(self.update_progress)
        self.download_thread.download_info.connect(self.update_download_info)
        self.download_thread.download_complete.connect(self.download_finished)
        self.download_thread.download_error.connect(self.download_error)
        self.download_thread.metadata_download_finished.connect(self.apply_mp3_metadata) # Connect new signal
        self.download_thread.start()

    def update_progress(self, value):
        if value == -1:
            self.progress_bar.setRange(0, 0)
            self.status_label.setText("Downloading...")
        else:
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(value)
            if value < 10:
                 self.status_label.setText("Processing video...")
            elif value < 99:
                self.status_label.setText("Downloading...")
            else:
                self.status_label.setText("Finishing download...")


    def update_download_info(self, info):
        self.download_info_label.setText(info)
        self.tray_icon.setToolTip(f"HwYtVidGrabber - {info}")

        if not self.isVisible() and ("%" in info or "downloaded" in info) and "ETA" in info:
             # Show notification for significant progress updates (with ETA)
             self.tray_icon.showMessage(
                 "Download Progress",
                 info,
                 QSystemTrayIcon.MessageIcon.Information,
                 1000
             )


    def apply_mp3_metadata(self, metadata, file_path):
        if file_path.endswith('.mp3'):
            try:
                audiofile = eyed3.load(file_path)
                if audiofile.tag is None:
                    audiofile.initTag()

                audiofile.tag.title = metadata.get('title', 'N/A')
                audiofile.tag.artist = metadata.get('channel', 'N/A')
                audiofile.tag.album = "YouTube"
                audiofile.tag.save()
                print(f"Applied metadata to {os.path.basename(file_path)}")
            except Exception as e:
                print(f"Error applying MP3 metadata to {os.path.basename(file_path)}: {str(e)}")


    def download_finished(self, file_path):
        # Convert to H.264 if it's a video file
        if file_path.endswith('.mp4'):
            file_path = self.convert_to_h264(file_path)
        
        self.progress_bar.setValue(100)
        self.status_label.setText(f"Download complete: {os.path.basename(file_path)}")
        self.download_btn.setEnabled(True)
        self.download_info_label.setText("Download complete")
        self.metadata_group.setVisible(False) # Hide metadata after download
    
        self.tray_icon.showMessage(
            "Download Complete",
            f"File saved: {os.path.basename(file_path)}",
            QSystemTrayIcon.MessageIcon.Information,
            3000
        )
    
        reply = QMessageBox.question(self, "Download Complete",
                                    f"File saved to: {file_path}\n\nDo you want to open the containing folder?",
                                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
    
        if reply == QMessageBox.StandardButton.Yes:
            if platform.system() == 'Windows':
                os.startfile(os.path.dirname(file_path))
            elif platform.system() == 'Darwin':
                subprocess.call(['open', os.path.dirname(file_path)])
            else:
                subprocess.call(['xdg-open', os.path.dirname(file_path)])
        
        # Execute post-download action
        self.execute_post_download_action()

    def download_error(self, error_msg):
        self.progress_bar.setValue(0)
        self.status_label.setText("Error occurred")
        self.download_btn.setEnabled(True)
        self.download_info_label.setText("")
        self.metadata_group.setVisible(False)
        QMessageBox.critical(self, "Download Error", error_msg)

    def format_duration(self, seconds):
        if seconds is None:
            return "N/A"
        m, s = divmod(seconds, 60)
        h, m = divmod(m, 60)
        return f"{int(h):02d}:{int(m):02d}:{int(s):02d}"

    def format_views(self, views):
        if views is None:
            return "N/A"
        if views < 1000:
            return str(views)
        elif views < 1000000:
            return f"{views/1000:.1f}K"
        else:
            return f"{views/1000000:.1f}M"

    def open_search_dialog(self):
        search_dialog = SearchDialog(self)
        search_dialog.exec()

    def execute_post_download_action(self):
        action = self.settings.value("post_download_action", "Nothing")
        if action == "Nothing":
            pass
        elif action == "Sleep PC":
            if platform.system() == 'Windows':
                os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")
            elif platform.system() == 'Darwin':  # macOS
                os.system("pmset sleepnow")
            else:  # Linux
                os.system("systemctl suspend")
        elif action == "Terminate App":
            self.close_application()
        elif action == "Restart PC":
            if platform.system() == 'Windows':
                os.system("shutdown /r /t 1")
            elif platform.system() == 'Darwin':  # macOS
                os.system("shutdown -r now")
            else:  # Linux
                os.system("shutdown -r now")
        elif action == "Shutdown PC":
            if platform.system() == 'Windows':
                os.system("shutdown /s /t 1")
            elif platform.system() == 'Darwin':  # macOS
                os.system("shutdown -h now")
            else:  # Linux
                os.system("shutdown -h now")

    def convert_to_h264(self, file_path):
        if not file_path.endswith('.mp4'):
            return file_path
            
        output_path = file_path + ".h264.mp4"
        self.status_label.setText("Converting to H.264...")
        self.download_info_label.setText("Converting video format...")
        
        try:
            cmd = [
                'ffmpeg',
                '-i', file_path,
                '-c:v', 'libx264',
                '-preset', 'medium',
                '-crf', '23',
                '-c:a', 'aac',
                '-b:a', '128k',
                output_path
            ]
            subprocess.run(cmd, check=True)
            
            # Replace original file with converted file
            os.remove(file_path)
            os.rename(output_path, file_path)
            return file_path
        except Exception as e:
            self.download_info_label.setText(f"Conversion error: {str(e)}")
            return file_path


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = HwYtVidGrabber()
    window.show()
    sys.exit(app.exec())
