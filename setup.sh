#!/bin/bash
# Setup Script para Unix - Sistema Planador ESP32
# Autor: Sistema Aeromodelo
# Data: 2025-07-04

set -e

echo "🚀 Sistema Planador ESP32 - Setup Unix"
echo "======================================"

# Detectar sistema
if [[ "$OSTYPE" == "darwin"* ]]; then
    PLATFORM="macOS"
    ARCH=$(uname -m)
    if [[ "$ARCH" == "arm64" ]]; then
        echo "🍎 macOS Apple Silicon detectado"
        BREW_PREFIX="/opt/homebrew"
    else
        echo "🍎 macOS Intel detectado"
        BREW_PREFIX="/usr/local"
    fi
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    PLATFORM="Linux"
    echo "🐧 Linux detectado"
    DISTRO=$(lsb_release -si 2>/dev/null || echo "Unknown")
    echo "   Distribuição: $DISTRO"
else
    echo "❌ Sistema não suportado: $OSTYPE"
    exit 1
fi

# Verificar Python
if command -v python3 >/dev/null 2>&1; then
    PYTHON_CMD="python3"
    echo "✅ Python3 detectado: $(python3 --version)"
elif command -v python >/dev/null 2>&1; then
    PYTHON_CMD="python"
    echo "✅ Python detectado: $(python --version)"
else
    echo "❌ Python não encontrado!"
    if [[ "$PLATFORM" == "macOS" ]]; then
        echo "📥 Instale com: brew install python3"
    elif [[ "$PLATFORM" == "Linux" ]]; then
        echo "📥 Instale com: sudo apt install python3 python3-pip"
    fi
    exit 1
fi

# Verificar se é macOS e precisa do Homebrew
if [[ "$PLATFORM" == "macOS" ]]; then
    if ! command -v brew >/dev/null 2>&1; then
        echo "📦 Instalando Homebrew..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        
        # Adicionar ao PATH
        echo "🔧 Configurando PATH..."
        echo 'eval "$('$BREW_PREFIX'/bin/brew shellenv)"' >> ~/.zshrc
        eval "$($BREW_PREFIX/bin/brew shellenv)"
    else
        echo "✅ Homebrew detectado"
    fi
fi

# Executar setup Python
echo "🔧 Executando setup de desenvolvimento..."
cd src/micropython
$PYTHON_CMD install_dev_tools.py

if [ $? -ne 0 ]; then
    echo "❌ Falha no setup"
    exit 1
fi

echo ""
echo "🎉 Setup concluído!"
echo ""
echo "💡 Próximos passos:"
echo "   1. $PYTHON_CMD build_dev.py"
echo "   2. cd dist/planador_esp32"
echo "   3. Conectar ESP32 via USB"

if [[ "$PLATFORM" == "macOS" ]]; then
    echo "   4. Verificar porta: ls /dev/cu.*"
    echo "   5. make flash PORT=/dev/cu.usbserial-0001"
elif [[ "$PLATFORM" == "Linux" ]]; then
    echo "   4. Verificar porta: ls /dev/ttyUSB*"
    echo "   5. make flash PORT=/dev/ttyUSB0"
    echo ""
    echo "⚠️  IMPORTANTE (Linux):"
    echo "   • Faça logout/login para aplicar permissões seriais"
    echo "   • Verifique: groups \$USER | grep dialout"
fi

echo ""
echo "🔗 Links úteis:"
if [[ "$PLATFORM" == "macOS" ]]; then
    echo "   • Drivers USB-Serial: https://www.silabs.com/developers/usb-to-uart-bridge-vcp-drivers"
    echo "   • ESP-IDF macOS: https://docs.espressif.com/projects/esp-idf/en/latest/esp32/get-started/macos-setup.html"
elif [[ "$PLATFORM" == "Linux" ]]; then
    echo "   • ESP-IDF Linux: https://docs.espressif.com/projects/esp-idf/en/latest/esp32/get-started/linux-setup.html"
fi
echo ""