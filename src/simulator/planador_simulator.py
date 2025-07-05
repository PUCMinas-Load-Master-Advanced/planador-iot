#!/usr/bin/env python3
"""
Simulador do Sistema Planador ESP32

Este simulador permite executar e testar o sistema planador localmente
sem necessidade de hardware real (ESP32, servos, sensores).
"""

import time
import math
import threading
import queue
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional
import custom_logging as logging

logger = logging.getLogger(__name__)

@dataclass
class SimulatedSensorData:
    """Dados simulados do sensor MPU6050"""
    roll: float = 0.0
    pitch: float = 0.0
    yaw_rate: float = 0.0
    timestamp: float = 0.0

@dataclass
class SimulatedServoState:
    """Estado simulado de um servo"""
    name: str
    current_angle: float = 90.0
    target_angle: float = 90.0
    moving: bool = False

class SimulatedHardware:
    """Simula todos os componentes de hardware do ESP32"""
    
    def __init__(self):
        self.leds = {
            'system_active': False,
            'alert': False,
            'release': False
        }
        
        self.servos = {
            'flaps_left': SimulatedServoState('flaps_left'),
            'flaps_right': SimulatedServoState('flaps_right'),
            'elevator': SimulatedServoState('elevator'),
            'rudder': SimulatedServoState('rudder'),
            'release': SimulatedServoState('release')
        }
        
        self.sensor_data = SimulatedSensorData()
        self.rc_signal = 1500  # Neutro
        self.system_time = 0
        
        # Simular perturbações no voo
        self.disturbance_amplitude = 5.0
        self.disturbance_frequency = 0.1
        
        logger.info("Hardware simulado inicializado")
    
    def set_led(self, led_name: str, state: bool):
        """Simula controle de LED"""
        if led_name in self.leds:
            self.leds[led_name] = state
            status = "LIGADO" if state else "DESLIGADO"
            logger.debug(f"LED {led_name}: {status}")
    
    def set_servo_angle(self, servo_name: str, angle: float):
        """Simula movimento de servo"""
        if servo_name in self.servos:
            # Limitar ângulo
            angle = max(30, min(150, angle))
            self.servos[servo_name].target_angle = angle
            self.servos[servo_name].moving = True
            logger.debug(f"Servo {servo_name}: {angle:.1f}°")
    
    def update_sensor_data(self, dt: float):
        """Atualiza dados do sensor com física simplificada"""
        self.system_time += dt
        
        # Simular perturbações naturais do voo
        base_roll = math.sin(self.system_time * self.disturbance_frequency) * self.disturbance_amplitude
        base_pitch = math.cos(self.system_time * self.disturbance_frequency * 0.7) * self.disturbance_amplitude * 0.5
        base_yaw_rate = math.sin(self.system_time * self.disturbance_frequency * 1.3) * 2.0
        
        # Simular efeito dos servos na estabilização
        servo_effect_roll = (self.servos['flaps_right'].current_angle - self.servos['flaps_left'].current_angle) * 0.1
        servo_effect_pitch = (90 - self.servos['elevator'].current_angle) * 0.1
        servo_effect_yaw = (self.servos['rudder'].current_angle - 90) * 0.05
        
        # Aplicar física simplificada (servos corrigem perturbações)
        self.sensor_data.roll = base_roll - servo_effect_roll
        self.sensor_data.pitch = base_pitch - servo_effect_pitch
        self.sensor_data.yaw_rate = base_yaw_rate - servo_effect_yaw
        self.sensor_data.timestamp = self.system_time
    
    def update_servos(self, dt: float):
        """Atualiza posição dos servos simulados"""
        servo_speed = 180.0  # graus por segundo
        
        for servo in self.servos.values():
            if servo.moving:
                diff = servo.target_angle - servo.current_angle
                if abs(diff) < servo_speed * dt:
                    servo.current_angle = servo.target_angle
                    servo.moving = False
                else:
                    servo.current_angle += math.copysign(servo_speed * dt, diff)
    
    def get_sensor_data(self) -> Tuple[float, float, float, bool]:
        """Retorna dados do sensor no formato esperado"""
        return (
            self.sensor_data.roll,
            self.sensor_data.pitch, 
            self.sensor_data.yaw_rate,
            True  # Sempre válido no simulador
        )
    
    def set_rc_signal(self, signal: int):
        """Simula sinal RC"""
        self.rc_signal = max(800, min(2200, signal))
    
    def get_rc_signal(self) -> int:
        """Retorna sinal RC atual"""
        return self.rc_signal

class PlanadorSimulator:
    """Simulador principal do sistema planador"""
    
    def __init__(self):
        self.hardware = SimulatedHardware()
        self.running = False
        self.pid_integral = [0.0, 0.0, 0.0]
        
        # Configurações do PID (do arquivo config.py)
        self.gains = (2.0, 0.15, 1.0, 2.5, 0.18, 1.2, 1.2, 0.06, 0.5)
        self.limits = (25, 30, 18)
        
        # Estatísticas
        self.loop_count = 0
        self.start_time = time.time()
        
        logger.info("Simulador do planador inicializado")
    
    def angle_to_duty(self, angle: float) -> int:
        """Converte ângulo para duty cycle (compatibilidade)"""
        return int(40 + (angle * 75) // 180)
    
    def calculate_pid(self, roll: float, pitch: float, yaw_rate: float) -> Tuple[float, float, float]:
        """Calcula saída do PID (mesmo algoritmo do ESP32)"""
        # Erros
        roll_error = -roll
        pitch_error = -pitch
        yaw_error = -yaw_rate
        
        # Integral
        self.pid_integral[0] += roll_error * 0.02
        self.pid_integral[1] += pitch_error * 0.02
        self.pid_integral[2] += yaw_error * 0.02
        
        # Limitar integral
        for i in range(3):
            self.pid_integral[i] = max(-10, min(10, self.pid_integral[i]))
        
        # Saída PID
        roll_out = self.gains[0] * roll_error + self.gains[1] * self.pid_integral[0]
        pitch_out = self.gains[3] * pitch_error + self.gains[4] * self.pid_integral[1]
        yaw_out = self.gains[6] * yaw_error + self.gains[7] * self.pid_integral[2]
        
        # Limitar saída
        roll_out = max(-self.limits[0], min(self.limits[0], roll_out))
        pitch_out = max(-self.limits[1], min(self.limits[1], pitch_out))
        yaw_out = max(-self.limits[2], min(self.limits[2], yaw_out))
        
        return (roll_out, pitch_out, yaw_out)
    
    def calculate_servo_commands(self, roll: float, pitch: float, yaw_rate: float) -> List[int]:
        """Calcula comandos dos servos"""
        pid_out = self.calculate_pid(roll, pitch, yaw_rate)
        
        flaps_left = 90 - pid_out[0]
        flaps_right = 90 + pid_out[0]
        elevator = 90 - pid_out[1]
        rudder = 90 + pid_out[2]
        
        return [
            max(30, min(150, int(flaps_left))),
            max(30, min(150, int(flaps_right))),
            max(30, min(150, int(elevator))),
            max(30, min(150, int(rudder)))
        ]
    
    def main_loop_iteration(self, dt: float):
        """Uma iteração do loop principal"""
        # Atualizar hardware simulado
        self.hardware.update_sensor_data(dt)
        self.hardware.update_servos(dt)
        
        # Ler sensores
        roll, pitch, yaw_rate, valid = self.hardware.get_sensor_data()
        
        # Calcular comandos de controle
        commands = self.calculate_servo_commands(roll, pitch, yaw_rate)
        
        # Aplicar comandos aos servos
        servo_names = ['flaps_left', 'flaps_right', 'elevator', 'rudder']
        for i, name in enumerate(servo_names):
            self.hardware.set_servo_angle(name, commands[i])
        
        # Atualizar LEDs
        self.hardware.set_led('system_active', True)
        
        self.loop_count += 1
        
        # Log periódico
        if self.loop_count % 100 == 0:
            elapsed = time.time() - self.start_time
            freq = self.loop_count / elapsed if elapsed > 0 else 0
            logger.info(f"Loop {self.loop_count}: R:{roll:.1f}° P:{pitch:.1f}° Y:{yaw_rate:.1f}°/s | Freq: {freq:.1f}Hz")
    
    def run_simulation(self, duration: float = 30.0, target_freq: float = 50.0):
        """Executa simulação por um período determinado"""
        logger.info(f"Iniciando simulação por {duration}s a {target_freq}Hz")
        
        self.running = True
        self.start_time = time.time()
        dt = 1.0 / target_freq
        
        try:
            while self.running and (time.time() - self.start_time) < duration:
                loop_start = time.time()
                
                self.main_loop_iteration(dt)
                
                # Controlar frequência
                loop_time = time.time() - loop_start
                sleep_time = dt - loop_time
                if sleep_time > 0:
                    time.sleep(sleep_time)
            
            elapsed = time.time() - self.start_time
            actual_freq = self.loop_count / elapsed
            logger.info(f"Simulação concluída: {self.loop_count} loops em {elapsed:.2f}s ({actual_freq:.1f}Hz)")
            
        except KeyboardInterrupt:
            logger.info("Simulação interrompida pelo usuário")
        finally:
            self.running = False
    
    def get_status(self) -> Dict:
        """Retorna status atual do simulador"""
        elapsed = time.time() - self.start_time if self.start_time else 0
        return {
            'running': self.running,
            'loop_count': self.loop_count,
            'elapsed_time': elapsed,
            'frequency': self.loop_count / elapsed if elapsed > 0 else 0,
            'sensor_data': {
                'roll': self.hardware.sensor_data.roll,
                'pitch': self.hardware.sensor_data.pitch,
                'yaw_rate': self.hardware.sensor_data.yaw_rate
            },
            'servo_positions': {
                name: servo.current_angle 
                for name, servo in self.hardware.servos.items()
            },
            'leds': self.hardware.leds.copy()
        }

def simulate_disturbance_scenario():
    """Simula cenário com perturbações externas"""
    logger.info("=== CENÁRIO: Perturbações Externas ===")
    
    sim = PlanadorSimulator()
    
    # Aumentar perturbações
    sim.hardware.disturbance_amplitude = 15.0
    sim.hardware.disturbance_frequency = 0.2
    
    sim.run_simulation(duration=20.0, target_freq=50.0)

def simulate_rc_release_test():
    """Simula teste de liberação via RC"""
    logger.info("=== CENÁRIO: Teste de Liberação RC ===")
    
    sim = PlanadorSimulator()
    
    def rc_sequence():
        """Simula sequência de sinais RC"""
        time.sleep(3)  # Sistema estabiliza
        
        logger.info("RC: Ativando liberação...")
        sim.hardware.set_rc_signal(1800)  # Sinal alto
        time.sleep(2)
        
        logger.info("RC: Liberação executada")
        sim.hardware.set_servo_angle('release', 135)  # Posição liberado
        time.sleep(1)
        
        logger.info("RC: Retornando ao neutro")
        sim.hardware.set_rc_signal(1500)  # Neutro
        sim.hardware.set_servo_angle('release', 45)   # Travado
    
    # Executar sequência RC em thread separada
    threading.Thread(target=rc_sequence, daemon=True).start()
    
    sim.run_simulation(duration=10.0, target_freq=50.0)

def main():
    """Função principal do simulador"""
    import sys
    
    logger.info("Simulador do Sistema Planador ESP32")
    logger.info("="*50)
    
    if len(sys.argv) > 1:
        scenario = sys.argv[1].lower()
        
        if scenario == "disturbance":
            simulate_disturbance_scenario()
        elif scenario == "release":
            simulate_rc_release_test()
        else:
            logger.error(f"Cenário desconhecido: {scenario}")
            logger.info("Cenários disponíveis: disturbance, release")
            return
    else:
        # Simulação padrão
        logger.info("=== SIMULAÇÃO PADRÃO ===")
        sim = PlanadorSimulator()
        sim.run_simulation(duration=15.0, target_freq=50.0)
        
        # Mostrar status final
        status = sim.get_status()
        logger.info("Status final:")
        logger.info(f"  Loops executados: {status['loop_count']}")
        logger.info(f"  Frequência média: {status['frequency']:.1f}Hz")
        logger.info(f"  Roll: {status['sensor_data']['roll']:.1f}°")
        logger.info(f"  Pitch: {status['sensor_data']['pitch']:.1f}°")

if __name__ == "__main__":
    main()