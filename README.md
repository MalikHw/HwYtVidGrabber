#   HwYtVidGrabber

HwYtVidGrabber is a desktop application that allows you to download videos and audio from YouTube. It supports various resolutions and formats, including MP4, MP3, and muted MP4.

## Screenshot:

![lol.png](screenshots/lol.png)

##   Features

* Download videos in resolutions up to 2160p.
* Download audio in MP3 format.
* Download muted videos (MP4 format).
* Option to prefer 60fps for high-definition video downloads.
* Save settings for video and audio download paths.
* System tray integration for background operation.
* Download progress tracking.
* Notifications for download completion.

##   Prerequisites

* **FFmpeg**: FFmpeg is required to process and convert audio and video files. The application will display an error message with installation instructions if FFmpeg is not found. (linux only)
* install with `sudo apt install ffmpeg` (debian) or `sudo dnf install ffmpeg` (fedora) or `sudo pacman -S ffmpeg` (arch)

##   Installation

No installation is necessary.

* On Windows, simply run the executable (.exe) file.
* For other operating systems, run the library directly. (python and the other dependcies are inside the app)(rename the file to `HwYtVidGrabber` ans run it with `./HwYtVidGrabber`. installation script, soon)

##   Usage

1.  Enter the YouTube URL in the provided field.
2.  Select the desired resolution.
3.  Choose the output format (MP4, MP3, or muted MP4).
4.  Check the "Prefer 60fps" option if desired (only available for video formats and 720p or higher resolution).
5.  Click the "Download" button.
6.  The download progress will be displayed in the progress bar and status label.
7.  Downloaded files are saved to the "Downloads/Vids" or "Downloads/Songs" directory by default, or to a user-defined location via the settings.

##   Settings

* The "Settings" button allows you to configure the default save paths for videos and audio.

##   System Tray

* The application can be minimized to the system tray.
* To close the application completely, use the "Quit" option in the system tray menu.

##   Support

If you find this application useful, consider supporting the developer:

* Click the "Support Development ☕" button to open the donation page.

##   Credits

* Developed by MalikHw47.
* Uses the yt-dlp library for downloading.
* Built with PyQt6.
