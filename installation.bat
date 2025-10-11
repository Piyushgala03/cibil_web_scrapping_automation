@echo off
setlocal

echo ===============================
echo    Python Virtual Env Setup
echo ===============================

if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)

echo Activating virtual environment...
call venv\Scripts\activate

echo Installing libraries from requirements.txt...
pip install --upgrade pip
pip install -r requirements.txt

echo Installing Playwright browsers...
playwright install

echo.
echo Setup completed successfully!
pause
