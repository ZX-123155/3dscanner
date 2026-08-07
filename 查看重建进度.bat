@echo off
rem Real-time viewer for the latest 3D rebuild log (auto refresh)
chcp 65001 >nul
cd /d %~dp0
set "LOGDIR=%CD%\output"

set "LATEST="
for /f "delims=" %%i in ('dir /b /o-d "%LOGDIR%\rebuild_*.log" 2^>nul') do (
  if not defined LATEST set "LATEST=%%i"
)

if not defined LATEST (
  echo [no rebuild log yet. upload photos and click Start Rebuild on the phone page first]
  pause
  exit /b
)

echo ============================================================
echo   Live log: %LOGDIR%\%LATEST%
echo   Press Ctrl+C to exit
echo ============================================================
powershell -NoProfile -Command "Get-Content -LiteralPath '%LOGDIR%\%LATEST%' -Wait -Encoding UTF8"
