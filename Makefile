.PHONY: help setup install-python install-platformio install-rust install-all
.PHONY: build-cpp build-rust build-python flash-cpp flash-rust flash-micropython
.PHONY: python-monitor python-dashboard mqtt-client wokwi monitor clean check-deps

# Detectar sistema operacional
UNAME_S := $(shell uname -s)
ifeq ($(UNAME_S),Linux)
    PLATFORM = linux
endif
ifeq ($(UNAME_S),Darwin)
    PLATFORM = macos
endif
ifneq (,$(findstring MINGW,$(UNAME_S)))
    PLATFORM = windows
endif

# -------------------------------------------------------------------
# Detecção automática de porta ESP32
# Usa ESP32_PORT (exportado no entrypoint), senão detecta automaticamente
# Baud padrão: 115200. Pode ser sobrescrito via:
#    make PORT=/dev/ttyUSB1 BAUD=9600 flash-cpp
# -------------------------------------------------------------------
PORT ?= $(ESP32_PORT)
ifeq ($(PORT),)
  PORT = $(shell for p in /dev/ttyUSB0 /dev/ttyUSB1 /dev/ttyACM0 /dev/ttyACM1; do [ -e "$$p" ] && echo "$$p" && break; done)
endif
ifeq ($(PORT),)
  PORT = /dev/ttyUSB0
endif

BAUD ?= 115200

PYTHON_CMD := $(shell command -v python3 2>/dev/null || command -v python 2>/dev/null)

help:
	@echo "🚀 IoT Template - Setup Completo Multi-Linguagem"
	@echo ""
	@echo "📦 INSTALAÇÃO:"
	@echo "  setup              Instalar TUDO (recomendado)"
	@echo "  install-python     Instalar Python/pip"
	@echo "  install-platformio Instalar PlatformIO"
	@echo "  install-rust       Instalar Rust + ESP32 tools"
	@echo "  check-deps         Verificar dependências"
	@echo ""
	@echo "🔨 BUILD & FLASH:"
	@echo "  build-cpp          Build C++ project"
	@echo "  build-rust         Build Rust project"
	@echo "  build-python       Preparar ambiente Python"
	@echo "  flash-cpp          Build + Flash + Monitor C++"
	@echo "  flash-rust         Build + Flash Rust"
	@echo "  flash-micropython  Flash MicroPython firmware"
	@echo ""
	@echo "🐍 PYTHON APPS:"
	@echo "  python-monitor     Monitor serial Python"
	@echo "  python-dashboard   Dashboard web Streamlit"
	@echo "  mqtt-client        Cliente MQTT Python"
	@echo ""
	@echo "📡 HARDWARE:"
	@echo "  detect-port        Detectar ESP32 conectado"
	@echo "  monitor            Monitor serial"
	@echo ""
	@echo "🎮 SIMULAÇÃO:"
	@echo "  wokwi              Build + Instruções Wokwi"
	@echo "  clean              Limpar builds"

# ============= INSTALAÇÃO COMPLETA =============

setup: check-system install-python install-platformio
	@echo ""
	@echo "🎉 Setup completo! Agora você pode usar:"
	@echo "  make flash-cpp    # Para C++"
	@echo "  make flash-rust   # Para Rust"
	@echo "  make wokwi        # Para simulação"

check-system:
	@echo "🔍 Verificando sistema..."
	@echo "Platform: $(PLATFORM)"
	@echo "Python: $(PYTHON_CMD)"
	@if [ -z "$(PYTHON_CMD)" ]; then \
		echo "❌ Python não encontrado!"; \
		echo "Install Python 3.8+ primeiro:"; \
		echo "  Ubuntu/Debian: sudo apt install python3 python3-pip"; \
		echo "  macOS: brew install python3"; \
		echo "  Windows: https://python.org/downloads"; \
		exit 1; \
	fi
	@echo "✅ Sistema OK"

install-python:
	@echo "🐍 Configurando Python..."
	@if ! $(PYTHON_CMD) -m pip --version >/dev/null 2>&1; then \
		echo "📦 Instalando pip..."; \
		curl -sSL https://bootstrap.pypa.io/get-pip.py | $(PYTHON_CMD) --user; \
	fi
	@echo "✅ Python/pip configurado"

install-platformio: install-python
	@echo "🔧 Instalando PlatformIO..."
	@if ! command -v pio >/dev/null 2>&1; then \
		echo "📦 Instalando PlatformIO..."; \
		$(PYTHON_CMD) -m pip install --user platformio; \
		echo 'export PATH="$$HOME/.local/bin:$$PATH"' >> ~/.bashrc || true; \
		echo 'export PATH="$$HOME/.local/bin:$$PATH"' >> ~/.zshrc || true; \
		export PATH="$$HOME/.local/bin:$$$${PATH}"; \
	fi
	@echo "🔌 Instalando plataforma ESP32..."
	@if command -v pio >/dev/null 2>&1; then \
		pio platform install espressif32 || true; \
	elif command -v ~/.local/bin/pio >/dev/null 2>&1; then \
		~/.local/bin/pio platform install espressif32 || true; \
	else \
		$(PYTHON_CMD) -m platformio platform install espressif32 || true; \
	fi
	@echo "✅ PlatformIO instalado"

install-rust:
	@echo "🦀 Instalando Rust..."
	@if ! command -v rustc >/dev/null 2>&1; then \
		echo "📦 Instalando Rust..."; \
		curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y; \
		. ~/.cargo/env; \
	fi
	@echo "🎯 Instalando targets ESP32..."
	@. ~/.cargo/env && rustup target add xtensa-esp32-none-elf || true
	@echo "🔧 Instalando ferramentas ESP32..."
	@. ~/.cargo/env && cargo install ldproxy espflash espmonitor cargo-espflash || true
	@echo "✅ Rust + ESP32 instalado"

check-deps:
	@echo "🔍 Verificando dependências instaladas..."
	@echo -n "Python: "
	@$(PYTHON_CMD) --version 2>/dev/null || echo "❌ Não instalado"
	@echo -n "pip: "
	@$(PYTHON_CMD) -m pip --version 2>/dev/null || echo "❌ Não instalado"
	@echo -n "PlatformIO: "
	@if command -v pio >/dev/null 2>&1; then \
		pio --version; \
	elif command -v ~/.local/bin/pio >/dev/null 2>&1; then \
		~/.local/bin/pio --version; \
	elif $(PYTHON_CMD) -c "import platformio" 2>/dev/null; then \
		$(PYTHON_CMD) -m platformio --version; \
	else \
		echo "❌ Não instalado - execute 'make install-platformio'"; \
	fi
	@echo -n "Rust: "
	@if command -v rustc >/dev/null 2>&1; then \
		rustc --version; \
	else \
		echo "❌ Rust não instalado - execute 'make install-rust'"; \
	fi
	@echo -n "ESP32 Target: "
	@if rustup target list --installed 2>/dev/null | grep -q xtensa-esp32-none-elf; then \
		echo "✅ Instalado"; \
	else \
		echo "❌ Não instalado"; \
	fi

# ============= BUILD & FLASH =============

build-cpp:
	@echo "🔧 Building C++ project..."
	@if command -v pio >/dev/null 2>&1; then \
		pio run; \
	elif command -v ~/.local/bin/pio >/dev/null 2>&1; then \
		~/.local/bin/pio run; \
	else \
		$(PYTHON_CMD) -m platformio run; \
	fi
	@echo "✅ Build C++ concluído"
	@echo "📁 Arquivos gerados:"
	@echo "  .pio/build/esp32dev/firmware.elf"
	@echo "  .pio/build/esp32dev/firmware.bin"

build-rust:
	@echo "🦀 Building Rust project..."
	@if command -v cargo >/dev/null 2>&1; then \
		. ~/.cargo/env && cargo build --release; \
	else \
		echo "❌ Rust não encontrado - execute 'make install-rust'"; \
		exit 1; \
	fi
	@echo "✅ Build Rust concluído"

build-python:
	@echo "🐍 Preparando ambiente Python..."
	@if [ ! -d "venv" ]; then \
		echo "📦 Criando ambiente virtual..."; \
		$(PYTHON_CMD) -m venv venv; \
	fi
	@echo "📦 Instalando dependências Python..."
	@. venv/bin/activate && pip install -r src/python/requirements.txt
	@echo "✅ Ambiente Python configurado"

flash-cpp: build-cpp
	@echo "📤 Flashing C++ para ESP32..."
	@if [ ! -e "$(PORT)" ]; then \
		echo "❌ ESP32 não encontrado em $(PORT)"; \
		echo "🔍 Execute: ./detect-esp32.sh"; \
		echo "💡 Ou use: make PORT=/dev/ttyACM0 flash-cpp"; \
		echo "🎮 Ou simule: make wokwi"; \
		exit 1; \
	fi
	@echo "📡 Usando porta: $(PORT)"
	@if command -v pio >/dev/null 2>&1; then \
		pio run --target upload --upload-port $(PORT) && \
		echo "📟 Iniciando monitor ($(BAUD) bauds)..." && \
		pio device monitor --port $(PORT) --baud $(BAUD); \
	elif command -v ~/.local/bin/pio >/dev/null 2>&1; then \
		~/.local/bin/pio run --target upload --upload-port $(PORT) && \
		echo "📟 Iniciando monitor ($(BAUD) bauds)..." && \
		~/.local/bin/pio device monitor --port $(PORT) --baud $(BAUD); \
	else \
		$(PYTHON_CMD) -m platformio run --target upload --upload-port $(PORT) && \
		$(PYTHON_CMD) -m platformio device monitor --port $(PORT) --baud $(BAUD); \
	fi

flash-rust: build-rust
	@echo "📤 Flashing Rust para ESP32..."
	@if command -v cargo >/dev/null 2>&1; then \
		. ~/.cargo/env && cargo run --release; \
	else \
		echo "❌ Rust não encontrado"; \
		exit 1; \
	fi

flash-micropython:
	@echo "📤 Flashing MicroPython para ESP32 ($(PORT))..."
	@if command -v esptool.py >/dev/null 2>&1; then \
		echo "🔄 Apagando flash..."; \
		esptool.py --chip esp32 --port $(PORT) erase_flash; \
		echo "📦 Instalando MicroPython..."; \
		curl -fSL https://micropython.org/resources/firmware/ESP32_GENERIC-20250415-v1.25.0.bin -o /tmp/micropython-esp32.bin; \
		esptool.py --chip esp32 --port $(PORT) --baud 460800 write_flash -z 0x1000 /tmp/micropython-esp32.bin; \
		echo "✅ MicroPython instalado!"; \
	else \
		echo "❌ esptool.py não encontrado - execute 'make setup'"; \
		exit 1; \
	fi

python-monitor: build-python
	@echo "🐍 Iniciando monitor Python..."
	@. venv/bin/activate && python3 src/python/main.py --port $(PORT) --baud $(BAUD)

python-dashboard: build-python
	@echo "🌐 Iniciando dashboard web..."
	@echo "💡 Acesse: http://localhost:8501"
	@. venv/bin/activate && streamlit run src/python/web_dashboard.py --server.port 8501

mqtt-client: build-python
	@echo "📡 Iniciando cliente MQTT..."
	@. venv/bin/activate && python3 src/python/mqtt_client.py

detect-port:
	@echo "🔍 Detectando ESP32 conectado..."
	@FOUND=false; \
	for port in /dev/ttyUSB{0..3} /dev/ttyACM{0..3}; do \
		if [ -e "$$port" ]; then \
			echo "✅ ESP32 encontrado: $$port"; \
			FOUND=true; \
		fi; \
	done; \
	if [ "$$FOUND" = false ]; then \
		echo "❌ Nenhum ESP32 encontrado"; \
		echo "🔧 Soluções:"; \
		echo "  • Conectar ESP32 via USB"; \
		echo "  • Verificar cabo de dados"; \
		echo "  • Pressionar RESET no ESP32"; \
		echo "  • Executar: lsusb"; \
		echo "  • Usar simulação: make wokwi"; \
	fi

monitor:
	@echo "📟 Monitor serial..."
	@if [ ! -e "$(PORT)" ]; then \
		echo "❌ ESP32 não encontrado em $(PORT)"; \
		echo "🔍 Execute: ./detect-esp32.sh"; \
		echo "💡 Ou use: make PORT=/dev/ttyACM0 monitor"; \
		exit 1; \
	fi
	@echo "📡 Usando porta: $(PORT) @ $(BAUD) bauds"
	@if command -v pio >/dev/null 2>&1; then \
		pio device monitor --port $(PORT) --baud $(BAUD); \
	elif command -v ~/.local/bin/pio >/dev/null 2>&1; then \
		~/.local/bin/pio device monitor --port $(PORT) --baud $(BAUD); \
	elif command -v screen >/dev/null 2>&1; then \
		screen $(PORT) $(BAUD); \
	else \
		echo "❌ Nenhum monitor disponível"; \
	fi

# ============= WOKWI =============

wokwi: build-cpp
	@echo "🎮 Preparando para simulação Wokwi..."
	@echo ""
	@echo "✅ Build concluído! Arquivos prontos:"
	@echo "  📁 .pio/build/esp32dev/firmware.elf"
	@echo "  📁 .pio/build/esp32dev/firmware.bin"
	@echo ""
	@echo "🌐 Para simular no Wokwi:"
	@echo "  1. Vá para: https://wokwi.com/projects/new/esp32"
	@echo "  2. Substitua sketch.ino por: src/cpp/main.cpp"
	@echo "  3. Substitua diagram.json por: diagram.json (raiz do projeto)"
	@echo "  4. Clique 'Start Simulation'"
	@echo ""
	@echo "📋 Ou use extensão VSCode 'Wokwi Simulator'"

# ============= LIMPEZA =============

clean:
	@echo "🧹 Limpando arquivos de build..."
	@rm -rf .pio build target
	@rm -f *.tmp *.log
	@echo "✅ Limpeza concluída"

# ============= ATALHOS =============

cpp: flash-cpp
rust: flash-rust
python: python-monitor
micropython: flash-micropython
dashboard: python-dashboard
mqtt: mqtt-client
sim: wokwi
deps: check-deps
install: setup
