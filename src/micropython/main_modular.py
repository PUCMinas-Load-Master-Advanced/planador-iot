"""
Orquestra o sistema de estabilizacao do planador em uma arquitetura modular.

Este modulo e o ponto de entrada principal, responsavel por inicializar e
gerenciar o hardware, os sensores, o sistema de liberacao e o controle PID.
"""

import time
import gc
import sys

from config import FLIGHT_MODES, SYSTEM_CONFIG
from hardware import HardwareManager
from sensors import SensorManager
from release_system import ReleaseSystem
from pid_controller import PIDController
import custom_logging as logging

logger = logging.getLogger(__name__)


class PlanadorSystem:
    """Gerencia o ciclo de vida e a operacao de todos os subsistemas do planador.

    Attributes:
        system_active (bool): Indica se o sistema de estabilizacao esta ativo.
        loop_count (int): Contador de ciclos do loop principal.
        last_telemetry_time (int): Timestamp da ultima telemetria enviada.
        hardware (HardwareManager): Gerenciador de hardware.
        sensors (SensorManager): Gerenciador de sensores.
        release_system (ReleaseSystem): Sistema de liberacao do planador.
        pid_controller (PIDController): Controlador PID para estabilizacao.
    """

    def __init__(self):
        """Inicializa o sistema completo, configurando hardware e todos os subsistemas.

        Returns:
            None

        Example:
            >>> system = PlanadorSystem()
            Inicializando o sistema modular do planador
            ...
        """
        logger.info("Inicializando o sistema modular do planador")
        self.system_active = False
        self.loop_count = 0
        self.last_telemetry_time = 0
        self._init_subsystems()
        gc.collect()
        logger.info(f"RAM livre apos inicializacao: {gc.mem_free()} bytes")

    def _init_subsystems(self):
        """Inicializa e interconecta os subsistemas de hardware e logica.

        Raises:
            Exception: Se houver um erro critico na inicializacao de qualquer subsistema.
        """
        try:
            logger.info("Inicializando subsistemas...")
            self.hardware = HardwareManager()
            self.sensors = SensorManager()
            self.release_system = ReleaseSystem(
                self.hardware.rc_receiver,
                self.hardware.leds
            )
            self.pid_controller = PIDController()
            logger.info("Todos os subsistemas foram inicializados")
        except Exception as e:
            logger.error(f"Erro critico na inicializacao: {e}")
            self._emergency_cleanup()
            raise

    def run(self):
        """Inicia o loop principal do sistema, que continuara ate uma interrupcao.

        Raises:
            KeyboardInterrupt: Quando o usuario pressiona Ctrl+C para parar o sistema.
            Exception: Para erros nao tratados durante a execucao do loop principal.

        Example:
            >>> system = PlanadorSystem()
            >>> system.run()
            Sistema operacional. Pressione Ctrl+C para parar.
            ...
        """
        self._show_system_info()
        try:
            logger.info("Sistema operacional. Pressione Ctrl+C para parar.")
            while True:
                self._main_loop()
                time.sleep_ms(1000 // SYSTEM_CONFIG['main_loop_frequency'])
        except KeyboardInterrupt:
            logger.info("Parando o sistema...")
        except Exception as e:
            logger.error(f"Erro critico: {e}")
            sys.print_exception(e)
        finally:
            self._shutdown()

    def _main_loop(self):
        """Executa um unico ciclo de leitura, processamento e atuacao do sistema.

        Raises:
            Exception: Se ocorrer um erro durante a execucao de qualquer etapa do loop.
        """
        self.loop_count += 1
        try:
            roll, pitch, yaw_rate, sensors_valid = self.sensors.read_attitude()
            self._handle_controls()

            if self.system_active:
                commands = self.pid_controller.calculate_servo_commands(roll, pitch, yaw_rate)
                self.hardware.servos.apply_commands(commands)
            else:
                self.hardware.servos.set_neutral()

            self.release_system.update()
            self._update_leds()

            if self.loop_count % 30 == 0:
                self._log_telemetry(roll, pitch, yaw_rate, sensors_valid)
        except Exception as e:
            logger.error(f"Erro no loop principal: {e}")
            self.hardware.servos.set_neutral()

    def _handle_controls(self):
        """Processa a entrada dos botoes para controlar o estado do sistema.

        Returns:
            None
        """
        buttons = self.hardware.buttons.read_buttons()
        if buttons['mode']:
            if not self.system_active:
                self._activate_system()
            else:
                self._switch_flight_mode()
        if buttons['power']:
            if self.system_active:
                self._deactivate_system()
            else:
                self.release_system.emergency_release()

    def _activate_system(self):
        """Ativa o sistema de estabilizacao, resetando o PID e atualizando o LED de status."

        Returns:
            None
        """
        self.system_active = True
        mode_info = self.pid_controller.get_flight_mode_info()
        logger.info(f"Sistema ativo - Modo: {mode_info['name']}")
        self.pid_controller.reset()
        self.hardware.leds.set_system_active(True)

    def _deactivate_system(self):
        """Desativa o sistema de estabilizacao, centraliza os servos e aciona o alerta visual."

        Returns:
            None
        """
        self.system_active = False
        logger.info("Sistema desativado")
        self.hardware.servos.set_neutral()
        self.hardware.leds.set_system_active(False)
        self.hardware.leds.alert_sequence(3)

    def _switch_flight_mode(self):
        """Alterna para o proximo modo de voo disponivel e reseta o PID."

        Returns:
            None
        """
        current_mode = self.pid_controller.flight_mode
        new_mode = (current_mode + 1) % len(FLIGHT_MODES)
        if self.pid_controller.set_flight_mode(new_mode):
            mode_info = self.pid_controller.get_flight_mode_info()
            logger.info(f"Modo de voo alterado para: {mode_info['name']}")

    def _update_leds(self):
        """Atualiza o estado visual dos LEDs com base no status do sistema e modo de voo."

        Returns:
            None
        """
        self.hardware.leds.set_system_active(self.system_active)
        self.hardware.leds.set_mode_pattern(
            self.pid_controller.flight_mode,
            self.system_active
        )

    def _log_telemetry(self, roll, pitch, yaw_rate, sensors_valid):
        """Registra uma mensagem de telemetria periodica com dados do sistema.

        Args:
            roll (float): Angulo de roll atual.
            pitch (float): Angulo de pitch atual.
            yaw_rate (float): Taxa de guinada atual.
            sensors_valid (bool): Indica se os dados do sensor sao validos (nao simulados).

        Returns:
            None
        """
        current_time = time.ticks_ms()
        if time.ticks_diff(current_time, self.last_telemetry_time) >= SYSTEM_CONFIG['telemetry_interval']:
            self.last_telemetry_time = current_time
            mode_name = self.pid_controller.get_flight_mode_info()['name']
            sensor_text = "REAL" if sensors_valid else "SIMULADO"
            status_text = "ATIVO" if self.system_active else "INATIVO"
            release_state = self.release_system.state
            rc_signal = self.release_system.get_rc_signal()
            ram_free = gc.mem_free()
            logger.info(f"{mode_name} | R:{roll:.1f} P:{pitch:.1f} Y:{yaw_rate:.1f}")
            logger.info(f"{status_text} | Sensor:{sensor_text} | Liberacao:{release_state} RC:{rc_signal} | RAM:{ram_free}")
            gc.collect()

    def _show_system_info(self):
        """Exibe um resumo do estado do sistema e dos subsistemas na inicializacao."

        Returns:
            None
        """
        logger.info("Sistema Planador ESP32 - Pronto")
        logger.info("Controles:")
        logger.info("  - Botao MODO: Ativar/Trocar modo de voo")
        if self.hardware.buttons.power_button:
            logger.info("  - Botao POWER: Desativar/Liberacao de emergencia")
        logger.info("Status dos Subsistemas:")
        sensor_status = self.sensors.get_sensor_status()
        logger.info(f"  - Sensores: {sensor_status['sensor_type']}")
        led_count = self.hardware.leds.get_available_count()
        logger.info(f"  - LEDs: {led_count}/4 disponiveis")
        release_status = self.release_system.get_status()
        logger.info(f"  - Liberacao: {release_status['state']}")
        logger.info("Modos de Voo:")
        for i, mode in FLIGHT_MODES.items():
            logger.info(f"  {i+1}. {mode['name']}")

    def _emergency_cleanup(self):
        """Executa uma limpeza de emergencia para colocar o sistema em estado seguro."

        Returns:
            None

        Raises:
            Exception: Se ocorrer um erro durante a limpeza de emergencia.
        """
        logger.info("Executando limpeza de emergencia")
        try:
            if hasattr(self, 'hardware') and hasattr(self.hardware, 'servos'):
                self.hardware.servos.set_neutral()
            if hasattr(self, 'release_system'):
                self.release_system.force_lock()
            if hasattr(self, 'hardware') and hasattr(self.hardware, 'leds'):
                self.hardware.leds.all_off()
        except Exception as e:
            logger.error(f"Erro na limpeza de emergencia: {e}")

    def _shutdown(self):
        """Realiza um desligamento seguro de todos os subsistemas."

        Returns:
            None

        Raises:
            Exception: Se ocorrer um erro durante o desligamento seguro.
        """
        logger.info("Desligamento seguro do sistema...")
        try:
            self.system_active = False
            if hasattr(self, 'release_system'):
                self.release_system.cleanup()
            if hasattr(self, 'hardware'):
                self.hardware.cleanup()
            if hasattr(self, 'pid_controller'):
                self.pid_controller.emergency_stop()
            logger.info("Sistema finalizado com seguranca")
        except Exception as e:
            logger.error(f"Erro no desligamento: {e}")

    def get_system_status(self):
        """Retorna um dicionario com o status completo do sistema."

        Returns:
            dict: Um dicionario contendo o estado atual do sistema.

        Raises:
            Exception: Se ocorrer um erro ao coletar o status do sistema.
        """
        try:
            return {
                'system_active': self.system_active,
                'loop_count': self.loop_count,
                'ram_free': gc.mem_free(),
                'sensors': self.sensors.get_sensor_status(),
                'pid': self.pid_controller.get_pid_status(),
                'release': self.release_system.get_status(),
                'uptime_ms': time.ticks_ms()
            }
        except Exception as e:
            return {'error': str(e)}

def main():
    """Ponto de entrada para iniciar o sistema do planador."

    Returns:
        None

    Raises:
        Exception: Se ocorrer um erro critico durante a inicializacao ou execucao do sistema.

    Example:
        >>> main()
        Iniciando o sistema modular do planador...
        ...
    """
    logger.info("Iniciando o sistema modular do planador...")
    try:
        planador = PlanadorSystem()
        planador.run()
    except Exception as e:
        logger.error(f"Erro critico no sistema: {e}")
        sys.print_exception(e)

if __name__ == "__main__":
    main()