@echo off
setlocal EnableExtensions

title Exportar Delta de Skills para ChatGPT - v31.2.6 Portable

echo ============================================================
echo  EXPORTAR DELTA DE SKILLS PARA CHATGPT - v31.2.6 PORTABLE
echo ============================================================
echo.

set "ROOT="

rem 1) Preferir o arsenal mestre portatil:
rem    X:\.gemini\baude-skills-brutas + X:\.gemini\skills
for %%D in (D E F G H I J K L M N O P Q R S T U V W X Y Z C) do (
  if not defined ROOT if exist "%%D:\.gemini\skills\" if exist "%%D:\.gemini\baude-skills-brutas\" (
    set "ROOT=%%D:\.gemini\skills"
  )
)

rem 2) Fallback: perfil do usuario.
if not defined ROOT if exist "%USERPROFILE%\.gemini\skills\" (
  set "ROOT=%USERPROFILE%\.gemini\skills"
)

if not defined ROOT (
  echo [ERRO] Nao encontrei um arsenal .gemini\skills.
  echo.
  echo Procurei primeiro por um HD com:
  echo   X:\.gemini\skills
  echo   X:\.gemini\baude-skills-brutas
  echo.
  echo Depois tentei:
  echo   %USERPROFILE%\.gemini\skills
  echo.
  pause
  exit /b 1
)

set "STAGE=%TEMP%\chatgpt-skills-delta-v31.2.6"
set "OUT=%~dp0skills-chatgpt-delta-v31.2.6.zip"
set "ADD=%~dp0skills-chatgpt-delta-v31.2.6-adicionar.txt"
set "SKIP=%~dp0skills-chatgpt-delta-v31.2.6-ja-existem.txt"
set "EXTRA=%~dp0skills-chatgpt-delta-v31.2.6-extras-ignoradas.txt"
set "MISS=%~dp0skills-chatgpt-delta-v31.2.6-faltando.txt"
set "PS1=%~dp0preparar-delta-chatgpt-v31.2.6.ps1"

if not exist "%PS1%" (
  echo [ERRO] Arquivo auxiliar nao encontrado:
  echo   %PS1%
  echo.
  pause
  exit /b 1
)

echo Fonte detectada:
echo   %ROOT%
echo.
echo ZIP:
echo   %OUT%
echo.

if exist "%STAGE%" rmdir /s /q "%STAGE%" >nul 2>nul
if exist "%OUT%" del /f /q "%OUT%" >nul 2>nul
if exist "%ADD%" del /f /q "%ADD%" >nul 2>nul
if exist "%SKIP%" del /f /q "%SKIP%" >nul 2>nul
if exist "%EXTRA%" del /f /q "%EXTRA%" >nul 2>nul
if exist "%MISS%" del /f /q "%MISS%" >nul 2>nul

echo [1/3] Selecionando somente as 165 skills gerenciadas da v31.2...
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%PS1%" ^
  -SkillsRoot "%ROOT%" ^
  -StageRoot "%STAGE%\skills" ^
  -AddList "%ADD%" ^
  -SkipList "%SKIP%" ^
  -ExtraList "%EXTRA%" ^
  -MissingList "%MISS%"

if errorlevel 1 (
  echo.
  echo [ERRO] O delta nao foi criado.
  echo A origem NAO foi alterada.
  if exist "%STAGE%" rmdir /s /q "%STAGE%" >nul 2>nul
  pause
  exit /b 1
)

echo [2/3] Criando ZIP somente com as 87 skills novas...
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -Command ^
  "Compress-Archive -Path '%STAGE%\skills' -DestinationPath '%OUT%' -CompressionLevel Optimal -Force"

if errorlevel 1 (
  echo [ERRO] Falha ao criar o ZIP.
  if exist "%STAGE%" rmdir /s /q "%STAGE%" >nul 2>nul
  pause
  exit /b 1
)

echo [3/3] Limpando temporarios...
rmdir /s /q "%STAGE%" >nul 2>nul

echo.
echo ============================================================
echo  CONCLUIDO
echo ============================================================
echo.
echo Envie ao ChatGPT SOMENTE:
echo   %OUT%
echo.
echo Auditoria:
echo   %ADD%
echo   %SKIP%
echo   %EXTRA%
echo   %MISS%
echo.
echo A pasta original .gemini\skills NAO foi modificada.
echo.
pause
exit /b 0
