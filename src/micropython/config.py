"""
Arquivo de configuracao central para o sistema do planador.

Este arquivo define todos os pinos de hardware, parametros de voo, configuracoes
de seguranca e outros valores ajustaveis que governam o comportamento do sistema.

Attributes:
    PLANADOR_SERVOS (dict): Mapeamento de nomes de servos para seus pinos GPIO.
    RELEASE_SERVO_PIN (int): Pino GPIO para o servo de liberacao.
    LED_SYSTEM_ACTIVE (int): Pino GPIO para o LED de status do sistema.
    LED_MODE (int): Pino GPIO para o LED de modo de voo.
    LED_ALERT (int): Pino GPIO para o LED de alerta.
    LED_RELEASE (int): Pino GPIO para o LED de status de liberacao.
    BUTTON_MODE_PIN (int): Pino GPIO para o botao de modo.
    BUTTON_POWER_PIN (int): Pino GPIO para o botao de energia.
    RC_RELEASE_PIN (int): Pino GPIO para o canal RC de liberacao.
    I2C_SDA (int): Pino GPIO para o barramento I2C (SDA).
    I2C_SCL (int): Pino GPIO para o barramento I2C (SCL).
    MPU6050_ADDR (int): Endereco I2C do sensor MPU6050.
    FLIGHT_MODES (dict): Dicionario de configuracoes para diferentes modos de voo.
                         Cada modo contem: 'name', 'gains' (Kp, Ki, Kd para roll, pitch, yaw),
                         'limits' (deflexao maxima), 'target' (alvo de roll/pitch), 'flaps' (posicao base).
    RELEASE_CONFIG (dict): Configuracoes para o sistema de liberacao.
    SYSTEM_CONFIG (dict): Configuracoes gerais do sistema, como frequencias e intervalos.
    SAFETY_LIMITS (dict): Limites de seguranca para operacao do hardware.

Example:
    >>> from config import SYSTEM_CONFIG
    >>> print(SYSTEM_CONFIG['main_loop_frequency'])
    10
"""

PLANADOR_SERVOS = {
    'flaps_left': 25,
    'flaps_right': 26,
    'elevator': 14,
    'rudder': 27
}
RELEASE_SERVO_PIN = 23
LED_SYSTEM_ACTIVE = 15
LED_ALERT = 19
LED_RELEASE = 5
RC_RELEASE_PIN = 13
I2C_SDA = 21
I2C_SCL = 22
MPU6050_ADDR = 0x68

STABILIZATION_GAINS = (2.0, 0.15, 1.0, 2.5, 0.18, 1.2, 1.2, 0.06, 0.5)
STABILIZATION_LIMITS = (25, 30, 18)

RELEASE_CONFIG = {
    'locked_position': 45,
    'release_position': 135,
    'rc_threshold': 1700,
    'safety_delay': 2000,
    'auto_lock_time': 5000,
    'emergency_override': True
}

SYSTEM_CONFIG = {
    'main_loop_frequency': 50,
    'telemetry_interval': 3000,
    'rc_read_interval': 50,
    'button_debounce': 300,
    'led_blink_fast': 200,
    'led_blink_slow': 1000,
    'servo_frequency': 50,
    'i2c_frequency': 400000
}

SAFETY_LIMITS = {
    'servo_min_angle': 30,
    'servo_max_angle': 150,
    'servo_neutral_angle': 90,
    'pwm_min_duty': 40,
    'pwm_max_duty': 115,
    'rc_min_pulse': 800,
    'rc_max_pulse': 2200,
    'rc_neutral_pulse': 1500,
    'max_pid_integral': 10,
    'sensor_timeout': 10000,
    'rc_timeout': 3000
}