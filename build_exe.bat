@echo off
echo 🏗️ Building Executable for Circular Automation...
pyinstaller --noconfirm --onefile --console ^
--add-data "fetched_data;fetched_data/" ^
--add-data "logs;logs/" ^
--add-data "utilities;utilities/" ^
--add-data "ms-playwright;ms-playwright/" ^
--icon "configurations/app.ico" ^
AutoScraper.py
echo ✅ Build complete! Executable is in the 'dist' folder.
pause
