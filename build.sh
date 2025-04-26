#!/bin/bash

# HwYtVidGrabber Build Script
# ---------------------------

echo "==================================="
echo "HwYtVidGrabber Build Script"
echo "==================================="

# Check for Python 3.8+
python_version=$(python3 --version 2>&1 | awk '{print $2}')
python_major=$(echo $python_version | cut -d. -f1)
python_minor=$(echo $python_version | cut -d. -f2)

if [ "$python_major" -lt 3 ] || ([ "$python_major" -eq 3 ] && [ "$python_minor" -lt 8 ]); then
    echo "Error: Python 3.8+ is required, but you have $python_version"
    echo "Please upgrade your Python installation."
    exit 1
fi

echo "✓ Python $python_version detected"

# Check for pip
if ! command -v pip3 &> /dev/null; then
    echo "Error: pip3 not found. Installing pip..."
    sudo apt-get update
    sudo apt-get install -y python3-pip
fi

echo "✓ pip detected"

# Check for PyInstaller
if ! pip3 show pyinstaller &> /dev/null; then
    echo "PyInstaller not found. Installing PyInstaller..."
    pip3 install pyinstaller
fi

echo "✓ PyInstaller detected"

# Install required packages
echo "Installing required packages..."
pip3 install PyQt6 yt-dlp


# Build the executable
echo "Building executable with PyInstaller..."
pyinstaller --name=HwYtVidGrabber \
            --onefile \
            --windowed \
            --add-data="icon.png:." \
            --icon=icon.png \
            --hidden-import=PyQt6 \
            --hidden-import=yt_dlp \
            HwYtVidGrabber.py

# Check if build was successful
if [ -f "dist/HwYtVidGrabber" ]; then
    echo ""
    echo "==================================="
    echo "Build completed successfully!"
    echo "==================================="
    echo "Executable created at: dist/HwYtVidGrabber"
    echo ""
    echo "To run the application:"
    echo "cd dist && ./HwYtVidGrabber"
    echo ""
    echo "To create a system-wide installation:"
    echo "sudo cp dist/HwYtVidGrabber /usr/local/bin/"
    echo "sudo cp icon.png /usr/share/icons/HwYtVidGrabber.png"
    echo ""
    
    # Create desktop entry in the local directory
    echo "Creating desktop entry file..."
    cat > HwYtVidGrabber.desktop << EOF
[Desktop Entry]
Name=HwYtVidGrabber
Comment=YouTube Video Downloader
Exec=/usr/local/bin/HwYtVidGrabber
Icon=/usr/share/icons/HwYtVidGrabber.png
Terminal=false
Type=Application
Categories=Utility;AudioVideo;
EOF
    
    echo "Desktop entry created at: $(pwd)/HwYtVidGrabber.desktop"
    echo "To install desktop entry system-wide:"
    echo "sudo cp HwYtVidGrabber.desktop /usr/share/applications/"
    echo "==================================="
else
    echo ""
    echo "==================================="
    echo "Build failed!"
    echo "Check the output above for errors."
    echo "==================================="
fi
