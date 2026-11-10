@echo off
chcp 65001 >nul
title J.A.R.V.I.S. Mark-LIV // Motor Soberano Local & Random Forest (Drive D:)
color 0b
echo ===============================================================================
echo   J.A.R.V.I.S. // MOTOR SOBERANO LOCAL, OFFLINE & RANDOM FOREST (DRIVE D:)
echo ===============================================================================
echo [*] Motor IA:      D:\Program Files\jarvis-arsenal\engine\random_forest_brain.py
echo [*] Base SQLite:   D:\Program Files\jarvis-arsenal\data\arsenal_library.sqlite
echo [*] Interface Web: http://127.0.0.1:8899
echo ===============================================================================
cd /d "E:\.skill-registry"

start "" "http://127.0.0.1:8899"
python -m tooling.remote_host --port 8899 --transport local
pause
