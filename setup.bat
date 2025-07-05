@echo off
REM Setup Script para Windows - Sistema Planador ESP32
REM Autor: Sistema Aeromodelo
REM Data: 2025-07-04

echo 🚀 Sistema Planador ESP32 - Setup Windows
echo ==========================================

REM Verificar se Python está instalado
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python não encontrado!
    echo 📥 Baixe e instale Python de: https://python.org/downloads
    echo ⚠️  IMPORTANTE: Marque "Add Python to PATH" durante instalação
    pause
    exit /b 1
)

echo ✅ Python detectado
python --version

REM Verificar se Git está instalado
git --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ⚠️  Git não encontrado
    echo 📥 Recomendamos instalar de: https://git-scm.com/download/win
)

REM Executar setup Python
echo 🔧 Executando setup de desenvolvimento...
cd src\micropython
python install_dev_tools.py

if %errorlevel% neq 0 (
    echo ❌ Falha no setup
    pause
    exit /b 1
)

echo.
echo 🎉 Setup concluído!
echo.
echo 💡 Próximos passos:
echo    1. python build_dev.py
echo    2. cd dist\planador_esp32
echo    3. Conectar ESP32 via USB
echo    4. Verificar porta COM no Device Manager
echo    5. make flash PORT=COM3
echo.
echo 🔗 Links úteis:
echo    • Drivers USB-Serial: https://www.silabs.com/developers/usb-to-uart-bridge-vcp-drivers
echo    • ESP-IDF Windows: https://docs.espressif.com/projects/esp-idf/en/latest/esp32/get-started/windows-setup.html
echo.
pause