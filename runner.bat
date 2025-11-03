@echo off
setlocal

echo Activating virtual environment...
call .venv\Scripts\activate

echo Running cibil web automation script...
python AutoScraper.py

echo Script executed successfully...
pause
