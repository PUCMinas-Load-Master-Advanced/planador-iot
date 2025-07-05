#!/usr/bin/env python3
"""
Configura o ambiente de compilacao para o ESP32 com MicroPython.

Este script automatiza a verificacao de requisitos do sistema e a instalacao
do ESP-IDF, alem de criar scripts auxiliares para o processo de build.
"""

import os
import subprocess
import sys
from pathlib import Path
import shutil
import logging


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)


def check_system_requirements():
    """Verifica se as ferramentas necessarias para o build estao instaladas no sistema."""
    logger.info("Verificando requisitos do sistema...")
    required_tools = [
        ('git', 'git --version'),
        ('python3', 'python3 --version'),
        ('cmake', 'cmake --version'),
        ('ninja', 'ninja --version')
    ]
    missing_tools = []
    for tool, cmd in required_tools:
        try:
            result = subprocess.run(cmd.split(), capture_output=True, text=True)
            if result.returncode == 0:
                version = result.stdout.strip().split('\n')[0]
                logger.info(f"  - {tool}: {version}")
            else:
                missing_tools.append(tool)
        except FileNotFoundError:
            missing_tools.append(tool)
            logger.error(f"  - {tool}: nao encontrado.")
    if missing_tools:
        logger.error(f"Instale as ferramentas ausentes: {', '.join(missing_tools)}")
        logger.info("Sugestao para Ubuntu/Debian: sudo apt install git python3 cmake ninja-build")
        return False
    return True


def install_esp_idf():
    """Instala o ESP-IDF no diretorio padrao do usuario (~/esp/esp-idf)."""
    logger.info("Configurando ESP-IDF...")
    esp_dir = Path.home() / "esp"
    esp_dir.mkdir(exist_ok=True)
    idf_dir = esp_dir / "esp-idf"
    if idf_dir.exists():
        logger.info(f"ESP-IDF ja existe em: {idf_dir}")
    else:
        logger.info("Clonando ESP-IDF...")
        try:
            subprocess.run([
                "git", "clone", "--recursive", "--depth", "1",
                "--branch", "v4.4.4",
                "https://github.com/espressif/esp-idf.git",
                str(idf_dir)
            ], check=True)
            logger.info("ESP-IDF clonado com sucesso.")
        except subprocess.CalledProcessError as e:
            logger.error(f"Erro clonando ESP-IDF: {e}")
            return False
    logger.info("Instalando ferramentas ESP-IDF...")
    try:
        install_script = idf_dir / "install.sh"
        if install_script.exists():
            subprocess.run([str(install_script), "esp32"], check=True, cwd=idf_dir)
            logger.info("Ferramentas ESP-IDF instaladas com sucesso.")
        else:
            logger.error("Script de instalacao do ESP-IDF nao encontrado.")
            return False
    except subprocess.CalledProcessError as e:
        logger.error(f"Erro instalando ferramentas ESP-IDF: {e}")
        return False
    return idf_dir


def create_env_script(idf_dir):
    """Cria um script shell para configurar as variaveis de ambiente do ESP-IDF."""
    logger.info("Criando script de ambiente...")
    env_script = Path("setup_esp_env.sh")
    script_content = f'''#!/bin/bash
# Script de configuracao do ambiente ESP-IDF
# Gerado automaticamente em {subprocess.check_output(['date'], text=True).strip()}

echo "Configurando ambiente ESP-IDF..."

export IDF_PATH="{idf_dir}"
source "$IDF_PATH/export.sh"

echo "Ambiente ESP-IDF configurado!"
echo "IDF_PATH: $IDF_PATH"
echo "idf.py version: $(idf.py --version)"

build_planador() {{
    echo "Compilando firmware do planador..."
    python3 build.py build
}}

flash_planador() {{
    local port="${{1:-/dev/ttyUSB0}}"
    echo "Gravando firmware no ESP32 ($port)..."
    python3 build.py flash "$port"
}}

echo ""
echo "Comandos disponiveis:"
echo "  build_planador  - Compila firmware"
echo "  flash_planador  - Grava firmware no ESP32"
echo ""
'''
    with open(env_script, 'w') as f:
        f.write(script_content)
    os.chmod(env_script, 0o755)
    logger.info(f"Script de ambiente criado: {env_script}")
    return env_script


def create_simplified_build():
    """Cria um script de build simplificado que nao requer o ESP-IDF completo."""
    logger.info("Criando build simplificado...")
    simplified_content = '''#!/usr/bin/env python3
"""
Build Simplificado - Apenas preparacao de modulos

Este script prepara os modulos Python para serem 'frozen', mas nao realiza
a compilacao completa do firmware, que requer o ESP-IDF.
"""

import os
import shutil
from pathlib import Path
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

def prepare_modules_only():
    """Prepara os modulos do projeto sem compilar o firmware."""
    logger.info("Preparacao de modulos (sem compilacao)...")
    exclude_files = {
        'build.py', 'compile_mpy.py', 'compile_nuitka.py', 
        'benchmark_performance.py', 'hardware_test.py',
        'config_minimal.py', 'setup_build_env.py', 'generic_pid.py', 'hybrid_system.py', 'upload_mpy.py'
    }
    modules = []
    for py_file in Path(".").glob("*.py"):
        if py_file.name not in exclude_files:
            modules.append(py_file.name)
    modules.sort()
    logger.info(f"Modulos encontrados: {len(modules)}")
    for module in modules:
        logger.info(f"  - {module}")
    prep_dir = Path("prepared_modules")
    prep_dir.mkdir(exist_ok=True)
    for module in modules:
        shutil.copy2(module, prep_dir / module)
        logger.info(f"  - {module} copiado.")
    manifest_content = f"""# Manifest para {len(modules)} modulos\nfreeze(".", (\n{chr(10).join(f'    "{module}",' for module in modules)}\n))\n"""
    with open(prep_dir / "manifest.py", "w") as f:
        f.write(manifest_content)
    logger.info(f"Modulos preparados em: {prep_dir}")
    logger.info("Para compilar, configure o ESP-IDF e execute: python build.py build")

if __name__ == "__main__":
    prepare_modules_only()
'''
    with open("build_simple.py", 'w') as f:
        f.write(simplified_content)
    os.chmod("build_simple.py", 0o755)
    logger.info("Script build_simple.py criado.")


def main():
    """Funcao principal para configurar o ambiente de build do ESP32."""
    logger.info("Iniciando configuracao do ambiente de build do ESP32.")
    if not check_system_requirements():
        return
    choice = input("Instalar ESP-IDF completo? (s/N): ").lower().strip()
    if choice in ['s', 'sim', 'y', 'yes']:
        idf_dir = install_esp_idf()
        if idf_dir:
            env_script = create_env_script(idf_dir)
            logger.info("Configuracao completa do ambiente de build concluida.")
            logger.info(f"Para usar, execute: source {env_script}")
            logger.info("Em seguida, compile o projeto com: python build.py build")
        else:
            create_simplified_build()
            logger.warning("Instalacao do ESP-IDF falhou, configurando build simplificado.")
    else:
        create_simplified_build()
        logger.info("Build simplificado configurado.")
        logger.info("Use: python build_simple.py para preparar os modulos.")


if __name__ == "__main__":
    main()
