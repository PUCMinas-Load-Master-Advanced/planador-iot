#!/usr/bin/env python3
"""
Instalacao de Ferramentas de Desenvolvimento - Multiplataforma

Este script instala as ferramentas necessarias para o desenvolvimento
em ambientes Windows, macOS e Linux, garantindo que o ambiente esteja
pronto para trabalhar com o ESP32 e MicroPython.
"""

import subprocess
import sys
import os
import platform
from pathlib import Path
from detect_platform import PlatformDetector
import logging


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)


def check_python_version():
    """Verifica se a versao do Python instalada e compativel (3.7+)."""
    logger.info("Verificando versao do Python...")
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 7):
        logger.error(f"Python {version.major}.{version.minor} e muito antigo. Requer Python 3.7+")
        return False
    logger.info(f"Python {version.major}.{version.minor}.{version.micro} detectado.")
    return True


def install_pip_package(package, python_cmd="python3"):
    """Instala um pacote Python usando pip."

    Args:
        package (str): O nome do pacote a ser instalado.
        python_cmd (str, optional): O comando Python a ser usado. Padrao e "python3".

    Returns:
        bool: True se a instalacao for bem-sucedida, False caso contrario.
    """
    try:
        logger.info(f"Instalando {package}...")
        subprocess.run([
            python_cmd, "-m", "pip", "install", "--user", package
        ], check=True, capture_output=True)
        logger.info(f"{package} instalado com sucesso.")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Erro ao instalar {package}: {e}")
        return False


def install_system_dependencies(detector):
    """Instala as dependencias de sistema especificas para a plataforma detectada."""
    platform_name = detector.platform_info['platform']
    logger.info(f"Instalando dependencias do sistema ({platform_name})...")
    if platform_name == 'macos':
        return install_macos_dependencies(detector)
    elif platform_name == 'linux':
        return install_linux_dependencies(detector)
    elif platform_name == 'windows':
        return install_windows_dependencies(detector)
    else:
        logger.error("Plataforma nao suportada para instalacao de dependencias.")
        return False


def install_macos_dependencies(detector):
    """Instala dependencias de sistema no macOS usando Homebrew."""
    if not detector.platform_info['brew_available']:
        logger.info("Instalando Homebrew...")
        try:
            subprocess.run([
                '/bin/bash', '-c',
                '$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)'
            ], check=True)
            logger.info("Homebrew instalado com sucesso.")
        except subprocess.CalledProcessError:
            logger.error("Falha ao instalar Homebrew.")
            return False
    deps = ['python3', 'git', 'cmake', 'ninja']
    for dep in deps:
        try:
            logger.info(f"Instalando {dep}...")
            subprocess.run(['brew', 'install', dep], check=True, capture_output=True)
            logger.info(f"{dep} instalado com sucesso.")
        except subprocess.CalledProcessError:
            logger.warning(f"{dep} ja instalado ou falha na instalacao.")
    return True


def install_linux_dependencies(detector):
    """Instala dependencias de sistema no Linux usando o gerenciador de pacotes apropriado."""
    distro = detector.platform_info.get('distro', 'ubuntu')
    if distro in ['ubuntu', 'debian']:
        logger.info("Instalando dependencias para Ubuntu/Debian...")
        try:
            subprocess.run(['sudo', 'apt', 'update'], check=True)
            subprocess.run([
                'sudo', 'apt', 'install', '-y',
                'python3', 'python3-pip', 'python3-venv',
                'git', 'cmake', 'ninja-build', 'build-essential'
            ], check=True)
            logger.info("Dependencias instaladas com sucesso.")
        except subprocess.CalledProcessError:
            logger.error("Falha ao instalar dependencias.")
            return False
    elif distro in ['fedora', 'rhel', 'centos']:
        logger.info("Instalando dependencias para Fedora/RHEL...")
        try:
            subprocess.run([
                'sudo', 'dnf', 'install', '-y',
                'python3', 'python3-pip', 'git', 'cmake', 'ninja-build', 'gcc', 'gcc-c++'
            ], check=True)
            logger.info("Dependencias instaladas com sucesso.")
        except subprocess.CalledProcessError:
            logger.error("Falha ao instalar dependencias.")
            return False
    try:
        subprocess.run(['sudo', 'usermod', '-a', '-G', 'dialout', os.getenv('USER')], check=True)
        logger.info("Usuario adicionado ao grupo dialout. Faca logout/login para aplicar permissoes.")
    except subprocess.CalledProcessError:
        logger.warning("Nao foi possivel configurar permissoes seriais.")
    return True


def install_windows_dependencies(detector):
    """Verifica e orienta sobre a instalacao de dependencias no Windows."""
    logger.info("Verificando dependencias no Windows...")
    try:
        result = subprocess.run(['python', '--version'], capture_output=True, text=True)
        logger.info(f"Python detectado: {result.stdout.strip()}")
    except FileNotFoundError:
        logger.error("Python nao encontrado! Instale Python de: https://python.org/downloads (Marque 'Add Python to PATH').")
        return False
    try:
        subprocess.run(['git', '--version'], capture_output=True, check=True)
        logger.info("Git detectado.")
    except FileNotFoundError:
        logger.warning("Git nao encontrado. Instale Git de: https://git-scm.com/download/win.")
    logger.info("Para ESP-IDF no Windows, e recomendado usar o ESP-IDF Tools Installer ou WSL2 com Ubuntu.")
    return True


def install_development_tools(detector):
    """Instala ferramentas Python essenciais para o desenvolvimento do ESP32/MicroPython."""
    logger.info("Instalando ferramentas de desenvolvimento...")
    python_cmd = detector.commands['python_cmd']
    tools = [
        ("adafruit-ampy", "Upload de arquivos para ESP32"),
        ("esptool", "Flash de firmware ESP32"),
        ("pyserial", "Comunicacao serial"),
        ("mpremote", "Controle remoto MicroPython"),
    ]
    optional_tools = [
        ("mpy-cross", "Cross-compiler MicroPython"),
        ("rshell", "Shell remoto para MicroPython"),
    ]
    if detector.platform_info['platform'] != 'windows':
        optional_tools.append(("thonny", "IDE para MicroPython"))
    success_count = 0
    for package, desc in tools:
        logger.info(f"Instalando {desc} ({package})...")
        if install_pip_package(package, python_cmd):
            success_count += 1
    install_optional = input(f"Instalar ferramentas opcionais? (s/N): ").lower().strip() in ['s', 'sim', 'y', 'yes']
    if install_optional:
        for package, desc in optional_tools:
            logger.info(f"Instalando {desc} ({package})...")
            if install_pip_package(package, python_cmd):
                success_count += 1
    logger.info(f"Resultado: {success_count} ferramentas instaladas.")
    return success_count > 0


def test_tools(detector):
    """Testa a disponibilidade e funcionalidade das ferramentas instaladas."""
    logger.info("Testando ferramentas...")
    if detector.platform_info['platform'] == 'windows':
        tools_to_test = [
            ("ampy", "ampy --help"),
            ("esptool.py", "esptool.py version"),
            ("mpremote", "mpremote --help"),
        ]
    else:
        tools_to_test = [
            ("ampy", "ampy --help"),
            ("esptool.py", "esptool.py version"),
            ("mpremote", "mpremote --help"),
            ("mpy-cross", "mpy-cross --version"),
        ]
    working_tools = []
    for tool, test_cmd in tools_to_test:
        try:
            result = subprocess.run(
                test_cmd.split(), 
                capture_output=True, 
                text=True, 
                timeout=10
            )
            if result.returncode == 0:
                logger.info(f"{tool}: OK.")
                working_tools.append(tool)
            else:
                logger.warning(f"{tool}: Disponivel mas com warnings.")
                working_tools.append(tool)
        except (FileNotFoundError, subprocess.TimeoutExpired):
            logger.error(f"{tool}: Nao encontrado.")
    ports = detector.get_serial_ports()
    if ports:
        logger.info(f"Portas seriais: {len(ports)} encontradas.")
        for port in ports[:3]:
            logger.info(f"  - {port}")
    else:
        logger.warning(f"Nenhuma porta serial encontrada.")
    return working_tools


def create_development_guide(detector):
    """Cria um guia de desenvolvimento com instrucoes especificas para a plataforma."""
    logger.info("Criando guia de desenvolvimento (DEV_GUIDE.md)...")
    guide_content = f"""# Guia de Desenvolvimento - Planador ESP32

## Ferramentas Instaladas

### ampy - Upload de arquivos
```bash
ampy -p /dev/ttyUSB0 ls
ampy -p /dev/ttyUSB0 put config.py
ampy -p /dev/ttyUSB0 run main.py
```

### esptool.py - Flash de firmware
```bash
esptool.py --port /dev/ttyUSB0 chip_id
esptool.py --port /dev/ttyUSB0 write_flash 0x1000 firmware.bin
```

### mpremote - Controle remoto
```bash
mpremote
mpremote exec "print('Hello ESP32')"
mpremote mount .
```

## Workflow de Desenvolvimento

### 1. Preparacao
```bash
python3 build_dev.py
cd dist/planador_esp32
```

### 2. Configuracao
```bash
cp configs/config_minimal.py modules/config.py
# OU
cp configs/config_default.py modules/config.py
```

### 3. Deploy
```bash
make flash PORT=/dev/ttyUSB0
# OU
cd modules
ampy -p /dev/ttyUSB0 put config.py
ampy -p /dev/ttyUSB0 put hardware.py
```

### 4. Teste
```bash
mpremote
# No REPL:
# from main_modular import main
# main()
```

### 5. Debug
```bash
mpremote
# Logs sao impressos via serial
```

## Estrutura de Desenvolvimento

```
src/micropython/
├── build_dev.py
├── build_frozen.py
├── compile_mpy.py
├── config.py
├── config_minimal.py
├── hardware.py
├── sensors.py
├── release_system.py
├── pid_controller.py
└── boot.py
```

## Troubleshooting

### Problema: Permission denied no /dev/ttyUSB0
```bash
sudo usermod -a -G dialout $USER
# Depois: logout/login
```

### Problema: ESP32 nao responde
```bash
# Reset manual: pressionar EN
# Boot mode: pressionar BOOT + EN
```

### Problema: Import errors
- Verificar se todos os modulos foram enviados
- Verificar sintaxe com: `python3 -m py_compile arquivo.py`

## Dicas

1. Use config_minimal.py durante desenvolvimento inicial.
2. Teste modulos individualmente antes do sistema completo.
3. Monitor serial sempre aberto para debug.
4. Faca backup da configuracao que funciona.
5. Teste em hardware real o mais cedo possivel.
"""
    with open("DEV_GUIDE.md", "w") as f:
        f.write(guide_content)
    logger.info("Guia de desenvolvimento (DEV_GUIDE.md) criado.")


def main():
    """Funcao principal para executar o processo de instalacao de ferramentas de desenvolvimento."""
    logger.info("Iniciando instalacao de ferramentas de desenvolvimento.")
    detector = PlatformDetector()
    detector.print()
    if not check_python_version():
        return
    logger.info(f"Configurando {detector.platform_info['platform'].upper()}...")
    if not install_system_dependencies(detector):
        logger.error("Falha ao instalar dependencias do sistema.")
        return
    if install_development_tools(detector):
        logger.info("Ferramentas instaladas com sucesso!")
    else:
        logger.error("Falha na instalacao de algumas ferramentas.")
        return
    working_tools = test_tools(detector)
    create_development_guide(detector)
    logger.info("Setup de desenvolvimento concluido!")
    logger.info(f"Plataforma: {detector.platform_info['platform']}")
    logger.info(f"Ferramentas funcionando: {len(working_tools)}")
    logger.info(f"Guia criado: DEV_GUIDE.md")
    python_cmd = detector.commands['python_cmd']
    logger.info(f"Proximos passos:")
    logger.info(f"  1. {python_cmd} build_dev.py")
    logger.info(f"  2. cd dist/planador_esp32")
    logger.info(f"  3. make flash")
    logger.info(f"  4. Leia: DEV_GUIDE.md")
    if detector.platform_info['platform'] == 'macos' and detector.platform_info['is_arm']:
        logger.info(f"NOTA APPLE SILICON: ESP-IDF pode precisar de Rosetta 2. Use: arch -x86_64 python3 se houver problemas.")
    elif detector.platform_info['platform'] == 'linux':
        logger.info(f"NOTA LINUX: Faca logout/login para aplicar permissoes seriais. Verifique: groups $USER | grep dialout.")
    elif detector.platform_info['platform'] == 'windows':
        logger.info(f"NOTA WINDOWS: Instale drivers USB-Serial se necessario. Use Gerenciador de Dispositivos para verificar porta COM. Para ESP-IDF: considere usar WSL2.")


if __name__ == "__main__":
    main()
