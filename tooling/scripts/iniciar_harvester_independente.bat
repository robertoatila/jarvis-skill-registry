@echo off
chcp 65001 >nul
title J.A.R.V.I.S. // Harvester Soberano 24/7 (Independente)
color 0b
echo ===============================================================================
echo   J.A.R.V.I.S. // COCKPIT TÁTICO - EXECUÇÃO INDEPENDENTE DE SEGUNDO PLANO
echo ===============================================================================
echo [*] Diretório de trabalho: E:\.skill-registry
echo [*] Banco Soberano SQLite: E:\.skill-registry\state\arsenal_library.sqlite
echo [*] Espelho no Drive D:    D:\Program Files\jarvis-arsenal\data\arsenal_library.sqlite
echo [*] Alvo: Java e tópicos táticos até 999 estrelas
echo ===============================================================================
cd /d "E:\.skill-registry"

python tooling\harvest_starred_by_keyword.py --words "language:java,topic:java,compression,data-analysis,data-manipulation,encoding,encryption,hashing,parsing" --min-stars 999

echo ===============================================================================
echo [CONCLUÍDO] Harvester encerrou o ciclo de ingestão e favoritamento.
echo ===============================================================================
pause
