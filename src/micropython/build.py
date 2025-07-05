#!/usr/bin/env python3
"""
Script de Build - MicroPython ESP32

Compila o firmware MicroPython padrão para ESP32.
"""

import os
import shutil
import subprocess
import sys
import re
from pathlib import Path
import logging


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

MICROPYTHON_REPO = "https://github.com/micropython/micropython.git"
ESP_IDF_VERSION = "v4.4.4"
PROJECT_NAME = "planador_esp32"


def setup_build_environment():
    """Configura o ambiente de build, clonando o repositorio MicroPython se necessario."""
    logger.info("Configurando ambiente de build...")
    build_dir = Path("build")
    build_dir.mkdir(exist_ok=True)
    mp_dir = build_dir / "micropython"
    if not mp_dir.exists():
        logger.info("Clonando MicroPython...")
        subprocess.run([
            "git", "clone", "--recursive", 
            MICROPYTHON_REPO, str(mp_dir)
        ], check=True)
    return mp_dir


def check_esp_idf():
    """Verifica se o ESP-IDF esta configurado corretamente no ambiente."""
    logger.info("Verificando ESP-IDF...")
    idf_path = os.environ.get('IDF_PATH')
    if not idf_path:
        logger.error("IDF_PATH nao definido.")
        return False
    logger.info(f"IDF_PATH: {idf_path}")
    try:
        result = subprocess.run(['idf.py', '--version'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            logger.info(f"idf.py: {result.stdout.strip()}")
            return True
        else:
            logger.error("idf.py nao funcional.")
            return False
    except (FileNotFoundError, subprocess.TimeoutExpired):
        logger.error("idf.py nao encontrado.")
        return False


def get_project_modules(source_dir=None):
    """Descobre automaticamente os modulos Python do projeto a serem incluidos no firmware.

    Args:
        source_dir (Path, optional): Diretorio onde procurar os modulos. Padrao e o diretorio atual.

    Returns:
        list: Uma lista de nomes de arquivos .py encontrados, excluindo scripts de build.
    """
    if source_dir is None:
        source_dir = Path(".")
    else:
        source_dir = Path(source_dir)
    logger.info(f"Procurando modulos em: {source_dir.absolute()}")
    exclude_files = {
        'build_frozen.py', 'compile_mpy.py', 'compile_nuitka.py', 
        'benchmark_performance.py', 'hardware_test.py',
        'config_minimal.py', 'generic_pid.py', 'hybrid_system.py',
        'upload_mpy.py', 'build.py' # Excluir o proprio script de build
    }
    project_modules = []
    for py_file in source_dir.glob("*.py"):
        if py_file.name not in exclude_files:
            project_modules.append(py_file.name)
    project_modules.sort()
    logger.info(f"Modulos detectados: {len(project_modules)}")
    for module in project_modules:
        logger.info(f"  - {module}")
    return project_modules


def analyze_dependencies(modules):
    """Analisa as dependencias dos modulos para inclusao no manifest."

    Args:
        modules (list): Lista de nomes de modulos Python do projeto.

    Returns:
        dict: Dicionario contendo dependencias MicroPython e locais.
    """
    logger.info("Analisando dependencias...")
    micropython_imports = set()
    local_imports = set()
    for module in modules:
        module_path = Path(module)
        if not module_path.exists():
            continue
        try:
            with open(module_path, 'r') as f:
                content = f.read()
            mp_patterns = [
                r'from machine import',
                r'import machine',
                r'import micropython',
                r'from micropython import',
                r'import gc',
                r'import time'
            ]
            for pattern in mp_patterns:
                if re.search(pattern, content):
                    micropython_imports.add(pattern.split()[-1])
            local_patterns = [
                r'from (\w+) import',
                r'import (\w+)'
            ]
            for pattern in local_patterns:
                matches = re.findall(pattern, content)
                for match in matches:
                    if f"{match}.py" in modules:
                        local_imports.add(match)
        except Exception as e:
            logger.warning(f"Erro analisando {module}: {e}")
    logger.info(f"Dependencias MicroPython: {sorted(micropython_imports)}")
    logger.info(f"Dependencias locais: {sorted(local_imports)}")
    return {
        'micropython': sorted(micropython_imports),
        'local': sorted(local_imports)
    }


def prepare_frozen_modules(mp_dir, project_source_dir=None):
    """Prepara os modulos do projeto para serem 'frozen' no firmware MicroPython."

    Copia os modulos para o diretorio de 'frozen modules' do MicroPython
    e gera o arquivo manifest.py.

    Args:
        mp_dir (Path): Caminho para o diretorio raiz do repositorio MicroPython.
        project_source_dir (Path, optional): Diretorio contendo os modulos do projeto.
                                             Padrao e o diretorio atual.

    Returns:
        tuple: Uma tupla contendo (lista_de_modulos_copiados, dependencias_analisadas).
    """
    logger.info("Preparando modulos frozen...")
    original_dir = os.getcwd()
    if project_source_dir is None:
        project_source_dir = original_dir
    frozen_dir = mp_dir / "ports" / "esp32" / "modules"
    frozen_dir.mkdir(exist_ok=True)
    os.chdir(project_source_dir)
    our_modules = get_project_modules()
    deps = analyze_dependencies(our_modules)
    source_dir = Path(".")
    copied_modules = []
    for module in our_modules:
        source_file = source_dir / module
        if source_file.exists():
            target_file = frozen_dir / module
            shutil.copy2(source_file, target_file)
            logger.info(f"  - {module} copiado.")
            copied_modules.append(module)
        else:
            logger.warning(f"  - {module} nao encontrado em {source_file.absolute()}.")
    os.chdir(original_dir)
    create_manifest(frozen_dir, copied_modules, deps)
    logger.info("Modulos preparados para frozen build.")
    return copied_modules, deps


def create_manifest(frozen_dir, modules, deps):
    """Cria o arquivo manifest.py dinamicamente para o build do MicroPython."

    Este arquivo lista os modulos Python que serao 'frozen' no firmware.

    Args:
        frozen_dir (Path): Diretorio onde o manifest.py sera criado.
        modules (list): Lista de nomes de modulos a serem incluidos.
        deps (dict): Dicionario de dependencias analisadas.
    """
    logger.info("Gerando manifest.py...")
    module_list = ',\n    '.join([f'"{module}"' for module in modules])
    has_asyncio = any('async' in module.lower() for module in modules)
    has_network = any(
        ('network' in dep.lower()) or ('wifi' in dep.lower())
        for dep in deps['micropython']
    )
    manifest_content = f'''# Manifest automatizado para modulos frozen\n# Gerado em: {subprocess.check_output(['date'], text=True).strip()}\n# Modulos: {len(modules)} encontrados\n\n# Modulos padrao do MicroPython sempre incluidos\ninclude("$(MPY_DIR)/extmod/webrepl/manifest.py")\n'''
    if has_asyncio:
        manifest_content += '''\n# AsyncIO (detectado uso de async/await)\ninclude("$(MPY_DIR)/extmod/uasyncio/manifest.py")\n'''
    if has_network:
        manifest_content += '''\n# Networking (detectado uso de network/wifi)\ninclude("$(MPY_DIR)/extmod/urequests/manifest.py")\n'''
    manifest_content += f'''\n# Nossos modulos do planador ({len(modules)} modulos)\nfreeze(".", (\n    {module_list}\n))\n\n# Bibliotecas MicroPython detectadas:\n# {", ".join(deps['micropython']) if deps['micropython'] else "Nenhuma especifica"}\n\n# Dependencias locais:\n# {", ".join(deps['local']) if deps['local'] else "Nenhuma"}\n'''
    with open(frozen_dir / "manifest.py", "w") as f:
        f.write(manifest_content)
    logger.info(f"Manifest criado com {len(modules)} modulos.")
    logger.info("Conteudo do manifest:")
    logger.info("=" * 40)
    logger.info(manifest_content)
    logger.info("=" * 40)


def create_custom_board():
    """Cria a configuracao de board customizada para o ESP32 no MicroPython."""
    logger.info("Criando board customizado...")
    mp_dir = setup_build_environment()
    boards_dir = mp_dir / "ports" / "esp32" / "boards"
    custom_board_dir = boards_dir / "PLANADOR_ESP32"
    custom_board_dir.mkdir(exist_ok=True)
    mpconfigboard_h = f'''\n// Configuracao customizada para Planador ESP32\n#define MICROPY_HW_BOARD_NAME "Planador ESP32"\n#define MICROPY_HW_MCU_NAME "ESP32"\n\n// Configuracoes de memoria otimizadas\n#define MICROPY_ALLOC_PATH_MAX      (128)\n\n// Habilitar modulos necessarios\n#define MICROPY_PY_MACHINE_PWM      (1)\n#define MICROPY_PY_MACHINE_I2C      (1)\n#define MICROPY_PY_MACHINE_SPI      (1)\n\n// Otimizacoes de performance\n#define MICROPY_OPT_COMPUTED_GOTO   (1)\n#define MICROPY_COMP_CONST_FOLDING  (1)\n'''
    with open(custom_board_dir / "mpconfigboard.h", "w") as f:
        f.write(mpconfigboard_h)
    mpconfigboard_cmake = '''\nset(IDF_TARGET esp32)\n\nset(SDKCONFIG_DEFAULTS\n    boards/sdkconfig.base\n    boards/sdkconfig.ble\n    boards/planador_sdkconfig\n)\n'''
    with open(custom_board_dir / "mpconfigboard.cmake", "w") as f:
        f.write(mpconfigboard_cmake)
    planador_sdkconfig = '''\n# Configuracoes otimizadas para Planador ESP32\n\n# Otimizacoes de CPU\nCONFIG_FREERTOS_HZ=1000\nCONFIG_ESP32_DEFAULT_CPU_FREQ_MHZ_240=y\n\n# Otimizacoes de memoria\nCONFIG_SPIRAM_SUPPORT=y\nCONFIG_SPIRAM_USE_MALLOC=y\nCONFIG_SPIRAM_MALLOC_ALWAYSINTERNAL=16384\n\n# Otimizacoes de flash\nCONFIG_ESPTOOLPY_FLASHMODE_QIO=y\nCONFIG_ESPTOOLPY_FLASHFREQ_80M=y\n\n# Otimizacoes de rede (desabilitar se nao usar)\nCONFIG_ESP_WIFI_ENABLED=n\nCONFIG_BT_ENABLED=n\n\n# Log otimizado\nCONFIG_LOG_DEFAULT_LEVEL_INFO=y\nCONFIG_LOG_COLORS=n\n'''
    with open(boards_dir / "planador_sdkconfig", "w") as f:
        f.write(planador_sdkconfig)
    logger.info("Board customizado criado.")
    return custom_board_dir




def build_firmware():
    """Compila o firmware MicroPython padrao para ESP32.

    Returns:
        Path: O caminho para o arquivo de firmware gerado, ou None em caso de falha.
    """
    logger.info("Compilando firmware MicroPython...")
    original_dir = os.getcwd()
    mp_dir = setup_build_environment()
    
    if not check_esp_idf():
        logger.error("ESP-IDF nao configurado. Configure primeiro:")
        logger.error("  1. Instale ESP-IDF: https://docs.espressif.com/projects/esp-idf/en/latest/esp32/get-started/")
        logger.error("  2. Execute: source $IDF_PATH/export.sh")
        return None
    
    esp32_dir = mp_dir / "ports" / "esp32"
    os.chdir(esp32_dir)
    
    # Limpar builds anteriores
    subprocess.run(["make", "clean", "BOARD=ESP32_GENERIC"], capture_output=True)
    
    logger.info("Configurando ESP-IDF...")
    subprocess.run(["make", "submodules"], check=True)
    
    logger.info("Iniciando compilacao (isso pode demorar...)...")
    build_cmd = [
        "make", 
        "BOARD=ESP32_GENERIC",
        "-j4"
    ]
    
    try:
        result = subprocess.run(build_cmd, check=True, capture_output=True, text=True)
        logger.info("Firmware MicroPython compilado com sucesso!")
        firmware_file = Path("build-ESP32_GENERIC") / "firmware.bin"
        if firmware_file.exists():
            logger.info(f"Firmware gerado: {firmware_file}")
            return firmware_file
        else:
            logger.error(f"Arquivo de firmware nao encontrado em: {firmware_file.absolute()}")
            logger.info("Listando arquivos no diretorio de build...")
            build_dir = Path("build-ESP32_GENERIC")
            logger.info(f"Procurando em: {build_dir.absolute()}")
            if build_dir.exists():
                for file in build_dir.glob("*.bin"):
                    logger.info(f"  - {file}")
            else:
                logger.error(f"Diretorio de build nao existe: {build_dir.absolute()}")
            return None
    except subprocess.CalledProcessError as e:
        logger.error(f"Erro na compilacao: {e}")
        logger.error(f"stdout: {e.stdout}")
        logger.error(f"stderr: {e.stderr}")
        return None
    finally:
        os.chdir(original_dir)


def flash_firmware(firmware_file, port="/dev/ttyUSB0"):
    """Grava o firmware compilado no ESP32."

    Args:
        firmware_file (Path): Caminho para o arquivo .bin do firmware.
        port (str, optional): Porta serial do ESP32. Padrao e "/dev/ttyUSB0".

    Returns:
        bool: True se o flash for bem-sucedido, False caso contrario.
    """
    if not firmware_file or not firmware_file.exists():
        logger.error("Firmware nao encontrado para flash.")
        return False
    logger.info(f"Iniciando flash no ESP32 ({port})...")
    try:
        flash_cmd = [
            "esptool.py",
            "--chip", "esp32",
            "--port", port,
            "--baud", "921600",
            "write_flash",
            "-z",
            "0x1000", str(firmware_file)
        ]
        subprocess.run(flash_cmd, check=True)
        logger.info("Flash concluido com sucesso!")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Erro no flash: {e}")
        return False


def main():
    """Funcao principal para executar as operacoes de build e flash."""
    logger.info("Iniciando build do MicroPython ESP32.")
    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == "build":
            firmware = build_firmware()
            if firmware:
                logger.info(f"Build concluido: {firmware}")
        elif command == "flash":
            port = sys.argv[2] if len(sys.argv) > 2 else "/dev/ttyUSB0"
            firmware = Path("build/micropython/ports/esp32/build-ESP32_GENERIC/firmware.bin")
            flash_firmware(firmware, port)
        elif command == "clean":
            shutil.rmtree("build", ignore_errors=True)
            logger.info("Diretorio de build limpo.")
        else:
            logger.info("Comando invalido. Use: build, flash [porta], ou clean.")
    else:
        logger.info("Uso: python build.py [build|flash|clean]")
        logger.info("Comandos:")
        logger.info("  build          - Compila firmware MicroPython padrao.")
        logger.info("  flash [porta]  - Grava o firmware (padrao: /dev/ttyUSB0).")
        logger.info("  clean          - Limpa o diretorio de build.")


if __name__ == "__main__":
    main()
