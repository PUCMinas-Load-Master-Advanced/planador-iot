#!/bin/bash

echo "🚀 Instalação completa do ambiente IoT"
echo "======================================="

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Detectar sistema
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    PLATFORM="linux"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    PLATFORM="macos"
elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
    PLATFORM="windows"
else
    PLATFORM="unknown"
fi

echo -e "${BLUE}Platform detectada: $PLATFORM${NC}"

# Verificar Python
echo -e "\n${YELLOW}1. Verificando Python...${NC}"
if command -v python3 >/dev/null 2>&1; then
    PYTHON_CMD="python3"
elif command -v python >/dev/null 2>&1; then
    PYTHON_CMD="python"
else
    echo -e "${RED}❌ Python não encontrado!${NC}"
    echo "Instale Python 3.8+ primeiro:"
    case $PLATFORM in
        "linux")
            echo "  sudo apt update && sudo apt install python3 python3-pip"
            ;;
        "macos")
            echo "  brew install python3"
            ;;
        "windows")
            echo "  Baixe de: https://python.org/downloads"
            ;;
    esac
    exit 1
fi

echo -e "${GREEN}✅ Python encontrado: $($PYTHON_CMD --version)${NC}"

# Instalar pip se necessário
echo -e "\n${YELLOW}2. Verificando pip...${NC}"
if ! $PYTHON_CMD -m pip --version >/dev/null 2>&1; then
    echo "📦 Instalando pip..."
    curl -sSL https://bootstrap.pypa.io/get-pip.py | $PYTHON_CMD --user
fi
echo -e "${GREEN}✅ pip configurado${NC}"

# Instalar PlatformIO
echo -e "\n${YELLOW}3. Instalando PlatformIO...${NC}"
if ! command -v pio >/dev/null 2>&1; then
    echo "📦 Instalando PlatformIO..."
    $PYTHON_CMD -m pip install --user platformio

    # Adicionar ao PATH
    PIO_PATH="$HOME/.local/bin"
    if [[ ":$PATH:" != *":$PIO_PATH:"* ]]; then
        echo "🔧 Adicionando ao PATH..."
        echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
        echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc 2>/dev/null || true
        export PATH="$HOME/.local/bin:$PATH"
    fi

    # Instalar plataforma ESP32
    echo "🔌 Instalando plataforma ESP32..."
    if command -v pio >/dev/null 2>&1; then
        pio platform install espressif32
    elif command -v ~/.local/bin/pio >/dev/null 2>&1; then
        ~/.local/bin/pio platform install espressif32
    else
        $PYTHON_CMD -m platformio platform install espressif32
    fi
else
    echo -e "${GREEN}✅ PlatformIO já instalado${NC}"
fi

# Instalar Rust
echo -e "\n${YELLOW}4. Instalando Rust...${NC}"
if ! command -v rustc >/dev/null 2>&1; then
    echo "📦 Instalando Rust..."
    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
    source ~/.cargo/env
else
    echo -e "${GREEN}✅ Rust já instalado: $(rustc --version)${NC}"
fi

# Configurar Rust para ESP32
echo -e "\n${YELLOW}5. Configurando Rust para ESP32...${NC}"
source ~/.cargo/env 2>/dev/null || true

if ! rustup target list --installed | grep -q xtensa-esp32-none-elf; then
    echo "🎯 Instalando target ESP32..."
    rustup target add xtensa-esp32-none-elf
fi

if ! command -v ldproxy >/dev/null 2>&1; then
    echo "🔧 Instalando ferramentas ESP32..."
    cargo install ldproxy espflash espmonitor cargo-espflash
fi

echo -e "${GREEN}✅ Rust + ESP32 configurado${NC}"

# Verificação final
echo -e "\n${BLUE}📋 Verificação final:${NC}"
echo -n "Python: " && $PYTHON_CMD --version
echo -n "pip: " && $PYTHON_CMD -m pip --version | head -1
echo -n "PlatformIO: "
if command -v pio >/dev/null 2>&1; then
    pio --version | head -1
elif command -v ~/.local/bin/pio >/dev/null 2>&1; then
    ~/.local/bin/pio --version | head -1
else
    $PYTHON_CMD -m platformio --version | head -1
fi
echo -n "Rust: " && rustc --version 2>/dev/null || echo "Erro - reinicie terminal"
echo -n "ESP32 Target: "
if rustup target list --installed 2>/dev/null | grep -q xtensa-esp32-none-elf; then
    echo "✅ Instalado"
else
    echo "❌ Erro"
fi

echo -e "\n${GREEN}🎉 Instalação concluída!${NC}"
echo ""
echo -e "${BLUE}Próximos passos:${NC}"
echo "  source ~/.bashrc  # ou reinicie o terminal"
echo "  make check-deps   # verificar instalação"
echo "  make flash-cpp    # testar C++"
echo "  make flash-rust   # testar Rust"
echo "  make wokwi        # simular no Wokwi"

# Aviso sobre PATH
if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
    echo ""
    echo -e "${YELLOW}⚠️  IMPORTANTE: Execute 'source ~/.bashrc' ou reinicie o terminal${NC}"
fi
