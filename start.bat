@echo off
echo ========================================================================
echo 🚀 SMART TILE SYSTEM - EASY START
echo ========================================================================
echo.

REM Check if database exists
if not exist "smart_tiles.db" (
    echo ⚠️  Database not found. Creating fresh database...
    python reset_database.py
    echo.
)

REM Check if app.py exists
if not exist "app.py" (
    echo ❌ ERROR: app.py not found!
    echo Make sure you're in the correct directory.
    pause
    exit /b 1
)

echo ✅ All checks passed!
echo.
echo 📋 Quick Tips:
echo    - Registration: http://localhost:5000/register
echo    - Login: http://localhost:5000/login
echo    - Password reset links show in THIS terminal
echo.
echo 🔍 Watch this terminal for:
echo    ✅ User created successfully
echo    ✅ Login successful
echo    📧 PASSWORD RESET LINK
echo.
echo ========================================================================
echo Starting Flask server...
echo ========================================================================
echo.

REM Start Flask
python app.py

pause