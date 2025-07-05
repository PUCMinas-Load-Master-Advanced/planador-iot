import unittest
from unittest.mock import patch, MagicMock, Mock
import sys
import os

# Adicionar o diretorio pai ao sys.path para permitir importacoes relativas
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src/micropython')))

# Mock dos modulos MicroPython
sys.modules['micropython'] = MagicMock()
sys.modules['machine'] = MagicMock()
sys.modules['time'] = MagicMock()
sys.modules['math'] = MagicMock()
sys.modules['struct'] = MagicMock()
sys.modules['gc'] = MagicMock()
sys.modules['custom_logging'] = MagicMock()

# Mock das configuracoes
mock_config = {
    'STABILIZATION_GAINS': (2.0, 0.15, 1.0, 2.5, 0.18, 1.2, 1.2, 0.06, 0.5),
    'STABILIZATION_LIMITS': (25, 30, 18),
    'SAFETY_LIMITS': {
        'max_pid_integral': 10,
        'servo_min_angle': 30,
        'servo_max_angle': 150,
        'servo_neutral_angle': 90,
    },
    'RELEASE_CONFIG': {
        'locked_position': 45,
        'release_position': 135,
        'rc_threshold': 1700,
        'safety_delay': 2000,
        'auto_lock_time': 5000,
        'emergency_override': True
    },
    'PLANADOR_SERVOS': {'flaps_left': 25, 'flaps_right': 26, 'elevator': 14, 'rudder': 27},
    'LED_SYSTEM_ACTIVE': 15,
    'LED_ALERT': 19,
    'LED_RELEASE': 5,
    'RELEASE_SERVO_PIN': 23,
    'RC_RELEASE_PIN': 13,
    'I2C_SDA': 21,
    'I2C_SCL': 22,
    'MPU6050_ADDR': 0x68
}

class TestSystemIntegration(unittest.TestCase):
    """Testes de integracao do sistema completo"""

    def setUp(self):
        """Setup para cada teste"""
        # Aplicar todos os patches de configuracao
        for key, value in mock_config.items():
            patcher = patch(f'config.{key}', value)
            patcher.start()
            self.addCleanup(patcher.stop)

    @patch('main.time')
    def test_main_loop_execution(self, mock_time):
        """Testa execucao do loop principal"""
        mock_time.ticks_ms.return_value = 1000
        
        from main import PlanadorESP32
        
        with patch.object(PlanadorESP32, 'run_tests'), \
             patch.object(PlanadorESP32, 'read_sensors') as mock_sensors, \
             patch.object(PlanadorESP32, 'apply_commands') as mock_apply, \
             patch.object(PlanadorESP32, 'update_release_system') as mock_release, \
             patch.object(PlanadorESP32, 'update_leds') as mock_leds:
            
            mock_sensors.return_value = (0.0, 0.0, 0.0, True)
            
            planador = PlanadorESP32()
            planador.main_loop()
            
            # Verificar se todas as funcoes foram chamadas
            mock_sensors.assert_called_once()
            mock_apply.assert_called_once()
            mock_release.assert_called_once()
            mock_leds.assert_called_once()

    def test_sensor_to_servo_pipeline(self):
        """Testa pipeline completo: sensores -> PID -> servos"""
        from main import PlanadorESP32
        
        with patch.object(PlanadorESP32, 'run_tests'):
            planador = PlanadorESP32()
            
            # Mock dos servos
            mock_servo = Mock()
            planador.servos = {
                'flaps_left': mock_servo,
                'flaps_right': mock_servo,
                'elevator': mock_servo,
                'rudder': mock_servo
            }
            
            # Simular dados de sensores
            roll, pitch, yaw_rate = 10.0, 5.0, 2.0
            
            # Calcular comandos
            commands = planador.calculate_commands(roll, pitch, yaw_rate)
            
            # Aplicar comandos
            planador.apply_commands(commands)
            
            # Verificar se servos foram acionados
            self.assertEqual(mock_servo.duty.call_count, 4)

    def test_stabilization_response(self):
        """Testa resposta de estabilizacao a perturbacoes"""
        from main import PlanadorESP32
        
        with patch.object(PlanadorESP32, 'run_tests'):
            planador = PlanadorESP32()
            
            # Testar resposta a roll
            commands = planador.calculate_commands(15.0, 0.0, 0.0)
            self.assertNotEqual(commands[0], commands[1])  # Flaps devem ser diferentes
            
            # Testar resposta a pitch
            commands = planador.calculate_commands(0.0, 10.0, 0.0)
            self.assertNotEqual(commands[2], 90)  # Elevator deve mover
            
            # Testar resposta a yaw
            commands = planador.calculate_commands(0.0, 0.0, 5.0)
            self.assertNotEqual(commands[3], 90)  # Rudder deve mover

    def test_system_startup_sequence(self):
        """Testa sequencia de inicializacao do sistema"""
        from main import PlanadorESP32
        
        with patch.object(PlanadorESP32, 'run_tests') as mock_tests, \
             patch.object(PlanadorESP32, 'init_hardware') as mock_hw, \
             patch.object(PlanadorESP32, 'init_sensors') as mock_sensors, \
             patch.object(PlanadorESP32, 'init_servos') as mock_servos, \
             patch.object(PlanadorESP32, 'init_release_system') as mock_release:
            
            mock_hw.return_value = True
            mock_sensors.return_value = True
            mock_servos.return_value = True
            mock_release.return_value = True
            
            planador = PlanadorESP32()
            
            # Verificar que sistema inicia ativo
            self.assertTrue(planador.system_active)
            
            # Verificar que testes foram executados
            mock_tests.assert_called_once()

    def test_error_handling_in_main_loop(self):
        """Testa tratamento de erros no loop principal"""
        from main import PlanadorESP32
        
        with patch.object(PlanadorESP32, 'run_tests'), \
             patch.object(PlanadorESP32, 'read_sensors') as mock_sensors, \
             patch.object(PlanadorESP32, 'set_neutral') as mock_neutral:
            
            # Simular erro no sensor
            mock_sensors.side_effect = Exception("Sensor error")
            
            planador = PlanadorESP32()
            planador.main_loop()
            
            # Verificar que set_neutral foi chamado em caso de erro
            mock_neutral.assert_called_once()

    def test_release_system_integration(self):
        """Testa integracao do sistema de liberacao"""
        from main import PlanadorESP32
        
        with patch.object(PlanadorESP32, 'run_tests'), \
             patch.object(PlanadorESP32, 'read_rc_signal') as mock_rc:
            
            planador = PlanadorESP32()
            planador.release_servo = Mock()
            planador.led_release = Mock()
            
            # Testar estado inicial
            self.assertEqual(planador.release_state, 'LOCKED')
            
            # Simular sinal RC alto
            mock_rc.return_value = 1800
            planador.update_release_system()
            
            # Sistema deve armar
            self.assertEqual(planador.release_state, 'ARMED')

    def test_performance_requirements(self):
        """Testa requisitos de performance em tempo real"""
        from main import PlanadorESP32
        
        with patch.object(PlanadorESP32, 'run_tests'):
            planador = PlanadorESP32()
            
            # Simular multiplas iteracoes do loop
            for i in range(100):
                planador.loop_count += 1
                commands = planador.calculate_commands(
                    float(i % 10), 
                    float((i + 5) % 10), 
                    float((i + 3) % 5)
                )
                
                # Verificar que comandos estao sempre dentro dos limites
                for cmd in commands:
                    self.assertGreaterEqual(cmd, 30)
                    self.assertLessEqual(cmd, 150)

if __name__ == '__main__':
    unittest.main()