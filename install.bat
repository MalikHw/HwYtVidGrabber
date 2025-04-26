@echo off
echo ======================================
echo HwYtVidGrabber Windows Installation
echo ======================================

:: Check if running with administrative privileges
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo This installation requires administrative privileges.
    echo Please right-click this file and select "Run as administrator".
    pause
    exit /b 1
)

echo Checking for required files...

:: Check if HwYtVidGrabber.exe exists
if not exist "HwYtVidGrabber.exe" (
    echo HwYtVidGrabber.exe not found in folder.
    echo Please run build.bat first to create the executable.
    pause
    exit /b 1
)

echo Creating installation directory...
if not exist "C:\Program Files\HwYtVidGrabber" mkdir "C:\Program Files\HwYtVidGrabber"

echo Copying files...
copy "HwYtVidGrabber.exe" "C:\Program Files\HwYtVidGrabber"
copy "icon.ico" "C:\Program Files\HwYtVidGrabber"
copy "icon.png" "C:\Program Files\HwYtVidGrabber"

echo Creating desktop shortcut...
powershell -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut('%userprofile%\Desktop\HwYtVidGrabber.lnk'); $s.TargetPath = 'C:\Program Files\HwYtVidGrabber\HwYtVidGrabber.exe'; $s.IconLocation = 'C:\Program Files\HwYtVidGrabber\icon.ico'; $s.Save()"

echo Creating Start Menu shortcut...
if not exist "%ProgramData%\Microsoft\Windows\Start Menu\Programs\HwYtVidGrabber" (
    mkdir "%ProgramData%\Microsoft\Windows\Start Menu\Programs\HwYtVidGrabber"
)

powershell -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut('%ProgramData%\Microsoft\Windows\Start Menu\Programs\HwYtVidGrabber\HwYtVidGrabber.lnk'); $s.TargetPath = 'C:\Program Files\HwYtVidGrabber\HwYtVidGrabber.exe'; $s.IconLocation = 'C:\Program Files\HwYtVidGrabber\icon.ico'; $s.Save()"

:: Create uninstaller
echo Creating uninstaller...
(
    echo @echo off
    echo echo Uninstalling HwYtVidGrabber...
    echo del "%%userprofile%%\Desktop\HwYtVidGrabber.lnk" ^> nul 2^>^&1
    echo rmdir /s /q "%%ProgramData%%\Microsoft\Windows\Start Menu\Programs\HwYtVidGrabber" ^> nul 2^>^&1
    echo rmdir /s /q "C:\Program Files\HwYtVidGrabber"
    echo echo HwYtVidGrabber has been uninstalled.
    echo pause
) > "C:\Program Files\HwYtVidGrabber\uninstall.bat"

:: Create uninstaller shortcut in Start Menu
powershell -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut('%ProgramData%\Microsoft\Windows\Start Menu\Programs\HwYtVidGrabber\Uninstall HwYtVidGrabber.lnk'); $s.TargetPath = 'C:\Windows\System32\cmd.exe'; $s.Arguments = '/c \"C:\Program Files\HwYtVidGrabber\uninstall.bat\"'; $s.Save()"

echo ======================================
echo Installation completed successfully!
echo ======================================
echo HwYtVidGrabber has been installed to:
echo C:\Program Files\HwYtVidGrabber
echo.
echo Shortcuts have been created on your desktop and Start Menu.
echo To uninstall, use the uninstaller in the Start Menu or in the installation folder.
echo ======================================

pause
