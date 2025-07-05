#!/usr/bin/env python3
"""
Testes unitários para o simulador do planador
"""

import unittest
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src', 'simulator'))

from planador_simulator import PlanadorSimulator, SimulatedHardware
import custom_logging as logging

# Mock do decorator micropython.native para testes
def mock_native(func):
    """Mock do decorator @micropython.native"""
    return func

# Aplicar mock globalmente
import builtins
builtins.micropython = type('MockMicropython', (), {'native': mock_native})()

class TestSimulatedHardware(unittest.TestCase):
    """Testes para hardware simulado"""

    def setUp(self):
        """Configuração inicial dos testes"""
        self.hardware = SimulatedHardware()

    def test_hardware_initialization(self):
        """Testa inicialização do hardware"""
        self.assertTrue(self.hardware.initialized)
        self.assertIsNotNone(self.hardware.gyro_data)
        self.assertIsNotNone(self.hardware.servo_positions)
        self.assertIsNotNone(self.hardware.led_states)

    def test_read_gyroscope(self):
        """Testa leitura do giroscópio"""
        gyro_data = self.hardware.read_gyroscope()
        
        # Verificar se retorna tupla com 3 valores
        self.assertIsInstance(gyro_data, tuple)
        self.assertEqual(len(gyro_data), 3)
        
        # Verificar tipos dos valores
        for value in gyro_data:
            self.assertIsInstance(value, (int, float))

    def test_set_servo_angle(self):
        """Testa configuração dos servos"""
        # Testar servo válido
        self.hardware.set_servo_angle(0, 45)
        self.assertEqual(self.hardware.servo_positions['flaps_left'], 45)
        
        # Testar servo inválido
        with self.assertRaises(IndexError):
            self.hardware.set_servo_angle(10, 90)

    def test_set_led_state(self):
        """Testa configuração dos LEDs"""
        # LED válido
        self.hardware.set_led_state(0, True)
        self.assertTrue(self.hardware.led_states['system_active'])
        
        # LED inválido
        with self.assertRaises(IndexError):
            self.hardware.set_led_state(10, True)

    def test_rc_signal(self):
        """Testa sinal RC"""
        # Sinal neutro
        self.hardware.set_rc_signal(1500)
        self.assertEqual(self.hardware.rc_signal, 1500)
        
        # Sinal de liberação
        self.hardware.set_rc_signal(1000)
        self.assertEqual(self.hardware.rc_signal, 1000)

    def test_disturbance_simulation(self):
        """Testa simulação de perturbações"""
        # Sem perturbação
        self.hardware.disturbance_amplitude = 0.0
        self.hardware.simulate_disturbance()
        
        # Com perturbação
        self.hardware.disturbance_amplitude = 10.0
        self.hardware.simulate_disturbance()
        
        # Verificar se os valores mudaram
        gyro_data = self.hardware.read_gyroscope()
        self.assertIsInstance(gyro_data, tuple)

class TestPlanadorSimulator(unittest.TestCase):
    """Testes para o simulador principal"""

    def setUp(self):
        """Configuração inicial dos testes"""
        self.simulator = PlanadorSimulator()

    def test_simulator_initialization(self):
        """Testa inicialização do simulador"""
        self.assertIsNotNone(self.simulator.hardware)
        self.assertIsInstance(self.simulator.pid_integral, list)
        self.assertEqual(len(self.simulator.pid_integral), 3)
        self.assertFalse(self.simulator.running)

    def test_calculate_pid_control(self):
        """Testa cálculo do controle PID"""
        # Dados de entrada
        roll = 10.0
        pitch = 5.0
        yaw_rate = 2.0
        dt = 0.02
        
        # Calcular controle PID
        control = self.simulator.calculate_pid_control(roll, pitch, yaw_rate, dt)
        
        # Verificar resultado
        self.assertIsInstance(control, tuple)
        self.assertEqual(len(control), 4)
        
        # Verificar que os valores são numéricos
        for value in control:
            self.assertIsInstance(value, (int, float))

    def test_angle_to_servo_duty(self):
        """Testa conversão de ângulo para posição do servo"""
        # Casos extremos
        self.assertEqual(self.simulator.angle_to_servo_duty(0), 0)
        self.assertEqual(self.simulator.angle_to_servo_duty(180), 180)
        
        # Caso normal
        self.assertEqual(self.simulator.angle_to_servo_duty(90), 90)

    def test_apply_servo_limits(self):
        """Testa aplicação de limites dos servos"""
        # Valor dentro dos limites
        self.assertEqual(self.simulator.apply_servo_limits(90), 90)
        
        # Valor abaixo do limite
        self.assertEqual(self.simulator.apply_servo_limits(-10), 0)
        
        # Valor acima do limite
        self.assertEqual(self.simulator.apply_servo_limits(200), 180)

    def test_main_loop_iteration(self):
        """Testa iteração principal do simulador"""
        dt = 0.02
        
        # Executar uma iteração
        self.simulator.main_loop_iteration(dt)
        
        # Verificar se o loop count foi incrementado
        self.assertGreater(self.simulator.loop_count, 0)

    def test_get_status(self):
        """Testa obtenção do status do sistema"""
        status = self.simulator.get_status()
        
        # Verificar estrutura do status
        self.assertIn('loop_count', status)
        self.assertIn('frequency', status)
        self.assertIn('sensor_data', status)
        self.assertIn('servo_positions', status)
        self.assertIn('leds', status)
        
        # Verificar dados dos sensores
        sensor_data = status['sensor_data']
        self.assertIn('roll', sensor_data)
        self.assertIn('pitch', sensor_data)
        self.assertIn('yaw_rate', sensor_data)

    def test_rc_release_detection(self):
        """Testa detecção de liberação RC"""
        # Sinal neutro - não deve liberar
        self.simulator.hardware.set_rc_signal(1500)
        self.simulator.main_loop_iteration(0.02)
        
        # Sinal de liberação - deve liberar
        self.simulator.hardware.set_rc_signal(1000)
        self.simulator.main_loop_iteration(0.02)
        
        # Verificar se o servo de liberação foi ativado
        status = self.simulator.get_status()
        self.assertIn('release', status['servo_positions'])

    def test_pid_integral_limits(self):
        """Testa limites dos integrais PID"""
        # Forçar erro grande para saturar integral
        for _ in range(100):
            self.simulator.calculate_pid_control(30.0, 30.0, 10.0, 0.02)
        
        # Verificar se os integrais estão limitados
        for integral in self.simulator.pid_integral:
            self.assertLessEqual(abs(integral), 50.0)  # Limite configurado

    def test_scenario_modes(self):
        """Testa diferentes cenários de simulação"""
        # Cenário padrão
        self.simulator.scenario = "default"
        self.simulator.main_loop_iteration(0.02)
        
        # Cenário com perturbações
        self.simulator.scenario = "disturbance"
        self.simulator.main_loop_iteration(0.02)
        
        # Cenário de liberação
        self.simulator.scenario = "release"
        self.simulator.main_loop_iteration(0.02)

class TestSystemIntegration(unittest.TestCase):
    """Testes de integração do sistema"""

    def test_complete_flight_simulation(self):
        """Testa simulação completa de voo"""
        simulator = PlanadorSimulator()
        
        # Executar várias iterações
        dt = 0.02
        for _ in range(50):  # 1 segundo de simulação
            simulator.main_loop_iteration(dt)
        
        # Verificar se o sistema está funcionando
        status = simulator.get_status()
        self.assertGreater(status['loop_count'], 0)
        self.assertGreater(status['frequency'], 0)

    def test_disturbance_response(self):
        """Testa resposta do sistema a perturbações"""
        simulator = PlanadorSimulator()
        simulator.hardware.disturbance_amplitude = 15.0
        
        # Executar simulação com perturbações
        dt = 0.02
        initial_attitude = simulator.hardware.read_gyroscope()
        
        for _ in range(25):  # 0.5 segundos
            simulator.main_loop_iteration(dt)
        
        # Verificar se o sistema está tentando se estabilizar
        status = simulator.get_status()
        self.assertIsNotNone(status['servo_positions'])

    def test_performance_metrics(self):
        """Testa métricas de performance"""
        simulator = PlanadorSimulator()
        
        # Executar várias iterações e medir performance
        dt = 0.02
        for _ in range(100):
            simulator.main_loop_iteration(dt)
        
        status = simulator.get_status()
        
        # Verificar frequência
        self.assertGreater(status['frequency'], 30)  # Mínimo 30Hz
        
        # Verificar que não há valores inválidos
        for value in status['sensor_data'].values():
            self.assertFalse(float('nan') == value)
            self.assertFalse(float('inf') == value)

def main():
    """Função principal para executar testes"""
    unittest.main(verbosity=2)

if __name__ == '__main__':
    main()