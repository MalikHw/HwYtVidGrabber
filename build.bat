@echo off
echo ===================================
echo HwYtVidGrabber Windows Build Script
echo ===================================

:: Check for Python
python --version > nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Error: Python not found.
    echo Please install Python 3.8 or later and add it to your PATH.
    exit /b 1
)

:: Check Python version
for /f "tokens=2 delims=." %%a in ('python -c "import sys; print(sys.version.split()[0])"') do set PYTHON_MINOR=%%a
if %PYTHON_MINOR% LSS 8 (
    echo Error: Python 3.8+ is required.
    echo Please upgrade your Python installation.
    exit /b 1
)

echo [✓] Python detected

:: Check for pip
pip --version > nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Error: pip not found.
    echo Please install pip and add it to your PATH.
    exit /b 1
)

echo [✓] pip detected

:: Check and install required packages
echo Installing required packages...
pip install -r requirements.txt


:: Create directory for FFmpeg
if not exist "ffmpeg_temp" mkdir ffmpeg_temp
cd ffmpeg_temp

:: Download FFmpeg if not already present
if not exist "ffmpeg.exe" (
    echo Downloading FFmpeg...
    powershell -Command "& {Invoke-WebRequest -Uri 'https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip' -OutFile 'ffmpeg.zip'}"
    
    echo Extracting FFmpeg...
    powershell -Command "& {Expand-Archive -Force 'ffmpeg.zip' '.'}"
    
    echo Moving FFmpeg binary...
    for /d %%G in (*) do (
        if exist "%%G\bin\ffmpeg.exe" copy "%%G\bin\ffmpeg.exe" ..\
    )
    
    echo Cleaning up...
    cd ..
    rmdir /s /q ffmpeg_temp
) else (
    echo [✓] FFmpeg already downloaded
    cd ..
)

echo [✓] FFmpeg prepared

:: Build with PyInstaller
echo Building executable with PyInstaller...
pyinstaller --name=HwYtVidGrabber ^
            --onefile ^
            --windowed ^
            --icon=icon.ico ^
            --add-data="icon.ico;." ^
            --add-data="icon.png;." ^
            --add-data="ffmpeg.exe;." ^
            --hidden-import=PyQt6 ^
            --hidden-import=yt_dlp ^
            HwYtVidGrabber.py

:: Check if build was successful
if exist "dist\HwYtVidGrabber.exe" (
    echo.
    echo ===================================
    echo Build completed successfully!
    echo ===================================
    echo Executable created at: dist\HwYtVidGrabber.exe
    echo.
    echo The executable includes FFmpeg and can be distributed as a standalone application.
    echo ===================================
) else (
    echo.
    echo ===================================
    echo Build failed!
    echo Check the output above for errors.
    echo ===================================
)

pause
