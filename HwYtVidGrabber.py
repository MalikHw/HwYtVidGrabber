import sys
import os
import webbrowser
import json
import subprocess
import platform
import re
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
from yt_dlp import YoutubeDL

class DownloadWorker(QThread):
    progress_signal = pyqtSignal(dict)
    finished_signal = pyqtSignal()
    error_signal = pyqtSignal(str)
    info_signal = pyqtSignal(dict)
    available_formats_signal = pyqtSignal(dict)
    
    def __init__(self, url, save_path, format_option, resolution, fps_60=False):
        super().__init__()
        self.url = url
        self.save_path = save_path
        self.format_option = format_option
        self.resolution = resolution
        self.fps_60 = fps_60
        self.is_paused = False
        self.is_cancelled = False
        self.is_rickroll = "xvFZjo5PgG0" in url
        
    def get_proper_download_path(self):
        """Get the proper download path based on OS and format"""
        if platform.system() == "Windows":
            # Windows path
            base_path = os.path.join(os.path.expanduser("~"), "Downloads", "HwYtVidGrabber")
        else:
            # Linux/Unix path
            base_path = os.path.join(os.path.expanduser("~"), "Downloads", "HwYtVidGrabber")
        
        # Add subfolder based on format
        if self.format_option == "mp3":
            subfolder = "Audios"
        else:
            subfolder = "Videos"
            
        final_path = os.path.join(base_path, subfolder)
        
        # Create directory if it doesn't exist
        try:
            os.makedirs(final_path, exist_ok=True)
        except Exception as e:
            print(f"Error creating directory {final_path}: {e}")
            # Fallback to base path if subfolder creation fails
            os.makedirs(base_path, exist_ok=True)
            final_path = base_path
            
        return final_path
        
    def run(self):
        try:
            # Get the proper download path
            actual_save_path = self.get_proper_download_path()
            
            # First fetch video info
            with YoutubeDL({'quiet': True}) as ydl:
                info = ydl.extract_info(self.url, download=False)
                
                if self.is_rickroll:
                    video_info = {
                        'title': '????',
                        'uploader': '????'
                    }
                else:
                    video_info = {
                        'title': info.get('title', 'Unknown'),
                        'uploader': info.get('uploader', 'Unknown')
                    }
                
                self.info_signal.emit(video_info)
                
                # Get available formats
                formats = info.get('formats', [])
                max_height = 0
                for f in formats:
                    if f.get('height') and f.get('height') > max_height:
                        max_height = f.get('height')
                
                # Map height to resolution name
                res_name = "144p"
                if max_height >= 2160:
                    res_name = "4K"
                elif max_height >= 1440:
                    res_name = "2K"  
                elif max_height >= 1080:
                    res_name = "FHD"
                elif max_height >= 720:
                    res_name = "HD"
                elif max_height >= 480:
                    res_name = "480p"
                elif max_height >= 360:
                    res_name = "360p"
                
                self.available_formats_signal.emit({
                    'max_resolution': res_name,
                    'max_height': max_height
                })
            
            # Make format string based on options
            if self.format_option == "mp3":
                format_str = "bestaudio/best"
                postprocessors = [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }]
            else:
                res_map = {
                    "144p": "best[height<=144]",
                    "360p": "best[height<=360]",
                    "480p": "best[height<=480]",
                    "HD": "best[height<=720]",
                    "FHD": "best[height<=1080]",
                    "2K": "best[height<=1440]",
                    "4K": "best[height<=2160]",
                    "Max": "best"
                }
                
                base_format = res_map.get(self.resolution, "best")
                if self.fps_60:
                    format_str = f"{base_format}[fps>=60]/best[fps>=60]/best"
                else:
                    format_str = base_format
                
                if self.format_option == "mp4":
                    format_str = f"bestvideo[ext=mp4]{res_map.get(self.resolution, '')[4:]}+bestaudio/bestvideo+bestaudio/best"
                    postprocessors = [{
                        'key': 'FFmpegVideoConvertor',
                        'preferedformat': 'mp4',
                    }]
                else:  # muted mp4
                    format_str = f"bestvideo[ext=mp4]{res_map.get(self.resolution, '')[4:]}/best"
                    postprocessors = [{
                        'key': 'FFmpegVideoConvertor',
                        'preferedformat': 'mp4',
                    }]
            
            def clean_ansi(text):
                if not text:
                    return text
                ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
                return ansi_escape.sub('', text)
            
            def my_hook(d):
                if self.is_cancelled:
                    raise Exception("Download cancelled")
                
                if d['status'] == 'downloading':
                    p_str = clean_ansi(d.get('_percent_str', '0%')).strip()
                    try:
                        p = float(p_str.replace('%', '')) if '%' in p_str else 0
                    except ValueError:
                        p = 0
                    
                    s = clean_ansi(d.get('_speed_str', '0KiB/s')).strip()
                    ts = clean_ansi(d.get('_total_bytes_str', 'N/A')).strip()
                    eta = clean_ansi(d.get('_eta_str', 'N/A')).strip()
                    
                    self.progress_signal.emit({
                        'percent': p, 
                        'speed': s,
                        'total_size': ts,
                        'eta': eta
                    })
                    
                    while self.is_paused:
                        QThread.sleep(1)
                        if self.is_cancelled:
                            raise Exception("Download cancelled")
            
            if self.is_rickroll:
                output_template = os.path.join(actual_save_path, '????.%(ext)s')
            else:
                output_template = os.path.join(actual_save_path, '%(uploader)s - %(title)s.%(ext)s')
            
            ydl_opts = {
                'format': format_str,
                'postprocessors': postprocessors,
                'outtmpl': output_template,
                'progress_hooks': [my_hook],
                'quiet': False,
                'no_warnings': False
            }
            
            with YoutubeDL(ydl_opts) as ydl:
                ydl.download([self.url])
            
            self.finished_signal.emit()
            
        except Exception as e:
            self.error_signal.emit(str(e))
    
    def pause(self):
        self.is_paused = True
    
    def resume(self):
        self.is_paused = False
    
    def cancel(self):
        self.is_cancelled = True


class HwYtVidGrabber(QMainWindow):
    def __init__(self):
        super().__init__()
        self.title_click_count = 0
        self.download_worker = None
        self.initUI()
        self.loadSettings()
        self.checkFFmpeg()
    
    def initUI(self):
        self.setWindowTitle("HwYtVidGrabber v1.4.1")
        self.setFixedSize(600, 400)
        self.setAcceptDrops(True)
        
        # Set app icon with Linux path checking
        icon_path = None
        if platform.system() == "Windows":
            icon_path = "icon.ico"
        else:
            possible_icon_paths = [
                "/usr/share/pixmaps/HwYtVidGrabber.png",
                os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon.png")
            ]
            
            for path in possible_icon_paths:
                if os.path.exists(path):
                    icon_path = path
                    break
        
        if icon_path:
            self.setWindowIcon(QIcon(icon_path))
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Create title label with clickable property
        title_label = QLabel("HwYtVidGrabber v1.4.1")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("font-size: 20px; font-weight: bold;")
        title_label.mousePressEvent = self.titleClicked
        main_layout.addWidget(title_label)
        
        # URL input
        url_layout = QHBoxLayout()
        url_label = QLabel("YouTube URL:")
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Enter YouTube URL here...")
        self.url_input.textChanged.connect(self.urlChanged)
        url_layout.addWidget(url_label)
        url_layout.addWidget(self.url_input)
        main_layout.addLayout(url_layout)
        
        # Video info display
        info_layout = QHBoxLayout()
        self.title_label = QLabel("Title: ")
        self.author_label = QLabel("Channel: ")
        info_layout.addWidget(self.title_label)
        info_layout.addWidget(self.author_label)
        main_layout.addLayout(info_layout)
        
        # Format options
        format_layout = QHBoxLayout()
        format_label = QLabel("Format:")
        self.format_combo = QComboBox()
        self.format_combo.addItems(["mp4", "mp3", "muted mp4"])
        format_layout.addWidget(format_label)
        format_layout.addWidget(self.format_combo)
        main_layout.addLayout(format_layout)
        
        # Resolution options
        res_layout = QHBoxLayout()
        res_label = QLabel("Resolution:")
        self.res_combo = QComboBox()
        self.res_combo.addItems(["144p", "360p", "480p", "HD", "FHD", "2K", "4K", "Max"])
        res_layout.addWidget(res_label)
        res_layout.addWidget(self.res_combo)
        self.res_combo.setCurrentText("Max")
        self.fps_checkbox = QCheckBox("60fps")
        res_layout.addWidget(self.fps_checkbox)
        main_layout.addLayout(res_layout)
        
        # Download button
        self.download_btn = QPushButton("Download")
        self.download_btn.setStyleSheet("background-color: #ff3333; color: white; font-weight: bold;")
        self.download_btn.clicked.connect(self.startDownload)
        main_layout.addWidget(self.download_btn)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        main_layout.addWidget(self.progress_bar)
        
        # Progress info labels
        progress_info_layout = QHBoxLayout()
        self.speed_label = QLabel("Speed: -")
        self.size_label = QLabel("Size: -")
        self.eta_label = QLabel("ETA: -")
        progress_info_layout.addWidget(self.speed_label)
        progress_info_layout.addWidget(self.size_label)
        progress_info_layout.addWidget(self.eta_label)
        main_layout.addLayout(progress_info_layout)
        
        # Control buttons
        control_layout = QHBoxLayout()
        self.pause_btn = QPushButton("Pause")
        self.pause_btn.clicked.connect(self.togglePause)
        self.pause_btn.setEnabled(False)
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.cancelDownload)
        self.cancel_btn.setEnabled(False)
        control_layout.addWidget(self.pause_btn)
        control_layout.addWidget(self.cancel_btn)
        main_layout.addLayout(control_layout)
        
        # Bottom buttons
        bottom_layout = QHBoxLayout()
        settings_btn = QPushButton("Settings")
        settings_btn.clicked.connect(self.openSettings)
        support_btn = QPushButton("Support Dev")
        support_btn.clicked.connect(lambda: webbrowser.open("https://www.ko-fi.com/MalikHw47"))
        bottom_layout.addWidget(settings_btn)
        bottom_layout.addWidget(support_btn)
        main_layout.addLayout(bottom_layout)
        
        # Status label
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.status_label)
        
        # Default settings
        if platform.system() == "Windows":
            self.save_path = os.path.join(os.path.expanduser("~"), "Downloads", "HwYtVidGrabber")
        else:
            self.save_path = os.path.join(os.path.expanduser("~"), "Downloads", "HwYtVidGrabber")
        self.dark_mode = False
        self.checkSavePathPermissions()
    
    def urlChanged(self, url):
        if "xvFZjo5PgG0" in url:
            self.title_label.setText("Title: ????")
            self.author_label.setText("Channel: ????")
    
    def checkSavePathPermissions(self):
        try:
            if not os.path.exists(self.save_path):
                os.makedirs(self.save_path)
            
            test_file = os.path.join(self.save_path, ".write_test")
            with open(test_file, 'w') as f:
                f.write("test")
            os.remove(test_file)
        except Exception as e:
            QMessageBox.warning(self, "Permission Error", 
                               f"Cannot write to save directory: {self.save_path}\nError: {str(e)}\n\nPlease choose a different directory in Settings.")
    
    def titleClicked(self, event):
        self.title_click_count += 1
        if self.title_click_count == 10:
            self.url_input.setText("https://youtu.be/xvFZjo5PgG0?si=vMD2fi9Qf85nPLws")
            self.title_click_count = 0
    
    def updateVideoInfo(self, info):
        title = info.get('title', 'Unknown')
        uploader = info.get('uploader', 'Unknown')
    
        self.title_label.setText(f"Title: {title}")
        self.author_label.setText(f"Channel: {uploader}")
    
        if uploader == "Hatsune Miku":
            self.showMikuDialog()

    def showMikuDialog(self):
        reply = QMessageBox.question(self, "Miku Question", 
                                    "Is Miku your Waifu?",
                                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
    
        if reply == QMessageBox.StandardButton.Yes:
            self.setWindowTitle("LOSER")
        else:
            msg = QMessageBox(self)
            msg.setWindowTitle("Just Kidding")
            msg.setText("Nah bro just kidding")
            cool_button = msg.addButton("Cool", QMessageBox.ButtonRole.AcceptRole)
            msg.exec()
    
    def updateAvailableFormats(self, format_info):
        max_res = format_info.get('max_resolution')
        current_res = self.res_combo.currentText()
        if current_res != "Max":
            res_hierarchy = ["144p", "360p", "480p", "HD", "FHD", "2K", "4K"]
            current_index = res_hierarchy.index(current_res) if current_res in res_hierarchy else -1
            max_index = res_hierarchy.index(max_res) if max_res in res_hierarchy else -1
            
            if current_index > max_index and max_index >= 0:
                self.res_combo.setCurrentText(max_res)
                self.status_label.setText(f"Adjusted to maximum available resolution: {max_res}")
    
    def startDownload(self):
        url = self.url_input.text().strip()
        if not url:
            QMessageBox.warning(self, "Error", "Please enter a YouTube URL!")
            return
        
        self.download_btn.setEnabled(False)
        self.status_label.setText("Processing...")
        
        format_option = self.format_combo.currentText()
        resolution = self.res_combo.currentText()
        fps_60 = self.fps_checkbox.isChecked()
        
        self.checkSavePathPermissions()
        
        self.progress_bar.setValue(0)
        self.speed_label.setText("Speed: -")
        self.size_label.setText("Size: -")
        self.eta_label.setText("ETA: -")
        
        self.download_worker = DownloadWorker(url, self.save_path, format_option, resolution, fps_60)
        self.download_worker.progress_signal.connect(self.updateProgress)
        self.download_worker.finished_signal.connect(self.downloadFinished)
        self.download_worker.error_signal.connect(self.downloadError)
        self.download_worker.info_signal.connect(self.updateVideoInfo)
        self.download_worker.available_formats_signal.connect(self.updateAvailableFormats)
        
        self.download_worker.start()
        
        self.pause_btn.setEnabled(True)
        self.pause_btn.setText("Pause")
        self.cancel_btn.setEnabled(True)
    
    def updateProgress(self, progress_info):
        self.status_label.setText("")
        
        try:
            percent = int(progress_info['percent'])
            if 0 <= percent <= 100:
                self.progress_bar.setValue(percent)
        except (ValueError, TypeError):
            pass
            
        self.speed_label.setText(f"Speed: {progress_info['speed']}")
        self.size_label.setText(f"Size: {progress_info['total_size']}")
        self.eta_label.setText(f"ETA: {progress_info['eta']}")
    
    def downloadFinished(self):
        self.progress_bar.setValue(100)
        self.download_btn.setEnabled(True)
        self.pause_btn.setEnabled(False)
        self.cancel_btn.setEnabled(False)
        self.speed_label.setText("Speed: -")
        self.eta_label.setText("ETA: -")
        self.status_label.setText("Download completed!")
        QMessageBox.information(self, "Success", "Download completed successfully!")
    
    def downloadError(self, error_msg):
        if "Download cancelled" not in error_msg:
            QMessageBox.warning(self, "Error", f"Download failed: {error_msg}")
        
        self.download_btn.setEnabled(True)
        self.pause_btn.setEnabled(False)
        self.cancel_btn.setEnabled(False)
        self.speed_label.setText("Speed: -")
        self.size_label.setText("Size: -")
        self.eta_label.setText("ETA: -")
        self.status_label.setText("")
    
    def togglePause(self):
        if not self.download_worker:
            return
        
        if self.download_worker.is_paused:
            self.download_worker.resume()
            self.pause_btn.setText("Pause")
            self.status_label.setText("Downloading...")
        else:
            self.download_worker.pause()
            self.pause_btn.setText("Resume")
            self.status_label.setText("Paused")
    
    def cancelDownload(self):
        if not self.download_worker:
            return
        
        self.download_worker.cancel()
        self.progress_bar.setValue(0)
        self.download_btn.setEnabled(True)
        self.pause_btn.setEnabled(False)
        self.cancel_btn.setEnabled(False)
        self.status_label.setText("Download cancelled")
    
    def checkFFmpeg(self):
        try:
            if platform.system() == "Windows":
                if getattr(sys, 'frozen', False):
                    exe_dir = os.path.dirname(sys.executable)
                else:
                    exe_dir = os.path.dirname(os.path.abspath(__file__))
                
                ffmpeg_path = os.path.join(exe_dir, "ffmpeg.exe")
                c_drive_ffmpeg = "C:\\ffmpeg.exe"
                
                # Check if ffmpeg exists in application directory
                if os.path.exists(ffmpeg_path):
                    os.environ['PATH'] = exe_dir + os.pathsep + os.environ['PATH']
                # Check if ffmpeg exists at C:\ffmpeg.exe
                elif os.path.exists(c_drive_ffmpeg):
                    os.environ['PATH'] = "C:\\" + os.pathsep + os.environ['PATH']
                else:
                    reply = QMessageBox.question(
                        self, 
                        "FFmpeg Not Found",
                        "FFmpeg is required but not found in the application directory or at C:\\ffmpeg.exe.\n"
                        "Do you want to download and extract ffmpeg.exe to this directory?\n"
                        f"Directory: {exe_dir}",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                    )
                    
                    if reply == QMessageBox.StandardButton.Yes:
                        webbrowser.open("https://www.gyan.dev/ffmpeg/builds/ffmpeg-git-essentials.7z")
                        QMessageBox.information(
                            self,
                            "Instructions",
                            "Please download ffmpeg-git-essentials.7z from the opened link,\n"
                            "extract it, and place ffmpeg.exe in one of these directories:\n"
                            f"{exe_dir}\n"
                            "OR\n"
                            "C:\\ffmpeg.exe\n\n"
                            "Then restart the application."
                        )
                        sys.exit(1)
                    else:
                        QMessageBox.warning(
                            self,
                            "FFmpeg Required",
                            "The application cannot function without FFmpeg.\n"
                            "Please install ffmpeg.exe in the application directory or at C:\\ffmpeg.exe"
                        )
                        sys.exit(1)
            
            result = subprocess.run(["ffmpeg", "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if result.returncode != 0:
                raise Exception("FFmpeg returned non-zero exit code")
                
        except Exception as e:
            if platform.system() != "Windows":
                reply = QMessageBox.question(self, "FFmpeg Not Found",
                                     "FFmpeg is not installed. Do you want to install it now?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                if reply == QMessageBox.StandardButton.Yes:
                    if platform.system() == "Linux":
                        try:
                            with open("/etc/os-release", "r") as f:
                                os_info = f.read().lower()
                                if "ubuntu" in os_info or "debian" in os_info:
                                    cmd = "sudo apt-get install ffmpeg"
                                elif "fedora" in os_info:
                                    cmd = "sudo dnf install ffmpeg"
                                elif "arch" in os_info:
                                    cmd = "sudo pacman -S ffmpeg"
                                else:
                                    cmd = "sudo apt-get install ffmpeg"
                        except:
                            cmd = "sudo apt-get install ffmpeg"
                    else:
                        cmd = "sudo apt-get install ffmpeg"
                    
                    try:
                        os.system(f"x-terminal-emulator -e '{cmd}'")
                        self.checkFFmpegAfterInstall()
                    except Exception as e:
                        QMessageBox.warning(self, "Error", f"Failed to launch terminal: {str(e)}")
            else:
                QMessageBox.warning(self, "FFmpeg Error", f"FFmpeg is not working: {str(e)}")
                sys.exit(1)

    def checkFFmpegAfterInstall(self):
        QTimer.singleShot(5000, lambda: self._checkFFmpegInstalled())
    
    def _checkFFmpegInstalled(self):
        try:
            subprocess.run(["ffmpeg", "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            QMessageBox.information(self, "Success", "FFmpeg installed successfully!")
        except:
            QMessageBox.warning(self, "Error", "FFmpeg installation may have failed. Please install it manually.")
    
    def openSettings(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Settings")
        layout = QVBoxLayout(dialog)
        
        # Save path
        path_layout = QHBoxLayout()
        path_label = QLabel("Save Path:")
        path_input = QLineEdit(self.save_path)
        browse_btn = QPushButton("Browse")
        
        def browsePath():
            path = QFileDialog.getExistingDirectory(dialog, "Select Directory", self.save_path)
            if path:
                path_input.setText(path)
        
        browse_btn.clicked.connect(browsePath)
        
        path_layout.addWidget(path_label)
        path_layout.addWidget(path_input)
        path_layout.addWidget(browse_btn)
        layout.addLayout(path_layout)
        
        # Dark mode
        dark_mode_check = QCheckBox("Dark Mode")
        dark_mode_check.setChecked(self.dark_mode)
        layout.addWidget(dark_mode_check)
        
        # Buttons
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Save")
        cancel_btn = QPushButton("Cancel")
        
        def saveSettings():
            new_path = os.path.normpath(path_input.text())
            try:
                if not os.path.exists(new_path):
                    os.makedirs(new_path)
                test_file = os.path.join(new_path, ".write_test")
                with open(test_file, 'w') as f:
                    f.write("test")
                os.remove(test_file)
                self.save_path = new_path
            except Exception as e:
                QMessageBox.warning(dialog, "Permission Error", 
                                   f"Cannot write to selected directory: {str(e)}")
                return
                
            self.dark_mode = dark_mode_check.isChecked()
            self.applyDarkMode(self.dark_mode)
            self.saveSettings()
            dialog.accept()
        
        save_btn.clicked.connect(saveSettings)
        cancel_btn.clicked.connect(dialog.reject)
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)
        
        dialog.setLayout(layout)
        dialog.exec()
    
    def loadSettings(self):
        try:
            if os.path.exists("settings.json"):
                with open("settings.json", "r") as f:
                    settings = json.load(f)
                    self.save_path = settings.get("save_path", self.save_path)
                    self.dark_mode = settings.get("dark_mode", False)
                    self.applyDarkMode(self.dark_mode)
        except Exception:
            pass
    
    def saveSettings(self):
        try:
            with open("settings.json", "w") as f:
                json.dump({
                    "save_path": self.save_path,
                    "dark_mode": self.dark_mode
                }, f)
        except Exception:
            pass
    
    def applyDarkMode(self, enabled):
        if enabled:
            self.setStyleSheet("""
                QWidget {
                    background-color: #333;
                    color: #EEE;
                }
                QPushButton {
                    background-color: #555;
                    color: #EEE;
                    border: 1px solid #777;
                    padding: 5px;
                }
                QPushButton:hover {
                    background-color: #666;
                }
                QPushButton#download_btn {
                    background-color: #ff3333;
                    color: white;
                    font-weight: bold;
                }
                QLineEdit, QComboBox {
                    background-color: #444;
                    color: #EEE;
                    border: 1px solid #777;
                    padding: 3px;
                }
                QProgressBar {
                    border: 1px solid #777;
                    text-align: center;
                }
                QProgressBar::chunk {
                    background-color: #5AF;
                }
            """)
        else:
            self.setStyleSheet("""
                QPushButton#download_btn {
                    background-color: #ff3333;
                    color: white;
                    font-weight: bold;
                }
            """)
    
    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            text = event.mimeData().text()
            if any(domain in text for domain in ['youtube.com', 'youtu.be', 'm.youtube.com']):
                event.acceptProposedAction()
            else:
                event.ignore()
        else:
            event.ignore()

    def dropEvent(self, event):
        text = event.mimeData().text().strip()
        if text:
            self.url_input.setText(text)
            event.acceptProposedAction()
    
    def closeEvent(self, event):
        event.accept()


def main():
    app = QApplication(sys.argv)
    window = HwYtVidGrabber()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
