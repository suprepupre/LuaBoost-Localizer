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
python -m pip install pyinstaller

echo.
echo [2/2] Building executable...
python -m PyInstaller --onefile --name "luaboost_localizer" --distpath . --clean luaboost_localizer.py

echo.
echo Cleaning up build artifacts...
if exist build rd /s /q build
if exist __pycache__ rd /s /q __pycache__
if exist luaboost_localizer.spec del luaboost_localizer.spec

echo.
if exist luaboost_localizer.exe (
    echo SUCCESS: luaboost_localizer.exe created in current folder
) else (
    echo ERROR: Build failed
)
echo.
pause