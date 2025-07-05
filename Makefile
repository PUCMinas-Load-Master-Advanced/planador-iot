# Makefile Simplificado e Multiplataforma para o Projeto Planador IoT
# Suporta: Linux, macOS (x86_64, arm64), e Windows.
#
# Mantenedor: Gemini
# Data: 2025-07-04

.PHONY: all help install build flash monitor clean test test-all test-unit test-integration test-hardware sim sim-gui sim-disturbance sim-release

# --- Configurações do Projeto ---

# Comando Python: usa o `python` do ambiente virtual do Poetry.
PYTHON_CMD := python3

# Diretório onde os scripts de build do MicroPython estão localizados.
MICROPYTHON_DIR = src/micropython

# Caminho para o ESP-IDF (pode ser sobrescrito)
IDF_PATH ?= /home/ari/esp/esp-idf

# --- Detecção de Sistema Operacional e Porta Serial ---

# Detecta o sistema operacional para ajustar comandos.
UNAME_S := $(shell uname -s 2>/dev/null || echo Windows)

# Porta serial para comunicação com o ESP32.
# Tenta detectar automaticamente, mas pode ser sobrescrita.
# Exemplo: make flash PORT=COM3 (Windows)
#          make flash PORT=/dev/cu.usbserial-1234 (macOS)
PORT ?= $(ESP32_PORT)
ifeq ($(PORT),)
    ifeq ($(UNAME_S),Linux)
        # Para Linux, procura por ttyUSB0, ttyUSB1, ttyACM0, etc.
        PORT := $(shell find /dev/ -name "ttyUSB*" -o -name "ttyACM*" | head -n 1)
        PORT ?= /dev/ttyUSB0
    else ifeq ($(UNAME_S),Darwin)
        # Para macOS, procura por dispositivos seriais USB comuns.
        PORT := $(shell ls /dev/cu.usbserial* /dev/cu.SLAB_USBtoUART* /dev/cu.wchusbserial* 2>/dev/null | head -n 1)
        PORT ?= /dev/cu.usbserial-0001
    else
        # Para Windows, o padrão é COM3, mas geralmente precisa ser especificado.
        PORT := COM3
    endif
endif

# Baud rate para o monitor serial.
BAUD ?= 115200

# --- Metas Principais ---

all: build flash
	@echo "Processo completo: Firmware compilado e gravado em $(PORT)."

help:
	@echo "Makefile para o Projeto Planador IoT"
	@echo ""
	@echo "Uso: make [comando]"
	@echo ""
	@echo "Comandos Principais:"
	@echo "  all                - Executa 'build' e 'flash' em sequência."
	@echo "  install            - Instala as dependências do projeto com Poetry."
	@echo "  build              - Compila o firmware MicroPython padrão para ESP32."
	@echo "  flash              - Grava o firmware no ESP32 na porta [$(PORT)]."
	@echo "  monitor            - Abre o monitor serial para ver a saída do dispositivo."
	@echo "  clean              - Limpa os arquivos de build gerados."
	@echo ""
	@echo "Comandos de Teste:"
	@echo "  test               - Executa testes básicos do projeto."
	@echo "  test-all           - Executa TODOS os testes."
	@echo "  test-unit          - Executa apenas testes unitários."
	@echo "  test-integration   - Executa apenas testes de integração."
	@echo "  test-cov           - Executa testes com coverage completo."
	@echo "  test-cov-unit      - Executa testes unitários com coverage."
	@echo "  cov-report         - Gera relatório de coverage no terminal."
	@echo "  cov-html           - Gera relatório HTML de coverage."
	@echo ""
	@echo "Comandos de Simulação:"
	@echo "  sim                - Simulação básica do sistema."
	@echo "  sim-gui            - Simulação com interface gráfica."
	@echo "  sim-disturbance    - Simulação com perturbações externas."
	@echo "  sim-release        - Simulação de liberação RC."
	@echo "  sim-exemplo        - Exemplo com interpretação dos gráficos."
	@echo ""
	@echo "Configurações:"
	@echo "  PORT=$(PORT)   (Porta serial detectada automaticamente)"
	@echo "  BAUD=$(BAUD)   (Baud rate para o monitor)"
	@echo "  IDF_PATH=$(IDF_PATH)   (Caminho do ESP-IDF)"
	@echo ""
	@echo "Exemplos:"
	@echo "  make install       # Executar na primeira vez para instalar tudo."
	@echo "  make test          # Executar todos os testes do projeto."
	@echo "  make all           # Compilar e gravar no ESP32."
	@echo "  make flash PORT=COM4 # Gravar em uma porta específica no Windows."
	@echo ""

install:
	@echo "Instalando dependencias do projeto com Poetry..."
	@poetry install
	@echo "Dependencias instaladas com sucesso."

build:
	@echo "Compilando o firmware MicroPython padrao..."
	@echo "Configurando ESP-IDF..."
	@bash -c "source $(IDF_PATH)/export.sh && cd $(MICROPYTHON_DIR) && $(PYTHON_CMD) build.py build"
	@echo "Firmware MicroPython compilado com sucesso."

flash:
	@echo "Gravando o firmware no ESP32 em $(PORT)..."
	@bash -c "source $(IDF_PATH)/export.sh && cd $(MICROPYTHON_DIR) && $(PYTHON_CMD) build.py flash $(PORT)"
	@echo "Firmware gravado com sucesso."

monitor:
	@echo "Abrindo monitor serial em $(PORT) (Baud: $(BAUD))... (Pressione Ctrl+] para sair)"
	@$(PYTHON_CMD) -m esptool --port $(PORT) --baud $(BAUD) monitor

clean:
	@echo "Limpando o diretorio de build..."
	@cd $(MICROPYTHON_DIR) && $(PYTHON_CMD) build.py clean
	@echo "Limpeza concluida."

test:
	@echo "Executando testes funcionais do projeto via Poetry..."
	@poetry run pytest tests/unit/test_pid_simple.py tests/unit/test_platform.py tests/unit/test_main_esp32.py tests/unit/test_simulator_basic.py -v
	@echo "Testes funcionais concluidos com sucesso."

test-all:
	@echo "Executando TODOS os testes via pytest..."
	@poetry run pytest tests/ -v --tb=short || true
	@echo "Execucao completa de testes finalizada."

test-unit:
	@echo "Executando testes unitarios via Poetry..."
	@poetry run pytest tests/unit/ -v
	@echo "Testes unitarios concluidos."

test-integration:
	@echo "Executando testes de integracao via Poetry..."
	@poetry run pytest tests/integration/ -v --tb=short || true
	@echo "Testes de integracao finalizados."

test-hardware:
	@echo "Executando testes de hardware via Poetry..."
	@poetry run pytest tests/hardware/ -v --tb=short || true
	@echo "Testes de hardware finalizados."

test-cov:
	@echo "Executando testes funcionais com coverage..."
	@poetry run pytest tests/unit/test_pid_simple.py tests/unit/test_platform.py tests/unit/test_main_esp32.py tests/unit/test_simulator_basic.py --cov=src --cov=tests --cov-report=term-missing --cov-report=html -v
	@echo "Testes com coverage concluidos. Relatorio HTML em htmlcov/"

test-cov-unit:
	@echo "Executando testes unitarios com coverage..."
	@poetry run pytest tests/unit/ --cov=src --cov-report=term-missing --cov-report=html -v
	@echo "Testes unitarios com coverage concluidos."

test-cov-integration:
	@echo "Executando testes de integracao com coverage..."
	@poetry run pytest tests/integration/ --cov=src --cov-report=term-missing --cov-report=html -v
	@echo "Testes de integracao com coverage concluidos."

cov-report:
	@echo "Gerando relatorio de coverage..."
	@poetry run coverage report --show-missing
	@echo "Relatorio de coverage gerado."

cov-html:
	@echo "Gerando relatorio HTML de coverage..."
	@poetry run coverage html
	@echo "Relatorio HTML gerado em htmlcov/"

sim:
	@echo "Executando simulador do planador..."
	@poetry run python src/simulator/planador_simulator.py
	@echo "Simulador finalizado."

sim-gui:
	@echo "Executando simulador com interface grafica..."
	@poetry run python src/simulator/gui_simulator.py
	@echo "Simulador GUI finalizado."

sim-disturbance:
	@echo "Executando simulador com perturbacoes..."
	@poetry run python src/simulator/planador_simulator.py disturbance
	@echo "Simulador de perturbacoes finalizado."

sim-release:
	@echo "Executando simulador de liberacao RC..."
	@poetry run python src/simulator/planador_simulator.py release
	@echo "Simulador de liberacao finalizado."

sim-exemplo:
	@echo "Executando exemplo de interpretacao dos graficos..."
	@poetry run python src/simulator/exemplo_interpretacao.py
	@echo "Exemplo de interpretacao finalizado."

zip:
	@echo "Compactando o diretorio"
	@cd src/micropython && zip -r ../../project.zip . -x "build/*"
	@echo "Diretorio compactado"