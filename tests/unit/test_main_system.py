import unittest
from unittest.mock import patch, MagicMock, Mock
import sys
import os

# Adicionar o diretorio pai ao sys.path para permitir importacoes relativas
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src/micropython')))

# Mock do modulo micropython para evitar ImportError  
micropython_mock = MagicMock()
micropython_mock.native = lambda f: f  # Decorator que não faz nada
sys.modules['micropython'] = micropython_mock
sys.modules['machine'] = MagicMock()
sys.modules['time'] = MagicMock()
sys.modules['math'] = MagicMock()
sys.modules['struct'] = MagicMock()
sys.modules['gc'] = MagicMock()
sys.modules['custom_logging'] = MagicMock()

# Mock das configuracoes
mock_stabilization_gains = (2.0, 0.15, 1.0, 2.5, 0.18, 1.2, 1.2, 0.06, 0.5)
mock_stabilization_limits = (25, 30, 18)
mock_safety_limits = {
    'max_pid_integral': 10,
    'servo_min_angle': 30,
    'servo_max_angle': 150,
    'servo_neutral_angle': 90,
}
mock_release_config = {
    'locked_position': 45,
    'release_position': 135,
    'rc_threshold': 1700,
    'safety_delay': 2000,
    'auto_lock_time': 5000,
    'emergency_override': True
}

class TestPlanadorESP32(unittest.TestCase):
    
    @patch('config.STABILIZATION_GAINS', mock_stabilization_gains)
    @patch('config.STABILIZATION_LIMITS', mock_stabilization_limits)
    @patch('config.SAFETY_LIMITS', mock_safety_limits)
    @patch('config.RELEASE_CONFIG', mock_release_config)
    @patch('config.PLANADOR_SERVOS', {'flaps_left': 25, 'flaps_right': 26, 'elevator': 14, 'rudder': 27})
    @patch('config.LED_SYSTEM_ACTIVE', 15)
    @patch('config.LED_ALERT', 19)
    @patch('config.LED_RELEASE', 5)
    @patch('config.RELEASE_SERVO_PIN', 23)
    @patch('config.RC_RELEASE_PIN', 13)
    @patch('config.I2C_SDA', 21)
    @patch('config.I2C_SCL', 22)
    @patch('config.MPU6050_ADDR', 0x68)
    def setUp(self):
        from main import PlanadorESP32
        with patch.object(PlanadorESP32, 'run_tests'):
            self.planador = PlanadorESP32()

    def test_init_system_active(self):
        """Testa se o sistema inicia ativo automaticamente"""
        self.assertTrue(self.planador.system_active)

    def test_calculate_pid_basic(self):
        """Testa calculo basico do PID"""
        roll_out, pitch_out, yaw_out = self.planador.calculate_pid(0, 0, 0)
        self.assertEqual(roll_out, 0.0)
        self.assertEqual(pitch_out, 0.0) 
        self.assertEqual(yaw_out, 0.0)

    def test_calculate_pid_with_errors(self):
        """Testa calculo do PID com erros"""
        roll_out, pitch_out, yaw_out = self.planador.calculate_pid(10, 5, 2)
        # Com os ganhos mockados, devemos ter saidas proporcionais
        self.assertNotEqual(roll_out, 0.0)
        self.assertNotEqual(pitch_out, 0.0)
        self.assertNotEqual(yaw_out, 0.0)

    def test_calculate_commands(self):
        """Testa calculo de comandos para servos"""
        commands = self.planador.calculate_commands(0, 0, 0)
        self.assertEqual(len(commands), 4)
        # Com PID zero, todos devem estar em 90 graus
        for cmd in commands:
            self.assertEqual(cmd, 90)

    def test_angle_to_duty(self):
        """Testa conversao de angulo para duty cycle"""
        # Teste valores conhecidos
        self.assertEqual(self.planador.angle_to_duty(0), 40)
        self.assertEqual(self.planador.angle_to_duty(90), int(40 + (90 * 75) // 180))
        self.assertEqual(self.planador.angle_to_duty(180), 115)

    def test_servo_command_limits(self):
        """Testa se comandos dos servos respeitam limites"""
        # Simular erro grande para testar limites
        self.planador.pid_integral = [50, 50, 50]  # Integral grande
        commands = self.planador.calculate_commands(100, 100, 100)
        
        for cmd in commands:
            self.assertGreaterEqual(cmd, 30)  # Limite minimo
            self.assertLessEqual(cmd, 150)    # Limite maximo

    def test_handle_controls_no_button(self):
        """Testa controles sem botao (sempre ativo)"""
        initial_state = self.planador.system_active
        self.planador.handle_controls()
        # Sistema deve permanecer no mesmo estado
        self.assertEqual(self.planador.system_active, initial_state)

    def test_set_neutral(self):
        """Testa posicionamento neutro dos servos"""
        # Mock dos servos
        mock_servo = Mock()
        self.planador.servos = {'test_servo': mock_servo}
        
        self.planador.set_neutral()
        
        # Verificar se duty foi chamado com valor neutro (90 graus)
        expected_duty = self.planador.angle_to_duty(90)
        mock_servo.duty.assert_called_with(expected_duty)

    def test_read_rc_signal_no_pin(self):
        """Testa leitura RC sem pino configurado"""
        self.planador.rc_signal_pin = None
        signal = self.planador.read_rc_signal()
        self.assertEqual(signal, 1500)  # Valor neutro

    def test_pid_integral_limits(self):
        """Testa se integral do PID respeita limites"""
        # Simular multiplas iteracoes com erro constante
        for _ in range(100):
            self.planador.calculate_pid(50, 50, 50)
        
        # Integral deve estar limitado
        for integral in self.planador.pid_integral:
            self.assertGreaterEqual(integral, -10)
            self.assertLessEqual(integral, 10)

if __name__ == '__main__':
    unittest.main()