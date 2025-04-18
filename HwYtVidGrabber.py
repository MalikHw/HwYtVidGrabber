import sys
import os
import re
import json
import yt_dlp
import time
from PyQt6.QtWidgets import (QApplication, QMainWindow, QLabel, QLineEdit, 
                            QPushButton, QComboBox, QVBoxLayout, QHBoxLayout, 
                            QWidget, QProgressBar, QMessageBox, QFileDialog,
                            QDialog, QFormLayout, QCheckBox, QSystemTrayIcon, QMenu)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QIcon, QFont, QAction
import subprocess

def check_ffmpeg():
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
        return True
    except FileNotFoundError:
        return False

if not check_ffmpeg():
    # Display error message to the user with installation instructions
    print("Error: FFmpeg is not installed. Please install it...")
    # ... (Add instructions for common Linux distributions)
    sys.exit(1) # Exit the application

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
        
    def initUI(self):
        self.setWindowTitle("Settings")
        self.setGeometry(200, 200, 400, 150)
        
        layout = QFormLayout()
        
        # Video save path
        self.video_path_input = QLineEdit(self.parent.video_save_path)
        browse_video_btn = QPushButton("Browse...")
        browse_video_btn.clicked.connect(self.browse_video_path)
        
        video_path_layout = QHBoxLayout()
        video_path_layout.addWidget(self.video_path_input)
        video_path_layout.addWidget(browse_video_btn)
        
        # Audio save path
        self.audio_path_input = QLineEdit(self.parent.audio_save_path)
        browse_audio_btn = QPushButton("Browse...")
        browse_audio_btn.clicked.connect(self.browse_audio_path)
        
        audio_path_layout = QHBoxLayout()
        audio_path_layout.addWidget(self.audio_path_input)
        audio_path_layout.addWidget(browse_audio_btn)
        
        layout.addRow("Video Save Path:", video_path_layout)
        layout.addRow("Audio Save Path:", audio_path_layout)
        
        # Save button
        save_btn = QPushButton("Save Settings")
        save_btn.clicked.connect(self.save_settings)
        layout.addRow("", save_btn)
        
        self.setLayout(layout)
    
    def browse_video_path(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Directory for Videos")
        if folder:
            self.video_path_input.setText(folder)
    
    def browse_audio_path(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Directory for Audio")
        if folder:
            self.audio_path_input.setText(folder)
    
    def save_settings(self):
        self.parent.video_save_path = self.video_path_input.text()
        self.parent.audio_save_path = self.audio_path_input.text()
        
        # Save settings to file
        settings = {
            "video_save_path": self.parent.video_save_path,
            "audio_save_path": self.parent.audio_save_path
        }
        
        try:
            os.makedirs(os.path.dirname(self.parent.settings_file), exist_ok=True)
            with open(self.parent.settings_file, 'w') as f:
                json.dump(settings, f)
            QMessageBox.information(self, "Settings Saved", "Settings have been saved successfully.")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not save settings: {str(e)}")
        
        self.accept()


class DownloadProgressHook:
    def __init__(self, progress_callback, info_callback):
        self.progress_callback = progress_callback
        self.info_callback = info_callback
        self.start_time = time.time()
        self.last_downloaded_bytes = 0
        self.last_update_time = self.start_time
        
    def __call__(self, d):
        if d['status'] == 'downloading':
            # Calculate elapsed time since last update
            current_time = time.time()
            elapsed = current_time - self.last_update_time
            
            # Update at most once per second to avoid GUI overload
            if elapsed < 1.0 and d['status'] != 'finished':
                return
                
            self.last_update_time = current_time
            
            downloaded = d.get('downloaded_bytes', 0)
            total = d.get('total_bytes', 0)
            speed = d.get('speed', 0)
            
            # Calculate progress and speed
            if total > 0:
                percentage = int((downloaded / total) * 100)
                self.progress_callback.emit(percentage)
                
                # Format file sizes nicely
                downloaded_str = self.format_size(downloaded)
                total_str = self.format_size(total)
                
                # Format speed nicely
                if speed:
                    speed_str = self.format_size(speed) + "/s"
                else:
                    # Calculate speed manually if not provided by yt-dlp
                    elapsed_total = current_time - self.start_time
                    if elapsed_total > 0:
                        speed = downloaded / elapsed_total
                        speed_str = self.format_size(speed) + "/s"
                    else:
                        speed_str = "N/A"
                
                # Send download info to main thread
                self.info_callback.emit(f"{downloaded_str} of {total_str} ({speed_str})")
            else:
                # If we don't know total size, use a pulsing effect
                self.progress_callback.emit(-1)
                
                # Still show downloaded amount and speed
                downloaded_str = self.format_size(downloaded)
                
                if speed:
                    speed_str = self.format_size(speed) + "/s"
                else:
                    # Calculate speed manually
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
    
    def format_size(self, bytes):
        """Format bytes to human-readable size"""
        if bytes < 1024:
            return f"{bytes} B"
        elif bytes < 1024 * 1024:
            return f"{bytes/1024:.1f} KB"
        elif bytes < 1024 * 1024 * 1024:
            return f"{bytes/(1024*1024):.1f} MB"
        else:
            return f"{bytes/(1024*1024*1024):.2f} GB"


class DownloadThread(QThread):
    progress_update = pyqtSignal(int)
    download_info = pyqtSignal(str)
    download_complete = pyqtSignal(str)
    download_error = pyqtSignal(str)
    
    def __init__(self, url, resolution, format_type, save_path, prefer_60fps=False):
        super().__init__()
        self.url = url
        self.resolution = resolution
        self.format_type = format_type
        self.save_path = save_path
        self.prefer_60fps = prefer_60fps
        
    def run(self):
        try:
            self.progress_update.emit(5)
            self.download_info.emit("Initializing download...")
            
            # Make sure the save directory exists
            os.makedirs(self.save_path, exist_ok=True)
            
            # Configure yt-dlp options based on format type and resolution
            ydl_opts = {
                'progress_hooks': [DownloadProgressHook(self.progress_update, self.download_info)],
                'quiet': True,
                'no_warnings': True
            }
            
            # Set filename template
            output_template = '%(uploader)s - %(title)s'
            
            # Configure format based on user selection
            if self.format_type == "mp3":
                # Audio only (MP3)
                ydl_opts.update({
                    'format': 'bestaudio/best',
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': '192',
                    }],
                    'outtmpl': os.path.join(self.save_path, output_template + '.%(ext)s')
                })
            elif self.format_type == "mp4":
                # Video with audio (MP4)
                format_string = f'bestvideo[height<={self.resolution}]+bestaudio/best[height<={self.resolution}]'
                if self.prefer_60fps and int(self.resolution) >= 720:
                    format_string = f'bestvideo[height<={self.resolution}][fps>=60]+bestaudio/best[height<={self.resolution}]'
                
                ydl_opts.update({
                    'format': format_string,
                    'merge_output_format': 'mp4',
                    'outtmpl': os.path.join(self.save_path, output_template + '.%(ext)s')
                })
            elif self.format_type == "muted_mp4":
                # Video without audio (muted MP4)
                format_string = f'bestvideo[height<={self.resolution}]'
                if self.prefer_60fps and int(self.resolution) >= 720:
                    format_string = f'bestvideo[height<={self.resolution}][fps>=60]'
                
                ydl_opts.update({
                    'format': format_string,
                    'merge_output_format': 'mp4',
                    'outtmpl': os.path.join(self.save_path, output_template + ' (muted).%(ext)s'),
                    'postprocessors': [{
                        'key': 'FFmpegVideoRemuxer',
                        'preferedformat': 'mp4',
                    }]
                })
                
            self.progress_update.emit(10)
            self.download_info.emit("Fetching video information...")
            
            # Print the actual save path for debugging
            self.download_info.emit(f"Saving to: {self.save_path}")
            
            # Create a custom file name handler to get the output path
            output_file = None
            
            def custom_path_hook(info_dict, ydl):
                nonlocal output_file
                outtmpl = ydl.outtmpl_dict['default'] 
                output_file = ydl.prepare_filename(info_dict)
                return outtmpl % info_dict
            
            ydl_opts['outtmpl_dict'] = {'default': ydl_opts.pop('outtmpl')}
            ydl_opts['prepare_filename'] = custom_path_hook
            
            # Download the video
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([self.url])
            
            if output_file:
                self.download_complete.emit(output_file)
            else:
                self.download_complete.emit("Download complete")
            
        except Exception as e:
            self.download_error.emit(f"Error: {str(e)}")


class HwYtVidGrabber(QMainWindow):
    def __init__(self):
        super().__init__()
        # Set up settings file path
        self.settings_file = os.path.join(os.path.expanduser("~"), ".hwytvidgrabber", "settings.json")
        
        # Get default paths based on OS
        default_video_path, default_audio_path = get_default_paths()
        
        # Set initial values
        self.video_save_path = default_video_path
        self.audio_save_path = default_audio_path
        
        # Try to load saved settings
        self.load_settings()
        
        # Ensure directories exist
        os.makedirs(self.video_save_path, exist_ok=True)
        os.makedirs(self.audio_save_path, exist_ok=True)
        
        # Initialize system tray
        self.setup_tray()
        
        # Initialize UI
        self.initUI()
        
    def load_settings(self):
        # Try to load saved settings
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r') as f:
                    settings = json.load(f)
                    
                    # Only use paths from settings if they exist or can be created
                    video_path = settings.get("video_save_path")
                    audio_path = settings.get("audio_save_path")
                    
                    if video_path:
                        try:
                            os.makedirs(video_path, exist_ok=True)
                            self.video_save_path = video_path
                        except:
                            pass  # Use default if can't create
                            
                    if audio_path:
                        try:
                            os.makedirs(audio_path, exist_ok=True)
                            self.audio_save_path = audio_path
                        except:
                            pass  # Use default if can't create
        except Exception as e:
            print(f"Error loading settings: {e}")
            # If settings can't be loaded, use defaults
            pass
    
    def setup_tray(self):
        # Create system tray icon
        self.tray_icon = QSystemTrayIcon(self)
        
        # Try to load an icon
        try:
            # Try to use a system icon first
            app_icon = QIcon.fromTheme("video-display")
            if app_icon.isNull():
                # Fall back to a generic icon
                app_icon = QIcon.fromTheme("applications-multimedia")
                if app_icon.isNull():
                    # As a last resort, create a simple icon from the system
                    app_icon = self.style().standardIcon(QApplication.style().StandardPixmap.SP_MediaPlay)
        except:
            # If all else fails, use a system standard icon
            app_icon = self.style().standardIcon(QApplication.style().StandardPixmap.SP_MediaPlay)
        
        self.tray_icon.setIcon(app_icon)
        self.setWindowIcon(app_icon)
        
        # Create tray menu
        tray_menu = QMenu()
        
        # Add menu actions
        show_action = QAction("Show", self)
        show_action.triggered.connect(self.show)
        
        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(self.close_application)
        
        tray_menu.addAction(show_action)
        tray_menu.addAction(quit_action)
        
        # Set the menu for tray icon
        self.tray_icon.setContextMenu(tray_menu)
        
        # Connect the tray icon activated signal to its slot
        self.tray_icon.activated.connect(self.tray_icon_activated)
        
        # Make the tray icon visible
        self.tray_icon.show()
    
    def tray_icon_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            # Show main window on double click
            self.show()
    
    def hide_to_background(self):
        # Hide the main window but keep running in background
        self.hide()
        self.tray_icon.showMessage(
            "HwYtVidGrabber",
            "Application is still running in the background",
            QSystemTrayIcon.MessageIcon.Information,
            2000  # Show for 2 seconds
        )
    
    def close_application(self):
        # Properly close the application
        self.tray_icon.hide()
        QApplication.quit()
    
    def closeEvent(self, event):
        # Override the close event to minimize to tray instead of quitting
        if self.tray_icon.isVisible():
            QMessageBox.information(
                self,
                "HwYtVidGrabber",
                "The application will keep running in the system tray. "
                "To terminate the program, choose 'Quit' in the context menu "
                "of the system tray entry."
            )
            self.hide()
            event.ignore()
        else:
            event.accept()
        
    def initUI(self):
        self.setWindowTitle("HwYtVidGrabber v1.1 by MalikHw47")
        self.setGeometry(100, 100, 600, 450)  # Made window taller for new elements
        
        # Main widget and layout
        main_widget = QWidget()
        main_layout = QVBoxLayout()
        
        # App title
        title_label = QLabel("HwYtVidGrabber v1.1")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title_label)
        
        # Author label
        author_label = QLabel("By: MalikHw47")
        author_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(author_label)
        
        # Add donation button
        donate_btn = QPushButton("Support Development ☕")
        donate_btn.setStyleSheet("background-color: #ff5f5f; color: white; font-weight: bold;")
        donate_btn.clicked.connect(self.open_donation_page)
        main_layout.addWidget(donate_btn)
        
        # Add some spacing
        main_layout.addSpacing(20)
        
        # URL Input
        url_layout = QHBoxLayout()
        url_label = QLabel("YouTube URL:")
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Paste YouTube URL here...")
        url_layout.addWidget(url_label)
        url_layout.addWidget(self.url_input)
        main_layout.addLayout(url_layout)
        
        # Resolution selection
        resolution_layout = QHBoxLayout()
        resolution_label = QLabel("Resolution:")
        self.resolution_combo = QComboBox()
        self.resolution_combo.addItems(["144", "240", "360", "480", "720", "1080", "1440", "2160"])
        self.resolution_combo.setCurrentText("720")
        resolution_layout.addWidget(resolution_label)
        resolution_layout.addWidget(self.resolution_combo)
        main_layout.addLayout(resolution_layout)
        
        # Format type selection
        format_layout = QHBoxLayout()
        format_label = QLabel("Format:")
        self.format_combo = QComboBox()
        self.format_combo.addItems(["mp4", "mp3", "muted_mp4"])
        format_layout.addWidget(format_label)
        format_layout.addWidget(self.format_combo)
        main_layout.addLayout(format_layout)
        
        # 60fps option for HD resolutions
        fps_layout = QHBoxLayout()
        self.fps_checkbox = QCheckBox("Prefer 60fps (for 720p and above)")
        self.fps_checkbox.setChecked(True)
        # Only enable when resolution is 720p or higher and it's a video format
        self.update_fps_checkbox_state()
        self.resolution_combo.currentTextChanged.connect(self.update_fps_checkbox_state)
        self.format_combo.currentTextChanged.connect(self.update_fps_checkbox_state)
        fps_layout.addWidget(self.fps_checkbox)
        main_layout.addLayout(fps_layout)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        main_layout.addWidget(self.progress_bar)
        
        # Status label
        self.status_label = QLabel("Ready to download")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.status_label)
        
        # Download info (speed and size)
        self.download_info_label = QLabel("")
        self.download_info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.download_info_label)
        
        # Save path info - make it very visible
        save_path_frame = QWidget()
        save_path_frame.setStyleSheet("background-color: #f0f0f0; border-radius: 5px; padding: 5px;")
        save_path_layout = QVBoxLayout(save_path_frame)
        
        save_path_heading = QLabel("Current Save Location:")
        save_path_heading.setStyleSheet("font-weight: bold;")
        
        self.save_path_label = QLabel("")
        self.save_path_label.setWordWrap(True)
        
        save_path_layout.addWidget(save_path_heading)
        save_path_layout.addWidget(self.save_path_label)
        
        main_layout.addWidget(save_path_frame)
        
        # Update the save path label with the current path
        self.update_save_path_label()
        
        # Buttons layout
        buttons_layout = QHBoxLayout()
        
        # Download button
        self.download_btn = QPushButton("Download")
        self.download_btn.clicked.connect(self.start_download)
        buttons_layout.addWidget(self.download_btn)
        
        # Hide to background button
        self.hide_btn = QPushButton("Hide to Background")
        self.hide_btn.clicked.connect(self.hide_to_background)
        buttons_layout.addWidget(self.hide_btn)
        
        # Settings button
        self.settings_btn = QPushButton("Settings")
        self.settings_btn.clicked.connect(self.open_settings)
        buttons_layout.addWidget(self.settings_btn)
        
        main_layout.addLayout(buttons_layout)
        
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)
        
        # Connect signal to update save path when format changes
        self.format_combo.currentTextChanged.connect(self.update_save_path_label)
    
    def update_save_path_label(self):
        # Update the label showing the save path based on current format selection
        if hasattr(self, 'format_combo'):
            format_type = self.format_combo.currentText()
            save_path = self.audio_save_path if format_type == "mp3" else self.video_save_path
            
            # Check that the path exists and create it if it doesn't
            os.makedirs(save_path, exist_ok=True)
            
            # Display path more clearly
            self.save_path_label.setText(save_path)
    
    def open_donation_page(self):
        # Open the Ko-fi donation page
        url = "https://ko-fi.com/MalikHw47"
        
        # Open URL in the default web browser
        if sys.platform == 'win32':
            os.startfile(url)
        elif sys.platform == 'darwin':  # macOS
            subprocess.call(['open', url])
        else:  # Linux
            subprocess.call(['xdg-open', url])
    
    def update_fps_checkbox_state(self):
        resolution = int(self.resolution_combo.currentText())
        format_type = self.format_combo.currentText()
        
        # Enable 60fps checkbox only for HD video formats
        self.fps_checkbox.setEnabled(resolution >= 720 and format_type != "mp3")
        
        if not self.fps_checkbox.isEnabled():
            self.fps_checkbox.setChecked(False)
    
    def open_settings(self):
        settings_dialog = SettingsDialog(self)
        settings_dialog.exec()
        
        # Make sure directories exist
        os.makedirs(self.video_save_path, exist_ok=True)
        os.makedirs(self.audio_save_path, exist_ok=True)
        
        # Update the save path label after settings dialog is closed
        self.update_save_path_label()
    
    def start_download(self):
        url = self.url_input.text().strip()
        if not url:
            QMessageBox.warning(self, "Error", "Please enter a YouTube URL")
            return
            
        resolution = self.resolution_combo.currentText()
        format_type = self.format_combo.currentText()
        prefer_60fps = self.fps_checkbox.isChecked()
        
        # Determine save path based on format
        save_path = self.audio_save_path if format_type == "mp3" else self.video_save_path
        
        # Check if directory exists and create it if not
        try:
            os.makedirs(save_path, exist_ok=True)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not create directory: {str(e)}")
            return
        
        # Update the save path label
        self.update_save_path_label()
        
        # Disable download button while downloading
        self.download_btn.setEnabled(False)
        self.status_label.setText("Getting video information...")
        self.progress_bar.setValue(0)
        self.download_info_label.setText("Initializing...")
        
        # Create and start download thread
        self.download_thread = DownloadThread(url, resolution, format_type, save_path, prefer_60fps)
        self.download_thread.progress_update.connect(self.update_progress)
        self.download_thread.download_info.connect(self.update_download_info)
        self.download_thread.download_complete.connect(self.download_finished)
        self.download_thread.download_error.connect(self.download_error)
        self.download_thread.start()
    
    def update_progress(self, value):
        if value == -1:
            # Indeterminate progress
            self.progress_bar.setRange(0, 0)  # Makes the progress bar "busy"
            self.status_label.setText("Downloading...")
        else:
            self.progress_bar.setRange(0, 100)  # Restore normal range
            self.progress_bar.setValue(value)
            if value < 50:
                self.status_label.setText("Processing video...")
            else:
                self.status_label.setText("Downloading...")
    
    def update_download_info(self, info):
        # Update the download information label
        self.download_info_label.setText(info)
        
        # Also update the tray tooltip if minimized
        self.tray_icon.setToolTip(f"HwYtVidGrabber - {info}")
        
        # If window is hidden, also show a notification for significant progress
        if not self.isVisible() and "%" in info and "%" not in self.tray_icon.toolTip():
            self.tray_icon.showMessage(
                "Download Progress", 
                info,
                QSystemTrayIcon.MessageIcon.Information,
                1000  # Show for 1 second
            )
    
    def download_finished(self, file_path):
        self.progress_bar.setValue(100)
        self.status_label.setText(f"Download complete: {os.path.basename(file_path)}")
        self.download_btn.setEnabled(True)
        self.download_info_label.setText("Download complete")
        
        # Show notification in system tray
        self.tray_icon.showMessage(
            "Download Complete",
            f"File saved: {os.path.basename(file_path)}",
            QSystemTrayIcon.MessageIcon.Information,
            3000  # Show for 3 seconds
        )
        
        # Ask user if they want to open the file
        reply = QMessageBox.question(self, "Download Complete", 
                                     f"File saved to: {file_path}\n\nDo you want to open the containing folder?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            # Open file explorer with the file selected
            if sys.platform == 'win32':
                os.startfile(os.path.dirname(file_path))
            elif sys.platform == 'darwin':  # macOS
                subprocess.call(['open', os.path.dirname(file_path)])
            else:  # Linux
                subprocess.call(['xdg-open', os.path.dirname(file_path)])
    
    def download_error(self, error_msg):
        self.progress_bar.setValue(0)
        self.status_label.setText("Error occurred")
        self.download_btn.setEnabled(True)
        self.download_info_label.setText("")
        QMessageBox.critical(self, "Download Error", error_msg)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = HwYtVidGrabber()
    window.show()
    sys.exit(app.exec())
