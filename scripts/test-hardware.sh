#!/bin/bash

echo "🔧 Teste de Hardware ESP32"
echo "=========================="

# Verificar porta serial
echo "📡 Procurando ESP32..."

PORTS=()
if [ -e /dev/ttyUSB0 ]; then PORTS+=("/dev/ttyUSB0"); fi
if [ -e /dev/ttyUSB1 ]; then PORTS+=("/dev/ttyUSB1"); fi
if [ -e /dev/ttyACM0 ]; then PORTS+=("/dev/ttyACM0"); fi
if [ -e /dev/cu.usbserial* ]; then PORTS+=(/dev/cu.usbserial*); fi

if [ ${#PORTS[@]} -eq 0 ]; then
    echo "❌ Nenhuma porta serial encontrada"
    echo "Conecte o ESP32 via USB"
    exit 1
fi

echo "✅ Portas encontradas:"
for port in "${PORTS[@]}"; do
    echo "  $port"
done

PORT=${PORTS[0]}
echo "🔌 Usando porta: $PORT"

# Testar conexão
echo "📋 Testando conexão..."
if command -v esptool.py >/dev/null 2>&1; then
    esptool.py --port $PORT chip_id
elif command -v pio >/dev/null 2>&1; then
    pio run --target upload --upload-port $PORT
else
    echo "❌ Ferramentas ESP32 não encontradas"
    echo "Execute: make setup"
    exit 1
fi

echo "✅ Hardware ESP32 OK!"
