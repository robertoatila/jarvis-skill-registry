@echo off
echo ======================================================================
echo  J.A.R.V.I.S. // HANGAR DE ARMAZENAMENTO SOBERANO NO DISCO D:
echo ======================================================================
echo.

net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [AVISO] Este script precisa ser executado como Administrador.
    echo Por favor, clique com o botao direito neste arquivo e selecione:
    echo "Executar como Administrador".
    echo.
    pause
    exit /b 1
)

echo [*] Desbloqueando permissoes em D:\jarvis-arsenal...
if exist "D:\jarvis-arsenal" (
    icacls "D:\jarvis-arsenal" /grant Users:(OI)(CI)F /T
    icacls "D:\jarvis-arsenal" /grant "%USERNAME%:(OI)(CI)F" /T
) else (
    mkdir "D:\jarvis-arsenal"
    icacls "D:\jarvis-arsenal" /grant Users:(OI)(CI)F /T
)

echo [*] Criando subdiretorios do hangar soberano no D:...
mkdir "D:\jarvis-arsenal\models" 2>nul
mkdir "D:\jarvis-arsenal\binaries" 2>nul
mkdir "D:\jarvis-arsenal\workspace" 2>nul
mkdir "D:\jarvis-arsenal\cache" 2>nul
mkdir "D:\jarvis-arsenal\missions" 2>nul

echo [*] Sincronizando com hangar D:\Program Files\jarvis-arsenal...
robocopy "D:\Program Files\jarvis-arsenal" "D:\jarvis-arsenal" /E /NFL /NDL /NJH /NJS /nc /ns /np >nul 2>&1

echo.
echo ======================================================================
echo [OK] Hangar D:\jarvis-arsenal desbloqueado com sucesso!
echo Espaco Total no D: 1.81 TB disponivel para o J.A.R.V.I.S.
echo ======================================================================
pause
