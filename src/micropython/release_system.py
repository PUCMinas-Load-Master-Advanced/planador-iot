"""
Gerencia a maquina de estados e o hardware para o sistema de liberacao.

Este modulo controla o servo de liberacao e interpreta o sinal do receptor RC
para operar um mecanismo de liberacao seguro, com estados como LOCKED, ARMED,
RELEASING, e RELEASED.
"""

import time
from machine import Pin, PWM
import micropython
from config import RELEASE_SERVO_PIN, SYSTEM_CONFIG, SAFETY_LIMITS, RELEASE_CONFIG
import custom_logging as logging

logger = logging.getLogger(__name__)


class ReleaseSystem:
    """Implementa uma maquina de estados para um sistema de liberacao seguro."

    Attributes:
        rc_receiver (RCReceiver): Instancia do RCReceiver para ler o sinal do radio.
        led_manager (LEDManager): Instancia do LEDManager para feedback visual.
        state (str): O estado atual do sistema de liberacao (LOCKED, ARMED, RELEASING, RELEASED).
        armed_time (int): Timestamp em ms quando o sistema foi armado.
        release_time (int): Timestamp em ms quando a liberacao foi iniciada.
        servo (PWM): Instancia do servo de liberacao.
    """

    def __init__(self, rc_receiver, led_manager):
        """Inicializa o sistema de liberacao.

        Args:
            rc_receiver (RCReceiver): Instancia do RCReceiver para ler o sinal do radio.
            led_manager (LEDManager): Instancia do LEDManager para feedback visual.

        Returns:
            None

        Raises:
            Exception: Se houver um erro ao inicializar o servo de liberacao.
        """
        self.rc_receiver = rc_receiver
        self.led_manager = led_manager
        self.state = 'LOCKED'
        self.armed_time = 0
        self.release_time = 0
        self.servo = None
        try:
            self._init_servo()
            logger.info("Sistema de liberacao inicializado.")
        except Exception as e:
            logger.error(f"Erro no sistema de liberacao: {e}")
            raise

    def _init_servo(self):
        """Inicializa o servo de liberacao e o move para a posicao travada."

        Returns:
            None
        """
        self.servo = PWM(Pin(RELEASE_SERVO_PIN), freq=SYSTEM_CONFIG['servo_frequency'])
        self._set_servo_position(RELEASE_CONFIG['locked_position'])
        self.state = 'LOCKED'
        logger.info(f"Sistema travado na posicao {RELEASE_CONFIG['locked_position']} graus.")

    @micropython.native
    def _angle_to_duty(self, angle):
        """Converte um angulo para o valor de duty cycle do PWM."

        Args:
            angle (int): O angulo em graus (0-180) para o servo.

        Returns:
            int: O valor do duty cycle PWM correspondente.
        """
        return int(SAFETY_LIMITS['pwm_min_duty'] + (angle * (SAFETY_LIMITS['pwm_max_duty'] - SAFETY_LIMITS['pwm_min_duty'])) // 180)

    def _set_servo_position(self, angle):
        """Move o servo de liberacao para um angulo especifico."

        Args:
            angle (int): O angulo alvo em graus.

        Returns:
            None
        """
        if self.servo:
            self.servo.duty(self._angle_to_duty(angle))

    def update(self):
        """Executa a maquina de estados do sistema de liberacao a cada ciclo."

        Returns:
            None
        """
        if not self.servo: return
        current_time = time.ticks_ms()
        rc_signal = self.rc_receiver.read_channel()
        state_handlers = {
            'LOCKED': self._handle_locked_state,
            'ARMED': self._handle_armed_state,
            'RELEASING': self._handle_releasing_state,
            'RELEASED': self._handle_released_state
        }
        handler = state_handlers.get(self.state)
        if handler:
            handler(current_time, rc_signal)
        self.led_manager.set_release_pattern(self.state)

    def _handle_locked_state(self, current_time, rc_signal):
        """Gerencia o estado LOCKED: aguarda o sinal do RC para armar o sistema."

        Args:
            current_time (int): O timestamp atual em ms.
            rc_signal (int): O valor do sinal RC.

        Returns:
            None
        """
        if rc_signal > RELEASE_CONFIG['rc_threshold']:
            self.state = 'ARMED'
            self.armed_time = current_time
            logger.info("Sistema ARMADO para liberacao.")

    def _handle_armed_state(self, current_time, rc_signal):
        """Gerencia o estado ARMED: aguarda a confirmacao de liberacao ou desarma."

        Args:
            current_time (int): O timestamp atual em ms.
            rc_signal (int): O valor do sinal RC.

        Returns:
            None
        """
        if rc_signal < RELEASE_CONFIG['rc_threshold']:
            self.state = 'LOCKED'
            logger.info("Sistema DESARMADO - voltando ao travado.")
            return
        if time.ticks_diff(current_time, self.armed_time) >= RELEASE_CONFIG['safety_delay']:
            if rc_signal > RELEASE_CONFIG['rc_threshold']:
                self._initiate_release(current_time)

    def _handle_releasing_state(self, current_time):
        """Gerencia o estado RELEASING: aguarda o servo completar o movimento de liberacao."

        Args:
            current_time (int): O timestamp atual em ms.

        Returns:
            None
        """
        if time.ticks_diff(current_time, self.release_time) >= 500:
            self.state = 'RELEASED'
            logger.info("Planador LIBERADO!")

    def _handle_released_state(self, current_time):
        """Gerencia o estado RELEASED: aguarda o tempo para travar automaticamente novamente."

        Args:
            current_time (int): O timestamp atual em ms.

        Returns:
            None
        """
        if time.ticks_diff(current_time, self.release_time) >= RELEASE_CONFIG['auto_lock_time']:
            self.lock()

    def _initiate_release(self, current_time):
        """Inicia o processo de liberacao movendo o servo para a posicao de liberacao."

        Args:
            current_time (int): O timestamp atual em ms.

        Returns:
            None
        """
        self.state = 'RELEASING'
        self.release_time = current_time
        self._set_servo_position(RELEASE_CONFIG['release_position'])
        logger.info("Liberando planador!")

    def lock(self):
        """Forca o sistema a entrar no estado LOCKED, movendo o servo para a posicao travada."

        Returns:
            None
        """
        if self.servo:
            self._set_servo_position(RELEASE_CONFIG['locked_position'])
            self.state = 'LOCKED'
            logger.info("Sistema de liberacao TRAVADO.")

    def emergency_release(self):
        """Ativa a liberacao de emergencia, ignorando os estados de seguranca."

        Returns:
            bool: True se a liberacao de emergencia foi ativada, False caso contrario.
        """
        if not RELEASE_CONFIG['emergency_override'] or not self.servo: return False
        logger.warning("Liberacao de emergencia ativada!")
        self._set_servo_position(RELEASE_CONFIG['release_position'])
        self.state = 'RELEASED'
        self.release_time = time.ticks_ms()
        self.led_manager.alert_sequence(5)
        return True

    def get_status(self):
        """Retorna um dicionario com o estado atual do sistema de liberacao."

        Returns:
            dict: Um dicionario contendo:
                  - 'state' (str): O estado atual do sistema.
                  - 'servo_available' (bool): Se o servo de liberacao esta disponivel.
        """
        return {
            'state': self.state,
            'servo_available': self.servo is not None
        }

    def get_rc_signal(self):
        """Retorna o ultimo valor lido do canal RC."

        Returns:
            int: A largura do pulso RC em microssegundos.
        """
        return self.rc_receiver.read_channel()

    def cleanup(self):
        """Coloca o sistema em um estado seguro e desliga o servo."

        Returns:
            None
        """
        logger.info("Travando sistema por seguranca...")
        if self.servo:
            try:
                self._set_servo_position(RELEASE_CONFIG['locked_position'])
                time.sleep_ms(500)
                self.servo.deinit()
                self.servo = None
            except Exception as e:
                logger.error(f"Erro na limpeza do sistema de liberacao: {e}")

    def force_lock(self):
        """Forca o travamento imediato do servo para casos de emergencia."

        Returns:
            None
        """
        if self.servo:
            self._set_servo_position(RELEASE_CONFIG['locked_position'])
            self.state = 'LOCKED'
            logger.warning("Travamento forcado!")