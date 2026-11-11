@echo off
set TARGET=%~1
if "%TARGET%"=="" set TARGET=http://127.0.0.1:8899/

if "%TARGET:~0,4%"=="http" (
    start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" --profile-directory="Profile 2" --new-window "%TARGET%"
) else (
    start "" %TARGET%
)
