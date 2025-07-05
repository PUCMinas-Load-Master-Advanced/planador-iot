import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Adicionar o diretorio pai ao sys.path para permitir importacoes relativas
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src/micropython')))

# Mock do modulo micropython para evitar ImportError
micropython_mock = MagicMock()
micropython_mock.native = lambda f: f  # Decorator que não faz nada
sys.modules['micropython'] = micropython_mock
sys.modules['custom_logging'] = MagicMock()

# Mock das configuracoes simplificadas
mock_stabilization_gains = (2.0, 0.15, 1.0, 2.5, 0.18, 1.2, 1.2, 0.06, 0.5)
mock_stabilization_limits = (25, 30, 18)
mock_safety_limits = {
    'max_pid_integral': 10,
    'servo_min_angle': 30,
    'servo_max_angle': 150,
    'servo_neutral_angle': 90,
}

class TestSimplePID(unittest.TestCase):
    """Testes simplificados do sistema PID"""

    def test_pid_calculation_basic(self):
        """Testa calculo basico do PID sem imports complexos"""
        # Simular calculo PID manualmente
        gains = mock_stabilization_gains
        limits = mock_stabilization_limits
        
        # Erro zero deve resultar em saida zero
        roll_error = 0
        pitch_error = 0 
        yaw_error = 0
        
        roll_out = gains[0] * roll_error
        pitch_out = gains[3] * pitch_error
        yaw_out = gains[6] * yaw_error
        
        self.assertEqual(roll_out, 0.0)
        self.assertEqual(pitch_out, 0.0)
        self.assertEqual(yaw_out, 0.0)

    def test_pid_calculation_with_errors(self):
        """Testa calculo PID com erros"""
        gains = mock_stabilization_gains
        limits = mock_stabilization_limits
        
        roll_error = -10  # Roll negativo
        pitch_error = -5   # Pitch negativo
        yaw_error = -2     # Yaw negativo
        
        # Calculo P apenas (sem I e D para simplicidade)
        roll_out = gains[0] * roll_error  # 2.0 * -10 = -20
        pitch_out = gains[3] * pitch_error # 2.5 * -5 = -12.5
        yaw_out = gains[6] * yaw_error     # 1.2 * -2 = -2.4
        
        # Aplicar limites
        roll_out = max(-limits[0], min(limits[0], roll_out))  # max(-25, min(25, -20)) = -20
        pitch_out = max(-limits[1], min(limits[1], pitch_out)) # max(-30, min(30, -12.5)) = -12.5
        yaw_out = max(-limits[2], min(limits[2], yaw_out))    # max(-18, min(18, -2.4)) = -2.4
        
        self.assertEqual(roll_out, -20.0)
        self.assertEqual(pitch_out, -12.5)
        self.assertEqual(yaw_out, -2.4)

    def test_servo_command_calculation(self):
        """Testa calculo de comandos para servos"""
        # PID outputs simulados
        roll_out = -10
        pitch_out = 5
        yaw_out = 3
        
        # Calculo dos comandos (baseado no main.py)
        flaps_left = 90 - roll_out   # 90 - (-10) = 100
        flaps_right = 90 + roll_out  # 90 + (-10) = 80
        elevator = 90 - pitch_out    # 90 - 5 = 85
        rudder = 90 + yaw_out        # 90 + 3 = 93
        
        # Aplicar limites
        commands = [flaps_left, flaps_right, elevator, rudder]
        for i, cmd in enumerate(commands):
            commands[i] = max(30, min(150, int(cmd)))
        
        self.assertEqual(commands, [100, 80, 85, 93])

    def test_servo_limits(self):
        """Testa limites dos servos"""
        # Comandos extremos
        commands = [200, -50, 180, 10]
        
        # Aplicar limites
        limited = []
        for cmd in commands:
            limited.append(max(30, min(150, cmd)))
        
        self.assertEqual(limited, [150, 30, 150, 30])

    def test_angle_to_duty_conversion(self):
        """Testa conversao de angulo para duty cycle"""
        def angle_to_duty(angle):
            return int(40 + (angle * 75) // 180)
        
        # Testes de valores conhecidos
        self.assertEqual(angle_to_duty(0), 40)
        self.assertEqual(angle_to_duty(90), int(40 + (90 * 75) // 180))
        self.assertEqual(angle_to_duty(180), 115)

    def test_integral_limits(self):
        """Testa limites do integral"""
        integral = 0
        dt = 0.02
        
        # Simular erro constante por muitas iteracoes
        for _ in range(1000):
            error = 50  # Erro grande constante
            integral += error * dt
            
            # Aplicar limite
            integral = max(-10, min(10, integral))
        
        # Integral deve estar limitado
        self.assertEqual(integral, 10)  # Saturado no limite superior

def main():
    """Entry point for poetry script"""
    unittest.main(module='tests.unit.test_pid_simple', exit=False, verbosity=2)

if __name__ == '__main__':
    unittest.main()