#!/bin/bash


echo "==================================="
echo "HwYtVidGrabber Installation Script"
echo "==================================="


if [ ! -f "HwYtVidGrabber" ]; then
    echo "Error: HwYtVidGrabber binary not found in dist directory."
    echo "Please download first HwYtVidGrabber from https://github.com/MalikHw/HwYtVidGrabber/releases/ and copy it here"
    exit 1
fi

# Create installation directories
echo "Creating installation directories..."
sudo mkdir -p /usr/local/bin
sudo mkdir -p /usr/share/applications
sudo mkdir -p /usr/share/icons/hicolor/256x256/apps

# Copy files
echo "Installing application..."
sudo cp HwYtVidGrabber /usr/local/bin/
sudo chmod +x /usr/local/bin/HwYtVidGrabber
sudo cp icon.png /usr/share/icons/hicolor/256x256/apps/HwYtVidGrabber.png

# Create desktop entry
echo "Creating desktop entry..."
cat > HwYtVidGrabber.desktop << EOF
[Desktop Entry]
Name=HwYtVidGrabber
Comment=YouTube Video Downloader
Exec=/usr/local/bin/HwYtVidGrabber
Icon=HwYtVidGrabber
Terminal=false
Type=Application
Categories=Utility;AudioVideo;
EOF

sudo cp HwYtVidGrabber.desktop /usr/share/applications/
rm HwYtVidGrabber.desktop

# Update icon cache
echo "Updating icon cache..."
if command -v gtk-update-icon-cache &> /dev/null; then
    sudo gtk-update-icon-cache -f /usr/share/icons/hicolor
fi

echo ""
echo "==================================="
echo "Installation completed successfully!"
echo "==================================="
echo "HwYtVidGrabber has been installed to /usr/local/bin"
echo "You can now launch it from your applications menu or by typing 'HwYtVidGrabber' in a terminal."
echo ""
echo "To uninstall, run:"
echo "sudo rm /usr/local/bin/HwYtVidGrabber"
echo "sudo rm /usr/share/applications/HwYtVidGrabber.desktop"
echo "sudo rm /usr/share/icons/hicolor/256x256/apps/HwYtVidGrabber.png"
echo "==================================="
