@echo off
echo Setting up RPA Invoice Bot...
echo Installing Python dependencies...

pip install -r invoice_bot/requirements.txt

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Installation failed. Make sure Python and pip are installed and added to PATH.
    pause
    exit /b %errorlevel%
)

echo.
echo [SUCCESS] Setup complete!
echo You can now launch the bot by running: python invoice_bot/run_bot.py
echo.
pause
