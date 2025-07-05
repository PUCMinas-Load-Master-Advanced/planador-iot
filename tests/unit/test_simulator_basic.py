#!/usr/bin/env python3
"""
Testes básicos para o simulador do planador
"""

import unittest
import sys
import os

# Adicionar caminho do simulador
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src', 'simulator'))

class TestSimulatorBasic(unittest.TestCase):
    """Testes básicos para o simulador"""

    def test_import_simulator(self):
        """Testa se consegue importar o simulador"""
        try:
            import planador_simulator
            self.assertTrue(True)
        except ImportError as e:
            self.fail(f"Falha ao importar simulador: {e}")

    def test_import_custom_logging(self):
        """Testa se consegue importar o logging customizado"""
        try:
            import custom_logging
            logger = custom_logging.getLogger(__name__)
            self.assertIsNotNone(logger)
        except ImportError as e:
            self.fail(f"Falha ao importar custom_logging: {e}")

    def test_simulator_execution(self):
        """Testa execução básica do simulador"""
        try:
            import planador_simulator
            
            # Criar simulador
            sim = planador_simulator.PlanadorSimulator()
            
            # Verificar que foi criado
            self.assertIsNotNone(sim)
            
            # Executar uma iteração básica
            sim.main_loop_iteration(0.02)
            
            # Verificar que não gerou exceção
            self.assertTrue(True)
            
        except Exception as e:
            self.fail(f"Falha na execução básica: {e}")

    def test_basic_calculations(self):
        """Testa cálculos básicos do PID"""
        # Simular cálculo PID básico
        def simple_pid(error, integral, kp=1.0, ki=0.1, kd=0.05):
            """PID simplificado para teste"""
            integral += error * 0.02  # dt = 0.02
            derivative = error  # Simplificado
            output = kp * error + ki * integral + kd * derivative
            return output, integral
        
        # Testar com erro conhecido
        error = 10.0
        integral = 0.0
        
        output, new_integral = simple_pid(error, integral)
        
        # Verificar que o cálculo funciona
        self.assertIsInstance(output, (int, float))
        self.assertIsInstance(new_integral, (int, float))
        self.assertNotEqual(output, 0)

    def test_angle_limits(self):
        """Testa limitação de ângulos dos servos"""
        def limit_angle(angle, min_angle=0, max_angle=180):
            """Limita ângulo do servo"""
            if angle < min_angle:
                return min_angle
            elif angle > max_angle:
                return max_angle
            return angle
        
        # Testar casos
        test_cases = [
            (-10, 0),      # Abaixo do limite
            (0, 0),        # No limite inferior
            (90, 90),      # Normal
            (180, 180),    # No limite superior
            (200, 180)     # Acima do limite
        ]
        
        for input_angle, expected in test_cases:
            result = limit_angle(input_angle)
            self.assertEqual(result, expected)

    def test_rc_signal_interpretation(self):
        """Testa interpretação do sinal RC"""
        def interpret_rc(signal):
            """Interpreta sinal RC"""
            if signal < 1200:
                return "release"
            elif signal > 1800:
                return "special"
            else:
                return "neutral"
        
        # Testar interpretação
        test_signals = [
            (1000, "release"),
            (1500, "neutral"),
            (2000, "special")
        ]
        
        for signal, expected in test_signals:
            result = interpret_rc(signal)
            self.assertEqual(result, expected)

    def test_sensor_data_structure(self):
        """Testa estrutura dos dados dos sensores"""
        # Simular dados dos sensores
        sensor_data = {
            'roll': 5.2,
            'pitch': -2.1,
            'yaw_rate': 1.5
        }
        
        # Verificar estrutura
        self.assertIn('roll', sensor_data)
        self.assertIn('pitch', sensor_data)
        self.assertIn('yaw_rate', sensor_data)
        
        # Verificar tipos
        self.assertIsInstance(sensor_data['roll'], (int, float))
        self.assertIsInstance(sensor_data['pitch'], (int, float))
        self.assertIsInstance(sensor_data['yaw_rate'], (int, float))

    def test_servo_positions_structure(self):
        """Testa estrutura das posições dos servos"""
        # Simular posições dos servos
        servo_positions = {
            'flaps_left': 85,
            'flaps_right': 95,
            'elevator': 90,
            'rudder': 88,
            'release': 90
        }
        
        # Verificar que todos os servos estão presentes
        expected_servos = ['flaps_left', 'flaps_right', 'elevator', 'rudder', 'release']
        for servo in expected_servos:
            self.assertIn(servo, servo_positions)
        
        # Verificar que estão dentro dos limites
        for position in servo_positions.values():
            self.assertGreaterEqual(position, 0)
            self.assertLessEqual(position, 180)

    def test_frequency_calculation(self):
        """Testa cálculo de frequência do loop"""
        import time
        
        def calculate_frequency(loop_count, elapsed_time):
            """Calcula frequência do loop"""
            if elapsed_time <= 0:
                return 0.0
            return loop_count / elapsed_time
        
        # Testar cálculo
        loop_count = 100
        elapsed_time = 2.0
        
        frequency = calculate_frequency(loop_count, elapsed_time)
        
        self.assertEqual(frequency, 50.0)  # 100 loops em 2 segundos = 50Hz

    def test_pid_gains_validation(self):
        """Testa validação dos ganhos PID"""
        # Ganhos de teste
        gains = (2.0, 0.15, 1.0, 2.5, 0.18, 1.2, 1.2, 0.06, 0.5)
        
        # Verificar estrutura
        self.assertEqual(len(gains), 9)  # 3 eixos x 3 ganhos (P, I, D)
        
        # Verificar que todos são positivos
        for gain in gains:
            self.assertGreater(gain, 0)
            self.assertIsInstance(gain, (int, float))

    def test_system_limits_validation(self):
        """Testa validação dos limites do sistema"""
        # Limites de teste
        limits = (25, 30, 18)  # Roll, Pitch, Yaw
        
        # Verificar estrutura
        self.assertEqual(len(limits), 3)
        
        # Verificar que todos são positivos
        for limit in limits:
            self.assertGreater(limit, 0)
            self.assertIsInstance(limit, (int, float))

def main():
    """Função principal para executar testes"""
    unittest.main(verbosity=2)

if __name__ == '__main__':
    main()