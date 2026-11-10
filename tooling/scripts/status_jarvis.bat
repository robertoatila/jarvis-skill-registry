@echo off
cd /d "E:\.skill-registry"
echo ========================================================
echo  J.A.R.V.I.S. Resident Host - Status do Servico
echo ========================================================
python jarvis.py service status
echo.
python jarvis.py remote-doctor
echo.
pause
