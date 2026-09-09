@echo off
setlocal EnableExtensions EnableDelayedExpansion
chcp 65001 >nul
cls

title SALVAR SKILLS - v30.0 HASH + CONFLITOS

set "VERSION=30.0"
set "NO_PAUSE=0"
if /I "%~1"=="--no-pause" set "NO_PAUSE=1"

call :detect_hd
call :desktop

set "USER_HOME=%USERPROFILE%"
if not defined USER_HOME set "USER_HOME=C:\Users\alunos"
set "BASE=%HD%\.gemini"
set "BAU=%BASE%\baude-skills-brutas"
set "LOCAL_BKP=%BAU%\__local-active-skills"
set "HISTORY_ROOT=%BAU%\__local-active-skills-history"
set "HISTORY=%HISTORY_ROOT%\%DATE:/=-%_%RANDOM%-%RANDOM%"
set "LOG=%DESKTOP%\salvar-skills-v30.0.txt"
set "MANIFEST=%DESKTOP%\salvar-skills-manifest-v30.0.csv"
set "SEEN=%TEMP%\salvar-skills-v30.0-seen-%RANDOM%%RANDOM%.txt"

mkdir "%BASE%" >nul 2>nul
mkdir "%BAU%" >nul 2>nul
mkdir "%HISTORY_ROOT%" >nul 2>nul
mkdir "%HISTORY%" >nul 2>nul

if exist "%LOCAL_BKP%\" (
  move "%LOCAL_BKP%" "%HISTORY%\snapshot-anterior" >nul 2>nul
  if errorlevel 1 (
    echo [ERRO] Nao foi possivel preservar o snapshot anterior.
    goto failed
  )
)
mkdir "%LOCAL_BKP%" >nul 2>nul
if not exist "%LOCAL_BKP%\" goto failed

> "%LOG%" echo SALVAR SKILLS v%VERSION% - %DATE% %TIME%
>> "%LOG%" echo HD=%HD%\
>> "%LOG%" echo USER_HOME=%USER_HOME%
>> "%LOG%" echo BAU=%BAU%
>> "%LOG%" echo HISTORY=%HISTORY%
> "%MANIFEST%" echo nome,sha256,origem,source,destino,status
> "%SEEN%" rem nome^|sha256^|origem^|source

echo ============================================================
echo  SALVAR SKILLS - v%VERSION%
echo ============================================================
echo HD:        %HD%\
echo Usuario:   %USER_HOME%
echo Bau:       %BAU%
echo Backup:    %LOCAL_BKP%
echo Historico: %HISTORY%
echo.
echo Duplicatas iguais sao deduplicadas por SHA-256.
echo Mesmo nome com conteudo diferente vira CONFLITO e nao sobrescreve.
echo ============================================================
echo.

set /a COP=0
set /a FAIL=0
set /a SKIP_DUP=0
set /a CONFLICT=0
set /a SKIP_BAD=0
set /a ROOTS=0

call :scan_root "%USER_HOME%\.agent\skills" "USER:.agent\skills"
call :scan_root "%USER_HOME%\.agents\skills" "USER:.agents\skills"
call :scan_root "%USER_HOME%\.codex\skills" "USER:.codex\skills"
call :scan_root "%USER_HOME%\.claude\skills" "USER:.claude\skills"
call :scan_root "%USER_HOME%\.gemini\skills" "USER:.gemini\skills"
call :scan_root "%USER_HOME%\.gemini\config\skills" "USER:.gemini\config\skills"
call :scan_root "%USER_HOME%\.gemini\antigravity-ide\skills" "USER:.gemini\antigravity-ide\skills"
call :scan_root "%USER_HOME%\antigravity\skills" "USER:antigravity\skills"

call :scan_root "%HD%\.agent\skills" "HD:.agent\skills"
call :scan_root "%HD%\.agents\skills" "HD:.agents\skills"
call :scan_root "%HD%\.codex\skills" "HD:.codex\skills"
call :scan_root "%HD%\.claude\skills" "HD:.claude\skills"
call :scan_root "%BASE%\skills" "HD:.gemini\skills"
call :scan_root "%BASE%\config\skills" "HD:.gemini\config\skills"
call :scan_root "%BASE%\antigravity-ide\skills" "HD:.gemini\antigravity-ide\skills"
call :scan_root "%BASE%\antigravity\skills" "HD:.gemini\antigravity\skills"

del /f /q "%SEEN%" >nul 2>nul

if %COP% LEQ 0 (
  echo [ERRO] Nenhuma skill ativa foi encontrada.
  set /a FAIL+=1
)

echo.
echo ============================================================
echo  SALVAR SKILLS CONCLUIDO - v%VERSION%
echo ============================================================
echo Raizes encontradas:  %ROOTS%
echo Skills canonicas:   %COP%
echo Duplicadas iguais:  %SKIP_DUP%
echo Conflitos:           %CONFLICT%
echo Lixo pulado:         %SKIP_BAD%
echo Falhas:              %FAIL%
echo Log:                 %LOG%
echo Manifesto:           %MANIFEST%
echo ============================================================
if %CONFLICT% GTR 0 echo [AVISO] Revise os conflitos no historico antes de escolher uma versao.
if %FAIL% GTR 0 goto failed
if not "%NO_PAUSE%"=="1" pause
exit /b 0

:scan_root
set "ROOT=%~1"
set "ORIG=%~2"
if not exist "%ROOT%\" exit /b 0
set /a ROOTS+=1
echo [ROOT] %ROOT%
>> "%LOG%" echo ROOT=%ROOT%
for /d %%S in ("%ROOT%\*") do if exist "%%~fS\SKILL.md" call :copy_one "%%~fS" "%%~nxS" "%ORIG%"
exit /b 0

:copy_one
set "SRC=%~1"
set "N=%~2"
set "ORIG=%~3"
if /I "%N%"=="__github-repos" goto skip_bad
if /I "%N%"=="node_modules" goto skip_bad
if /I "%N%"==".git" goto skip_bad
if /I "%N%"=="dist" goto skip_bad
if /I "%N%"=="build" goto skip_bad
if /I "%N%"=="target" goto skip_bad
if /I "%N%"=="coverage" goto skip_bad
if /I "%N%"==".next" goto skip_bad
if /I "%N%"==".turbo" goto skip_bad

set "HASH_FILE=%SRC%\SKILL.md"
set "HASH="
for /f "usebackq delims=" %%H in (`powershell -NoProfile -Command "(Get-FileHash -Algorithm SHA256 -LiteralPath $env:HASH_FILE).Hash" 2^>nul`) do if not defined HASH set "HASH=%%H"
if not defined HASH goto copy_failed

findstr /I /B /L /C:"%N%|" "%SEEN%" >nul 2>nul
if not errorlevel 1 (
  findstr /I /B /L /C:"%N%|%HASH%|" "%SEEN%" >nul 2>nul
  if not errorlevel 1 (
    set /a SKIP_DUP+=1
    >> "%MANIFEST%" echo "%N%","%HASH%","%ORIG%","%SRC%","","DUPLICATA_IGUAL"
    exit /b 0
  )
  set /a CONFLICT+=1
  set "CONFLICT_DIR=%HISTORY%\conflitos\%N%\!CONFLICT!"
  mkdir "!CONFLICT_DIR!" >nul 2>nul
  robocopy "%SRC%" "!CONFLICT_DIR!" /E /R:1 /W:1 /NFL /NDL /NJH /NJS /NC /NS /NP /XD .git node_modules dist build .venv venv target coverage __pycache__ .next .turbo >nul
  if errorlevel 8 goto copy_failed
  echo [CONFLITO] %N% - hash diferente em %ORIG%
  >> "%LOG%" echo CONFLITO=%N% ^| %HASH% ^| %ORIG% ^| %SRC%
  >> "%MANIFEST%" echo "%N%","%HASH%","%ORIG%","%SRC%","!CONFLICT_DIR!","CONFLITO"
  exit /b 0
)

robocopy "%SRC%" "%LOCAL_BKP%\%N%" /E /R:1 /W:1 /NFL /NDL /NJH /NJS /NC /NS /NP /XD .git node_modules dist build .venv venv target coverage __pycache__ .next .turbo >nul
if errorlevel 8 goto copy_failed
if not exist "%LOCAL_BKP%\%N%\SKILL.md" goto copy_failed

>> "%SEEN%" echo %N%^|%HASH%^|%ORIG%^|%SRC%
set /a COP+=1
echo [OK] %N%
>> "%LOG%" echo OK=%N% ^| %HASH% ^| %SRC%
>> "%MANIFEST%" echo "%N%","%HASH%","%ORIG%","%SRC%","%LOCAL_BKP%\%N%","CANONICA"
exit /b 0

:copy_failed
set /a FAIL+=1
echo [FALHA] %N%
>> "%LOG%" echo FALHA=%N% - %SRC%
exit /b 0

:skip_bad
set /a SKIP_BAD+=1
exit /b 0

:detect_hd
set "HD="
set "SCRIPT_DRIVE=%~d0"
if not "%SCRIPT_DRIVE%"=="" if exist "%SCRIPT_DRIVE%\.gemini\" set "HD=%SCRIPT_DRIVE%"
if not defined HD if exist "D:\.gemini\" set "HD=D:"
if not defined HD if exist "E:\.gemini\" set "HD=E:"
if not defined HD for %%D in (F G H I J K L M N O P Q R S T U V W X Y Z C) do if not defined HD if exist "%%D:\.gemini\" set "HD=%%D:"
if not defined HD if not "%SCRIPT_DRIVE%"=="" set "HD=%SCRIPT_DRIVE%"
if not defined HD set "HD=E:"
exit /b 0

:desktop
set "DESKTOP=%USERPROFILE%\Desktop"
if exist "%DESKTOP%\" exit /b 0
if defined OneDrive if exist "%OneDrive%\Desktop\" set "DESKTOP=%OneDrive%\Desktop"
if exist "%DESKTOP%\" exit /b 0
set "DESKTOP=%HD%\Desktop"
mkdir "%DESKTOP%" >nul 2>nul
exit /b 0

:failed
if not "%NO_PAUSE%"=="1" pause
exit /b 1
