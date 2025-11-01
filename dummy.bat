@echo off
echo 🏗️ Building Executable for Circular Automation...
pyinstaller --noconfirm --onefile --console hello.py
echo ✅ Build complete! Executable is in the 'dist' folder.
pause
