#!/bin/bash

echo "🚀 Quick Start - IoT Template"
echo "============================="

# Verificar se make existe
if ! command -v make >/dev/null 2>&1; then
    echo "❌ 'make' não encontrado. Instale:"
    echo "  Ubuntu/Debian: sudo apt install build-essential"
    echo "  macOS: xcode-select --install"
    exit 1
fi

echo "1️⃣ Instalando dependências..."
make setup

echo ""
echo "2️⃣ Verificando instalação..."
make check-deps

echo ""
echo "3️⃣ Testando build C++..."
make build-cpp

echo ""
echo "🎉 Setup concluído!"
echo ""
echo "▶️ Comandos disponíveis:"
echo "  make flash-cpp    # Flash C++ no ESP32"
echo "  make flash-rust   # Flash Rust no ESP32"
echo "  make wokwi        # Simular no Wokwi"
echo "  make monitor      # Monitor serial"
echo "  make help         # Ver todos os comandos"
