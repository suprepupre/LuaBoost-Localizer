@echo off
echo ============================================
echo   LuaBoost Localizer - Build EXE
echo ============================================
echo.

where python >nul 2>nul
if errorlevel 1 (
    echo ERROR: Python not found. Install from python.org
    pause
    exit /b 1
)

echo [1/2] Installing PyInstaller...
pip install pyinstaller

echo.
echo [2/2] Building executable...
pyinstaller --onefile --name "luaboost_localizer" --icon=NONE luaboost_localizer.py

echo.
echo Done! Output: dist\luaboost_localizer.exe
echo.
pause