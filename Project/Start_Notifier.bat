:: Place this file in the same directory as your Python script.

@echo off
title Crafty Player Monitor
cd /d "%~dp0"

:loop
cls
echo ============================================
echo      This is the Crafty Player Monitor
echo  Watching for joins, leaves, deaths, and
echo              player achievements
echo ============================================

echo.
echo Starting Minecraft Notifier...
python mc_discord_notifier.py

echo.
echo Script crashed or exited. Restarting in 5 seconds...
timeout /t 5 >nul
goto loop
