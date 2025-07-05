"""
Configuracao minima para o sistema do planador ESP32.

Este arquivo define um conjunto de parametros otimizados para prototipagem
com hardware minimo, desabilitando componentes nao essenciais como LEDs.

Attributes:
    PLANADOR_SERVOS (dict): Mapeamento de nomes de servos para seus pinos GPIO.
    I2C_SDA (int): Pino GPIO para o barramento I2C (SDA).
    I2C_SCL (int): Pino GPIO para o barramento I2C (SCL).
    MPU6050_ADDR (int): Endereco I2C do sensor MPU6050.
    RELEASE_SERVO_PIN (int): Pino GPIO para o servo de liberacao.
    RC_RELEASE_PIN (int): Pino GPIO para o canal RC de liberacao.
    LED_SYSTEM_ACTIVE (int): Pino GPIO para o LED de status do sistema (desabilitado).
    LED_MODE (int): Pino GPIO para o LED de modo de voo (desabilitado).
    LED_ALERT (int): Pino GPIO para o LED de alerta (desabilitado).
    LED_RELEASE (int): Pino GPIO para o LED de status de liberacao (desabilitado).
    BUTTON_MODE_PIN (int): Pino GPIO para o botao de modo.
    BUTTON_POWER_PIN (int): Pino GPIO para o botao de energia.
    FLIGHT_MODES (dict): Dicionario de configuracoes para diferentes modos de voo.
    RELEASE_CONFIG (dict): Configuracoes para o sistema de liberacao.
    SAFETY_LIMITS (dict): Limites de seguranca para operacao do sistema.
    SYSTEM_CONFIG (dict): Configuracoes gerais do sistema, como frequencias e intervalos.

Example:
    >>> from config_minimal import PLANADOR_SERVOS
    >>> print(PLANADOR_SERVOS['flaps_left'])
    25
"""

import custom_logging as logging

logger = logging.getLogger(__name__)


PLANADOR_SERVOS = {
    'flaps_left': 25,
    'flaps_right': 26,
    'elevator': 14,
    'rudder': 27
}

I2C_SDA = 21
I2C_SCL = 22
MPU6050_ADDR = 0x68

RELEASE_SERVO_PIN = 23
RC_RELEASE_PIN = 13

LED_SYSTEM_ACTIVE = 99
LED_MODE = 98
LED_ALERT = 97
LED_RELEASE = 96

BUTTON_MODE_PIN = 34
BUTTON_POWER_PIN = 18


FLIGHT_MODES = {
    0: {  # Termicas
        'name': 'TERMICAS',
        'flaps': 10,
        'kp_roll': 1.5,
        'ki_roll': 0.05,
        'kp_pitch': 1.0,
        'ki_pitch': 0.03
    },
    1: {  # Cruzeiro
        'name': 'CRUZEIRO',
        'flaps': 20,
        'kp_roll': 2.0,
        'ki_roll': 0.08,
        'kp_pitch': 1.3,
        'ki_pitch': 0.05
    },
    2: {  # Pouso
        'name': 'POUSO',
        'flaps': 35,
        'kp_roll': 2.5,
        'ki_roll': 0.1,
        'kp_pitch': 1.8,
        'ki_pitch': 0.07
    }
}


RELEASE_CONFIG = {
    'locked_position': 45,
    'release_position': 135,
    'rc_threshold': 1700,
    'safety_delay': 2000,
    'release_duration': 500,
    'auto_lock_delay': 5000
}


SAFETY_LIMITS = {
    'servo_min_angle': 0,
    'servo_max_angle': 180,
    'servo_neutral_angle': 90,
    'pwm_min_duty': 40,
    'pwm_max_duty': 115,
    'rc_min_pulse': 1000,
    'rc_max_pulse': 2000,
    'rc_neutral_pulse': 1500,
    'rc_timeout': 10000,
    'sensor_timeout': 1000,
    'max_attitude_error': 45
}


SYSTEM_CONFIG = {
    'main_loop_frequency': 10,
    'servo_frequency': 50,
    'rc_read_interval': 50,
    'led_blink_fast': 200,
    'led_blink_slow': 800,
    'button_debounce': 200,
    'telemetry_interval': 3000
}