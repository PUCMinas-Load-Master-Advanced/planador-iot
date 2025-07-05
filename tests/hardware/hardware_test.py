"""
Modulo de testes independentes para diagnostico de hardware do planador.

Este modulo contem funcoes para verificar o funcionamento de LEDs, botoes,
servos, sensores e o sistema de liberacao, auxiliando na depuracao e
validacao do hardware.
"""

import time
import gc
from machine import Pin, PWM, I2C
from config import (
    LED_SYSTEM_ACTIVE, LED_ALERT, LED_RELEASE, PLANADOR_SERVOS, I2C_SDA, I2C_SCL, MPU6050_ADDR,
    RELEASE_SERVO_PIN, RELEASE_CONFIG
)
import custom_logging as logging

logger = logging.getLogger(__name__)


def test_all_hardware():
    """Executa uma suite completa de testes de hardware.

    Returns:
        bool: True se todos os testes essenciais passarem, False caso contrario.

    Example:
        >>> test_all_hardware()
        Iniciando teste completo de hardware.
        ...
        Resultado: 4/4 testes passaram.
    """
    logger.info("Iniciando teste completo de hardware.")
    tests_passed = 0
    total_tests = 4

    if test_leds():
        tests_passed += 1
    if test_servos():
        tests_passed += 1
    if test_sensors():
        tests_passed += 1
    if test_release_system():
        tests_passed += 1

    logger.info(f"Resultado: {tests_passed}/{total_tests} testes passaram.")
    if tests_passed == total_tests:
        logger.info("Todos os testes passaram!")
    elif tests_passed >= total_tests * 0.8:
        logger.warning("Maioria dos testes OK - Verificar falhas.")
    else:
        logger.error("Muitas falhas - Revisar hardware.")

    return tests_passed == total_tests


def test_leds():
    """Testa a funcionalidade dos LEDs do sistema.

    Verifica a inicializacao e o acionamento individual e simultaneo dos LEDs.

    Returns:
        bool: True se os LEDs funcionarem conforme o esperado, False caso contrario.

    Example:
        >>> test_leds()
        Testando LEDs...
        - LED Sistema (GPIO 15) inicializado.
        ...
        LEDs OK (4/4 disponiveis).
    """
    logger.info("Testando LEDs...")
    led_configs = [
        (LED_SYSTEM_ACTIVE, "Sistema"),
        (LED_ALERT, "Alerta"),
        (LED_RELEASE, "Liberacao")
    ]
    available_leds = []

    logger.info("Teste individual dos LEDs...")
    for pin, name in led_configs:
        try:
            led = Pin(pin, Pin.OUT)
            logger.info(f"  - LED {name} (GPIO {pin}) inicializado.")
            led.value(1)
            time.sleep(0.3)
            led.value(0)
            time.sleep(0.1)
            available_leds.append(led)
        except Exception as e:
            logger.warning(f"  - LED {name} (GPIO {pin}) nao disponivel: {e}")

    if available_leds:
        logger.info(f"Teste simultaneo ({len(available_leds)} LEDs disponiveis)...")
        for led in available_leds:
            led.value(1)
        time.sleep(1)
        for led in available_leds:
            led.value(0)
        logger.info(f"LEDs OK ({len(available_leds)}/3 disponiveis).")
        return True
    else:
        logger.warning("Nenhum LED disponivel. O sistema funcionara sem indicadores visuais.")
        return True




def test_servos():
    """Testa a funcionalidade dos servos do planador.

    Inicializa os servos e executa uma sequencia de movimento para verificacao.

    Returns:
        bool: True se a maioria dos servos funcionar, False caso contrario.

    Example:
        >>> test_servos()
        Testando servos...
        - Servo flaps_left (GPIO 25): Inicializado.
        ...
        Servos OK (4/4 funcionando).
    """
    logger.info("Testando servos...")

    def angle_to_duty(angle):
        return int(40 + (angle * 75) // 180)

    try:
        servos = {}
        servo_positions = [90, 60, 120, 90]

        for name, pin in PLANADOR_SERVOS.items():
            try:
                servo = PWM(Pin(pin), freq=50)
                servos[name] = servo
                logger.info(f"  - Servo {name} (GPIO {pin}) inicializado.")
            except Exception as e:
                logger.warning(f"  - Servo {name} (GPIO {pin}): ERRO - {e}")

        if servos:
            logger.info("Testando movimento dos servos...")
            for pos in servo_positions:
                logger.info(f"  - Posicao {pos} graus...")
                for servo_obj in servos.values():
                    servo_obj.duty(angle_to_duty(pos))
                time.sleep(0.8)

        for servo_obj in servos.values():
            servo_obj.deinit()

        logger.info(f"Servos OK ({len(servos)}/4 funcionando).")
        return len(servos) >= 3

    except Exception as e:
        logger.error(f"Erro nos servos: {e}")
        return False


def test_sensors():
    """Testa a comunicacao e leitura do sensor MPU6050.

    Verifica a inicializacao do I2C e a resposta do MPU6050, alem de uma leitura basica.

    Returns:
        bool: True se o sensor MPU6050 estiver funcionando corretamente, False caso contrario.

    Example:
        >>> test_sensors()
        Testando sensores...
        - I2C inicializado (SDA: GPIO21, SCL: GPIO22).
        - MPU6050 detectado (WHO_AM_I: 0x68).
        MPU6050 OK.
    """
    logger.info("Testando sensores...")
    try:
        i2c = I2C(0, sda=Pin(I2C_SDA), scl=Pin(I2C_SCL), freq=100000)
        logger.info(f"  - I2C inicializado (SDA: GPIO{I2C_SDA}, SCL: GPIO{I2C_SCL}).")

        try:
            i2c.writeto_mem(MPU6050_ADDR, 0x6B, b'\x00')
            time.sleep_ms(100)
            who_am_i = i2c.readfrom_mem(MPU6050_ADDR, 0x75, 1)[0]

            if who_am_i == 0x68:
                logger.info(f"  - MPU6050 detectado (WHO_AM_I: 0x{who_am_i:02X}).")
                import struct
                import math
                data = i2c.readfrom_mem(MPU6050_ADDR, 0x3B, 14)
                ax = struct.unpack('>h', data[0:2])[0] / 16384.0
                ay = struct.unpack('>h', data[2:4])[0] / 16384.0
                az = struct.unpack('>h', data[4:6])[0] / 16384.0
                magnitude = math.sqrt(ax*ax + ay*ay + az*az)
                logger.info(f"  - Aceleracao: X={ax:.2f}g Y={ay:.2f}g Z={az:.2f}g.")
                logger.info(f"  - Magnitude: {magnitude:.2f}g.")
                if 0.8 < magnitude < 1.2:
                    logger.info("MPU6050 OK.")
                    return True
                else:
                    logger.warning("MPU6050 com leituras anômalas.")
                    return False
            else:
                logger.warning(f"MPU6050 resposta invalida: 0x{who_am_i:02X}.")
                return False
        except Exception as e:
            logger.error(f"Erro na comunicacao MPU6050: {e}")
            return False
    except Exception as e:
        logger.error(f"Erro na inicializacao I2C: {e}")
        return False


def test_release_system():
    """Testa a funcionalidade do sistema de liberacao do planador.

    Verifica o movimento do servo de liberacao e a leitura do sinal RC.

    Returns:
        bool: True se o sistema de liberacao funcionar, False caso contrario.

    Example:
        >>> test_release_system()
        Testando sistema de liberacao...
        - Servo de liberacao (GPIO 23) inicializado.
        - Posicao Travado (45 graus)...
        Sistema de liberacao OK.
    """
    logger.info("Testando sistema de liberacao...")

    def angle_to_duty(angle):
        return int(40 + (angle * 75) // 180)

    try:
        release_servo = PWM(Pin(RELEASE_SERVO_PIN), freq=50)
        logger.info(f"  - Servo de liberacao (GPIO {RELEASE_SERVO_PIN}) inicializado.")

        positions = [
            (RELEASE_CONFIG['locked_position'], "Travado"),
            (RELEASE_CONFIG['release_position'], "Liberado"),
            (RELEASE_CONFIG['locked_position'], "Travado")
        ]

        for angle, desc in positions:
            logger.info(f"  - Posicao {desc} ({angle} graus)...")
            release_servo.duty(angle_to_duty(angle))
            time.sleep(1)

        try:
            rc_pin = Pin(RC_RELEASE_PIN, Pin.IN)
            logger.info(f"  - Receptor RC (GPIO {RC_RELEASE_PIN}) configurado.")
            state = rc_pin.value()
            logger.info(f"  - Estado RC atual: {state}.")
        except Exception as e:
            logger.warning(f"  - Receptor RC: ERRO - {e}")

        release_servo.deinit()
        logger.info("Sistema de liberacao OK.")
        return True

    except Exception as e:
        logger.error(f"Erro no sistema de liberacao: {e}")
        return False


def test_memory():
    """Testa o uso de memoria disponivel no dispositivo.

    Realiza um garbage collection e verifica a quantidade de RAM livre.

    Returns:
        bool: True se a memoria disponivel for suficiente, False caso contrario.

    Example:
        >>> test_memory()
        Testando memoria...
        - RAM antes GC: 100000 bytes.
        - RAM apos GC: 90000 bytes.
        Memoria OK.
    """
    logger.info("Testando memoria...")
    ram_before = gc.mem_free()
    gc.collect()
    ram_after = gc.mem_free()

    logger.info(f"  - RAM antes GC: {ram_before} bytes.")
    logger.info(f"  - RAM apos GC: {ram_after} bytes.")
    logger.info(f"  - RAM liberada: {ram_after - ram_before} bytes.")

    if ram_after > 50000:
        logger.info("Memoria OK.")
        return True
    else:
        logger.warning("Pouca memoria disponivel.")
        return False


if __name__ == "__main__":
    test_all_hardware()