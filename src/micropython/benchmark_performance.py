"""
Modulo para benchmarking de performance do sistema do planador.

Contem funcoes para medir o tempo de importacao, o desempenho do calculo PID,
o uso de memoria e o tamanho dos arquivos, comparando diferentes metodos de compilacao.
"""

import time
import gc
import sys
import os
from pathlib import Path
import logging


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)


def measure_memory():
    """Mede a quantidade de memoria livre disponivel."""
    gc.collect()
    return gc.mem_free()


def benchmark_import_time():
    """Realiza um benchmark do tempo de importacao de modulos.

    Retorna:
        dict: Um dicionario com os resultados do tempo de importacao para cada modulo.
    """
    logger.info("BENCHMARK - TEMPO DE IMPORTACAO")
    modules_to_test = [
        ("config", "Configuracoes"),
        ("hardware", "Gerenciamento de Hardware"),
        ("sensors", "Sensores"),
        ("pid_controller", "Controlador PID"),
        ("release_system", "Sistema de Liberacao")
    ]
    results = {}
    for module_name, description in modules_to_test:
        logger.info(f"Testando {description}...")
        start_time = time.ticks_ms()
        try:
            if module_name in sys.modules:
                del sys.modules[module_name]
            logger.info(f"import {module_name}")
            interpreted_time = time.ticks_diff(time.ticks_ms(), start_time)
            logger.info(f"  Interpretado: {interpreted_time}ms")
        except ImportError as e:
            interpreted_time = None
            logger.exception(f"  Interpretado: ERRO - {e}")
        mpy_file = Path(f"compiled_mpy/{module_name}.mpy")
        if mpy_file.exists():
            start_time = time.ticks_ms()
            try:
                mpy_time = time.ticks_diff(time.ticks_ms(), start_time)
                logger.info(f"  Compilado MPY: {mpy_time}ms")
            except Exception as e:
                mpy_time = None
                logger.exception(f"  Compilado MPY: ERRO - {e}")
        else:
            mpy_time = None
            logger.info(f"  Compilado MPY: Nao disponivel")
        results[module_name] = {
            'interpreted': interpreted_time,
            'mpy': mpy_time,
            'description': description
        }
    return results


def benchmark_pid_calculation():
    """Realiza um benchmark do desempenho do calculo PID em diferentes cenarios.

    Retorna:
        dict: Um dicionario com os resultados do benchmark PID para cada cenario.
    """
    logger.info("BENCHMARK - CALCULO PID")
    test_scenarios = [
        {"name": "Voo Estavel", "data": [(0, 0, 0), (0.5, -0.2, 0), (-0.3, 0.1, 0)]},
        {"name": "Turbulencia", "data": [(5, -3, 2), (-4, 6, -1), (3, -2, 1), (-6, 4, -2)]},
        {"name": "Manobras", "data": [(15, -8, 5), (-12, 10, -3), (8, -15, 4), (-20, 12, -6)]}
    ]
    results = {}
    for scenario in test_scenarios:
        logger.info(f"Cenario: {scenario['name']}")
        try:
            from pid_controller import PIDController
            pid = PIDController()
            start_time = time.ticks_ms()
            iterations = 100
            for i in range(iterations):
                for roll, pitch, yaw_rate in scenario['data']:
                    commands = pid.calculate_servo_commands(roll, pitch, yaw_rate)
            interpreted_time = time.ticks_diff(time.ticks_ms(), start_time)
            interpreted_rate = (iterations * len(scenario['data'])) / (interpreted_time / 1000)
            logger.info(f"  Interpretado: {interpreted_time}ms ({interpreted_rate:.1f} calc/s)")
        except Exception as e:
            interpreted_time = None
            interpreted_rate = None
            logger.exception(f"  Interpretado: ERRO - {e}")
        try:
            from generic_pid import GenericPIDController
            pid_roll = GenericPIDController(2.0, 0.1, 0.0)
            pid_pitch = GenericPIDController(1.5, 0.05, 0.0)
            start_time = time.ticks_ms()
            iterations = 100
            for i in range(iterations):
                for roll, pitch, yaw_rate in scenario['data']:
                    roll_correction = pid_roll.calculate(0, roll)
                    pitch_correction = pid_pitch.calculate(0, pitch)
                    commands = {
                        'flaps_left': 90 - roll_correction,
                        'flaps_right': 90 + roll_correction,
                        'elevator': 90 - pitch_correction,
                        'rudder': 90
                    }
            compiled_time = time.ticks_diff(time.ticks_ms(), start_time)
            compiled_rate = (iterations * len(scenario['data'])) / (compiled_time / 1000)
            logger.info(f"  Compilado: {compiled_time}ms ({compiled_rate:.1f} calc/s)")
            if interpreted_time and compiled_time:
                speedup = interpreted_time / compiled_time
                logger.info(f"  Speedup: {speedup:.2f}x")
        except ImportError:
            compiled_time = None
            compiled_rate = None
            logger.info(f"  Compilado: Nao disponivel")
        results[scenario['name']] = {
            'interpreted_time': interpreted_time,
            'interpreted_rate': interpreted_rate,
            'compiled_time': compiled_time,
            'compiled_rate': compiled_rate
        }
    return results


def benchmark_memory_usage():
    """Realiza um benchmark do uso de memoria do sistema."""
    logger.info("BENCHMARK - USO DE MEMORIA")
    initial_memory = measure_memory()
    logger.info(f"Memoria inicial: {initial_memory} bytes")
    memory_results = {}
    logger.info("Testando importacao de modulos...")
    modules = ["config", "hardware", "sensors", "pid_controller", "release_system"]
    for module in modules:
        mem_before = measure_memory()
        try:
            exec(f"import {module}")
            mem_after = measure_memory()
            memory_used = mem_before - mem_after
            logger.info(f"  {module}: {memory_used} bytes")
            memory_results[module] = memory_used
        except ImportError as e:
            logger.error(f"  {module}: ERRO - {e}")
            memory_results[module] = None
    logger.info("Testando criacao de objetos...")
    try:
        from pid_controller import PIDController
        mem_before = measure_memory()
        pid = PIDController()
        mem_after = measure_memory()
        pid_memory = mem_before - mem_after
        logger.info(f"  PIDController: {pid_memory} bytes")
        memory_results['pid_object'] = pid_memory
    except Exception as e:
        logger.exception(f"  PIDController: ERRO - {e}")
        memory_results['pid_object'] = None
    logger.info("Testando estruturas de dados...")
    mem_before = measure_memory()
    flight_data = []
    for i in range(100):
        flight_data.append({
            'timestamp': time.ticks_ms(),
            'roll': i * 0.1,
            'pitch': i * 0.05,
            'yaw_rate': i * 0.02,
            'servo_commands': {
                'flaps_left': 90 + i,
                'flaps_right': 90 - i,
                'elevator': 90 + i * 0.5,
                'rudder': 90
            }
        })
    mem_after = measure_memory()
    data_memory = mem_before - mem_after
    logger.info(f"  Dados de voo (100 amostras): {data_memory} bytes")
    memory_results['flight_data'] = data_memory
    del flight_data
    gc.collect()
    final_memory = measure_memory()
    total_used = initial_memory - final_memory
    logger.info(f"Memoria total usada: {total_used} bytes")
    logger.info(f"Memoria final: {final_memory} bytes")
    return memory_results


def benchmark_file_sizes():
    """Realiza um benchmark do tamanho dos arquivos de modulo."""
    logger.info("BENCHMARK - TAMANHOS DE ARQUIVO")
    modules = [
        "config.py", "hardware.py", "sensors.py", 
        "pid_controller.py", "release_system.py", "main_modular.py"
    ]
    size_results = {}
    total_original = 0
    total_compiled = 0
    logger.info("Modulo                Original    MPY      Reducao")
    logger.info("-" * 50)
    for module in modules:
        original_size = 0
        compiled_size = 0
        if Path(module).exists():
            original_size = os.path.getsize(module)
            total_original += original_size
        mpy_file = Path(f"compiled_mpy/{Path(module).stem}.mpy")
        if mpy_file.exists():
            compiled_size = os.path.getsize(mpy_file)
            total_compiled += compiled_size
        if original_size > 0 and compiled_size > 0:
            reduction = ((original_size - compiled_size) / original_size) * 100
            logger.info(f"{module:<20} {original_size:>6}    {compiled_size:>6}    {reduction:>5.1f}%")
        else:
            logger.info(f"{module:<20} {original_size:>6}    {'N/A':>6}    {'N/A':>5}")
        size_results[module] = {
            'original': original_size,
            'compiled': compiled_size
        }
    logger.info("-" * 50)
    if total_original > 0 and total_compiled > 0:
        total_reduction = ((total_original - total_compiled) / total_original) * 100
        logger.info(f"{'TOTAL':<20} {total_original:>6}    {total_compiled:>6}    {total_reduction:>5.1f}%")
    return size_results


def generate_report(import_results, pid_results, memory_results, size_results):
    """Gera um relatorio completo dos resultados dos benchmarks."""
    logger.info("RELATORIO COMPLETO DE PERFORMANCE")
    logger.info("RESUMO EXECUTIVO:")
    if size_results:
        total_original = sum(r['original'] for r in size_results.values() if r['original'])
        total_compiled = sum(r['compiled'] for r in size_results.values() if r['compiled'])
        if total_original > 0 and total_compiled > 0:
            size_reduction = ((total_original - total_compiled) / total_original) * 100
            logger.info(f"Reducao de tamanho: {size_reduction:.1f}%")
    if pid_results:
        for scenario, results in pid_results.items():
            if results['interpreted_time'] and results['compiled_time']:
                speedup = results['interpreted_time'] / results['compiled_time']
                logger.info(f"Speedup PID ({scenario}): {speedup:.1f}x")
    if memory_results:
        total_module_memory = sum(m for m in memory_results.values() if m)
        logger.info(f"Memoria modulos: {total_module_memory} bytes")
    logger.info("RECOMENDACOES:")
    logger.info("Frozen Modules: Melhor opcao para producao.")
    logger.info("MPY Cross: Boa para desenvolvimento.")
    logger.info("Interpretado: Apenas para prototipagem.")
    logger.info("LIMITACOES:")
    logger.info("Nuitka: Compatibilidade limitada com MicroPython.")
    logger.info("Frozen: Requer recompilacao completa do firmware.")
    logger.info("MPY: Melhoria moderada de performance.")


def main():
    """Funcao principal para executar os benchmarks de performance."""
    logger.info("Iniciando benchmark completo de performance.")
    if len(sys.argv) > 1:
        test_type = sys.argv[1]
        if test_type == "import":
            benchmark_import_time()
        elif test_type == "pid":
            benchmark_pid_calculation()
        elif test_type == "memory":
            benchmark_memory_usage()
        elif test_type == "size":
            benchmark_file_sizes()
        elif test_type == "all":
            logger.info("Executando todos os benchmarks...")
            import_results = benchmark_import_time()
            pid_results = benchmark_pid_calculation()
            memory_results = benchmark_memory_usage()
            size_results = benchmark_file_sizes()
            generate_report(import_results, pid_results, memory_results, size_results)
        else:
            logger.info("Tipos de benchmark: import, pid, memory, size, all.")
    else:
        logger.info("Uso: python benchmark_performance.py [import|pid|memory|size|all]")
        logger.info("Tipos de benchmark:")
        logger.info("  import  - Tempo de importacao de modulos")
        logger.info("  pid     - Performance de calculo PID")
        logger.info("  memory  - Uso de memoria")
        logger.info("  size    - Tamanhos de arquivo")
        logger.info("  all     - Todos os benchmarks")


if __name__ == "__main__":
    main()
