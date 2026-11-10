@echo off
setlocal EnableExtensions EnableDelayedExpansion
chcp 65001 >nul
cls

title NAMESKILLS - v30.0 CANONICAL + SHA256

set "VERSION=30.0"
set "NO_PAUSE=0"
if /I "%~1"=="--no-pause" set "NO_PAUSE=1"

call :resolve_drive
call :resolve_desktop

set "BASE=%HD%\.gemini"
set "BAU=%BASE%\baude-skills-brutas"
set "PACOTE=%BASE%\pacote-escola-skills"
set "OUT=%DESKTOP%\nameSkills.txt"
set "OUTN=%DESKTOP%\nameSkills-somente-nomes.txt"
set "OUTCSV=%DESKTOP%\nameSkills-detalhado.csv"
set "OUTCONFLICT=%DESKTOP%\nameSkills-conflitos.txt"
set "TMPRAW=%TEMP%\nameskills-v30.0-%RANDOM%%RANDOM%-raw.txt"
set "TMPSORT=%TEMP%\nameskills-v30.0-%RANDOM%%RANDOM%-sort.txt"
set "TMPUNIQ=%TEMP%\nameskills-v30.0-%RANDOM%%RANDOM%-uniq.txt"

del /f /q "%TMPRAW%" "%TMPSORT%" "%TMPUNIQ%" >nul 2>nul
> "%OUTCONFLICT%" echo Conflitos de mesmo name YAML com SHA-256 diferente - v%VERSION%

echo ============================================================
echo  NAMESKILLS - v%VERSION%
echo ============================================================
echo HD:      %HD%
echo Usuario: %USER_HOME%
echo Bau:     %BAU%
echo.
echo Usa o campo YAML name como identidade canonica e calcula SHA-256.
echo O cache __github-repos nao e varrido para manter a execucao rapida.
echo ============================================================
echo.

call :collect_active
call :collect_package_fast
call :collect_bau_fast

if not exist "%TMPRAW%" (
  echo [ERRO] Nenhuma skill encontrada.
  goto failed
)

sort "%TMPRAW%" /o "%TMPSORT%" >nul 2>nul
set /a RAW=0
set /a UNIQ=0
set /a LOCAL=0
set /a CONFLICT=0
set "LAST="
set "LAST_HASH="
if exist "%TMPUNIQ%" del /f /q "%TMPUNIQ%" >nul 2>nul

for /f "usebackq tokens=1,2,3,4,5,6 delims=|" %%A in ("%TMPSORT%") do (
  set /a RAW+=1
  set "N=%%A"
  set "H=%%F"
  if /I not "!N!"=="!LAST!" (
    set /a UNIQ+=1
    set "LAST=!N!"
    set "LAST_HASH=!H!"
    echo %%A^|%%C^|%%D^|%%E^|%%F>> "%TMPUNIQ%"
    if /I "%%C"=="LOCAL" set /a LOCAL+=1
  ) else (
    if /I not "!H!"=="!LAST_HASH!" (
      set /a CONFLICT+=1
      >> "%OUTCONFLICT%" echo %%A ^| hash selecionado=!LAST_HASH! ^| outro=%%F ^| %%C ^| %%D
    )
  )
)

> "%OUT%" echo ============================================================
>> "%OUT%" echo  NAMESKILLS - v%VERSION%
>> "%OUT%" echo ============================================================
>> "%OUT%" echo HD: %HD%
>> "%OUT%" echo Usuario: %USER_HOME%
>> "%OUT%" echo Bau: %BAU%
>> "%OUT%" echo Total bruto coletado: %RAW%
>> "%OUT%" echo Total unico por YAML name: %UNIQ%
>> "%OUT%" echo Skills locais selecionadas: %LOCAL%
>> "%OUT%" echo Conflitos de hash: %CONFLICT%
>> "%OUT%" echo.
>> "%OUT%" echo NAME YAML ^| ORIGEM ^| CAMINHO ^| PASTA ^| SHA256

> "%OUTN%" echo # nameSkills somente nomes canonicos - v%VERSION%
> "%OUTCSV%" echo name_yaml,origem,caminho,pasta,sha256
for /f "usebackq tokens=1,2,3,4,5 delims=|" %%A in ("%TMPUNIQ%") do (
  echo %%A>> "%OUTN%"
  echo %%A ^| %%B ^| %%C ^| %%D ^| %%E>> "%OUT%"
  echo "%%A","%%B","%%C","%%D","%%E">> "%OUTCSV%"
)

echo ============================================================
echo  NAMESKILLS CONCLUIDO - v%VERSION%
echo ============================================================
echo Total unico:   %UNIQ%
echo Locais:        %LOCAL%
echo Conflitos:     %CONFLICT%
echo.
echo Saidas:
echo  %OUT%
echo  %OUTN%
echo  %OUTCSV%
echo  %OUTCONFLICT%
echo ============================================================

del /f /q "%TMPRAW%" "%TMPSORT%" "%TMPUNIQ%" >nul 2>nul
if not "%NO_PAUSE%"=="1" pause
exit /b 0

:collect_active
echo Coletando skills locais ativas...
for %%R in (
  "%USER_HOME%\.agent\skills"
  "%USER_HOME%\.agents\skills"
  "%USER_HOME%\.codex\skills"
  "%USER_HOME%\.claude\skills"
  "%USER_HOME%\.gemini\skills"
  "%USER_HOME%\.gemini\config\skills"
  "%USER_HOME%\.gemini\antigravity-ide\skills"
  "%USER_HOME%\antigravity\skills"
) do if exist "%%~R" for /d %%S in ("%%~R\*") do if exist "%%~S\SKILL.md" call :add "%%~nxS" "%%~fS" "LOCAL"
exit /b 0

:collect_package_fast
echo Coletando pacote escola...
for %%R in (
  "%PACOTE%\.agent\skills"
  "%PACOTE%\.agents\skills"
  "%PACOTE%\.codex\skills"
  "%PACOTE%\.claude\skills"
  "%PACOTE%\.gemini\skills"
  "%PACOTE%\.gemini\config\skills"
  "%PACOTE%\.gemini\antigravity-ide\skills"
  "%PACOTE%\antigravity\skills"
) do if exist "%%~R" for /d %%S in ("%%~R\*") do if exist "%%~S\SKILL.md" call :add "%%~nxS" "%%~fS" "PACOTE"
exit /b 0

:collect_bau_fast
if not exist "%BAU%" exit /b 0
echo Coletando backup local canonico...
if exist "%BAU%\__local-active-skills" for /d %%S in ("%BAU%\__local-active-skills\*") do if exist "%%~S\SKILL.md" call :add "%%~nxS" "%%~fS" "BAU"
exit /b 0

:add
set "FOLDER=%~1"
set "P=%~2"
set "O=%~3"
if not defined FOLDER exit /b 0

set "SKILL_FILE=%P%\SKILL.md"
set "YAML_NAME="
for /f "usebackq delims=" %%Y in (`powershell -NoProfile -Command "$m=Get-Content -LiteralPath $env:SKILL_FILE -TotalCount 60 | Where-Object { $_ -match '^\s*name\s*:\s*(.+?)\s*$' } | Select-Object -First 1; if($m){ ($m -replace '^\s*name\s*:\s*','').Trim().Trim([char]34,[char]39) }" 2^>nul`) do if not defined YAML_NAME set "YAML_NAME=%%Y"
if not defined YAML_NAME set "YAML_NAME=%FOLDER%"

set "HASH_FILE=%SKILL_FILE%"
set "HASH="
for /f "usebackq delims=" %%H in (`powershell -NoProfile -Command "(Get-FileHash -Algorithm SHA256 -LiteralPath $env:HASH_FILE).Hash" 2^>nul`) do if not defined HASH set "HASH=%%H"
if not defined HASH set "HASH=(hash-error)"

set "PRI=9"
if /I "%O%"=="LOCAL" set "PRI=0"
if /I "%O%"=="PACOTE" set "PRI=1"
if /I "%O%"=="BAU" set "PRI=2"
echo %YAML_NAME%^|%PRI%^|%O%^|%P%^|%FOLDER%^|%HASH%>> "%TMPRAW%"
exit /b 0

:resolve_drive
set "USER_HOME=%USERPROFILE%"
if not defined USER_HOME set "USER_HOME=C:\Users\alunos"
set "HD=%~d0\"
if exist "%HD%\.gemini\baude-skills-brutas" exit /b 0
for %%D in (D E F G H I J K L M N O P Q R S T U V W X Y Z C) do if exist "%%D:\.gemini\baude-skills-brutas" (
  set "HD=%%D:\"
  exit /b 0
)
if not defined HD set "HD=E:\"
exit /b 0

:resolve_desktop
set "DESKTOP=%USER_HOME%\Desktop"
if exist "%DESKTOP%\" exit /b 0
if defined OneDrive if exist "%OneDrive%\Desktop\" set "DESKTOP=%OneDrive%\Desktop"
if exist "%DESKTOP%\" exit /b 0
set "DESKTOP=%HD%Desktop"
mkdir "%DESKTOP%" >nul 2>nul
exit /b 0

:failed
if not "%NO_PAUSE%"=="1" pause
exit /b 1
