#!/usr/bin/env python3
"""
Detecta automaticamente a plataforma do sistema operacional e fornece
informacoes relevantes para configuracao do ambiente de desenvolvimento.

Este modulo e util para scripts de setup que precisam se adaptar a diferentes
sistemas operacionais (Linux, macOS, Windows).
"""

import os
import sys
import platform
import subprocess
from pathlib import Path
import logging


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)


class PlatformDetector:
    """Detecta e fornece informacoes detalhadas sobre a plataforma atual."""

    def __init__(self):
        """Inicializa o detector de plataforma, coletando informacoes do sistema."""
        self.platform_info = self._detect_platform()
        self.paths = self._get_platform_paths()
        self.commands = self._get_platform_commands()

    def _detect_platform(self):
        """Detecta o sistema operacional, arquitetura e outras informacoes relevantes."""
        system = platform.system().lower()
        machine = platform.machine().lower()
        info = {
            'system': system,
            'machine': machine,
            'python_version': f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            'is_admin': self._check_admin_rights()
        }
        if system == 'darwin':
            info['platform'] = 'macos'
            info['is_arm'] = machine in ['arm64', 'aarch64']
            info['brew_available'] = self._check_command('brew')
            info['recommended_shell'] = 'zsh'
        elif system == 'linux':
            info['platform'] = 'linux'
            info['is_arm'] = machine in ['arm64', 'aarch64', 'armv7l']
            info['distro'] = self._detect_linux_distro()
            info['recommended_shell'] = 'bash'
        elif system == 'windows':
            info['platform'] = 'windows'
            info['is_wsl'] = 'microsoft' in platform.release().lower()
            info['powershell_available'] = self._check_command('powershell')
            info['recommended_shell'] = 'powershell'
        else:
            info['platform'] = 'unknown'
        return info

    def _detect_linux_distro(self):
        """Detecta a distribuicao Linux lendo o arquivo /etc/os-release."""
        try:
            with open('/etc/os-release', 'r') as f:
                for line in f:
                    if line.startswith('ID='):
                        return line.split('=')[1].strip().strip('"')
        except:
            pass
        return 'unknown'

    def _check_admin_rights(self):
        """Verifica se o script esta sendo executado com privilegios administrativos."""
        if self.platform_info.get('platform') == 'windows':
            try:
                import ctypes
                return ctypes.windll.shell32.IsUserAnAdmin() != 0
            except:
                return False
        else:
            return os.geteuid() == 0 if hasattr(os, 'geteuid') else False

    def _check_command(self, command):
        """Verifica se um comando especifico esta disponivel no PATH do sistema."""
        try:
            subprocess.run([command, '--version'], 
                         capture_output=True, check=True)
            return True
        except:
            return False

    def _get_platform_paths(self):
        """Retorna um dicionario de caminhos de sistema comuns para a plataforma detectada."""
        system = self.platform_info['platform']
        if system == 'macos':
            return {
                'home': Path.home(),
                'pip_user': Path.home() / '.local/bin',
                'brew_prefix': Path('/opt/homebrew') if self.platform_info['is_arm'] else Path('/usr/local'),
                'serial_ports': ['/dev/cu.usbserial*', '/dev/cu.SLAB_USBtoUART*', '/dev/cu.wchusbserial*'],
                'esp_idf_path': Path.home() / 'esp/esp-idf',
                'shell_rc': Path.home() / '.zshrc'
            }
        elif system == 'linux':
            return {
                'home': Path.home(),
                'pip_user': Path.home() / '.local/bin',
                'serial_ports': ['/dev/ttyUSB*', '/dev/ttyACM*'],
                'esp_idf_path': Path.home() / 'esp/esp-idf',
                'shell_rc': Path.home() / '.bashrc'
            }
        elif system == 'windows':
            return {
                'home': Path.home(),
                'pip_user': Path.home() / 'AppData/Local/Programs/Python/Python*/Scripts',
                'serial_ports': ['COM*'],
                'esp_idf_path': Path('C:/esp/esp-idf'),
                'shell_rc': Path.home() / 'Documents/WindowsPowerShell/Microsoft.PowerShell_profile.ps1'
            }
        else:
            return {}

    def _get_platform_commands(self):
        """Retorna um dicionario de comandos de shell comuns para a plataforma detectada."""
        system = self.platform_info['platform']
        if system == 'macos':
            return {
                'package_manager': 'brew',
                'install_python': 'brew install python3',
                'install_git': 'brew install git',
                'install_cmake': 'brew install cmake',
                'install_ninja': 'brew install ninja',
                'python_cmd': 'python3',
                'pip_cmd': 'pip3',
                'serial_list': 'ls /dev/cu.*',
                'add_to_path': 'export PATH="$PATH:{}"'
            }
        elif system == 'linux':
            distro = self.platform_info.get('distro', 'ubuntu')
            if distro in ['ubuntu', 'debian']:
                pkg_mgr = 'apt'
                install_cmd = 'sudo apt update && sudo apt install -y'
            elif distro in ['fedora', 'rhel', 'centos']:
                pkg_mgr = 'dnf'
                install_cmd = 'sudo dnf install -y'
            elif distro in ['arch', 'manjaro']:
                pkg_mgr = 'pacman'
                install_cmd = 'sudo pacman -S'
            else:
                pkg_mgr = 'apt'
                install_cmd = 'sudo apt install -y'
            return {
                'package_manager': pkg_mgr,
                'install_python': f'{install_cmd} python3 python3-pip python3-venv',
                'install_git': f'{install_cmd} git',
                'install_cmake': f'{install_cmd} cmake',
                'install_ninja': f'{install_cmd} ninja-build',
                'python_cmd': 'python3',
                'pip_cmd': 'pip3',
                'serial_list': 'ls /dev/tty*',
                'add_to_path': 'export PATH="$PATH:{}"',
                'add_user_dialout': 'sudo usermod -a -G dialout $USER'
            }
        elif system == 'windows':
            return {
                'package_manager': 'chocolatey',
                'install_python': 'choco install python3',
                'install_git': 'choco install git',
                'install_cmake': 'choco install cmake',
                'install_ninja': 'choco install ninja',
                'python_cmd': 'python',
                'pip_cmd': 'pip',
                'serial_list': 'Get-WmiObject Win32_SerialPort',
                'add_to_path': '$env:PATH += ";{}"'
            }
        else:
            return {}

    def get_serial_ports(self):
        """Lista as portas seriais disponiveis no sistema."""
        system = self.platform_info['platform']
        if system == 'macos':
            import glob
            ports = []
            for pattern in self.paths['serial_ports']:
                ports.extend(glob.glob(pattern))
            return sorted(ports)
        elif system == 'linux':
            import glob
            ports = []
            for pattern in self.paths['serial_ports']:
                ports.extend(glob.glob(pattern))
            return sorted([p for p in ports if os.access(p, os.R_OK | os.W_OK)])
        elif system == 'windows':
            try:
                import serial.tools.list_ports
                return [port.device for port in serial.tools.list_ports.comports()]
            except ImportError:
                return ['COM1', 'COM2', 'COM3', 'COM4']
        return []

    def get_installation_instructions(self):
        """Retorna instrucoes de instalacao de dependencias especificas para a plataforma."""
        system = self.platform_info['platform']
        if system == 'macos':
            arch_note = " (Apple Silicon)" if self.platform_info['is_arm'] else " (Intel)"
            return f"""
macOS{arch_note} - Instrucoes de Instalacao:

1. Instalar Homebrew (se nao tiver):
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

2. Instalar dependencias:
   {self.commands['install_python']}
   {self.commands['install_git']}
   {self.commands['install_cmake']}
   {self.commands['install_ninja']}

3. Instalar ferramentas Python:
   pip3 install --user esptool adafruit-ampy mpremote

4. Adicionar ao PATH (adicione ao ~/.zshrc):
   export PATH="/opt/homebrew/bin:$PATH"
   export PATH="$HOME/.local/bin:$PATH"

5. Reiniciar terminal ou executar:
   source ~/.zshrc
"""
        elif system == 'linux':
            distro_name = self.platform_info.get('distro', 'Ubuntu/Debian').title()
            return f"""
Linux ({distro_name}) - Instrucoes de Instalacao:

1. Atualizar sistema:
   sudo apt update  # ou dnf update / pacman -Syu

2. Instalar dependencias:
   {self.commands['install_python']}
   {self.commands['install_git']}
   {self.commands['install_cmake']}
   {self.commands['install_ninja']}

3. Instalar ferramentas Python:
   pip3 install --user esptool adafruit-ampy mpremote

4. Configurar permissoes serial:
   {self.commands['add_user_dialout']}
   # Depois: logout/login

5. Adicionar ao PATH (adicione ao ~/.bashrc):
   export PATH="$HOME/.local/bin:$PATH"

6. Reiniciar terminal ou executar:
   source ~/.bashrc
"""
        elif system == 'windows':
            wsl_note = " (WSL)" if self.platform_info['is_wsl'] else ""
            return f"""
Windows{wsl_note} - Instrucoes de Instalacao:

1. Instalar Python:
   - Download: https://python.org/downloads
   - Marcar "Add Python to PATH"

2. Instalar Git:
   - Download: https://git-scm.com/download/win

3. Instalar Visual C++ Build Tools:
   - Download: https://visualstudio.microsoft.com/visual-cpp-build-tools/

4. Instalar ferramentas Python (PowerShell como Admin):
   pip install esptool adafruit-ampy mpremote

5. Instalar driver USB-Serial:
   - CP2102: https://www.silabs.com/developers/usb-to-uart-bridge-vcp-drivers
   - CH340: http://www.wch.cn/downloads/CH341SER_ZIP.html

6. Verificar porta COM:
   Gerenciador de Dispositivos > Portas (COM & LPT)
"""
        return "Sistema nao suportado"

    def print(self):
        """Imprime um resumo das informacoes da plataforma detectada."""
        info = self.platform_info
        logger.info("DETECCAO DE PLATAFORMA")
        logger.info(f"Sistema: {info['system'].title()}")
        logger.info(f"Arquitetura: {info['machine']}")
        logger.info(f"Plataforma: {info['platform']}")
        logger.info(f"Python: {info['python_version']}")
        if info['platform'] == 'macos':
            logger.info(f"Apple Silicon: {'Sim' if info['is_arm'] else 'Nao'}")
            logger.info(f"Homebrew: {'Disponivel' if info['brew_available'] else 'Nao disponivel'}")
        elif info['platform'] == 'linux':
            logger.info(f"Distribuicao: {info['distro']}")
            logger.info(f"ARM: {'Sim' if info['is_arm'] else 'Nao'}")
        elif info['platform'] == 'windows':
            logger.info(f"WSL: {'Sim' if info['is_wsl'] else 'Nao'}")
            logger.info(f"PowerShell: {'Disponivel' if info['powershell_available'] else 'Nao disponivel'}")
        logger.info(f"Shell recomendado: {info.get('recommended_shell', 'bash')}")
        ports = self.get_serial_ports()
        logger.info(f"Portas seriais detectadas: {len(ports)}")
        for port in ports[:5]:
            logger.info(f"  - {port}")
        if len(ports) > 5:
            logger.info(f"  ... e mais {len(ports) - 5}")


def main():
    """Funcao principal para executar a deteccao de plataforma e exibir instrucoes."""
    detector = PlatformDetector()
    detector.print()
    logger.info(detector.get_installation_instructions())


if __name__ == "__main__":
    main()
