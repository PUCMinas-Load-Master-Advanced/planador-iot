"""
Referencia de pinos para o sistema planador ESP32.

Este arquivo serve como documentacao de referencia rapida dos pinos
utilizados no projeto. NAO altere os valores sem verificar as conexoes fisicas.
"""

# ============================================================================
# MAPEAMENTO DE PINOS - ESP32 DevKit v1
# ============================================================================

# SERVOS DO PLANADOR (PWM - 5V)
# IMPORTANTE: Servos devem ser alimentados com 5V, NAO 3.3V!
SERVO_FLAPS_LEFT = 25    # GPIO 25 - Servo flaps esquerdo
SERVO_FLAPS_RIGHT = 26   # GPIO 26 - Servo flaps direito  
SERVO_ELEVATOR = 14      # GPIO 14 - Servo elevador
SERVO_RUDDER = 27        # GPIO 27 - Servo leme
SERVO_RELEASE = 23       # GPIO 23 - Servo de liberacao

# LEDS INDICADORES (3.3V com resistor 220 ohm)
# Verde: Sistema ativo
# Amarelo: Alertas do sistema
# Vermelho: Status da liberacao
LED_SYSTEM_ACTIVE = 15   # GPIO 15 - LED verde (sistema ativo)
LED_ALERT = 19          # GPIO 19 - LED amarelo (alertas)
LED_RELEASE = 5         # GPIO 5  - LED vermelho (liberacao)

# SENSORES I2C (3.3V)
# MPU6050: Giroscopio e acelerometro
# IMPORTANTE: Usar 3.3V, NAO 5V!
I2C_SDA = 21            # GPIO 21 - Dados I2C (SDA)
I2C_SCL = 22            # GPIO 22 - Clock I2C (SCL)
MPU6050_ADDRESS = 0x68  # Endereco I2C do MPU6050

# CONTROLE RC (3.3V ou 5V conforme receptor)
RC_RELEASE_CHANNEL = 13  # GPIO 13 - Canal RC para liberacao

# CONTROLE MANUAL (Opcional)
BUTTON_POWER = 18       # GPIO 18 - Botao liga/desliga (com pull-up interno)

# ============================================================================
# ESPECIFICACOES ELETRICAS
# ============================================================================

# TENSOES DE OPERACAO
VOLTAGE_LOGIC = 3.3     # Tensao logica do ESP32
VOLTAGE_SERVO = 5.0     # Tensao de alimentacao dos servos
VOLTAGE_INPUT = 5.0     # Tensao de entrada recomendada (VIN)

# CORRENTES TIPICAS (mA)
CURRENT_ESP32 = 240     # Consumo tipico do ESP32
CURRENT_SERVO_IDLE = 100    # Servo em repouso
CURRENT_SERVO_MOVING = 600  # Servo em movimento
CURRENT_MPU6050 = 4     # Consumo do MPU6050
CURRENT_LED = 20        # Consumo por LED

# CORRENTE TOTAL ESTIMADA
CURRENT_TOTAL_MIN = 800  # Minimo (mA)
CURRENT_TOTAL_MAX = 3000 # Maximo com todos servos movendo (mA)

# ============================================================================
# CONFIGURACOES PWM
# ============================================================================

# SERVOS (PWM 50Hz)
PWM_FREQUENCY = 50      # Frequencia PWM para servos (Hz)
PWM_DUTY_MIN = 40       # Duty cycle minimo (0 graus)
PWM_DUTY_MAX = 115      # Duty cycle maximo (180 graus)
PWM_DUTY_NEUTRAL = 77   # Duty cycle neutro (90 graus)

# ANGULOS DOS SERVOS
SERVO_ANGLE_MIN = 30    # Angulo minimo de seguranca
SERVO_ANGLE_MAX = 150   # Angulo maximo de seguranca  
SERVO_ANGLE_NEUTRAL = 90 # Angulo neutro

# ============================================================================
# CONFIGURACOES I2C
# ============================================================================

I2C_FREQUENCY = 400000  # Frequencia I2C (400kHz)
I2C_TIMEOUT = 1000     # Timeout I2C (ms)

# REGISTRADORES MPU6050
MPU6050_PWR_MGMT_1 = 0x6B   # Gerenciamento de energia
MPU6050_ACCEL_XOUT_H = 0x3B # Inicio dos dados do acelerometro
MPU6050_GYRO_XOUT_H = 0x43  # Inicio dos dados do giroscopio
MPU6050_WHO_AM_I = 0x75     # Registrador de identificacao

# ============================================================================
# PINOS RESERVADOS - NAO USAR
# ============================================================================
"""
GPIO 0  - Boot (pull-up necessario para boot normal)
GPIO 1  - TX0 (UART0 - Serial monitor)
GPIO 2  - Boot (deve estar LOW no boot)
GPIO 3  - RX0 (UART0 - Serial monitor) 
GPIO 6  - Flash SPI (reservado)
GPIO 7  - Flash SPI (reservado)
GPIO 8  - Flash SPI (reservado)
GPIO 9  - Flash SPI (reservado)
GPIO 10 - Flash SPI (reservado)
GPIO 11 - Flash SPI (reservado)
GPIO 12 - Boot (deve estar LOW no boot)
GPIO 15 - Boot (pull-up necessario)
GPIO 16 - Nao disponivel em alguns modulos
GPIO 17 - Nao disponivel em alguns modulos
"""

# ============================================================================
# PINOS DISPONIVEIS PARA EXPANSAO
# ============================================================================
"""
GPIO 2  - Disponivel (cuidado no boot)
GPIO 4  - Disponivel
GPIO 12 - Disponivel (cuidado no boot)
GPIO 13 - Disponivel
GPIO 32 - Disponivel
GPIO 33 - Disponivel  
GPIO 34 - Apenas entrada (sem pull-up interno)
GPIO 35 - Apenas entrada (sem pull-up interno)
GPIO 36 - Apenas entrada (sem pull-up interno)
GPIO 39 - Apenas entrada (sem pull-up interno)
"""

# ============================================================================
# FUNCOES DE UTILIDADE
# ============================================================================

def validate_pin_assignment():
    """Valida se nao ha conflitos na atribuicao de pinos."""
    used_pins = [
        SERVO_FLAPS_LEFT, SERVO_FLAPS_RIGHT, SERVO_ELEVATOR, 
        SERVO_RUDDER, SERVO_RELEASE,
        LED_SYSTEM_ACTIVE, LED_ALERT, LED_RELEASE,
        I2C_SDA, I2C_SCL, RC_RELEASE_CHANNEL, BUTTON_POWER
    ]
    
    # Verificar pinos duplicados
    if len(used_pins) != len(set(used_pins)):
        raise ValueError("ERRO: Pinos duplicados detectados!")
    
    # Verificar pinos reservados
    reserved_pins = [0, 1, 3, 6, 7, 8, 9, 10, 11]
    conflicts = set(used_pins) & set(reserved_pins)
    if conflicts:
        raise ValueError(f"ERRO: Pinos reservados em uso: {conflicts}")
    
    return True

def get_pin_map():
    """Retorna um dicionario com todos os pinos utilizados."""
    return {
        'servos': {
            'flaps_left': SERVO_FLAPS_LEFT,
            'flaps_right': SERVO_FLAPS_RIGHT,
            'elevator': SERVO_ELEVATOR,
            'rudder': SERVO_RUDDER,
            'release': SERVO_RELEASE
        },
        'leds': {
            'system_active': LED_SYSTEM_ACTIVE,
            'alert': LED_ALERT,
            'release': LED_RELEASE
        },
        'i2c': {
            'sda': I2C_SDA,
            'scl': I2C_SCL
        },
        'rc': {
            'release_channel': RC_RELEASE_CHANNEL
        },
        'buttons': {
            'power': BUTTON_POWER
        }
    }

def print_pin_summary():
    """Imprime um resumo dos pinos utilizados."""
    pin_map = get_pin_map()
    
    print("=== RESUMO DE PINOS ESP32 ===")
    print(f"Servos:")
    for name, pin in pin_map['servos'].items():
        print(f"  {name:12} -> GPIO {pin}")
    
    print(f"LEDs:")
    for name, pin in pin_map['leds'].items():
        print(f"  {name:12} -> GPIO {pin}")
    
    print(f"I2C:")
    for name, pin in pin_map['i2c'].items():
        print(f"  {name:12} -> GPIO {pin}")
    
    print(f"RC:")
    for name, pin in pin_map['rc'].items():
        print(f"  {name:12} -> GPIO {pin}")
    
    print(f"Botoes:")
    for name, pin in pin_map['buttons'].items():
        print(f"  {name:12} -> GPIO {pin}")

if __name__ == "__main__":
    # Executar validacao quando o arquivo for importado
    try:
        validate_pin_assignment()
        print("✓ Configuracao de pinos validada com sucesso!")
        print_pin_summary()
    except ValueError as e:
        print(f"✗ Erro na configuracao de pinos: {e}")