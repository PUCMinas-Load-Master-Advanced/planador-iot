#!/usr/bin/env python3
"""
Script de configuracao simples para o sistema do planador ESP32.

Este script auxilia na instalacao das ferramentas essenciais para compilar
e gravar o firmware no ESP32, como esptool e ferramentas de build.
"""

import subprocess
import sys
import platform
import os
import logging


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)


def install_esptool():
    """Instala a ferramenta esptool via pip, necessaria para gravar o firmware."""
    logger.info("Instalando esptool...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "esptool"], check=True)
        logger.info("esptool instalado com sucesso.")
        return True
    except subprocess.CalledProcessError:
        logger.error("Falha ao instalar esptool.")
        return False


def check_git():
    """Verifica se o Git esta disponivel no sistema."

    Retorna:
        bool: True se o Git for encontrado, False caso contrario.
    """
    try:
        subprocess.run(["git", "--version"], capture_output=True, check=True)
        logger.info("Git disponivel.")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        logger.error("Git nao encontrado.")
        logger.info("Por favor, instale o Git primeiro. Sugestoes:")
        if platform.system() == "Darwin":
            logger.info("  - macOS: brew install git")
        elif platform.system() == "Linux":
            logger.info("  - Linux: sudo apt install git")
        else:
            logger.info("  - Windows: Baixe em https://git-scm.com/download")
        return False


def check_build_tools():
    """Verifica a disponibilidade de ferramentas de build essenciais para o sistema operacional."

    Retorna:
        bool: True se as ferramentas forem encontradas, False caso contrario.
    """
    system = platform.system()
    if system == "Darwin":
        logger.info("macOS detectado.")
        try:
            subprocess.run(["xcode-select", "--version"], capture_output=True, check=True)
            logger.info("Xcode Command Line Tools disponiveis.")
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.error("Xcode Command Line Tools necessarios.")
            logger.info("Execute: xcode-select --install")
            return False
    elif system == "Linux":
        logger.info("Linux detectado.")
        try:
            subprocess.run(["gcc", "--version"], capture_output=True, check=True)
            logger.info("GCC disponivel.")
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.error("Ferramentas de build (build-essential) necessarias.")
            logger.info("Execute: sudo apt install build-essential")
            return False
    else:
        logger.info("Windows detectado.")
        logger.warning("Para Windows, e recomendado usar WSL2 com Ubuntu para o ambiente de desenvolvimento.")
        return True


def install_esp_idf():
    """Fornece instrucoes para a instalacao manual do ESP-IDF, necessario para a compilacao do firmware."""
    logger.info("ESP-IDF e necessario para a compilacao do firmware.")
    logger.info("Por favor, siga as instrucoes abaixo para instalar o ESP-IDF:")
    system = platform.system()
    if system == "Darwin":
        logger.info("Instalacao no macOS:")
        logger.info("1. brew install cmake ninja")
        logger.info("2. mkdir -p ~/esp && cd ~/esp")
        logger.info("3. git clone --recursive https://github.com/espressif/esp-idf.git")
        logger.info("4. cd esp-idf && ./install.sh esp32")
        logger.info("5. source ./export.sh")
        logger.info("6. Adicione 'source ~/esp/esp-idf/export.sh' ao seu ~/.zshrc")
    elif system == "Linux":
        logger.info("Instalacao no Linux:")
        logger.info("1. sudo apt update")
        logger.info("2. sudo apt install git wget flex bison gperf python3-pip cmake ninja-build")
        logger.info("3. mkdir -p ~/esp && cd ~/esp")
        logger.info("4. git clone --recursive https://github.com/espressif/esp-idf.git")
        logger.info("5. cd esp-idf && ./install.sh esp32")
        logger.info("6. source ./export.sh")
        logger.info("7. Adicione 'source ~/esp/esp-idf/export.sh' ao seu ~/.bashrc")
    else:
        logger.info("Instalacao no Windows:")
        logger.info("1. Use o instalador de ferramentas do ESP-IDF: https://docs.espressif.com/projects/esp-idf/en/latest/esp32/get-started/windows-setup.html")
        logger.info("2. Alternativamente, use WSL2 com Ubuntu e siga os passos para Linux.")
    logger.info("Apos instalar o ESP-IDF, execute 'source ~/esp/esp-idf/export.sh' em cada nova sessao do terminal antes de compilar o projeto.")
    logger.info("Em seguida, voce pode compilar o projeto com: python build.py build")


def main():
    """Funcao principal para executar o processo de configuracao do ambiente."""
    logger.info("Iniciando configuracao do Planador ESP32.")
    logger.info(f"Versao do Python: {sys.version}")
    success = True
    if not check_git():
        success = False
    if not check_build_tools():
        success = False
    if not install_esptool():
        success = False
    if success:
        logger.info("Configuracao basica concluida com sucesso.")
        install_esp_idf()
    else:
        logger.error("Por favor, resolva os problemas acima antes de continuar.")


if __name__ == "__main__":
    main()
