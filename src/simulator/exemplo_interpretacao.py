#!/usr/bin/env python3
"""
Exemplo de Interpretação dos Gráficos do Simulador

Este script roda uma simulação curta e explica o que está acontecendo
nos gráficos em tempo real.
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

import custom_logging as logging
from planador_simulator import PlanadorSimulator
import time

logger = logging.getLogger(__name__)

def interpretar_dados(status):
    """Interpreta os dados do simulador e explica o que está acontecendo"""
    
    # Dados do sensor
    roll = status['sensor_data']['roll']
    pitch = status['sensor_data']['pitch']
    yaw_rate = status['sensor_data']['yaw_rate']
    
    # Posições dos servos
    flaps_l = status['servo_positions']['flaps_left']
    flaps_r = status['servo_positions']['flaps_right']
    elevator = status['servo_positions']['elevator']
    rudder = status['servo_positions']['rudder']
    
    interpretacao = []
    
    # Análise da atitude
    if abs(roll) < 2 and abs(pitch) < 2:
        interpretacao.append("✅ ATITUDE ESTÁVEL: Planador bem nivelado")
    elif abs(roll) < 10 and abs(pitch) < 10:
        interpretacao.append("🟡 ATITUDE MODERADA: Sistema corrigindo")
    else:
        interpretacao.append("🔴 ATITUDE INSTÁVEL: Correções necessárias")
    
    # Análise do yaw rate
    if abs(yaw_rate) < 1:
        interpretacao.append("✅ YAW ESTÁVEL: Sem rotação indesejada")
    elif abs(yaw_rate) < 5:
        interpretacao.append("🟡 YAW MODERADO: Pequena rotação")
    else:
        interpretacao.append("🔴 YAW ALTO: Rotação significativa")
    
    # Análise dos flaps (controle de roll)
    diff_flaps = abs(flaps_l - flaps_r)
    if diff_flaps < 5:
        interpretacao.append("✅ FLAPS NEUTROS: Sem correção de roll")
    elif diff_flaps < 20:
        interpretacao.append("🟡 FLAPS ATIVOS: Corrigindo roll moderado")
    else:
        interpretacao.append("🔴 FLAPS EXTREMOS: Correção forte de roll")
    
    # Análise do elevator (controle de pitch)
    elevator_neutral = abs(elevator - 90)
    if elevator_neutral < 5:
        interpretacao.append("✅ ELEVATOR NEUTRO: Sem correção de pitch")
    elif elevator_neutral < 20:
        interpretacao.append("🟡 ELEVATOR ATIVO: Corrigindo pitch")
    else:
        interpretacao.append("🔴 ELEVATOR EXTREMO: Correção forte de pitch")
    
    # Análise do rudder (controle de yaw)
    rudder_neutral = abs(rudder - 90)
    if rudder_neutral < 5:
        interpretacao.append("✅ RUDDER NEUTRO: Sem correção de yaw")
    elif rudder_neutral < 20:
        interpretacao.append("🟡 RUDDER ATIVO: Corrigindo yaw")
    else:
        interpretacao.append("🔴 RUDDER EXTREMO: Correção forte de yaw")
    
    return interpretacao

def exemplo_interpretacao():
    """Roda simulação com interpretação em tempo real"""
    
    logger.info("=== EXEMPLO DE INTERPRETAÇÃO DOS GRÁFICOS ===")
    logger.info("Iniciando simulação com explicações...")
    
    # Criar simulador
    simulator = PlanadorSimulator()
    simulator.hardware.disturbance_amplitude = 8.0  # Perturbação média
    
    # Simular por 10 segundos
    dt = 1.0 / 50.0  # 50Hz
    duration = 10.0
    
    simulator.running = True
    simulator.start_time = time.time()
    
    loop_count = 0
    
    while simulator.running and (time.time() - simulator.start_time) < duration:
        loop_start = time.time()
        
        # Executar iteração do simulador
        simulator.main_loop_iteration(dt)
        
        loop_count += 1
        
        # A cada 50 loops (1 segundo), interpretar os dados
        if loop_count % 50 == 0:
            status = simulator.get_status()
            segundos = int(time.time() - simulator.start_time)
            
            logger.info(f"\n--- SEGUNDO {segundos} ---")
            logger.info(f"Roll: {status['sensor_data']['roll']:.1f}° | "
                       f"Pitch: {status['sensor_data']['pitch']:.1f}° | "
                       f"Yaw Rate: {status['sensor_data']['yaw_rate']:.1f}°/s")
            
            logger.info(f"Flaps: L={status['servo_positions']['flaps_left']:.0f}° "
                       f"R={status['servo_positions']['flaps_right']:.0f}° | "
                       f"Elevator: {status['servo_positions']['elevator']:.0f}° | "
                       f"Rudder: {status['servo_positions']['rudder']:.0f}°")
            
            interpretacoes = interpretar_dados(status)
            for interp in interpretacoes:
                logger.info(f"  {interp}")
        
        # Controlar frequência
        loop_time = time.time() - loop_start
        sleep_time = dt - loop_time
        if sleep_time > 0:
            time.sleep(sleep_time)
    
    simulator.running = False
    
    # Status final
    final_status = simulator.get_status()
    logger.info(f"\n=== ANÁLISE FINAL ===")
    logger.info(f"Loops executados: {final_status['loop_count']}")
    logger.info(f"Frequência média: {final_status['frequency']:.1f}Hz")
    
    interpretacoes_finais = interpretar_dados(final_status)
    for interp in interpretacoes_finais:
        logger.info(f"  {interp}")
    
    logger.info("\n=== COMO LER OS GRÁFICOS ===")
    logger.info("1. Atitude (Roll/Pitch): Mostra se o planador está nivelado")
    logger.info("2. Yaw Rate: Mostra se o planador está girando")
    logger.info("3. Servos Flaps: Movimentos opostos corrigem roll")
    logger.info("4. Elevator/Rudder: Corrigem pitch e yaw respectivamente")
    logger.info("\nConsulte EXPLICACAO_GRAFICOS.md para detalhes completos!")

if __name__ == "__main__":
    exemplo_interpretacao()