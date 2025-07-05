#!/usr/bin/env python3
"""
Teste de Compatibilidade Multiplataforma
Autor: Sistema Aeromodelo
Data: 2025-07-04

Verifica se o projeto funciona corretamente em diferentes plataformas
"""

import sys
import os
import subprocess
import platform
from pathlib import Path

def run_command(cmd, description="", timeout=30):
    """Executa comando e retorna resultado"""
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, 
            text=True, timeout=timeout
        )
        return {
            'success': result.returncode == 0,
            'stdout': result.stdout,
            'stderr': result.stderr,
            'description': description
        }
    except subprocess.TimeoutExpired:
        return {
            'success': False,
            'stdout': '',
            'stderr': 'Timeout',
            'description': description
        }
    except Exception as e:
        return {
            'success': False,
            'stdout': '',
            'stderr': str(e),
            'description': description
        }

import custom_logging as logging

logger = logging.getLogger(__name__)

def test_python_environment():
    """Testa ambiente Python"""
    logger.info("Testando ambiente Python...")
    
    tests = [
        (f"{sys.executable} --version", "Versão Python"),
        (f"{sys.executable} -m pip --version", "Pip disponível"),
        (f"{sys.executable} -c 'import platform; print(platform.system())'", "Platform module"),
        (f"{sys.executable} -c 'import pathlib'", "Pathlib module"),
    ]
    
    results = []
    for cmd, desc in tests:
        result = run_command(cmd, desc)
        status = "OK" if result['success'] else "ERRO"
        logger.info(f"  {status} {desc}")
        if not result['success']:
            logger.error(f"    Erro: {result['stderr']}")
        results.append(result)
    
    return results

def test_platform_detection():
    """Testa detecção de plataforma"""
    print("\n🖥️  Testando detecção de plataforma...")
    
    micropython_dir = Path("src/micropython")
    if not micropython_dir.exists():
        print("  ❌ Diretório src/micropython não encontrado")
        return [{'success': False, 'description': 'MicroPython dir missing'}]
    
    # Testar script de detecção
    os.chdir(micropython_dir)
    result = run_command(f"{sys.executable} detect_platform.py", "Detecção de plataforma")
    os.chdir("../..")
    
    status = "✅" if result['success'] else "❌"
    print(f"  {status} Detecção de plataforma")
    
    if result['success']:
        print("    Info da plataforma:")
        for line in result['stdout'].split('\n')[:10]:  # Primeiras 10 linhas
            if line.strip():
                print(f"    {line}")
    else:
        print(f"    Erro: {result['stderr']}")
    
    return [result]

def test_makefile_targets():
    """Testa targets do Makefile"""
    print("\n🔨 Testando Makefile...")
    
    # Verificar se Makefile existe
    if not Path("Makefile").exists():
        print("  ❌ Makefile não encontrado")
        return [{'success': False, 'description': 'Makefile missing'}]
    
    # Detectar comando make
    make_cmd = "make"
    if platform.system() == "Windows":
        # Tentar diferentes opções no Windows
        for cmd in ["make", "mingw32-make", "gmake"]:
            if run_command(f"where {cmd}", timeout=5)['success']:
                make_cmd = cmd
                break
    
    tests = [
        (f"{make_cmd} --version", "Make disponível"),
        (f"{make_cmd} help", "Help do projeto"),
        (f"{make_cmd} check-system", "Verificação do sistema"),
        (f"{make_cmd} status", "Status do projeto"),
    ]
    
    results = []
    for cmd, desc in tests:
        result = run_command(cmd, desc, timeout=10)
        status = "✅" if result['success'] else "❌"
        print(f"  {status} {desc}")
        if not result['success']:
            print(f"    Erro: {result['stderr'][:200]}")  # Primeiros 200 chars
        results.append(result)
    
    return results

def test_build_scripts():
    """Testa scripts de build"""
    print("\n📦 Testando scripts de build...")
    
    micropython_dir = Path("src/micropython")
    if not micropython_dir.exists():
        print("  ❌ Diretório src/micropython não encontrado")
        return []
    
    os.chdir(micropython_dir)
    
    scripts = [
        ("build_dev.py", "Build desenvolvimento"),
        ("compile_mpy.py", "Compilação MPY"),
        ("install_dev_tools.py", "Instalação ferramentas"),
    ]
    
    results = []
    for script, desc in scripts:
        if Path(script).exists():
            # Testar sintaxe
            result = run_command(f"{sys.executable} -m py_compile {script}", f"Sintaxe {script}")
            status = "✅" if result['success'] else "❌"
            print(f"  {status} {desc} - sintaxe")
            results.append(result)
        else:
            print(f"  ❌ {script} não encontrado")
            results.append({'success': False, 'description': f'{script} missing'})
    
    os.chdir("../..")
    return results

def test_setup_scripts():
    """Testa scripts de setup"""
    print("\n⚙️  Testando scripts de setup...")
    
    results = []
    
    # Testar setup.sh (Unix)
    if Path("setup.sh").exists():
        result = run_command("bash -n setup.sh", "Sintaxe setup.sh")
        status = "✅" if result['success'] else "❌"
        print(f"  {status} setup.sh - sintaxe")
        results.append(result)
    else:
        print("  ⚠️  setup.sh não encontrado")
    
    # Testar setup.bat (Windows)
    if Path("setup.bat").exists():
        print("  ✅ setup.bat encontrado")
        results.append({'success': True, 'description': 'setup.bat exists'})
    else:
        print("  ⚠️  setup.bat não encontrado")
    
    return results

def test_project_structure():
    """Testa estrutura do projeto"""
    print("\n📁 Testando estrutura do projeto...")
    
    required_paths = [
        "src/micropython/config.py",
        "src/micropython/hardware.py",
        "src/micropython/sensors.py",
        "src/micropython/release_system.py",
        "src/micropython/pid_controller.py",
        "src/micropython/main_modular.py",
        "src/micropython/boot.py",
        "Makefile",
        "README.md"
    ]
    
    results = []
    for path in required_paths:
        exists = Path(path).exists()
        status = "✅" if exists else "❌"
        print(f"  {status} {path}")
        results.append({
            'success': exists,
            'description': f'{path} exists'
        })
    
    return results

def generate_report(all_results):
    """Gera relatório final"""
    print("\n" + "=" * 60)
    print("📋 RELATÓRIO DE COMPATIBILIDADE MULTIPLATAFORMA")
    print("=" * 60)
    
    total_tests = 0
    passed_tests = 0
    
    for category, results in all_results.items():
        total_tests += len(results)
        passed_tests += sum(1 for r in results if r['success'])
        
        category_passed = sum(1 for r in results if r['success'])
        category_total = len(results)
        
        print(f"\n📊 {category}: {category_passed}/{category_total} testes passaram")
        
        # Mostrar falhas
        failures = [r for r in results if not r['success']]
        if failures:
            print("   Falhas:")
            for failure in failures[:3]:  # Máximo 3 falhas
                print(f"   • {failure['description']}")
    
    # Resultado geral
    success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
    
    print(f"\n🎯 RESULTADO GERAL: {passed_tests}/{total_tests} ({success_rate:.1f}%)")
    
    if success_rate >= 90:
        print("🎉 EXCELENTE: Projeto totalmente compatível!")
    elif success_rate >= 75:
        print("✅ BOM: Projeto funcionará com pequenos ajustes")
    elif success_rate >= 50:
        print("⚠️  MÉDIO: Alguns problemas precisam ser resolvidos")
    else:
        print("❌ RUIM: Muitos problemas de compatibilidade")
    
    # Informações da plataforma atual
    print(f"\n🖥️  PLATAFORMA TESTADA:")
    print(f"   Sistema: {platform.system()}")
    print(f"   Versão: {platform.release()}")
    print(f"   Arquitetura: {platform.machine()}")
    print(f"   Python: {sys.version}")
    
    print("=" * 60)

def main():
    """Função principal"""
    print("🧪 TESTE DE COMPATIBILIDADE MULTIPLATAFORMA")
    print("Sistema Planador ESP32")
    print("=" * 60)
    
    # Executar todos os testes
    all_results = {
        "Ambiente Python": test_python_environment(),
        "Detecção Plataforma": test_platform_detection(),
        "Makefile": test_makefile_targets(),
        "Scripts Build": test_build_scripts(),
        "Scripts Setup": test_setup_scripts(),
        "Estrutura Projeto": test_project_structure(),
    }
    
    # Gerar relatório
    generate_report(all_results)

if __name__ == "__main__":
    main()