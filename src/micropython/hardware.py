"""
Abstrai o controle de componentes de hardware, como LEDs, botoes e servos.

Este modulo fornece classes para gerenciar o estado e as interacoes com
o hardware de baixo nivel, tornando o codigo principal mais limpo e focado na
logica de voo.
"""

import time
from machine import Pin, PWM
import micropython
from config import (LED_SYSTEM_ACTIVE, LED_MODE, LED_ALERT, LED_RELEASE,
                    BUTTON_MODE_PIN, BUTTON_POWER_PIN, PLANADOR_SERVOS,
                    RC_RELEASE_PIN, SYSTEM_CONFIG, SAFETY_LIMITS)
import custom_logging as logging

logger = logging.getLogger(__name__)


class LEDManager:
    """Gerencia o estado e os padroes de pisca de todos os LEDs do sistema."""

    def __init__(self):
        """Inicializa todos os LEDs, tratando falhas de forma individual."

        Returns:
            None
        """
        self.available_leds = {}
        led_configs = [
            ('system_active', LED_SYSTEM_ACTIVE, 'Sistema'),
            ('mode', LED_MODE, 'Modo'),
            ('alert', LED_ALERT, 'Alerta'),
            ('release', LED_RELEASE, 'Liberacao')
        ]
        logger.info("Inicializando LEDs...")
        for name, pin, desc in led_configs:
            try:
                led = Pin(pin, Pin.OUT)
                self.available_leds[name] = led
                logger.info(f"  - LED {desc} (GPIO {pin}) inicializado.")
            except Exception as e:
                logger.warning(f"  - LED {desc} (GPIO {pin}) nao disponivel: {e}")
                self.available_leds[name] = None
        self.test_sequence()
        self.all_off()
        logger.info(f"LEDs disponiveis: {self.get_available_count()}/4")

    def test_sequence(self):
        """Executa uma sequencia de teste para verificar os LEDs disponiveis."

        Returns:
            None
        """
        for led in self.available_leds.values():
            if led:
                led.value(1)
                time.sleep_ms(100)
                led.value(0)

    def all_off(self):
        """Desliga todos os LEDs disponiveis."

        Returns:
            None
        """
        for led in self.available_leds.values():
            if led:
                led.value(0)

    def set_system_active(self, active):
        """Controla o LED que indica se o sistema de estabilizacao esta ativo."

        Args:
            active (bool): True para ligar o LED, False para desligar.

        Returns:
            None
        """
        if self.available_leds.get('system_active'):
            self.available_leds['system_active'].value(1 if active else 0)

    def set_mode_pattern(self, mode_index, active):
        """Define um padrao de pisca para o LED de modo de voo."

        Args:
            mode_index (int): Indice do modo de voo atual.
            active (bool): True para ativar o padrao de pisca, False para desligar o LED.

        Returns:
            None
        """
        led = self.available_leds.get('mode')
        if not led or not active:
            if led: led.value(0)
            return
        blinks = mode_index + 1
        cycle = (time.ticks_ms() // SYSTEM_CONFIG['led_blink_fast']) % (blinks + 2)
        led.value(1 if cycle < blinks else 0)

    def set_release_pattern(self, release_state):
        """Define um padrao de pisca para o LED do sistema de liberacao."

        Args:
            release_state (str): O estado atual do sistema de liberacao (e.g., 'LOCKED', 'ARMED').

        Returns:
            None
        """
        led = self.available_leds.get('release')
        if not led: return
        current_time = time.ticks_ms()
        patterns = {
            'LOCKED': 1,
            'ARMED': (current_time // SYSTEM_CONFIG['led_blink_fast']) % 2,
            'RELEASING': 0,
            'RELEASEED': (current_time // SYSTEM_CONFIG['led_blink_slow']) % 2
        }
        led.value(patterns.get(release_state, 0))

    def alert_sequence(self, count=5):
        """Executa uma sequencia de alerta para indicar um evento importante."

        Args:
            count (int, optional): Numero de piscadas do LED de alerta. Padrao e 5.

        Returns:
            None
        """
        led = self.available_leds.get('alert')
        if not led: return
        for _ in range(count):
            led.value(1)
            time.sleep_ms(100)
            led.value(0)
            time.sleep_ms(100)

    def get_led_status(self):
        """Retorna um dicionario com o status de cada LED (disponivel ou nao).

        Returns:
            dict: Dicionario onde a chave e o nome do LED e o valor e um booleano.
        """
        return {name: led is not None for name, led in self.available_leds.items()}

    def has_led(self, led_name):
        """Verifica se um LED especifico esta disponivel."

        Args:
            led_name (str): O nome do LED a ser verificado.

        Returns:
            bool: True se o LED estiver disponivel, False caso contrario.
        """
        return self.available_leds.get(led_name) is not None

    def get_available_count(self):
        """Retorna o numero de LEDs que foram inicializados com sucesso."

        Returns:
            int: O numero de LEDs disponiveis.
        """
        return sum(1 for led in self.available_leds.values() if led)


class ButtonManager:
    """Gerencia a leitura de botoes com debounce para evitar leituras multiplas."""

    def __init__(self):
        """Inicializa os pinos dos botoes com resistores de pull-up."

        Returns:
            None

        Raises:
            Exception: Se houver um erro ao inicializar os pinos dos botoes.
        """
        try:
            self.mode_button = Pin(BUTTON_MODE_PIN, Pin.IN, Pin.PULL_UP)
            self.power_button = Pin(BUTTON_POWER_PIN, Pin.IN, Pin.PULL_UP) if BUTTON_POWER_PIN else None
        except Exception as e:
            logger.error(f"Erro ao inicializar botoes: {e}")
            raise
        self.mode_button_last = False
        self.power_button_last = False
        self.last_button_time = 0

    def read_buttons(self):
        """
        Le o estado dos botoes, aplicando um debounce para retornar um unico evento.

        Returns:
            dict: Um dicionario com o estado de clique de cada botao.

        Example:
            >>> buttons = button_manager.read_buttons()
            >>> if buttons['mode']:
            >>>     print("Botao de modo pressionado!")
        """
        current_time = time.ticks_ms()
        if time.ticks_diff(current_time, self.last_button_time) < SYSTEM_CONFIG['button_debounce']:
            return {'mode': False, 'power': False}
        mode_pressed = not self.mode_button.value()
        mode_clicked = mode_pressed and not self.mode_button_last
        power_clicked = False
        if self.power_button:
            power_pressed = not self.power_button.value()
            power_clicked = power_pressed and not self.power_button_last
            self.power_button_last = power_pressed
        if mode_clicked or power_clicked:
            self.last_button_time = current_time
        self.mode_button_last = mode_pressed
        return {'mode': mode_clicked, 'power': power_clicked}


class ServoManager:
    """Gerencia a inicializacao e o controle de todos os servos do planador."""

    def __init__(self):
        """Inicializa os servos e os coloca em uma posicao neutra."

        Returns:
            None

        Raises:
            Exception: Se houver um erro ao inicializar os servos.
        """
        self.servos = {}
        self.servo_names = ['flaps_left', 'flaps_right', 'elevator', 'rudder']
        try:
            for name, pin in PLANADOR_SERVOS.items():
                servo = PWM(Pin(pin), freq=SYSTEM_CONFIG['servo_frequency'])
                servo.duty(self.angle_to_duty(SAFETY_LIMITS['servo_neutral_angle']))
                self.servos[name] = servo
            logger.info(f"{len(self.servos)} servos inicializados")
        except Exception as e:
            logger.error(f"Erro ao inicializar servos: {e}")
            raise

    @micropython.native
    def angle_to_duty(self, angle):
        """Converte um angulo (0-180) para um valor de duty cycle PWM."

        Args:
            angle (int): O angulo em graus (0-180) para o servo.

        Returns:
            int: O valor do duty cycle PWM correspondente.
        """
        angle = max(SAFETY_LIMITS['servo_min_angle'], min(SAFETY_LIMITS['servo_max_angle'], angle))
        return int(SAFETY_LIMITS['pwm_min_duty'] + (angle * (SAFETY_LIMITS['pwm_max_duty'] - SAFETY_LIMITS['pwm_min_duty'])) // 180)

    def set_neutral(self):
        """Move todos os servos para a posicao neutra."

        Returns:
            None
        """
        neutral_duty = self.angle_to_duty(SAFETY_LIMITS['servo_neutral_angle'])
        for servo in self.servos.values():
            servo.duty(neutral_duty)

    @micropython.native
    def apply_commands(self, commands):
        """Aplica uma lista de comandos de angulo aos servos correspondentes."

        Args:
            commands (list): Uma lista de angulos em graus para os servos.

        Returns:
            None
        """
        for i, name in enumerate(self.servo_names):
            if name in self.servos and i < len(commands):
                self.servos[name].duty(self.angle_to_duty(commands[i]))

    def cleanup(self):
        """Desliga os servos para economizar energia e evitar ruido."

        Returns:
            None
        """
        self.set_neutral()
        for servo in self.servos.values():
            try:
                servo.deinit()
            except: pass


class RCReceiver:
    """Le o sinal PWM de um canal do receptor de radio controle."""

    def __init__(self):
        """Inicializa o pino para leitura do sinal do receptor RC."

        Returns:
            None

        Raises:
            Exception: Se houver um erro ao inicializar o pino RC.
        """
        try:
            self.rc_pin = Pin(RC_RELEASE_PIN, Pin.IN)
            self.last_read_time = 0
            logger.info("Receptor RC inicializado")
        except Exception as e:
            logger.error(f"Erro ao inicializar RC: {e}")
            self.rc_pin = None

    @micropython.native
    def read_channel(self):
        """Mede a largura do pulso do sinal PWM do canal RC."

        Returns:
            int: A largura do pulso em microssegundos, ou o valor neutro se houver erro ou timeout.
        """
        if not self.rc_pin or time.ticks_diff(time.ticks_ms(), self.last_read_time) < SYSTEM_CONFIG['rc_read_interval']:
            return SAFETY_LIMITS['rc_neutral_pulse']
        self.last_read_time = time.ticks_ms()
        try:
            timeout = 0
            while self.rc_pin.value() == 0:
                if timeout > SAFETY_LIMITS['sensor_timeout']: return SAFETY_LIMITS['rc_neutral_pulse']
                time.sleep_us(1)
                timeout += 1
            start_time = time.ticks_us()
            timeout = 0
            while self.rc_pin.value() == 1:
                if timeout > SAFETY_LIMITS['rc_timeout']: break
                time.sleep_us(1)
                timeout += 1
            pulse_width = time.ticks_diff(time.ticks_us(), start_time)
            return pulse_width if SAFETY_LIMITS['rc_min_pulse'] <= pulse_width <= SAFETY_LIMITS['rc_max_pulse'] else SAFETY_LIMITS['rc_neutral_pulse']
        except:
            return SAFETY_LIMITS['rc_neutral_pulse']


class HardwareManager:
    """Agrega e gerencia todos os componentes de hardware como uma unica entidade."""

    def __init__(self):
        """Inicializa todos os gerenciadores de hardware."

        Returns:
            None

        Raises:
            Exception: Se houver um erro critico na inicializacao de qualquer gerenciador de hardware.
        """
        logger.info("Inicializando o gerenciador de hardware...")
        try:
            self.leds = LEDManager()
            self.buttons = ButtonManager()
            self.servos = ServoManager()
            self.rc_receiver = RCReceiver()
            logger.info("Gerenciador de hardware inicializado com sucesso")
        except Exception as e:
            logger.error(f"Erro critico no gerenciador de hardware: {e}")
            raise

    def cleanup(self):
        """Executa a limpeza de todos os componentes de hardware."

        Returns:
            None
        """
        logger.info("Limpando o hardware...")
        try:
            self.servos.cleanup()
            self.leds.all_off()
            logger.info("Hardware limpo com sucesso")
        except Exception as e:
            logger.error(f"Erro na limpeza do hardware: {e}")
