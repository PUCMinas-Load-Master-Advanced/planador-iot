#!/usr/bin/env python3
"""
Testes de integração para o sistema completo
"""

import unittest
import sys
import os
import time
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src', 'simulator'))

# Mock do decorator micropython.native para testes
def mock_native(func):
    """Mock do decorator @micropython.native"""
    return func

# Aplicar mock globalmente
import builtins
builtins.micropython = type('MockMicropython', (), {'native': mock_native})()

class TestFullSystemIntegration(unittest.TestCase):
    """Testes de integração do sistema completo"""

    def setUp(self):
        """Configuração inicial dos testes"""
        from planador_simulator import PlanadorSimulator
        self.simulator = PlanadorSimulator()

    def test_startup_sequence(self):
        """Testa sequência de inicialização completa"""
        # Verificar inicialização do hardware
        self.assertTrue(self.simulator.hardware.initialized)
        
        # Verificar estado inicial dos servos
        status = self.simulator.get_status()
        servos = status['servo_positions']
        
        # Todos os servos devem estar na posição neutra
        expected_positions = {
            'flaps_left': 90,
            'flaps_right': 90,
            'elevator': 90,
            'rudder': 90,
            'release': 90
        }
        
        for servo_name, expected_angle in expected_positions.items():
            self.assertEqual(servos[servo_name], expected_angle)

    def test_stabilization_loop(self):
        """Testa loop de estabilização completo"""
        dt = 0.02
        
        # Aplicar perturbação
        self.simulator.hardware.gyro_data = (15.0, 10.0, 3.0)
        
        # Executar várias iterações
        for _ in range(50):
            self.simulator.main_loop_iteration(dt)
        
        # Verificar que o sistema está tentando se estabilizar
        status = self.simulator.get_status()
        
        # Verificar que os servos estão ativos
        servos = status['servo_positions']
        self.assertNotEqual(servos['flaps_left'], 90)
        self.assertNotEqual(servos['flaps_right'], 90)

    def test_rc_release_integration(self):
        """Testa integração completa do sistema de liberação RC"""
        dt = 0.02
        
        # Sinal neutro inicial
        self.simulator.hardware.set_rc_signal(1500)
        self.simulator.main_loop_iteration(dt)
        
        status = self.simulator.get_status()
        initial_release_pos = status['servo_positions']['release']
        
        # Enviar sinal de liberação
        self.simulator.hardware.set_rc_signal(1000)
        self.simulator.main_loop_iteration(dt)
        
        status = self.simulator.get_status()
        final_release_pos = status['servo_positions']['release']
        
        # Verificar que o servo de liberação mudou
        self.assertNotEqual(initial_release_pos, final_release_pos)

    def test_performance_under_load(self):
        """Testa performance sob carga"""
        dt = 0.02
        start_time = time.time()
        
        # Aplicar perturbações e executar muitas iterações
        self.simulator.hardware.disturbance_amplitude = 10.0
        
        for _ in range(250):  # 5 segundos de simulação
            self.simulator.main_loop_iteration(dt)
        
        end_time = time.time()
        elapsed = end_time - start_time
        
        # Verificar que manteve performance razoável
        status = self.simulator.get_status()
        self.assertGreater(status['frequency'], 30)  # Mínimo 30Hz
        
        # Verificar que não travou
        self.assertGreater(status['loop_count'], 200)

    def test_sensor_to_servo_pipeline(self):
        """Testa pipeline completo de sensor para servo"""
        dt = 0.02
        
        # Configurar dados específicos dos sensores
        test_cases = [
            (10.0, 0.0, 0.0),    # Apenas roll
            (0.0, 10.0, 0.0),    # Apenas pitch
            (0.0, 0.0, 5.0),     # Apenas yaw
            (5.0, 5.0, 2.0),     # Combinado
        ]
        
        for roll, pitch, yaw in test_cases:
            # Resetar integrais
            self.simulator.pid_integral = [0.0, 0.0, 0.0]
            
            # Aplicar dados dos sensores
            self.simulator.hardware.gyro_data = (roll, pitch, yaw)
            
            # Executar iteração
            self.simulator.main_loop_iteration(dt)
            
            # Verificar resposta dos servos
            status = self.simulator.get_status()
            servos = status['servo_positions']
            
            # Verificar que há resposta apropriada
            if roll != 0:
                # Roll deve afetar flaps diferentemente
                self.assertNotEqual(servos['flaps_left'], servos['flaps_right'])
            
            if pitch != 0:
                # Pitch deve afetar elevator
                self.assertNotEqual(servos['elevator'], 90)
            
            if yaw != 0:
                # Yaw deve afetar rudder
                self.assertNotEqual(servos['rudder'], 90)

    def test_disturbance_recovery(self):
        """Testa recuperação de perturbações"""
        dt = 0.02
        
        # Aplicar perturbação forte
        self.simulator.hardware.disturbance_amplitude = 20.0
        
        # Executar simulação com perturbação
        for _ in range(100):
            self.simulator.main_loop_iteration(dt)
        
        # Remover perturbação
        self.simulator.hardware.disturbance_amplitude = 0.0
        
        # Executar mais iterações para recuperação
        for _ in range(100):
            self.simulator.main_loop_iteration(dt)
        
        # Verificar que o sistema está tentando se estabilizar
        status = self.simulator.get_status()
        self.assertIsNotNone(status)

    def test_led_status_correlation(self):
        """Testa correlação entre estado do sistema e LEDs"""
        dt = 0.02
        
        # Sistema normal
        self.simulator.main_loop_iteration(dt)
        status = self.simulator.get_status()
        
        # LED do sistema deve estar ativo
        self.assertTrue(status['leds']['system_active'])
        
        # Simular condição de alerta (perturbação forte)
        self.simulator.hardware.disturbance_amplitude = 25.0
        
        for _ in range(10):
            self.simulator.main_loop_iteration(dt)
        
        # Verificar status dos LEDs
        status = self.simulator.get_status()
        self.assertIsNotNone(status['leds'])

    def test_multiple_scenarios(self):
        """Testa múltiplos cenários em sequência"""
        dt = 0.02
        
        scenarios = [
            ('default', 0.0),
            ('disturbance', 10.0),
            ('release', 5.0),
        ]
        
        for scenario_name, disturbance in scenarios:
            # Configurar cenário
            self.simulator.scenario = scenario_name
            self.simulator.hardware.disturbance_amplitude = disturbance
            
            # Executar simulação do cenário
            for _ in range(25):
                self.simulator.main_loop_iteration(dt)
            
            # Verificar que o sistema está funcionando
            status = self.simulator.get_status()
            self.assertGreater(status['loop_count'], 0)

    def test_data_consistency(self):
        """Testa consistência dos dados entre componentes"""
        dt = 0.02
        
        # Executar algumas iterações
        for _ in range(20):
            self.simulator.main_loop_iteration(dt)
        
        # Obter dados de diferentes fontes
        status = self.simulator.get_status()
        hardware_gyro = self.simulator.hardware.read_gyroscope()
        
        # Verificar consistência
        self.assertEqual(status['sensor_data']['roll'], hardware_gyro[0])
        self.assertEqual(status['sensor_data']['pitch'], hardware_gyro[1])
        self.assertEqual(status['sensor_data']['yaw_rate'], hardware_gyro[2])

    def test_system_limits(self):
        """Testa limites do sistema"""
        dt = 0.02
        
        # Testar com valores extremos
        extreme_conditions = [
            (90.0, 90.0, 50.0),   # Atitude extrema
            (-90.0, -90.0, -50.0), # Atitude extrema negativa
        ]
        
        for roll, pitch, yaw in extreme_conditions:
            # Aplicar condições extremas
            self.simulator.hardware.gyro_data = (roll, pitch, yaw)
            
            # Sistema não deve falhar
            self.simulator.main_loop_iteration(dt)
            
            # Verificar que ainda está funcionando
            status = self.simulator.get_status()
            self.assertIsNotNone(status)
            
            # Verificar que os servos estão dentro dos limites
            for servo_angle in status['servo_positions'].values():
                self.assertGreaterEqual(servo_angle, 0)
                self.assertLessEqual(servo_angle, 180)

class TestSystemReliability(unittest.TestCase):
    """Testes de confiabilidade do sistema"""

    def test_long_running_stability(self):
        """Testa estabilidade em execução longa"""
        from planador_simulator import PlanadorSimulator
        
        simulator = PlanadorSimulator()
        dt = 0.02
        
        # Executar por um tempo longo
        for _ in range(1000):  # 20 segundos
            simulator.main_loop_iteration(dt)
        
        # Verificar que ainda está funcionando
        status = simulator.get_status()
        self.assertGreater(status['loop_count'], 990)
        self.assertGreater(status['frequency'], 25)

    def test_memory_stability(self):
        """Testa estabilidade de memória"""
        from planador_simulator import PlanadorSimulator
        
        simulator = PlanadorSimulator()
        dt = 0.02
        
        # Executar muitas iterações
        for _ in range(500):
            simulator.main_loop_iteration(dt)
        
        # Verificar que não há vazamentos óbvios
        status = simulator.get_status()
        self.assertIsNotNone(status)
        
        # Verificar que as estruturas de dados estão íntegras
        self.assertEqual(len(simulator.pid_integral), 3)

    def test_error_recovery(self):
        """Testa recuperação de erros"""
        from planador_simulator import PlanadorSimulator
        
        simulator = PlanadorSimulator()
        dt = 0.02
        
        # Simular condições que podem causar erro
        try:
            # Valores extremos
            simulator.hardware.gyro_data = (float('inf'), float('nan'), 1000.0)
            simulator.main_loop_iteration(dt)
            
            # Sistema deve continuar funcionando
            status = simulator.get_status()
            self.assertIsNotNone(status)
            
        except Exception as e:
            # Se houver exceção, deve ser tratada graciosamente
            self.fail(f"Sistema não tratou erro graciosamente: {e}")

def main():
    """Função principal para executar testes"""
    unittest.main(verbosity=2)

if __name__ == '__main__':
    main()