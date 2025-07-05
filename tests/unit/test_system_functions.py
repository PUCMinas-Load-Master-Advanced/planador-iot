#!/usr/bin/env python3
"""
Testes unitários para funções específicas do sistema
"""

import unittest
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src', 'simulator'))

# Mock do decorator micropython.native para testes
def mock_native(func):
    """Mock do decorator @micropython.native"""
    return func

# Aplicar mock globalmente
import builtins
builtins.micropython = type('MockMicropython', (), {'native': mock_native})()

class TestSystemFunctions(unittest.TestCase):
    """Testes para funções específicas do sistema"""

    def test_pid_calculation_precision(self):
        """Testa precisão dos cálculos PID"""
        # Importar após configurar o mock
        from planador_simulator import PlanadorSimulator
        
        simulator = PlanadorSimulator()
        
        # Teste com valores conhecidos
        roll = 10.0
        pitch = 5.0
        yaw_rate = 2.0
        dt = 0.02
        
        # Calcular controle PID
        control = simulator.calculate_pid_control(roll, pitch, yaw_rate, dt)
        
        # Verificar que os valores são razoáveis
        self.assertIsInstance(control, tuple)
        self.assertEqual(len(control), 4)
        
        # Verificar que os valores estão dentro de limites esperados
        for value in control:
            self.assertGreaterEqual(value, -50)
            self.assertLessEqual(value, 50)

    def test_servo_angle_conversion(self):
        """Testa conversão de ângulos dos servos"""
        from planador_simulator import PlanadorSimulator
        
        simulator = PlanadorSimulator()
        
        # Testar conversões específicas
        test_cases = [
            (0, 0),      # Mínimo
            (90, 90),    # Neutro
            (180, 180),  # Máximo
            (45, 45),    # Intermediário
            (135, 135)   # Intermediário
        ]
        
        for input_angle, expected in test_cases:
            result = simulator.angle_to_servo_duty(input_angle)
            self.assertEqual(result, expected)

    def test_servo_limits_enforcement(self):
        """Testa aplicação rigorosa de limites dos servos"""
        from planador_simulator import PlanadorSimulator
        
        simulator = PlanadorSimulator()
        
        # Testar casos extremos
        extreme_cases = [
            (-100, 0),   # Muito abaixo
            (-1, 0),     # Ligeiramente abaixo
            (0, 0),      # Limite inferior
            (90, 90),    # Neutro
            (180, 180),  # Limite superior
            (181, 180),  # Ligeiramente acima
            (300, 180)   # Muito acima
        ]
        
        for input_value, expected in extreme_cases:
            result = simulator.apply_servo_limits(input_value)
            self.assertEqual(result, expected)

    def test_pid_integral_windup_protection(self):
        """Testa proteção contra windup dos integrais PID"""
        from planador_simulator import PlanadorSimulator
        
        simulator = PlanadorSimulator()
        
        # Aplicar erro constante grande por muito tempo
        large_error = 45.0
        dt = 0.02
        
        for _ in range(500):  # 10 segundos de erro constante
            simulator.calculate_pid_control(large_error, large_error, large_error, dt)
        
        # Verificar que os integrais estão limitados
        for integral in simulator.pid_integral:
            self.assertLessEqual(abs(integral), 50.0)

    def test_frequency_calculation(self):
        """Testa cálculo da frequência de loop"""
        from planador_simulator import PlanadorSimulator
        import time
        
        simulator = PlanadorSimulator()
        simulator.start_time = time.time()
        
        # Executar algumas iterações
        dt = 0.02
        for _ in range(50):
            simulator.main_loop_iteration(dt)
        
        status = simulator.get_status()
        
        # Verificar se a frequência está sendo calculada
        self.assertGreater(status['frequency'], 0)
        self.assertLess(status['frequency'], 100)  # Limite razoável

    def test_sensor_data_validation(self):
        """Testa validação dos dados dos sensores"""
        from planador_simulator import PlanadorSimulator
        
        simulator = PlanadorSimulator()
        
        # Obter dados dos sensores
        gyro_data = simulator.hardware.read_gyroscope()
        
        # Verificar que os dados são válidos
        self.assertIsInstance(gyro_data, tuple)
        self.assertEqual(len(gyro_data), 3)
        
        for value in gyro_data:
            self.assertIsInstance(value, (int, float))
            self.assertFalse(float('nan') == value)
            self.assertFalse(float('inf') == value)

    def test_rc_signal_processing(self):
        """Testa processamento do sinal RC"""
        from planador_simulator import PlanadorSimulator
        
        simulator = PlanadorSimulator()
        
        # Testar diferentes valores de RC
        test_values = [800, 1000, 1200, 1500, 1800, 2000, 2200]
        
        for rc_value in test_values:
            simulator.hardware.set_rc_signal(rc_value)
            self.assertEqual(simulator.hardware.rc_signal, rc_value)
            
            # Executar uma iteração para processar o sinal
            simulator.main_loop_iteration(0.02)

    def test_led_state_management(self):
        """Testa gerenciamento dos estados dos LEDs"""
        from planador_simulator import PlanadorSimulator
        
        simulator = PlanadorSimulator()
        
        # Testar diferentes estados
        simulator.hardware.set_led_state(0, True)  # Sistema ativo
        simulator.hardware.set_led_state(1, False) # Alerta
        simulator.hardware.set_led_state(2, True)  # Liberação
        
        status = simulator.get_status()
        
        # Verificar estados
        self.assertTrue(status['leds']['system_active'])
        self.assertFalse(status['leds']['alert'])
        self.assertTrue(status['leds']['release'])

    def test_disturbance_amplitude_effects(self):
        """Testa efeitos da amplitude de perturbação"""
        from planador_simulator import PlanadorSimulator
        
        simulator = PlanadorSimulator()
        
        # Testar diferentes amplitudes
        amplitudes = [0.0, 5.0, 10.0, 15.0, 20.0]
        
        for amplitude in amplitudes:
            simulator.hardware.disturbance_amplitude = amplitude
            
            # Executar algumas iterações
            for _ in range(10):
                simulator.main_loop_iteration(0.02)
            
            # Verificar que o sistema ainda está funcionando
            status = simulator.get_status()
            self.assertIsNotNone(status)

    def test_servo_response_timing(self):
        """Testa tempo de resposta dos servos"""
        from planador_simulator import PlanadorSimulator
        
        simulator = PlanadorSimulator()
        
        # Aplicar mudança súbita
        simulator.hardware.gyro_data = (20.0, 15.0, 5.0)
        
        # Executar uma iteração
        simulator.main_loop_iteration(0.02)
        
        status = simulator.get_status()
        
        # Verificar que os servos responderam
        servos = status['servo_positions']
        
        # Pelo menos um servo deve ter saído da posição neutra
        servo_values = [servos['flaps_left'], servos['flaps_right'], 
                       servos['elevator'], servos['rudder']]
        
        # Verificar que há resposta
        self.assertTrue(any(abs(servo - 90) > 1 for servo in servo_values))

class TestErrorHandling(unittest.TestCase):
    """Testes para tratamento de erros"""

    def test_invalid_servo_index(self):
        """Testa tratamento de índice inválido de servo"""
        from planador_simulator import SimulatedHardware
        
        hardware = SimulatedHardware()
        
        # Testar índice inválido
        with self.assertRaises(IndexError):
            hardware.set_servo_angle(999, 90)

    def test_invalid_led_index(self):
        """Testa tratamento de índice inválido de LED"""
        from planador_simulator import SimulatedHardware
        
        hardware = SimulatedHardware()
        
        # Testar índice inválido
        with self.assertRaises(IndexError):
            hardware.set_led_state(999, True)

    def test_extreme_sensor_values(self):
        """Testa tratamento de valores extremos dos sensores"""
        from planador_simulator import PlanadorSimulator
        
        simulator = PlanadorSimulator()
        
        # Testar valores extremos
        extreme_values = [
            (1000.0, 1000.0, 1000.0),  # Muito grandes
            (-1000.0, -1000.0, -1000.0),  # Muito pequenos
            (0.0, 0.0, 0.0),  # Zeros
        ]
        
        for roll, pitch, yaw in extreme_values:
            # Não deve gerar exceção
            control = simulator.calculate_pid_control(roll, pitch, yaw, 0.02)
            self.assertIsInstance(control, tuple)

    def test_zero_dt_handling(self):
        """Testa tratamento de dt zero"""
        from planador_simulator import PlanadorSimulator
        
        simulator = PlanadorSimulator()
        
        # dt zero não deve causar divisão por zero
        control = simulator.calculate_pid_control(10.0, 5.0, 2.0, 0.0)
        self.assertIsInstance(control, tuple)

def main():
    """Função principal para executar testes"""
    unittest.main(verbosity=2)

if __name__ == '__main__':
    main()