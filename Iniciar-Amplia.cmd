@rem Amplia - Heraldo Antunes - SPDX-License-Identifier: MIT
@echo off
cd /d "%~dp0"
set /p "AMPLIA_VERSION="<"VERSION"
if exist "dist\Amplia-%AMPLIA_VERSION%\Amplia.exe" (
  start "" "dist\Amplia-%AMPLIA_VERSION%\Amplia.exe"
  exit /b
)
if exist "dist\Amplia\Amplia.exe" (
  start "" "dist\Amplia\Amplia.exe"
  exit /b
)
python amplia_desktop.py
if errorlevel 1 pause
